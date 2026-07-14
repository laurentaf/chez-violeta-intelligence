#!/usr/bin/env python3
"""Dashboard funcional com previsao 120d por categoria."""
import json, os, csv, duckdb
from collections import defaultdict

BASE = 'F:/projects/chez-violeta-intelligence'
DB = BASE + '/artifacts/data/chez_gold.duckdb'
FCST = BASE + '/artifacts/data/prophet_forecast_future.csv'
OUT = BASE + '/artifacts/design/dashboard-comprador/index.html'

# Estoque por categoria
con = duckdb.connect(DB)
estoque = {}
for r in con.execute("""
    SELECT COALESCE(dp.des_categoria, 'OUTROS'), SUM(fe.qtd_estoque)
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
    WHERE fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
      AND dp.dat_fim_vigencia IS NULL AND dp.des_status = 'ATIVO'
    GROUP BY dp.des_categoria ORDER BY SUM(fe.qtd_estoque) DESC
""").fetchall():
    estoque[r[0]] = int(r[1])

total_estoque = sum(estoque.values())

# Previsao Prophet: 120 dias por categoria
prev = defaultdict(float)
cat_days = defaultdict(int)
with open(FCST) as f:
    reader = csv.DictReader(f)
    for row in reader:
        cat = row['categoria']
        if cat_days[cat] < 120:
            prev[cat] += float(row['yhat'])
            cat_days[cat] += 1

# Calcular necessidades
cats = []
total_precisa = 0
for cat in sorted(prev.keys()):
    est = estoque.get(cat, 0)
    p = round(prev[cat])
    precisa = max(0, p - est)
    total_precisa += precisa
    cov = round(est / (p/120)) if p > 0 else 999
    cats.append({"n": cat, "e": est, "p": p, "precisa": precisa, "cov": cov})

cats.sort(key=lambda c: c['precisa'], reverse=True)

# Categorias sem previsao (usar media simples)
for cat, est in estoque.items():
    if cat not in prev:
        # Usar estoque total conhecido
        cats.append({"n": cat, "e": est, "p": 0, "precisa": 0, "cov": 999})

con.close()

# Calcular precos medios por categoria para estimativa de valor
# (valor estimado = precisa * custo_medio_da_categoria)
# Usando dados do dim_produto

js = json.dumps(cats, ensure_ascii=False)
precise_count = sum(1 for c in cats if c['precisa'] > 0)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chez Violeta - Compras</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#F5F2ED;color:#2D2D2D}}
h1,h2{{font-family:Cormorant Garamond,serif;font-weight:700}}
.hd{{background:linear-gradient(135deg,#7B2D4E,#5B1D3A);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}}
.c{{max-width:1100px;margin:0 auto;padding:14px}}
.card{{background:#fff;border-radius:10px;padding:16px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06)}}
.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:14px}}
.k{{background:#fff;border-radius:10px;padding:14px;border-left:4px solid #C9A84C}}
.k .l{{font-size:0.6rem;text-transform:uppercase;color:#8C7A86;letter-spacing:0.4px;margin-bottom:2px}}
.k .v{{font-size:1.4rem;font-weight:700;color:#7B2D4E}}
.k.cr{{border-left-color:#DC3545}}.k.cr .v{{color:#DC3545}}
.k.ok{{border-left-color:#28A745}}.k.ok .v{{color:#28A745}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:6px}}
th{{background:#7B2D4E;color:#fff;padding:7px 10px;text-align:left;font-weight:600;font-size:0.75rem}}
td{{padding:6px 10px;border-bottom:1px solid #E8E4DE}}
tr:hover{{background:#FAF8F5}}
tr.cr{{background:#FFF5F5}}tr.cr:hover{{background:#FFECEC}}
.b{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.65rem;font-weight:600;color:#fff}}
.b-cr{{background:#DC3545}}.b-ok{{background:#2E7D32}}.b-wa{{background:#E65100}}
.f{{font-size:0.75rem;color:#8C7A86;margin:4px 0 8px}}
@media(max-width:640px){{.g{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class=hd><h1>Chez Violeta</h1><div style=font-size:0.8rem>Estoque: 30/11/2019 | Prophet 120d | 676.634 vendas historicas</div></div>
<div class=c id=r></div>
<script>
var D = {js};
var te = D.reduce(function(s,c){{return s+c.e}},0);
var tp = D.reduce(function(s,c){{return s+c.precisa}},0);
var nc = D.filter(function(c){{return c.precisa>0}}).length;
document.getElementById('r').innerHTML =
'<div class=g>' +
  '<div class=k><div class=l>Estoque Total</div><div class=v>' + te.toLocaleString('pt-BR') + '</div><div class=l>unidades</div></div>' +
  '<div class=k ' + (tp>0?'cr':'ok') + '><div class=l>Precisa Comprar</div><div class=v>' + tp.toLocaleString('pt-BR') + '</div><div class=l>para 120 dias de cobertura</div></div>' +
  '<div class=k><div class=l>Categorias</div><div class=v>' + D.length + '</div><div class=l>' + nc + ' precisam compra</div></div>' +
  '<div class=k ' + (nc>0?'cr':'ok') + '><div class=l>Status</div><div class=v>' + (tp>0 ? 'COMPRAR' : 'OK') + '</div><div class=l>' + (tp>0 ? 'Fazer pedidos' : 'Estoque suficiente') + '</div></div>' +
'</div>' +
'<div class=card><h2 style="margin-bottom:4px">Necessidade por Categoria</h2>' +
'<div class=f>Previsao Prophet com sazonalidade anual + feriados BR. Cobertura = estoque / (previsao_120d / 120).</div>' +
'<table><thead><tr><th>Categoria</th><th>Estoque</th><th>Previsao 120d</th><th>Precisa Comprar</th><th>Cobertura</th><th>Status</th></tr></thead><tbody>' +
D.map(function(c){{
  var s = c.precisa>0 ? '<span class=b b-cr>COMPRAR</span>' : (c.cov>180 ? '<span class=b b-ok>CONFORTAVEL</span>' : '<span class=b b-wa>ATENCAO</span>');
  return '<tr' + (c.precisa>0?' class=cr':'') + '><td><strong>' + c.n + '</strong></td><td>' + c.e.toLocaleString('pt-BR') + '</td><td>' + (c.p>0?c.p.toLocaleString('pt-BR'):'-') + '</td><td><strong>' + (c.precisa>0?c.precisa.toLocaleString('pt-BR'):'0') + '</strong></td><td>' + (c.cov>999?'N/A':c.cov+'d') + '</td><td>' + s + '</td></tr>';
}}).join('') +
'</tbody></table></div>' +

(tp>0 ?
'<div class=card style="background:#FFF5F5;border-left:4px solid #DC3545">' +
'<h2 style=color:#DC3545>Resumo de Compras</h2><ul style=margin:6px 0 0 16px;font-size:0.85rem>' +
D.filter(function(c){{return c.precisa>0}}).map(function(c){{return '<li><strong>' + c.n + '</strong>: comprar ' + c.precisa.toLocaleString('pt-BR') + ' un (estoque ' + c.e.toLocaleString('pt-BR') + ', previsao ' + c.p.toLocaleString('pt-BR') + ')</li>'}}).join('') +
'</ul></div>' : '');
</script>
</body>
</html>'''

with open(OUT, 'w', newline='\n', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard: {os.path.getsize(OUT):,} bytes")
print(f"Categorias: {len(cats)} | Precisa comprar: {total_precisa:,} un | {precise_count} categorias")
for c in cats:
    if c['precisa'] > 0:
        print(f"  {c['n']}: comprar {c['precisa']:,} un (est {c['e']:,}, prev {c['p']:,})")
