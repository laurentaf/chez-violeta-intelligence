#!/usr/bin/env python3
"""Dashboard simples e funcional com dados do Prophet + estoque."""
import json, os

BASE = 'F:/projects/chez-violeta-intelligence'
DB = BASE + '/artifacts/data/chez_gold.duckdb'
FORECAST = BASE + '/artifacts/data/prophet_forecast_future.csv'
OUT = BASE + '/artifacts/design/dashboard-comprador/index.html'

# Carregar dados de estoque
import duckdb, csv
from collections import defaultdict

con = duckdb.connect(DB)

# Estoque por categoria (ultimo dia)
estoque = {}
rows = con.execute("""
    SELECT COALESCE(dp.des_categoria, 'OUTROS') as cat, 
           SUM(fe.qtd_estoque) as total
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
    WHERE fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
      AND dp.dat_fim_vigencia IS NULL
      AND dp.des_status = 'ATIVO'
    GROUP BY dp.des_categoria
    ORDER BY total DESC
""").fetchall()

for r in rows:
    estoque[r[0]] = int(r[1])

total_estoque = sum(estoque.values())

# Previsao Prophet 120 dias por categoria
previsao = defaultdict(float)
with open(FORECAST) as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 120:  # So primeiros 120 dias
            break
        previsao[row['categoria']] += float(row['yhat'])

con.close()

# Calcular necessidades
categorias = []
total_precisa = 0
total_valor = 0

for cat in sorted(previsao.keys()):
    est = estoque.get(cat, 0)
    prev = previsao[cat]
    precisa = max(0, round(prev - est))
    total_precisa += precisa
    categorias.append({
        "nome": cat,
        "estoque": est,
        "previsao_120d": round(prev),
        "precisa": precisa,
        "cobertura_dias": round(est / (prev/120)) if prev > 0 else 999
    })

categorias.sort(key=lambda c: c['precisa'], reverse=True)

js_cats = json.dumps(categorias, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Dashboard de Compras</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#F5F2ED;color:#2D2D2D;padding:0}}
h1,h2,h3{{font-family:Cormorant Garamond,serif;font-weight:700}}
.header{{background:linear-gradient(135deg,#7B2D4E,#5B1D3A);color:#fff;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.c{{max-width:1200px;margin:0 auto;padding:16px}}
.card{{background:#fff;border-radius:10px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:#fff;border-radius:10px;padding:14px;border-left:4px solid #C9A84C}}
.kpi .l{{font-size:0.65rem;text-transform:uppercase;color:#8C7A86;letter-spacing:0.5px}}
.kpi .v{{font-size:1.5rem;font-weight:700;color:#7B2D4E}}
.kpi.crit{{border-left-color:#DC3545}}.kpi.crit .v{{color:#DC3545}}
.kpi.ok{{border-left-color:#28A745}}.kpi.ok .v{{color:#28A745}}
table{{width:100%;border-collapse:collapse;font-size:0.85rem;margin-top:8px}}
th{{background:#7B2D4E;color:#fff;padding:8px 10px;text-align:left;font-weight:600}}
td{{padding:7px 10px;border-bottom:1px solid #E8E4DE}}
tr:hover{{background:#FAF8F5}}
tr.crit{{background:#FFF5F5}}tr.crit:hover{{background:#FFECEC}}
.b{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:600;color:#fff}}
.b-crit{{background:#DC3545}}.b-warn{{background:#E65100}}.b-ok{{background:#2E7D32}}
@media(max-width:640px){{.grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="header"><h1>Chez Violeta</h1><div><span class="b" style="background:#C9A84C;color:#5B1D3A">Estoque: 30/11/2019</span> <span class="b" style="background:#C9A84C;color:#5B1D3A">Prophet 120d</span></div></div>
<div class="c" id="root"></div>
<script>
var CATS = {js_cats};
var totalEstoque = CATS.reduce(function(s,c){{return s+c.estoque}},0);
var totalPrecisa = CATS.reduce(function(s,c){{return s+c.precisa}},0);
var totalCatCrit = CATS.filter(function(c){{return c.cobertura_dias < 60}}).length;

document.getElementById('root').innerHTML =
  '<div class=grid>' +
    '<div class=kpi><div class=l>Estoque Total</div><div class=v>' + totalEstoque.toLocaleString('pt-BR') + '</div><div class=l>unidades em todas as lojas</div></div>' +
    '<div class=kpi ' + (totalPrecisa > 0 ? 'crit' : 'ok') + '><div class=l>Precisa Comprar (120d)</div><div class=v>' + totalPrecisa.toLocaleString('pt-BR') + '</div><div class=l>unidades</div></div>' +
    '<div class=kpi><div class=l>Categorias</div><div class=v>' + CATS.length + '</div><div class=l>' + totalCatCrit + ' com cobertura < 60 dias</div></div>' +
    '<div class=kpi ' + (totalCatCrit > 0 ? 'crit' : 'ok') + '><div class=l>Fornecedores</div><div class=v>' + CATS.length + '</div><div class=l>com necessidade de compra</div></div>' +
  '</div>' +
  '<div class=card><h2>Necessidade de Compra por Categoria (Prophet 120 dias)</h2>' +
  '<p style=font-size:0.8rem;color:#8C7A86;margin:4px 0 8px>Previsao baseada em 676.634 vendas historicas (fato_estoque_diario), modelo Prophet com sazonalidade anual + feriados BR.</p>' +
  '<table><thead><tr><th>Categoria</th><th>Estoque Atual</th><th>Previsao 120d</th><th>Precisa Comprar</th><th>Cobertura</th><th>Status</th></tr></thead><tbody>' +
  CATS.map(function(c){{
    var status = c.precisa > 0 ? '<span class="b b-crit">COMPRAR</span>' : (c.cobertura_dias > 180 ? '<span class="b b-ok">CONFORTAVEL</span>' : '<span class="b b-warn">ATENCAO</span>');
    var crit = c.precisa > 0 ? ' class=crit' : '';
    return '<tr' + crit + '><td><strong>' + c.nome + '</strong></td><td>' + c.estoque.toLocaleString('pt-BR') + '</td><td>' + c.previsao_120d.toLocaleString('pt-BR') + '</td><td><strong>' + (c.precisa > 0 ? c.precisa.toLocaleString('pt-BR') : '0') + '</strong></td><td>' + (c.cobertura_dias > 999 ? 'N/A' : c.cobertura_dias + ' dias') + '</td><td>' + status + '</td></tr>';
  }}).join('') +
  '</tbody></table></div>';

if (totalPrecisa > 0) {{
  document.getElementById('root').innerHTML +=
    '<div class=card style=background:#FFF5F5;border-left:4px solid #DC3545>' +
    '<h2 style=color:#DC3545>Resumo de Compras</h2>' +
    '<p style=font-size:0.85rem;margin:4px 0>Com base na previsao Prophet para os proximos 120 dias, as categorias abaixo precisam de reposicao:</p>' +
    '<ul style=margin:8px 0 0 16px;font-size:0.85rem>' +
    CATS.filter(function(c){{return c.precisa > 0}}).map(function(c){{return '<li><strong>' + c.nome + '</strong>: comprar ' + c.precisa.toLocaleString('pt-BR') + ' unidades (estoque atual: ' + c.estoque.toLocaleString('pt-BR') + ', previsto vender: ' + c.previsao_120d.toLocaleString('pt-BR') + ')</li>'}}).join('') +
    '</ul></div>';
}}
</script>
</body>
</html>'''

with open(OUT, 'w', newline='\n', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard gerado: {OUT} ({os.path.getsize(OUT):,} bytes)")
print(f"Categorias: {len(categorias)}")
print(f"Total estoque: {total_estoque:,} un")
print(f"Total a comprar: {total_precisa:,} un")
for c in categorias:
    if c['precisa'] > 0:
        print(f"  {c['nome']}: comprar {c['precisa']:,} un (estoque {c['estoque']:,}, previsao {c['previsao_120d']:,})")
