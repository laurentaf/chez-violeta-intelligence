#!/usr/bin/env python3
"""
Simple dashboard generator - reads data.json and creates a working HTML.
Uses only ASCII-safe chars and var (not const) for maximum compatibility.
"""
import json, os

BASE = "F:/projects/chez-violeta-intelligence"

with open(BASE + "/artifacts/design/dashboard-comprador/data.json", encoding="utf-8") as f:
    DATA = json.load(f)

ALERTS = DATA["alerts"]
SUPPLIERS = DATA["suppliers"]
SUMMARY = DATA["summary"]
STOCK = DATA["stockByProduct"]

alert_ids = set(a["id"] for a in ALERTS)
stock_filtered = {pid: entries for pid, entries in STOCK.items() if pid in alert_ids}

js_a = json.dumps(ALERTS, ensure_ascii=False)
js_s = json.dumps(SUPPLIERS, ensure_ascii=False)
js_m = json.dumps(SUMMARY, ensure_ascii=False)
js_t = json.dumps(stock_filtered, ensure_ascii=False)

# Build a clean, working HTML
html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Dashboard Comprador</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root{{--v:#7B2D4E;--d:#C9A84C;--w:#FAF8F5;--text:#2D1B24;--m:#8C7A86}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:var(--w);color:var(--text)}}
h1,h2{{font-family:Cormorant Garamond,serif;font-weight:600}}
.banner{{background:#FFF3CD;color:#856404;text-align:center;font-size:0.75rem;padding:3px 0}}
.header{{background:linear-gradient(135deg,#5C1F3A,#7B2D4E);color:#fff;padding:12px 20px;display:flex;justify-content:space-between}}
h2{{color:var(--v);font-size:1.3rem;border-bottom:2px solid var(--d);padding-bottom:6px;margin:20px 0 12px}}
.container{{max-width:1400px;margin:0 auto;padding:12px 16px}}
.card{{background:#fff;border-radius:10px;padding:16px;box-shadow:0 2px 8px rgba(123,45,78,0.08);margin-bottom:16px}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
th{{background:var(--v);color:#fff;padding:8px 10px;text-align:left;font-weight:600;position:sticky;top:0}}
td{{padding:7px 10px;border-bottom:1px solid #E8E0DA}}
tr:hover{{background:#F8F4F0}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:20px;color:#fff}}
.badge-CRITICAL{{background:#DC3545}}.badge-HIGH{{background:#FD7E14}}
.badge-MEDIUM{{background:#FFC107;color:#7B5A00}}.badge-LOW{{background:#28A745}}
.wrap{{overflow-x:auto;max-height:500px;overflow-y:auto}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:#fff;border-radius:10px;padding:16px;box-shadow:0 2px 8px rgba(123,45,78,0.08);border-left:4px solid var(--d)}}
.kpi .lbl{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.5px;color:var(--m)}}
.kpi .val{{font-size:1.5rem;font-weight:700;color:var(--v)}}
.kpi .sub{{font-size:0.75rem}}
.row2{{display:grid;grid-template-columns:2fr 1fr;gap:16px}}
@media(max-width:900px){{.row2{{grid-template-columns:1fr}}}}
select{{padding:5px 8px;border:1px solid #ccc;border-radius:6px;font-family:Inter;font-size:0.85rem;margin-right:8px;margin-bottom:6px}}
.filters{{margin-bottom:12px}}
.fc{{font-size:0.8rem;color:var(--m)}}
</style>
</head>
<body>
<div class="banner">MOCK - Dados de simulacao, nao para producao (Simulacao 360d, seed=42)</div>
<div class="header"><h1>Chez Violeta - Dashboard Comprador</h1><div class="fc" id="hdr">-</div></div>
<div class="container" id="app"></div>
<script>
var SUMMARY = {js_m};
var ALERTS = {js_a};
var SUPPLIERS = {js_s};
var STOCK = {js_t};

document.getElementById('hdr').textContent = 'Ultimo dia: ' + SUMMARY.latestDate + ' | Alertas: ' + SUMMARY.totalAlerts;

var allSuppliers = [...new Set(ALERTS.map(function(a){{return a.supplier}}))].sort();
var allCats = [...new Set(ALERTS.map(function(a){{return a.cat}}))].sort();

function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}

function render() {{
  var filtered = ALERTS;
  var urg = document.getElementById('fu') ? document.getElementById('fu').value : 'all';
  var cat = document.getElementById('fc') ? document.getElementById('fc').value : 'all';
  var sup = document.getElementById('fs') ? document.getElementById('fs').value : 'all';
  if (urg !== 'all') filtered = filtered.filter(function(a){{return a.urgency === urg}});
  if (cat !== 'all') filtered = filtered.filter(function(a){{return a.cat === cat}});
  if (sup !== 'all') filtered = filtered.filter(function(a){{return a.supplier === sup}});

  var supOpt = '<option value=\"all\">Todos</option>' + allSuppliers.map(function(s){{return '<option value=\"' + esc(s) + '\">' + esc(s) + '</option>'}}).join('');
  var catOpt = '<option value=\"all\">Todas</option>' + allCats.map(function(c){{return '<option value=\"' + esc(c) + '\">' + esc(c) + '</option>'}}).join('');

  document.getElementById('app').innerHTML =
    '<div class=\"kpis\">' +
      '<div class=\"kpi\"><div class=\"lbl\">Total Alertas</div><div class=\"val\">' + SUMMARY.totalAlerts + '</div><div class=\"sub\">No periodo</div></div>' +
      '<div class=\"kpi\" style=\"border-left-color:#DC3545\"><div class=\"lbl\">Risco Alto/Critico</div><div class=\"val\">' + SUMMARY.highCritPct + '%</div><div class=\"sub\">' + SUMMARY.highCritCount + ' alertas</div></div>' +
      '<div class=\"kpi\" style=\"border-left-color:#FD7E14\"><div class=\"lbl\">Rompe Antes do Pedido</div><div class=\"val\">' + SUMMARY.willRupture + '</div><div class=\"sub\">Cobertura < prazo</div></div>' +
      '<div class=\"kpi\" style=\"border-left-color:#17A2B8\"><div class=\"lbl\">Pior Fornecedor</div><div class=\"val\">' + esc(SUMMARY.worstSupplier) + '</div><div class=\"sub\">Compliance: ' + SUMMARY.worstCompliance + '%</div></div>' +
    '</div>' +
    '<div class=\"filters\"><label>Urgencia</label><select id=\"fu\" onchange=\"render()\"><option value=\"all\">Todas</option><option value=\"CRITICAL\">CRITICAL</option><option value=\"HIGH\">HIGH</option><option value=\"MEDIUM\">MEDIUM</option><option value=\"LOW\">LOW</option></select>' +
    '<label>Categoria</label><select id=\"fc\" onchange=\"render()\">' + catOpt + '</select>' +
    '<label>Fornecedor</label><select id=\"fs\" onchange=\"render()\">' + supOpt + '</select>' +
    '<span class=\"fc\">' + filtered.length + ' alertas</span></div>' +
    '<h2>Alertas de Compra</h2><div class=\"card\" style=\"padding:0\"><div class=\"wrap\"><table><thead><tr>' +
      '<th>Produto</th><th>Codigo</th><th>Categoria</th><th>Regime</th><th>Fornecedor</th><th>Cobertura</th><th>Qtd</th><th>Urgencia</th><th>Risco</th><th>Tem Pedido?</th><th>Prev Chegada</th><th>Chega Antes?</th><th>Custo Total</th>' +
    '</tr></thead><tbody>' + filtered.map(function(a){{return '<tr>' +
      '<td>' + esc(a.name) + '</td><td>' + esc(a.code) + '</td><td>' + a.cat + '</td><td>' + a.regime + '</td><td>' + esc(a.supplier) + '</td>' +
      '<td>' + a.coverage + 'd</td><td>' + a.qty + '</td>' +
      '<td><span class=\"badge badge-' + a.urgency + '\">' + a.urgency + '</span></td>' +
      '<td><span class=\"badge badge-' + a.risk + '\">' + a.risk + '</span></td>' +
      '<td>' + (a.hasPending ? 'Sim' : 'Nao') + '</td><td>' + (a.pendingDate || '-') + '</td>' +
      '<td>' + (a.arrivesBefore === 'SIM' ? 'SIM' : 'NAO') + '</td>' +
      '<td>' + (a.totalCost > 0 ? 'R$ ' + a.totalCost.toFixed(2) : '-') + '</td>' +
    '</tr>'}}).join('') +
    '</tbody></table></div></div>';
}}

render();
</script>
</body>
</html>'''

out_path = BASE + "/artifacts/design/dashboard-comprador/index.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out_path)
print(f"Generated: {out_path} ({size:,} bytes)")
print(f"Alerts: {len(ALERTS)}, Suppliers: {len(SUPPLIERS)}")
