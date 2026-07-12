#!/usr/bin/env python3
"""
Dashboard v3 - sorting, risco real, sem dados falsos
"""
import json, os

BASE = "F:/projects/chez-violeta-intelligence"

with open(BASE + "/artifacts/design/dashboard-comprador/data.json", encoding="utf-8") as f:
    DATA = json.load(f)

ALERTS = DATA["alerts"]
SUPPLIERS = DATA["suppliers"]
SUMMARY = DATA["summary"]

total = len(ALERTS)
high_crit = sum(1 for a in ALERTS if a["risk"] in ("CRITICAL", "HIGH"))
will_rupture = sum(1 for a in ALERTS if a["arrivesBefore"] == "NAO")
will_survive = sum(1 for a in ALERTS if a["arrivesBefore"] == "SIM")
sem_info = total - will_rupture - will_survive

# Piores fornecedores (menor compliance)
sorted_sup = sorted(SUPPLIERS, key=lambda s: s["compliance"])
worst_supplier = sorted_sup[0]["name"] if sorted_sup else "-"
worst_compliance = sorted_sup[0]["compliancePct"] if sorted_sup else 0

# Contagem por urgencia
urg_counts = SUMMARY.get("urgencyCounts", {})

js_a = json.dumps(ALERTS, ensure_ascii=False)
js_s = json.dumps(SUPPLIERS, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Dashboard Comprador</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--v:#7B2D4E;--d:#C9A84C;--w:#FAF8F5;--t:#2D1B24;--m:#8C7A86;--r:#DC3545;--h:#FD7E14;--g:#28A745}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:var(--w);color:var(--t);font-size:14px}}
h1,h2{{font-family:Cormorant Garamond,serif;font-weight:600}}
.banner{{background:#FFF3CD;color:#856404;text-align:center;font-size:0.75rem;padding:3px 0}}
.top{{background:linear-gradient(135deg,#5C1F3A,#7B2D4E);color:#fff;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
h2{{color:var(--v);font-size:1.3rem;border-bottom:2px solid var(--d);padding-bottom:6px;margin:18px 0 10px}}
.c{{max-width:1440px;margin:0 auto;padding:10px 16px}}
.card{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(123,45,78,0.08);margin-bottom:14px}}
table{{width:100%;border-collapse:collapse;font-size:0.78rem}}
th{{background:var(--v);color:#fff;padding:7px 8px;text-align:left;font-weight:600;position:sticky;top:0;white-space:nowrap;cursor:pointer;user-select:none}}
th:hover{{background:#9E3F6A}}
th::after{{content:" \\2195";opacity:0.4;font-size:0.65rem;margin-left:3px}}
th.sorted-asc::after{{content:" \\2191";opacity:1}}
th.sorted-desc::after{{content:" \\2193";opacity:1}}
td{{padding:6px 8px;border-bottom:1px solid #E8E0DA;white-space:nowrap}}
tr:hover{{background:#F8F4F0}}
tr.crit{{background:#FFF5F5}}tr.crit:hover{{background:#FFECEC}}
tr.high{{background:#FFF8F0}}tr.high:hover{{background:#FFF0E0}}
tr.ok{{background:#F0FFF0}}tr.ok:hover{{background:#E0FFE0}}
.b{{display:inline-block;font-size:0.6rem;font-weight:700;padding:2px 7px;border-radius:20px;color:#fff;letter-spacing:0.3px}}
.b-CRITICAL{{background:var(--r)}}.b-HIGH{{background:var(--h)}}
.b-MEDIUM{{background:#FFC107;color:#7B5A00}}.b-LOW{{background:var(--g)}}
.wrap{{overflow-x:auto;max-height:650px;overflow-y:auto}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:14px}}
.kp{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(123,45,78,0.08);border-left:4px solid var(--d)}}
.kp .l{{font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;color:var(--m)}}
.kp .v{{font-size:1.4rem;font-weight:700;color:var(--v)}}
.kp .s{{font-size:0.7rem;color:#5C4B55}}
.kp.crit{{border-left-color:var(--r)}}.kp.warn{{border-left-color:var(--h)}}
.kp.ok{{border-left-color:var(--g)}}
.kp.crit .v{{color:var(--r)}}.kp.warn .v{{color:var(--h)}}.kp.ok .v{{color:var(--g)}}
.f{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}}
.f label{{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.3px;color:var(--m)}}
.f select{{padding:4px 8px;border:1px solid #ccc;border-radius:6px;font-family:Inter;font-size:0.8rem}}
.fc{{font-size:0.8rem;color:var(--m);background:#F0EBE6;padding:4px 10px;border-radius:20px}}
.info{{font-size:0.75rem;color:var(--m);margin:6px 0;padding:6px 10px;background:#F0EBE6;border-radius:6px}}
@media(max-width:640px){{.k{{grid-template-columns:1fr 1fr}}.f{{flex-direction:column}}}}
</style>
</head>
<body>
<div class="banner">MOCK - Dados de simulacao (360d, seed=42). Atraso fornecedor = >45 dias. Todos os alertas tem pedido (simulacao auto-gera).</div>
<div class="top"><h1>Chez Violeta - Dashboard Comprador</h1><div class="fc" id="hdr">-</div></div>
<div class="c" id="app"></div>
<script>
var DATA = {js_a};
var SUPS = {js_s};
var TOTAL = {total};
var HCRIT = {high_crit};
var WRUP = {will_rupture};
var WSURV = {will_survive};
var WORSTS = "{worst_supplier}";
var WORSTC = {worst_compliance};

document.getElementById('hdr').innerHTML = 'Alertas: <b>' + TOTAL + '</b> | Rompem antes do pedido: <b style=color:#DC3545>' + WRUP + '</b> | Chegam a tempo: <b style=color:#28A745>' + WSURV + '</b> | Atraso >45d = late';

var allCats = [...new Set(DATA.map(function(a){{return a.cat}}))].sort();
var allSuppliers = [...new Set(DATA.map(function(a){{return a.supplier}}))].sort();

var SORT = {{col:'coverage',asc:true}};

function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}

function sortBy(col) {{
  if (SORT.col === col) SORT.asc = !SORT.asc;
  else {{ SORT.col = col; SORT.asc = true; }}
  render();
}}

function addClass(el, c) {{ el.classList.add(c); }}

function render() {{
  var urg = (document.getElementById('fu')||{{}}).value||'all';
  var cat = (document.getElementById('fc')||{{}}).value||'all';
  var sup = (document.getElementById('fs')||{{}}).value||'all';
  var risco = (document.getElementById('fr')||{{}}).value||'all';

  var filtered = DATA.filter(function(a){{
    if (urg !== 'all' && a.urgency !== urg) return false;
    if (cat !== 'all' && a.cat !== cat) return false;
    if (sup !== 'all' && a.supplier !== sup) return false;
    if (risco === 'rompe' && a.arrivesBefore !== 'NAO') return false;
    if (risco === 'chega' && a.arrivesBefore !== 'SIM') return false;
    return true;
  }});

  filtered.sort(function(a,b){{
    var va, vb;
    if (SORT.col === 'name') {{ va = a.name; vb = b.name; }}
    else if (SORT.col === 'cat') {{ va = a.cat; vb = b.cat; }}
    else if (SORT.col === 'supplier') {{ va = a.supplier; vb = b.supplier; }}
    else if (SORT.col === 'coverage') {{ va = a.coverage; vb = b.coverage; }}
    else if (SORT.col === 'qty') {{ va = a.qty; vb = b.qty; }}
    else if (SORT.col === 'urgency') {{ var u = {{CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3}}; va = u[a.urgency]||99; vb = u[b.urgency]||99; }}
    else if (SORT.col === 'risk') {{ var r = {{CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3}}; va = r[a.risk]||99; vb = r[b.risk]||99; }}
    else if (SORT.col === 'arrives') {{ va = a.daysUntilArrival||999; vb = b.daysUntilArrival||999; }}
    else if (SORT.col === 'cost') {{ va = a.totalCost||0; vb = b.totalCost||0; }}
    else return 0;
    if (typeof va === 'string') return SORT.asc ? va.localeCompare(vb) : vb.localeCompare(va);
    return SORT.asc ? (va - vb) : (vb - va);
  }});

  var rows = filtered.map(function(a){{
    var rc = a.risk==='CRITICAL' ? 'crit' : a.risk==='HIGH' ? 'high' : a.arrivesBefore==='SIM' ? 'ok' : '';
    var diasFaltam = a.daysUntilArrival||999;
    var situacao = a.hasPending
      ? (a.arrivesBefore==='SIM' ? '<span style=color:#28A745>Chega a tempo (+' + (a.coverage - diasFaltam) + 'd)</span>' : '<span style=color:#DC3545>Rompe antes (-' + (diasFaltam - a.coverage) + 'd)</span>')
      : '<span style=color:#DC3545;font-weight:700>SEM PEDIDO</span>';
    return '<tr class=' + rc + '><td>' + esc(a.name) + '</td><td>' + esc(a.code) + '</td><td>' + a.cat + '</td><td>' + a.regime + '</td><td>' + esc(a.supplier) + '</td><td>' + a.coverage + 'd</td><td>' + a.qty + '</td><td><span class=\"b b-' + a.urgency + '\">' + a.urgency + '</span></td><td><span class=\"b b-' + a.risk + '\">' + a.risk + '</span></td><td>' + situacao + '</td><td>' + (a.totalCost>0 ? 'R$'+a.totalCost.toFixed(0) : '-') + '</td></tr>';
  }}).join('');

  var supOpt = '<option value=all>Todos</option>' + allSuppliers.map(function(s){{return '<option value=\"' + esc(s) + '\">' + esc(s) + '</option>'}}).join('');
  var catOpt = '<option value=all>Todas</option>' + allCats.map(function(c){{return '<option value=\"' + esc(c) + '\">' + esc(c) + '</option>'}}).join('');

  document.getElementById('app').innerHTML =
    '<div class=k>' +
      '<div class=kp><div class=l>Total Alertas</div><div class=v>' + TOTAL + '</div><div class=s>Periodo: ' + DATA[0].date + ' a ' + DATA[DATA.length-1].date + '</div></div>' +
      '<div class=kp crit><div class=l>Rompem Antes do Pedido</div><div class=v>' + WRUP + '</div><div class=s>Cobertura < prazo de chegada</div></div>' +
      '<div class=kp ok><div class=l>Chegam a Tempo</div><div class=v>' + WSURV + '</div><div class=s>Cobertura > prazo de chegada</div></div>' +
      '<div class=kp warn><div class=l>Alto/Critico</div><div class=v>' + HCRIT + '</div><div class=s>' + (HCRIT/TOTAL*100).toFixed(1) + '% dos alertas</div></div>' +
    '</div>' +
    '<div class=info>Clique nos cabecalhos para ordenar. <b>Rompem Antes</b> = estoque acaba antes do pedido chegar. <b>Chegam a Tempo</b> = pedido chega antes do estoque zerar. Atraso real = >45 dias do pedido.</div>' +
    '<div class=f>' +
      '<label>Urgencia</label><select id=fu onchange=render()><option value=all>Todas</option><option value=CRITICAL>CRITICAL</option><option value=HIGH>HIGH</option><option value=MEDIUM>MEDIUM</option><option value=LOW>LOW</option></select>' +
      '<label>Categoria</label><select id=fc onchange=render()>' + catOpt + '</select>' +
      '<label>Fornecedor</label><select id=fs onchange=render()>' + supOpt + '</select>' +
      '<label>Risco</label><select id=fr onchange=render()><option value=all>Todos</option><option value=rompe>Rompe antes</option><option value=chega>Chega a tempo</option></select>' +
      '<span class=fc>' + filtered.length + ' alertas</span>' +
    '</div>' +
    '<div class=card style=padding:0><div class=wrap><table><thead><tr>' +
      '<th onclick=sortBy("name")>Produto</th><th onclick=sortBy("name")>Cod</th><th onclick=sortBy("cat")>Categoria</th><th>Regime</th><th onclick=sortBy("supplier")>Fornecedor</th>' +
      '<th onclick=sortBy("coverage")>Cobertura</th><th onclick=sortBy("qty")>Qtd</th>' +
      '<th onclick=sortBy("urgency")>Urgencia</th><th onclick=sortBy("risk")>Risco</th>' +
      '<th onclick=sortBy("arrives")>Situacao (vs Pedido)</th><th onclick=sortBy("cost")>Custo Total</th>' +
    '</tr></thead><tbody>' + rows + '</tbody></table></div></div>';
}}

render();
</script>
</body>
</html>'''

out_path = BASE + "/artifacts/design/dashboard-comprador/index.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out_path)
print(f"Generated v3: {out_path} ({size:,} bytes)")
print(f"Alertas: {total} | Rompem antes: {will_rupture} | Chegam a tempo: {will_survive} | Alto/Critico: {high_crit}")
