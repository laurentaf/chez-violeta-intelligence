#!/usr/bin/env python3
"""
Gerador do Dashboard de Pedidos v3 - BIJU/JOIAS como Compra Manual
==================================================================
Correções:
1. VESTUARIO: sempre vai pra aba vestuario, mesmo com cod_fornecedor preenchido
2. BIJU / JOIAS: tratado como Compra Manual (igual VESTUARIO), agrupado por des_produto
3. Velocidade diária: usa total de dias (632), não dias com venda
4. Custo zero: fallback para média da categoria
5. Previsão proporcional: share do SKU * previsão total da categoria (Prophet 120d)

Uso: uv run python generate.py
Saída: index.html (< 500KB)
"""

import duckdb, json, math
from collections import defaultdict

DB_PATH = "F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
OUTPUT_PATH = "F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html"

con = duckdb.connect(DB_PATH)
print("Carregando dados...")

# ── Total de dias no período (para velocidade correta) ──
TOTAL_DIAS = con.execute(
    "SELECT COUNT(DISTINCT id_data) FROM gold.fato_estoque_diario"
).fetchone()[0]
print(f"  Total dias no período: {TOTAL_DIAS}")

# ── Custo médio por categoria (fallback para custo zero) ──
custo_medio_cat = {}
for row in con.execute("""
    SELECT des_categoria, AVG(val_custo_inicial) as custo_medio
    FROM gold.dim_produto
    WHERE val_custo_inicial > 0 AND dat_fim_vigencia IS NULL
    GROUP BY des_categoria
""").fetchall():
    if row[1] is not None and row[1] > 0:
        custo_medio_cat[row[0]] = float(row[1])
# Global fallback
GLOBAL_CUSTO = sum(custo_medio_cat.values()) / len(custo_medio_cat) if custo_medio_cat else 15.0
print(f"  Custo medio global fallback: R$ {GLOBAL_CUSTO:.2f}")

# ── Previsão Prophet 120d por categoria ──
prophet_cat = {}
for row in con.execute("""
    SELECT categoria, SUM(yhat) as total_yhat
    FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv')
    WHERE ds < '2020-03-30'  -- 120 dias a partir de 2019-12-01
    GROUP BY categoria
""").fetchall():
    prophet_cat[row[0]] = float(row[1] or 0)
print(f"  Categorias com Prophet 120d: {list(prophet_cat.keys())}")

# ── Query principal: estoque + vendas por produto ──
produtos = con.execute(f"""
    WITH ultima_data AS (
        SELECT MAX(id_data) as max_id FROM gold.fato_estoque_diario
    ),
    estoque_atual AS (
        SELECT fe.id_produto, SUM(fe.qtd_estoque)::INTEGER as qtd_estoque
        FROM gold.fato_estoque_diario fe
        JOIN ultima_data u ON fe.id_data = u.max_id
        GROUP BY fe.id_produto
    ),
    vendas AS (
        SELECT fe.id_produto,
               SUM(fe.qtd_venda)::INTEGER as total_vendas
        FROM gold.fato_estoque_diario fe
        GROUP BY fe.id_produto
    )
    SELECT
        p.id_produto,
        p.des_produto,
        p.des_artigo,
        p.cod_artigo,
        p.cod_tamanho,
        COALESCE(NULLIF(p.cod_fornecedor, ''), 'SEM FORNECEDOR') as fornecedor,
        p.des_categoria,
        COALESCE(p.val_custo_inicial, 0) as val_custo,
        COALESCE(e.qtd_estoque, 0) as estoque,
        COALESCE(v.total_vendas, 0) as total_vendas
    FROM gold.dim_produto p
    LEFT JOIN estoque_atual e ON p.id_produto = e.id_produto
    LEFT JOIN vendas v ON p.id_produto = v.id_produto
    WHERE p.dat_fim_vigencia IS NULL
      AND p.des_status = 'ATIVO'
      AND (e.qtd_estoque > 0 OR e.qtd_estoque IS NOT NULL)
""").fetchdf()

print(f"  Produtos: {len(produtos)}")

# ── Calcular velocidade correta: total_vendas / TOTAL_DIAS (não dias com venda) ──
produtos['vel_diaria'] = produtos['total_vendas'] / TOTAL_DIAS

# ── Previsão proporcional por categoria usando Prophet ──
# Primeiro: calcular share de cada SKU dentro de sua categoria
produtos['vel_diaria'] = produtos['vel_diaria'].clip(lower=0.0001)  # evitar zero

# Para categorias que têm Prophet: previsão proporcional
# Primeiro: somar velocidades por categoria
cat_vel_sum = produtos.groupby('des_categoria')['vel_diaria'].sum().to_dict()

# Para BIJU / JOIAS, EROTICA, ACESSORIOS, FITNESS (sem Prophet): usar vel_diaria * 120
# Para as demais: share * prophet_total
CAT_COM_PROPHET = set(prophet_cat.keys())  # LINHA NOITE, MODA PRAIA, UNDERWARE, VESTUARIO, OUTROS

def calc_previsao(row):
    cat = row['des_categoria']
    vel = row['vel_diaria']
    stock = row['estoque']
    
    if cat in CAT_COM_PROPHET and cat in prophet_cat and prophet_cat[cat] > 0 and cat in cat_vel_sum and cat_vel_sum[cat] > 0:
        # Previsao proporcional: share do SKU * prophet_total
        share = vel / cat_vel_sum[cat]
        previsao = share * prophet_cat[cat]
    else:
        # Fallback: vel_diaria * 120 (para categorias sem Prophet)
        previsao = vel * 120
    
    precisa = max(0, previsao - stock)
    precisa_int = max(1, int(math.ceil(previsao - stock)))
    return previsao, precisa, precisa_int

prev_results = produtos.apply(lambda r: calc_previsao(r), axis=1, result_type='expand')
produtos['previsao_120d'] = prev_results[0]
produtos['precisa'] = prev_results[1]
produtos['precisa_int'] = prev_results[2]

# ── Custo: fallback para media da categoria ──
def calc_custo(row):
    cat = row['des_categoria']
    custo = row['val_custo']
    if custo is None or custo <= 0:
        if cat in custo_medio_cat:
            return custo_medio_cat[cat]
        return GLOBAL_CUSTO
    return custo

produtos['val_custo_real'] = produtos.apply(calc_custo, axis=1)
produtos['val_total'] = produtos['precisa_int'] * produtos['val_custo_real']
produtos['dias_cobertura'] = produtos.apply(
    lambda r: r['estoque'] / r['vel_diaria'] if r['vel_diaria'] > 0.0001 else 999, axis=1)

# Só o que precisa comprar
precisa = produtos[produtos['precisa_int'] > 0].copy()
print(f"  Precisa comprar: {len(precisa)} produtos")

# ── SEPARAR FORNECEDOR × COMPRA MANUAL ──
# Categorias tratadas como Compra Manual (sem fornecedor, agrupado por tipo)
CAT_MANUAL = {'VESTUARIO', 'BIJU / JOIAS'}
forn_df = precisa[~precisa['des_categoria'].isin(CAT_MANUAL)].copy()
manual_df = precisa[precisa['des_categoria'].isin(CAT_MANUAL)].copy()
vest_df = manual_df[manual_df['des_categoria'] == 'VESTUARIO'].copy()
biju_df = manual_df[manual_df['des_categoria'] == 'BIJU / JOIAS'].copy()

print(f"  Com fornecedor: {len(forn_df)}, Vestuario: {len(vest_df)}, Bijuterias: {len(biju_df)}")

# ── FORNECEDORES: agregar por fornecedor + artigo + tamanho ──
forn_agg = forn_df.groupby(['fornecedor', 'des_artigo', 'cod_tamanho']).agg({
    'estoque': 'sum', 'previsao_120d': 'sum', 'precisa_int': 'sum',
    'val_custo_real': 'mean', 'val_total': 'sum', 'dias_cobertura': 'mean',
    'des_produto': 'first', 'cod_artigo': 'first', 'id_produto': 'count'
}).reset_index()
forn_agg.rename(columns={'id_produto': 'qtd_skus', 'des_produto': 'produto_nome'}, inplace=True)
print(f"  Linhas agregadas fornecedor: {len(forn_agg)}")

# Agrupar por fornecedor
forn_groups = defaultdict(list)
for _, row in forn_agg.iterrows():
    forn_groups[row['fornecedor']].append(row.to_dict())

forn_list = []
for forn, items in forn_groups.items():
    cobertura = sum(it['dias_cobertura'] for it in items) / len(items)
    total_valor = sum(it['val_total'] for it in items)
    total_itens = sum(it['precisa_int'] for it in items)
    is_biju = any('BIJU' in str(it.get('produto_nome', '') or '').upper() or
                   str(forn).upper() in ['AMOR BIJU', 'KARISMA BIJU', 'RELUZ BIJU', 'INTER BIJU',
                                         'ENOQUE BIJU', 'MAURO BIJU']
                  for it in items)
    forn_list.append({
        'nome': forn, 'cobertura': round(cobertura, 1), 'total_itens': total_itens,
        'total_valor': round(total_valor, 2), 'qtd_produtos': len(items),
        'is_biju': is_biju,
        'items': sorted(items, key=lambda x: x['dias_cobertura'])
    })

forn_list.sort(key=lambda x: x['cobertura'])
# LIMITE: max 20 fornecedores
if len(forn_list) > 20:
    print(f"  Limitando de {len(forn_list)} para 20 fornecedores mais urgentes")
    forn_list = forn_list[:20]

# ── VESTUARIO: agregar por artigo + tamanho ──
vest_agg = vest_df.groupby(['des_artigo', 'cod_tamanho']).agg({
    'estoque': 'sum', 'previsao_120d': 'sum', 'precisa_int': 'sum',
    'id_produto': 'count'
}).reset_index()
vest_agg.rename(columns={'id_produto': 'qtd_skus'}, inplace=True)
print(f"  Linhas agregadas vestuario: {len(vest_agg)}")

# Agrupar por artigo
vest_tipos = defaultdict(list)
for _, row in vest_agg.iterrows():
    vest_tipos[row['des_artigo']].append(row.to_dict())

vest_list = []
for artigo, sizes in sorted(vest_tipos.items()):
    total_precisa = sum(s['precisa_int'] for s in sizes)
    vest_list.append({
        'artigo': artigo,
        'total_precisa': total_precisa,
        'sizes': sorted(sizes, key=lambda x: x['cod_tamanho'] or '')
    })

# LIMITE: max 30 tipos mais urgentes
vest_list.sort(key=lambda x: x['total_precisa'], reverse=True)
if len(vest_list) > 30:
    print(f"  Limitando de {len(vest_list)} para 30 tipos mais urgentes")
    vest_list = vest_list[:30]

# ── BIJU / JOIAS: agregar por tipo de produto (des_produto) + tamanho ──
biju_agg = biju_df.groupby(['des_produto', 'cod_tamanho', 'cod_artigo']).agg({
    'estoque': 'sum', 'previsao_120d': 'sum', 'precisa_int': 'sum',
    'id_produto': 'count'
}).reset_index()
biju_agg.rename(columns={'id_produto': 'qtd_skus'}, inplace=True)
print(f"  Linhas agregadas bijuterias: {len(biju_agg)}")

# Agrupar por tipo de produto (ANEL, BRINCO, COLAR, etc.)
biju_tipos = defaultdict(list)
for _, row in biju_agg.iterrows():
    biju_tipos[row['des_produto']].append(row.to_dict())

biju_list = []
for tipo, sizes in sorted(biju_tipos.items()):
    total_precisa = sum(s['precisa_int'] for s in sizes)
    biju_list.append({
        'tipo': tipo,
        'total_precisa': total_precisa,
        'items': sorted(sizes, key=lambda x: x['cod_tamanho'] or '')
    })

# LIMITE: max 20 tipos mais urgentes
biju_list.sort(key=lambda x: x['total_precisa'], reverse=True)
if len(biju_list) > 20:
    print(f"  Limitando de {len(biju_list)} para 20 tipos mais urgentes")
    biju_list = biju_list[:20]

# ── OVERVIEW ──
# Calcular valor total do vestuario com custo real
val_vest_total = float(vest_df['val_total'].sum()) if len(vest_df) > 0 else 0
qtd_vest_prod = int(vest_agg['precisa_int'].sum()) if len(vest_agg) > 0 else 0
# Valor total biju
val_biju_total = float(biju_df['val_total'].sum()) if len(biju_df) > 0 else 0
qtd_biju_prod = int(biju_agg['precisa_int'].sum()) if len(biju_agg) > 0 else 0

# Valor total da compra manual
val_manual_total = val_vest_total + val_biju_total
qtd_manual_prod = qtd_vest_prod + qtd_biju_prod
qtd_manual_tipos = len(vest_list) + len(biju_list)

overview = {
    'data_ref': '2019-11-30', 'dias': TOTAL_DIAS,
    'qtd_forn': len(forn_list),
    'qtd_forn_prod': int(forn_agg['precisa_int'].sum()) if len(forn_agg) > 0 else 0,
    'val_forn': round(sum(f['total_valor'] for f in forn_list), 2),
    'qtd_vest': len(vest_list),
    'qtd_vest_prod': qtd_vest_prod,
    'val_vest': round(val_vest_total, 2),
    'qtd_biju': len(biju_list),
    'qtd_biju_prod': qtd_biju_prod,
    'val_biju': round(val_biju_total, 2),
    'qtd_manual': qtd_manual_tipos,
    'qtd_manual_prod': qtd_manual_prod,
    'val_manual': round(val_manual_total, 2)
}

# ── GERAR HTML ──
print("Gerando HTML...")

def j(v):
    if v is None: return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        if math.isnan(v) or math.isinf(v): return '0'
        return str(v)
    return json.dumps(str(v))

# Fornecedores JS
f_js = []
for f in forn_list:
    its = ','.join(
        '{p:' + j(it.get('produto_nome','') or it.get('des_artigo','')) +
        ',a:' + j(it.get('cod_artigo','')) +
        ',t:' + j(it.get('cod_tamanho','')) +
        ',e:' + str(int(it['estoque'])) +
        ',v:' + str(int(round(it['previsao_120d']))) +
        ',c:' + str(it['precisa_int']) +
        ',cu:' + j(round(it['val_custo_real'],2)) +
        ',vt:' + j(round(it['val_total'],2)) +
        ',d:' + j(round(it['dias_cobertura'],1)) +
        '}'
        for it in f['items']
    )
    f_js.append(
        '{n:' + j(f['nome']) +
        ',c:' + j(f['cobertura']) +
        ',ti:' + str(f['total_itens']) +
        ',tv:' + j(f['total_valor']) +
        ',qp:' + str(f['qtd_produtos']) +
        ',b:' + j(f['is_biju']) +
        ',i:[' + its + ']}'
    )

# Vestuario JS
v_js = []
for v in vest_list:
    ss = ','.join(
        '{t:' + j(s['cod_tamanho']) +
        ',e:' + str(int(s['estoque'])) +
        ',v:' + str(int(round(s['previsao_120d']))) +
        ',c:' + str(s['precisa_int']) +
        '}'
        for s in v['sizes']
    )
    v_js.append('{a:' + j(v['artigo']) + ',tp:' + str(v['total_precisa']) + ',s:[' + ss + ']}')

# Bijuterias JS
b_js = []
for b in biju_list:
    its = ','.join(
        '{a:' + j(it.get('cod_artigo','')) +
        ',t:' + j(it.get('cod_tamanho','')) +
        ',e:' + str(int(it['estoque'])) +
        ',v:' + str(int(round(it['previsao_120d']))) +
        ',c:' + str(it['precisa_int']) +
        '}'
        for it in b['items']
    )
    b_js.append('{t:' + j(b['tipo']) + ',tp:' + str(b['total_precisa']) + ',i:[' + its + ']}')

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dashboard do Comprador - Chez Violeta</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#1a1a1a;color:#e0d5c8;font-size:14px}}
.banner{{background:#FFF3CD;color:#856404;text-align:center;font-size:0.7rem;padding:2px 0;font-family:sans-serif}}
.hdr{{background:linear-gradient(135deg,#2c1810,#4a1a10,#2c1810);border-bottom:3px solid #c9a84c;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}}
.hdr h1{{color:#c9a84c;font-size:1.3em;font-weight:300;letter-spacing:2px}}
.hdr .sub{{color:#a08060;font-size:.82em}}
.tabs{{display:flex;background:#2c1810;border-bottom:1px solid #3d2a18}}
.tab{{padding:10px 22px;cursor:pointer;color:#a08060;font-size:.88em;border-bottom:3px solid transparent;transition:all .15s}}
.tab:hover{{color:#e0d5c8;background:#3d2a18}}
.tab.act{{color:#c9a84c;border-bottom-color:#c9a84c;background:#2c1810}}
.bdg{{display:inline-block;background:#c9a84c;color:#1a1a1a;border-radius:10px;padding:1px 7px;font-size:.72em;margin-left:5px;font-weight:700}}
.cont{{display:none;padding:16px}}
.cont.act{{display:block}}
.ov{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:18px}}
.ovc{{background:#2c1810;border-radius:8px;padding:14px;border:1px solid #3d2a18;text-align:center}}
.ovc .vl{{font-size:1.5em;color:#c9a84c;font-weight:700}}
.ovc .lb{{font-size:.73em;color:#a08060;margin-top:3px;text-transform:uppercase;letter-spacing:1px}}
.sc{{background:#2c1810;border-radius:8px;margin-bottom:10px;border:1px solid #3d2a18;overflow:hidden}}
.sh{{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;cursor:pointer;transition:background .12s;gap:10px;flex-wrap:wrap}}
.sh:hover{{background:#3d2a18}}
.sh .nm{{font-size:1em;color:#e0d5c8;font-weight:600}}
.sh .nm .bj{{display:inline-block;background:#6b3a2a;color:#c9a84c;font-size:.58em;padding:1px 5px;border-radius:3px;margin-left:6px;vertical-align:middle;text-transform:uppercase;letter-spacing:1px}}
.sh .st{{display:flex;gap:16px;font-size:.84em;align-items:center}}
.sh .st>div{{text-align:right}}
.sh .st .n{{color:#c9a84c;font-weight:600;white-space:nowrap}}
.sh .st .l{{color:#a08060;font-size:.78em}}
.urg{{padding:3px 8px;border-radius:4px;font-size:.78em;font-weight:600;white-space:nowrap}}
.u-h{{background:#5c1a1a;color:#ff6b6b}}
.u-m{{background:#5c4a1a;color:#ffd93d}}
.u-l{{background:#1a3d2a;color:#6bcf7f}}
.sb{{display:none;padding:0 16px 12px;overflow-x:auto}}
.sb.o{{display:block}}
table{{width:100%;border-collapse:collapse;font-size:.8em;min-width:500px}}
th{{text-align:left;padding:6px 5px;border-bottom:1px solid #3d2a18;color:#a08060;text-transform:uppercase;letter-spacing:.4px;font-weight:600;font-size:.76em;white-space:nowrap}}
td{{padding:5px;border-bottom:1px solid #2a1a0a;white-space:nowrap}}
tr:hover td{{background:#2a1810}}
.nr{{text-align:right}}
.ph{{color:#ff6b6b;font-weight:700}}
.pm{{color:#ffd93b;font-weight:600}}
.vg{{margin-bottom:14px}}
.vg h3{{color:#c9a84c;font-size:.92em;margin-bottom:6px;border-left:3px solid #c9a84c;padding-left:10px}}
.vp{{background:#3d1a1a}}
.vp td:first-child{{color:#ff6b6b;font-weight:600}}
.em{{text-align:center;padding:30px;color:#a08060}}
.shb{{margin:18px 0 10px;padding:8px 14px;background:#1a2a1a;border-left:3px solid #6bcf7f;color:#a0d5a0;font-size:.78em;border-radius:0 6px 6px 0}}
.shb h4{{color:#c9a84c;font-size:.88em;margin-bottom:4px}}
.bc{{background:#6b3a2a;color:#c9a84c;font-size:.65em;padding:2px 6px;border-radius:3px;margin-left:6px;vertical-align:middle;text-transform:uppercase;letter-spacing:1px}}
@media(max-width:768px){{.sh .st{{gap:8px}}.ov{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="banner">MOCK - Dashboard do Comprador (v3: BIJU/JOIAS como Compra Manual)</div>
<div class="hdr"><div><h1>CHEZ VIOLETA</h1><div class="sub">Dashboard do Comprador</div></div><div class="sub">Base: {overview['data_ref']} &middot; {overview['dias']} dias</div></div>
<div class="tabs">
<div class="tab act" onclick="gt('forn',this)">Pedidos por Fornecedor <span class="bdg" id="bf">{overview['qtd_forn']}</span></div>
<div class="tab" onclick="gt('manual',this)">Compra Manual <span class="bdg" id="bm">{overview['qtd_manual']}</span></div>
</div>
<div id="tab-forn" class="cont act"><div class="ov" id="ovf"></div><div id="fl"></div></div>
<div id="tab-manual" class="cont"><div class="ov" id="ovm"></div><div id="vl"></div><div id="bl"></div></div>
<script>
var O={{dr:'{overview['data_ref']}',da:{overview['dias']},qf:{overview['qtd_forn']},qfp:{overview['qtd_forn_prod']},vf:{overview['val_forn']},qv:{overview['qtd_vest']},qvp:{overview['qtd_vest_prod']},vv:{overview['val_vest']},qb:{overview['qtd_biju']},qbp:{overview['qtd_biju_prod']},vb:{overview['val_biju']},qm:{overview['qtd_manual']},qmp:{overview['qtd_manual_prod']},vm:{overview['val_manual']}}};
var F=[{','.join(f_js)}];
var V=[{','.join(v_js)}];
var B=[{','.join(b_js)}];
function fm(n){{return n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'K':n.toFixed(0)}}
function f$(n){{return'R$ '+n.toFixed(2).replace('.',',')}}
function uc(d){{return d<=30?'u-h':d<=60?'u-m':'u-l'}}
function ul(d){{return d<=30?'URGENTE':d<=60?'ATENÇÃO':'OK'}}
function gt(t,el){{
document.querySelectorAll('.tab').forEach(e=>e.classList.remove('act'));
document.querySelectorAll('.cont').forEach(e=>e.classList.remove('act'));
el.classList.add('act');document.getElementById('tab-'+t).classList.add('act');
}}
document.getElementById('ovf').innerHTML=
'<div class="ovc"><div class="vl">'+O.qf+'</div><div class="lb">Fornecedores</div></div>'+
'<div class="ovc"><div class="vl">'+fm(O.qfp)+'</div><div class="lb">Itens a Comprar</div></div>'+
'<div class="ovc"><div class="vl">'+f$(O.vf)+'</div><div class="lb">Valor Total</div></div>';
document.getElementById('ovm').innerHTML=
'<div class="ovc"><div class="vl">'+O.qm+'</div><div class="lb">Tipos de Produto</div></div>'+
'<div class="ovc"><div class="vl">'+fm(O.qmp)+'</div><div class="lb">Itens a Comprar</div></div>'+
'<div class="ovc"><div class="vl">'+f$(O.vm)+'</div><div class="lb">Valor Total</div></div>';
var h='';
for(var i=0;i<F.length;i++){{var f=F[i],u=uc(f.c);h+=
'<div class="sc"><div class="sh" onclick="ts('+i+')"><div><span class="nm">'+f.n+(f.b?' <span class="bj">BIJU</span>':'')+'</span></div>'+
'<div class="st"><div><div class="n">'+f.qp+'</div><div class="l">Grupos</div></div>'+
'<div><div class="n">'+fm(f.ti)+'</div><div class="l">Itens</div></div>'+
'<div><div class="n">'+f$(f.tv)+'</div><div class="l">Valor</div></div>'+
'<div class="urg '+u+'">'+ul(f.c)+' ('+f.c.toFixed(0)+'d)</div></div></div>'+
'<div class="sb" id="sb'+i+'"><table><thead><tr><th>Produto</th><th>Cód</th><th>Tam</th><th class="nr">Estq</th><th class="nr">Prev120d</th><th class="nr">A Comprar</th><th class="nr">R$ Und</th><th class="nr">Total</th><th class="nr">Cob.</th></tr></thead><tbody>';
for(var j=0;j<f.i.length;j++){{var x=f.i[j],pc=x.c>10?'ph':(x.c>3?'pm':'');h+=
'<tr><td>'+(x.p||x.a||'-')+'</td><td>'+(x.a||'-')+'</td><td>'+(x.t||'-')+'</td>'+
'<td class="nr">'+Math.round(x.e)+'</td><td class="nr">'+Math.round(x.v)+'</td>'+
'<td class="nr '+pc+'">'+x.c+'</td><td class="nr">'+f$(x.cu)+'</td>'+
'<td class="nr">'+f$(x.vt)+'</td><td class="nr">'+(x.d>999?'-':x.d.toFixed(0)+'d')+'</td></tr>';
}}
h+='</tbody></table></div></div>';
}}
document.getElementById('fl').innerHTML=h;
function ts(i){{var e=document.getElementById('sb'+i);e.classList.toggle('o')}}
var vh='';
for(var i=0;i<V.length;i++){{var v=V[i];vh+=
'<div class="vg"><h3>'+v.a+'</h3><table><thead><tr><th>Tamanho</th><th class="nr">Estoque</th><th class="nr">Prev120d</th><th class="nr">A Comprar</th></tr></thead><tbody>';
for(var j=0;j<v.s.length;j++){{var s=v.s[j];vh+=
'<tr'+(s.c>0?' class="vp"':'')+'><td>'+s.t+'</td><td class="nr">'+s.e+'</td><td class="nr">'+s.v+'</td><td class="nr">'+s.c+'</td></tr>';
}}
vh+='</tbody></table></div>';
}}
document.getElementById('vl').innerHTML=vh||'<div class="em">Nenhum produto de vestuário precisa ser comprado.</div>';
var bh='';
if(B.length>0){{bh+='<div class="shb"><h4>BIJU / JOIAS</h4>Compra Manual &mdash; sem fornecedor &mdash; agrupado por tipo de produto (ANEL, BRINCO, COLAR, etc.)</div>';
for(var i=0;i<B.length;i++){{var b=B[i];bh+=
'<div class="vg"><h3>'+b.t+' <span class="bc">BIJU</span></h3><table><thead><tr><th>Cód</th><th>Tam</th><th class="nr">Estq</th><th class="nr">Prev120d</th><th class="nr">A Comprar</th></tr></thead><tbody>';
for(var j=0;j<b.i.length;j++){{var x=b.i[j];bh+=
'<tr'+(x.c>0?' class="vp"':'')+'><td>'+(x.a||'-')+'</td><td>'+(x.t||'-')+'</td>'+
'<td class="nr">'+Math.round(x.e)+'</td><td class="nr">'+Math.round(x.v)+'</td>'+
'<td class="nr '+(x.c>10?'ph':(x.c>3?'pm':''))+'">'+x.c+'</td></tr>';
}}
bh+='</tbody></table></div>';
}}}}
document.getElementById('bl').innerHTML=bh||'<div class="em">Nenhum produto de bijuterias precisa ser comprado.</div>';
</script>
</body>
</html>
"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = len(HTML.encode('utf-8')) / 1024
print(f"\nHTML gerado: {OUTPUT_PATH}")
print(f"Tamanho: {size_kb:.1f} KB")
print(f"Fornecedores: {len(forn_list)}, Vestuario tipos: {len(vest_list)}, Bijuterias tipos: {len(biju_list)}")
print(f"Prophet categorias usadas: {list(prophet_cat.keys())}")
print(f"Custo medio categorias: {list(custo_medio_cat.keys())}")

con.close()
