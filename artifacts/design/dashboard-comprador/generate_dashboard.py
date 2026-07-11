#!/usr/bin/env python3
"""Generate complete Chez Violeta Buyer Dashboard HTML with embedded data."""
import json, os

BASE = "F:/projects/chez-violeta-intelligence"

with open(os.path.join(BASE, "artifacts/design/dashboard-comprador/data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

ALERTS = DATA["alerts"]
SUPPLIERS = DATA["suppliers"]
SUMMARY = DATA["summary"]
STOCK = DATA["stockByProduct"]

# Build stock by alert product - only for products IN alerts
alert_product_ids = set(a["id"] for a in ALERTS)
stock_for_alerts = {pid: entries for pid, entries in STOCK.items() if pid in alert_product_ids}

js_alerts = json.dumps(ALERTS, ensure_ascii=False)
js_suppliers = json.dumps(SUPPLIERS, ensure_ascii=False)
js_summary = json.dumps(SUMMARY, ensure_ascii=False)
js_stock = json.dumps(stock_for_alerts, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta — Dashboard do Comprador v2</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {{
  --vinho: #7B2D4E; --vinho-light: #9E3F6A; --vinho-dark: #5C1F3A;
  --dourado: #C9A84C; --dourado-light: #E0C66A; --off-white: #FAF8F5;
  --warm-white: #F5F0EB; --text-primary: #2D1B24; --text-secondary: #5C4B55;
  --text-muted: #8C7A86; --bg-body: #FAF8F5; --bg-card: #FFFFFF;
  --border: #E8E0DA; --critical: #DC3545; --high: #FD7E14; --medium: #FFC107;
  --low: #28A745; --success: #28A745; --info: #17A2B8;
  --shadow: 0 2px 8px rgba(123,45,78,0.08);
  --radius: 12px; --radius-sm: 8px;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg-body);color:var(--text-primary);line-height:1.6}}
h1,h2,h3,h4{{font-family:'Cormorant Garamond',serif;font-weight:600}}
h1{{color:#fff;font-size:1.75rem;letter-spacing:0.3px}}
h1 small{{font-family:'Inter',sans-serif;font-weight:300;font-size:0.7rem;opacity:0.7;display:block}}
h2{{color:var(--vinho);font-size:1.35rem;border-bottom:2px solid var(--dourado);padding-bottom:6px;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
h2 .h2-count{{font-size:0.7rem;font-weight:400;color:var(--text-muted);font-family:'Inter',sans-serif}}
.synthetic-banner{{background:repeating-linear-gradient(45deg,#FFEAA7,#FFEAA7 20px,#FFF3CD 20px,#FFF3CD 40px);color:#856404;text-align:center;font-size:0.75rem;font-weight:600;padding:3px 0;letter-spacing:0.5px;position:sticky;top:0;z-index:100}}
.header{{background:linear-gradient(135deg,var(--vinho-dark),var(--vinho));color:#fff;padding:16px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}}
.header-date{{font-size:0.8rem;opacity:0.8}}
.header-logo{{display:flex;align-items:center;gap:12px}}
.header-logo-icon{{font-size:1.5rem;font-family:'Cormorant Garamond',serif;font-style:italic;background:var(--dourado);color:var(--vinho-dark);width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700}}
.container{{max-width:1440px;margin:0 auto;padding:16px 20px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:24px}}
.kpi-card{{background:var(--bg-card);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow);border-left:4px solid var(--dourado);transition:transform 0.15s,box-shadow 0.15s}}
.kpi-card:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(123,45,78,0.12)}}
.kpi-card .label{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:4px}}
.kpi-card .value{{font-size:1.6rem;font-weight:700;color:var(--vinho)}}
.kpi-card .sub{{font-size:0.75rem;color:var(--text-secondary);margin-top:2px}}
.kpi-card.critical{{border-left-color:var(--critical)}}.kpi-card.critical .value{{color:var(--critical)}}
.kpi-card.warning{{border-left-color:var(--high)}}.kpi-card.warning .value{{color:var(--high)}}
.kpi-card.success{{border-left-color:var(--success)}}.kpi-card.success .value{{color:var(--success)}}
.kpi-card.info{{border-left-color:var(--info)}}.kpi-card.info .value{{color:var(--info)}}
.filters{{background:var(--bg-card);border-radius:var(--radius);padding:14px 18px;box-shadow:var(--shadow);margin-bottom:20px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.filters label{{font-size:0.7rem;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.3px}}
.filters select,.filters input{{padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius-sm);font-family:'Inter',sans-serif;font-size:0.85rem;background:#fff;color:var(--text-primary);min-width:130px}}
.filters select:focus{{outline:2px solid var(--dourado);outline-offset:1px}}
.filter-count{{margin-left:auto;font-size:0.8rem;color:var(--text-muted);background:var(--warm-white);padding:4px 10px;border-radius:20px;white-space:nowrap}}
.section{{margin-bottom:28px}}
.card{{background:var(--bg-card);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px;overflow:hidden}}
.card-aux{{margin-bottom:14px;padding:14px 18px;border-radius:var(--radius-sm);font-size:0.8rem;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.card-aux.info{{background:#E8F4FD;border-left:3px solid var(--info)}}
.card-aux.warning{{background:#FFF3CD;border-left:3px solid var(--medium)}}
.chart-row{{display:grid;grid-template-columns:2fr 1fr;gap:16px}}
.chart-row-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}
@media(max-width:900px){{.chart-row,.chart-row-3{{grid-template-columns:1fr}}}}
.table-wrap{{overflow-x:auto;overflow-y:auto}}
table{{width:100%;border-collapse:collapse;font-size:0.81rem}}
thead th{{background:var(--vinho);color:#fff;text-align:left;padding:9px 10px;font-weight:600;white-space:nowrap;position:sticky;top:0;z-index:2}}
thead th.sortable{{cursor:pointer;user-select:none}}
thead th.sortable:hover{{background:var(--vinho-light)}}
thead th.sortable::after{{content:" ↕";opacity:0.5;font-size:0.7rem}}
thead th.sortable.asc::after{{content:" ↑";opacity:1}}
thead th.sortable.desc::after{{content:" ↓";opacity:1}}
tbody td{{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:middle}}
tbody tr:hover{{background:#F8F4F0}}
tbody tr.critical-row{{background:#FFF5F5}}
tbody tr.critical-row:hover{{background:#FFECEC}}
tbody tr.high-row{{background:#FFF8F0}}
tbody tr.high-row:hover{{background:#FFF0E0}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.4px;padding:2px 8px;border-radius:20px;color:#fff}}
.badge-critical{{background:var(--critical)}}.badge-high{{background:var(--high)}}
.badge-medium{{background:var(--medium);color:#7B5A00}}.badge-low{{background:var(--low)}}
.badge-CRITICAL{{background:var(--critical)}}.badge-HIGH{{background:var(--high)}}
.badge-MEDIUM{{background:var(--medium);color:#7B5A00}}.badge-LOW{{background:var(--low)}}
.badge-A{{background:var(--low)}}.badge-B{{background:var(--dourado);color:#7B5A00}}
.badge-C{{background:var(--high)}}.badge-D{{background:var(--critical)}}
.bar-wrap{{display:flex;align-items:center;gap:8px}}
.bar-bg{{flex:1;height:8px;background:#E8E0DA;border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px;background:var(--vinho);transition:width 0.3s}}
.bar-fill.good{{background:var(--success)}}.bar-fill.ok{{background:var(--dourado)}}
.bar-fill.bad{{background:var(--high)}}.bar-fill.crit{{background:var(--critical)}}
.risk-cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}}
.risk-card{{padding:14px;border-radius:var(--radius-sm);font-size:0.82rem}}
.risk-card h4{{font-family:'Inter',sans-serif;font-weight:700;font-size:0.85rem;margin-bottom:4px}}
.risk-card p{{font-size:0.75rem;opacity:0.85;line-height:1.4}}
.risk-card.green{{background:#E8F5E9;border-left:4px solid #28A745}}
.risk-card.yellow{{background:#FFF8E1;border-left:4px solid #FFC107}}
.risk-card.red{{background:#FFEBEE;border-left:4px solid #DC3545}}
.risk-card.black{{background:#F5F5F5;border-left:4px solid #343A40}}
@media(max-width:640px){{
  .header{{flex-direction:column;align-items:flex-start}}
  .kpi-grid{{grid-template-columns:1fr 1fr}}
  .filters{{flex-direction:column;align-items:stretch}}
  .filters select{{min-width:auto}}.filter-count{{margin-left:0}}
  .risk-cards{{grid-template-columns:1fr}}
}}
.text-muted{{color:var(--text-muted)}}
.text-center{{text-align:center}}
.empty-state{{text-align:center;padding:32px;color:var(--text-muted);font-style:italic}}
.stock-legend{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
.stock-legend-item{{font-size:0.7rem;padding:3px 8px;border-radius:4px;background:var(--off-white);border:1px solid var(--border)}}
</style>
</head>
<body>
<div class="synthetic-banner">⚠ MOCK — Dados de simulação, não para produção (Simulação 360 dias, seed=42)</div>
<header class="header">
  <div class="header-logo">
    <div class="header-logo-icon">CV</div>
    <div><h1>Chez Violeta <small>Dashboard do Comprador v2 — Simulação 360d</small></h1></div>
  </div>
  <div class="header-date" id="headerDate">—</div>
</header>
<div class="container" id="app"></div>

<script>
/* ═══════════════ EMBEDDED DATA ═══════════════ */
const SUMMARY = {js_summary};
const ALERTS = {js_alerts};
const SUPPLIERS = {js_suppliers};
const STOCK_BY_PRODUCT = {js_stock};

/* ═══════════════ ENGINE ═══════════════ */
const lastDate = SUMMARY.latestDate;
document.getElementById('headerDate').innerHTML = 'Último dia: <strong>' + lastDate + '</strong> | Total alertas: ' + SUMMARY.totalAlerts.toLocaleString() + ' | Fornecedores ativos: ' + SUMMARY.alertSupplierCount;

const allSuppliers = [...new Set(ALERTS.map(a => a.supplier))].sort();
const allCategories = [...new Set(ALERTS.map(a => a.cat))].sort();
const allDates = [...new Set(ALERTS.map(a => a.date))].sort().reverse();

let charts = {{}};
let sortState = {{ col: null, asc: true, tableId: null }};

/* ─── Utility ─── */
function esc(str) {{ return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
function urgencyBadge(urg) {{ return '<span class="badge badge-' + urg + '">' + urg + '</span>'; }}
function gradeBadge(g) {{ return '<span class="badge badge-' + g + '">' + g + '</span>'; }}
function rowClassByRisk(r) {{ return r === 'CRITICAL' ? 'critical-row' : (r === 'HIGH' ? 'high-row' : ''); }}
function pctBar(pct, cls) {{ return '<div class="bar-wrap"><span style="font-weight:600;font-size:0.75rem;width:36px;text-align:right">' + pct.toFixed(1) + '%</span><div class="bar-bg"><div class="bar-fill ' + cls + '" style="width:' + Math.min(pct,100) + '%"></div></div></div>'; }}
function coberturaRisk(coverage) {{ return coverage < 7 ? 'CRITICAL' : coverage < 15 ? 'HIGH' : coverage < 30 ? 'MEDIUM' : 'LOW'; }}

/* ─── Sorting Engine ─── */
function sortTable(arr, col, asc) {{
  return [...arr].sort((a, b) => {{
    let va = a[col], vb = b[col];
    if (typeof va === 'string') {{ 
      const cmp = va.localeCompare(vb);
      return asc ? cmp : -cmp;
    }}
    return asc ? (va - vb) : (vb - va);
  }});
}}

/* ─── Render KPI Cards ─── */
function renderKPIs() {{
  const g = document.getElementById('kpiGrid');
  g.innerHTML = [
    '<div class="kpi-card critical"><div class="label">Total Alertas</div><div class="value">' + SUMMARY.totalAlerts.toLocaleString() + '</div><div class="sub">No período da simulação</div></div>',
    '<div class="kpi-card critical"><div class="label">Risco ALTO/CRÍTICO</div><div class="value">' + SUMMARY.highCritPct + '%</div><div class="sub">' + SUMMARY.highCritCount.toLocaleString() + ' alertas</div></div>',
    '<div class="kpi-card warning"><div class="label">Rompem Antes do Pedido</div><div class="value">' + SUMMARY.willRupture.toLocaleString() + '</div><div class="sub">Produtos c/ cobertura < prazo de chegada</div></div>',
    '<div class="kpi-card info"><div class="label">Pior Fornecedor</div><div class="value">' + esc(SUMMARY.worstSupplier) + '</div><div class="sub">Compliance: ' + SUMMARY.worstCompliance + '%</div></div>'
  ].join('');
}}

/* ─── Filters ─── */
function setupFilters() {{
  ['filterUrgency','filterCategory','filterSupplier','filterRisk'].forEach(id => {{
    document.getElementById(id).addEventListener('change', renderAlertTable);
  }});
}}

function getFilteredAlerts() {{
  const urg = document.getElementById('filterUrgency').value;
  const cat = document.getElementById('filterCategory').value;
  const sup = document.getElementById('filterSupplier').value;
  const risk = document.getElementById('filterRisk').value;
  return ALERTS.filter(a => {{
    if (urg !== 'all' && a.urgency !== urg) return false;
    if (cat !== 'all' && a.cat !== cat) return false;
    if (sup !== 'all' && a.supplier !== sup) return false;
    if (risk !== 'all' && a.risk !== risk) return false;
    return true;
  }});
}}

/* ─── Render Alert Table ─── */
let alertSort = {{ col: 'date', asc: false }};

function renderAlertTable() {{
  const filtered = getFilteredAlerts();
  const tbody = document.getElementById('alertsBody');
  document.getElementById('filterCount').textContent = filtered.length + ' alertas';

  const sorted = sortTable(filtered, alertSort.col, alertSort.asc);

  if (sorted.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="13" class="empty-state">Nenhum alerta encontrado</td></tr>';
    return;
  }}

  tbody.innerHTML = sorted.map(a => {{
    const rc = rowClassByRisk(a.risk);
    const arrivesBadge = a.arrivesBefore === 'SIM' 
      ? '<span style="color:var(--success);font-weight:600">✓ SIM</span>'
      : a.arrivesBefore === 'NÃO'
        ? '<span style="color:var(--critical);font-weight:600">✗ NÃO</span>'
        : '<span class="text-muted">—</span>';
    const pendingBadge = a.hasPending 
      ? '<span style="color:var(--success)">Sim</span>' 
      : '<span style="color:var(--critical)">Não</span>';
    const costDisplay = a.totalCost > 0 ? 'R$ ' + a.totalCost.toLocaleString('pt-BR', {{minimumFractionDigits:2}}) : '—';

    return '<tr class="' + rc + '">' +
      '<td><strong>' + esc(a.name) + '</strong></td>' +
      '<td style="color:var(--text-muted);font-size:0.75rem">' + esc(a.code) + '</td>' +
      '<td>' + esc(a.cat) + '</td>' +
      '<td>' + esc(a.regime) + '</td>' +
      '<td>' + esc(a.supplier) + '</td>' +
      '<td><strong>' + a.coverage + 'd</strong></td>' +
      '<td>' + a.qty + '</td>' +
      '<td>' + urgencyBadge(a.urgency) + '</td>' +
      '<td>' + urgencyBadge(a.risk) + '</td>' +
      '<td>' + pendingBadge + '</td>' +
      '<td style="font-size:0.75rem">' + (a.pendingDate || '—') + '</td>' +
      '<td>' + arrivesBadge + '</td>' +
      '<td>' + costDisplay + '</td>' +
    '</tr>';
  }}).join('');

  // Update sort indicators
  document.querySelectorAll('#alertsTable th.sortable').forEach(th => {{
    th.classList.remove('asc','desc');
    if (th.dataset.col === alertSort.col) {{
      th.classList.add(alertSort.asc ? 'asc' : 'desc');
    }}
  }});
}}

function sortAlerts(col) {{
  if (alertSort.col === col) alertSort.asc = !alertSort.asc;
  else {{ alertSort.col = col; alertSort.asc = col === 'date' ? false : true; }}
  renderAlertTable();
}}

/* ─── Supplier Sort ─── */
let supplierSort = {{ col: 'compliance', asc: false }};

function renderSupplierTable() {{
  const tbody = document.getElementById('supplierBody');
  const alertSuppliers = new Set(ALERTS.map(a => a.supplier));
  const sorted = sortTable(
    SUPPLIERS.filter(s => alertSuppliers.has(s.name)),
    supplierSort.col, supplierSort.asc
  );

  tbody.innerHTML = sorted.map(s => {{
    return '<tr>' +
      '<td><strong>' + esc(s.name) + '</strong></td>' +
      '<td>' + s.orders + '</td>' +
      '<td>' + s.onTime + '</td>' +
      '<td style="color:' + (s.late > 5 ? 'var(--critical)' : 'var(--success)') + '">' + s.late + '</td>' +
      '<td>' + pctBar(s.compliancePct, s.compliancePct >= 90 ? 'good' : s.compliancePct >= 85 ? 'ok' : 'bad') + '</td>' +
      '<td>' + gradeBadge(s.grade) + '</td>' +
      '<td>' + s.avgDelay.toFixed(1) + 'd</td>' +
      '<td style="font-size:0.7rem;color:var(--text-muted);max-width:200px">' + esc(s.explanation) + '</td>' +
    '</tr>';
  }}).join('');

  document.querySelectorAll('#supplierTable th.sortable').forEach(th => {{
    th.classList.remove('asc','desc');
    if (th.dataset.col === supplierSort.col) {{
      th.classList.add(supplierSort.asc ? 'asc' : 'desc');
    }}
  }});
}}

function sortSuppliers(col) {{
  if (supplierSort.col === col) supplierSort.asc = !supplierSort.asc;
  else {{ supplierSort.col = col; supplierSort.asc = false; }}
  renderSupplierTable();
}}

/* ─── Stock by Store ─── */
function renderStockTable() {{
  const tbody = document.getElementById('stockBody');
  // Get unique products from alerts that have stock data
  const entries = [];
  const alertProducts = ALERTS.slice(0, 100); // Focus on recent 100
  for (const a of alertProducts) {{
    const pid = a.id;
    if (STOCK_BY_PRODUCT[pid]) {{
      for (const s of STOCK_BY_PRODUCT[pid]) {{
        entries.push({{
          store: s.store,
          product: a.name,
          code: a.code,
          qty: s.qty,
          coverage: a.coverage
        }});
      }}
    }}
  }}
  // Limit display
  const display = entries.slice(0, 200);
  document.getElementById('stockCount').textContent = entries.length + ' registros';
  
  if (display.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Sem dados de estoque por loja para produtos em alerta</td></tr>';
    return;
  }}

  tbody.innerHTML = display.map(e => {{
    const crit = e.coverage < 7 ? 'critical-row' : '';
    return '<tr class="' + crit + '">' +
      '<td>' + esc(e.store) + '</td>' +
      '<td>' + esc(e.product) + '</td>' +
      '<td style="font-size:0.75rem;color:var(--text-muted)">' + esc(e.code) + '</td>' +
      '<td><strong>' + e.qty + '</strong></td>' +
      '<td>' + e.coverage + 'd</td>' +
    '</tr>';
  }}).join('');
}}

/* ─── Rupture Risk Section ─── */
function renderRiskTable() {{
  const tbody = document.getElementById('riskBody');
  const sorted = sortTable(ALERTS, 'coverage', true).slice(0, 100);
  
  tbody.innerHTML = sorted.map(a => {{
    const risk = coberturaRisk(a.coverage);
    const riskLabel = risk === 'CRITICAL' ? '⚫ Crítico' : risk === 'HIGH' ? '🔴 Alto' : risk === 'MEDIUM' ? '🟡 Médio' : '🟢 Baixo';
    const rc = risk === 'CRITICAL' ? 'critical-row' : risk === 'HIGH' ? 'high-row' : '';
    return '<tr class="' + rc + '">' +
      '<td><strong>' + esc(a.name) + '</strong></td>' +
      '<td>' + a.coverage + 'd</td>' +
      '<td>' + (a.hasPending ? esc(a.pendingDate) : '—') + '</td>' +
      '<td>' + a.daysUntilArrival + 'd</td>' +
      '<td style="color:' + (a.daysUntilArrival > a.coverage ? 'var(--critical)' : 'var(--success)') + '">' + riskLabel + '</td>' +
    '</tr>';
  }}).join('');
}}

/* ─── Charts ─── */
function initCharts() {{
  // Pie: Risk Distribution
  const ctx1 = document.getElementById('chartRisk').getContext('2d');
  const rc = SUMMARY.urgencyCounts;
  charts.risk = new Chart(ctx1, {{
    type: 'doughnut',
    data: {{
      labels: ['CRITICAL','HIGH','MEDIUM','LOW'],
      datasets: [{{ data: [rc.CRITICAL||0, rc.HIGH||0, rc.MEDIUM||0, rc.LOW||0], 
        backgroundColor: ['#DC3545','#FD7E14','#FFC107','#28A745'], borderWidth: 0 }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 10, family: 'Inter' }}, padding: 8 }} }} }} }}
  }});

  // Bar: Category Distribution
  const ctx2 = document.getElementById('chartCategory').getContext('2d');
  const cats = Object.entries(SUMMARY.catCounts).sort((a,b) => b[1]-a[1]);
  charts.category = new Chart(ctx2, {{
    type: 'bar',
    data: {{
      labels: cats.map(c => c[0]),
      datasets: [{{
        label: 'Alertas',
        data: cats.map(c => c[1]),
        backgroundColor: '#7B2D4E',
        borderRadius: 4
      }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ ticks: {{ font: {{ size: 9, family: 'Inter' }} }} }}, y: {{ ticks: {{ font: {{ size: 9, family: 'Inter' }} }} }} }}
    }}
  }});

  // Bar: Top 10 Suppliers by Alert Value
  const suppValue = {{}};
  ALERTS.forEach(a => {{ if (a.totalCost > 0) suppValue[a.supplier] = (suppValue[a.supplier]||0) + a.totalCost; }});
  const topSupp = Object.entries(suppValue).sort((a,b) => b[1]-a[1]).slice(0, 10);
  const ctx3 = document.getElementById('chartSupplier').getContext('2d');
  charts.supplier = new Chart(ctx3, {{
    type: 'bar',
    data: {{
      labels: topSupp.map(s => s[0]),
      datasets: [{{
        label: 'Valor Total (R$)',
        data: topSupp.map(s => s[1]),
        backgroundColor: '#C9A84C',
        borderRadius: 4
      }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => 'R$ ' + ctx.parsed.x.toLocaleString('pt-BR', {{minimumFractionDigits:2}}) }} }}
      }},
      scales: {{
        x: {{ ticks: {{ font: {{ size: 9, family: 'Inter' }}, callback: v => 'R$ ' + v.toLocaleString('pt-BR') }} }},
        y: {{ ticks: {{ font: {{ size: 8, family: 'Inter' }} }} }}
      }}
    }}
  }});
}}

/* ═══════════════ BOOT ═══════════════ */
document.addEventListener('DOMContentLoaded', function() {{
  document.getElementById('app').innerHTML = [
    // KPI Grid
    '<div class="kpi-grid" id="kpiGrid"></div>',

    // ── Alert Filters ──
    '<div class="section">',
      '<h2>Alertas de Compra <span class="h2-count">— Interativo: clique nos cabeçalhos para ordenar</span></h2>',
      '<div class="filters">',
        '<label>Urgência</label><select id="filterUrgency">',
          '<option value="all">Todas</option>',
          '<option value="CRITICAL">CRITICAL</option>',
          '<option value="HIGH">HIGH</option>',
          '<option value="MEDIUM">MEDIUM</option>',
          '<option value="LOW">LOW</option>',
        '</select>',
        '<label>Categoria</label><select id="filterCategory"><option value="all">Todas</option>',
          allCategories.map(c => '<option value="' + c + '">' + c + '</option>').join(''),
        '</select>',
        '<label>Fornecedor</label><select id="filterSupplier"><option value="all">Todos</option>',
          allSuppliers.map(s => '<option value="' + s + '">' + s + '</option>').join(''),
        '</select>',
        '<label>Risco</label><select id="filterRisk">',
          '<option value="all">Todos</option>',
          '<option value="CRITICAL">CRÍTICO</option>',
          '<option value="HIGH">ALTO</option>',
          '<option value="MEDIUM">MÉDIO</option>',
          '<option value="LOW">BAIXO</option>',
        '</select>',
        '<span class="filter-count" id="filterCount">0 alertas</span>',
      '</div>',
      '<div class="card" style="padding:0;">',
        '<div class="table-wrap" id="alertsScroll" style="max-height:520px;overflow-y:auto;">',
          '<table id="alertsTable"><thead><tr>',
            '<th class="sortable" data-col="name" onclick="sortAlerts(\'name\')">Produto</th>',
            '<th class="sortable" data-col="code" onclick="sortAlerts(\'code\')">Código</th>',
            '<th class="sortable" data-col="cat" onclick="sortAlerts(\'cat\')">Categoria</th>',
            '<th class="sortable" data-col="regime" onclick="sortAlerts(\'regime\')">Regime</th>',
            '<th class="sortable" data-col="supplier" onclick="sortAlerts(\'supplier\')">Fornecedor</th>',
            '<th class="sortable" data-col="coverage" onclick="sortAlerts(\'coverage\')">Cobertura</th>',
            '<th class="sortable" data-col="qty" onclick="sortAlerts(\'qty\')">Qtd Sugerida</th>',
            '<th class="sortable" data-col="urgency" onclick="sortAlerts(\'urgency\')">Urgência</th>',
            '<th class="sortable" data-col="risk" onclick="sortAlerts(\'risk\')">Risco</th>',
            '<th class="sortable" data-col="hasPending" onclick="sortAlerts(\'hasPending\')">Tem Pedido?</th>',
            '<th class="sortable" data-col="pendingDate" onclick="sortAlerts(\'pendingDate\')">Prev. Chegada</th>',
            '<th class="sortable" data-col="arrivesBefore" onclick="sortAlerts(\'arrivesBefore\')">Chega Antes da Ruptura?</th>',
            '<th class="sortable" data-col="totalCost" onclick="sortAlerts(\'totalCost\')">Custo Total</th>',
          '</tr></thead><tbody id="alertsBody"></tbody></table>',
        '</div>',
      '</div>',
    '</div>',

    // ── Charts Row ──
    '<div class="section"><div class="chart-row">',
      '<div><h2>Distribuição de Risco</h2><div class="card"><canvas id="chartRisk" height="260"></canvas></div></div>',
      '<div><h2>Alertas por Categoria</h2><div class="card"><canvas id="chartCategory" height="260"></canvas></div></div>',
    '</div></div>',

    // ── Risk Section ──
    '<div class="section">',
      '<h2>Risco de Ruptura vs Pedidos</h2>',
      '<div class="risk-cards">',
        '<div class="risk-card green"><h4>🟢 Baixo Risco</h4><p>Cobertura &gt; lead time + margem de segurança. Estoque confortável.</p></div>',
        '<div class="risk-card yellow"><h4>🟡 Médio Risco</h4><p>Cobertura próxima ao lead time. Monitorar de perto.</p></div>',
        '<div class="risk-card red"><h4>🔴 Alto Risco</h4><p>Cobertura &lt; lead time. Vai romper antes do pedido chegar.</p></div>',
        '<div class="risk-card black"><h4>⚫ Crítico</h4><p>Cobertura &lt; 7 dias. Ruptura iminente.</p></div>',
      '</div>',
      '<div class="card-aux info">🔍 Produtos ordenados por cobertura (menor primeiro). Destaque vermelho = ruptura antes da reposição.</div>',
      '<div class="card" style="padding:0;">',
        '<div class="table-wrap" style="max-height:400px;overflow-y:auto;">',
          '<table><thead><tr>',
            '<th>Produto</th><th>Cobertura</th><th>Pedido Desde</th><th>Dias até Chegar</th><th>Risco</th>',
          '</tr></thead><tbody id="riskBody"></tbody></table>',
        '</div>',
      '</div>',
    '</div>',

    // ── Stock by Store ──
    '<div class="section">',
      '<h2>Cobertura por Loja <span class="h2-count">— <span id="stockCount">0</span></span></h2>',
      '<div class="card-aux info">📦 Estoque por loja para os produtos em alerta (últimos 100 alertas). Destaque vermelho = cobertura &lt; 7 dias.</div>',
      '<div class="card" style="padding:0;">',
        '<div class="table-wrap" style="max-height:400px;overflow-y:auto;">',
          '<table><thead><tr>',
            '<th>Loja</th><th>Produto</th><th>Código</th><th>Estoque Atual</th><th>Cobertura Est.</th>',
          '</tr></thead><tbody id="stockBody"></tbody></table>',
        '</div>',
      '</div>',
    '</div>',

    // ── Top Suppliers ──
    '<div class="section">',
      '<h2>Top Fornecedores por Valor em Alerta</h2>',
      '<div class="card"><canvas id="chartSupplier" height="280"></canvas></div>',
    '</div>',

    // ── Supplier Performance ──
    '<div class="section">',
      '<h2>Performance de Fornecedores <span class="h2-count">— Ordenável: clique nos cabeçalhos</span></h2>',
      '<div class="card-aux info">📊 <strong>Regra de cálculo:</strong> compliance_rate = entregas_no_prazo / total_pedidos. Atraso médio = média de dias de atraso apenas nas entregas com atraso.</div>',
      '<div class="card" style="padding:0;">',
        '<div class="table-wrap" style="max-height:500px;overflow-y:auto;">',
          '<table id="supplierTable"><thead><tr>',
            '<th class="sortable" data-col="name" onclick="sortSuppliers(\'name\')">Fornecedor</th>',
            '<th class="sortable" data-col="orders" onclick="sortSuppliers(\'orders\')">Pedidos</th>',
            '<th class="sortable" data-col="onTime" onclick="sortSuppliers(\'onTime\')">No Prazo</th>',
            '<th class="sortable" data-col="late" onclick="sortSuppliers(\'late\')">Atrasados</th>',
            '<th class="sortable" data-col="compliancePct" onclick="sortSuppliers(\'compliancePct\')">% Compliance</th>',
            '<th class="sortable" data-col="grade" onclick="sortSuppliers(\'grade\')">Nota</th>',
            '<th class="sortable" data-col="avgDelay" onclick="sortSuppliers(\'avgDelay\')">Atraso Médio</th>',
            '<th>Explicação</th>',
          '</tr></thead><tbody id="supplierBody"></tbody></table>',
        '</div>',
      '</div>',
    '</div>',
  ].join('\\n');

  renderKPIs();
  setupFilters();
  renderAlertTable();
  renderStockTable();
  renderRiskTable();
  renderSupplierTable();
  initCharts();
}});
</script>
</body>
</html>'''

output_path = os.path.join(BASE, "artifacts/design/dashboard-comprador/index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

html_size = len(html)
print(f"Dashboard generated: {output_path}")
print(f"Size: {html_size:,} bytes ({html_size/1024:.1f} KB)")
print(f"Alerts embedded: {len(ALERTS)}")
print(f"Suppliers embedded: {len(SUPPLIERS)}")
print(f"Stock entries for alert products: {sum(len(v) for v in stock_for_alerts.values())}")
