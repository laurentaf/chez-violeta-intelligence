#!/usr/bin/env python3
"""
Dashboard v4 - Compras por fornecedor com regras de negocio:
- Alertas agrupados por fornecedor (max 1 pedido/mes, 4/ano)
- Minimo R$10k (exceto biju)
- Cobertura alvo 120 dias
- Exibicao por produto (codigo)
- Substitutos identificados
- Extrato de compra por fornecedor
"""
import json, os
from collections import defaultdict

BASE = "F:/projects/chez-violeta-intelligence"

with open(BASE + "/artifacts/design/dashboard-comprador/data.json", encoding="utf-8") as f:
    DATA = json.load(f)

ALERTS = DATA["alerts"]
SUPPLIERS = DATA["suppliers"]
SUMMARY = DATA["summary"]

# --- Agrupar alertas por fornecedor ---
sup_orders = defaultdict(lambda: {
    "alerts": [], "total_qty": 0, "total_cost": 0,
    "n_skus": 0, "categories": set(), "min_coverage": 999,
    "max_urgency": "LOW", "products": []
})

for a in ALERTS:
    s = a["supplier"]
    sup_orders[s]["alerts"].append(a)
    sup_orders[s]["total_qty"] += a["qty"]
    sup_orders[s]["total_cost"] += a.get("totalCost", 0) or a["qty"] * (a.get("unitCost", 0) or 0)
    sup_orders[s]["categories"].add(a["cat"])
    sup_orders[s]["min_coverage"] = min(sup_orders[s]["min_coverage"], a["coverage"])
    
    # Urgencia: se qualquer alerta for CRITICAL, o grupo e CRITICAL
    urg_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    if urg_order.get(a["urgency"], 0) > urg_order.get(sup_orders[s]["max_urgency"], 0):
        sup_orders[s]["max_urgency"] = a["urgency"]
    
    # Produto unico (por codigo)
    prod_key = a.get("code", str(a["id"]))
    if not any(p["code"] == prod_key for p in sup_orders[s]["products"]):
        sup_orders[s]["products"].append({
            "code": prod_key,
            "name": a["name"],
            "cat": a["cat"],
            "qty": a["qty"],
            "coverage": a["coverage"],
            "risk": a["risk"],
            "cost": a.get("totalCost", 0) or a["qty"] * (a.get("unitCost", 0) or 0)
        })
        sup_orders[s]["n_skus"] += 1

# --- Aplicar regras de compra ---
supplier_orders = []
for sup_name, data in sup_orders.items():
    is_biju = "BIJU" in str(data["categories"])
    
    # Minimo R$10k (exceto biju)
    meets_minimum = is_biju or data["total_cost"] >= 10000
    
    # Calcular urgência do grupo
    if data["max_urgency"] == "CRITICAL":
        priority = 0
    elif data["max_urgency"] == "HIGH":
        priority = 1
    else:
        priority = 2
    
    # Encontrar compliance do fornecedor
    sup_info = next((s for s in SUPPLIERS if s["name"] == sup_name), None)
    compliance = sup_info["compliancePct"] if sup_info else 100
    
    supplier_orders.append({
        "name": sup_name,
        "n_skus": data["n_skus"],
        "total_qty": data["total_qty"],
        "total_cost": round(data["total_cost"], 2),
        "meets_minimum": meets_minimum,
        "min_coverage": data["min_coverage"],
        "urgency": data["max_urgency"],
        "priority": priority,
        "categories": sorted(data["categories"]),
        "compliance": compliance,
        "products": sorted(data["products"], key=lambda p: p["coverage"])
    })

# Ordenar: CRITICAL primeiro, depois HIGH, depois menor cobertura
supplier_orders.sort(key=lambda s: (s["priority"], s["min_coverage"]))

# --- Encontrar substitutos (commodities) ---
# Para cada produto COMMODITY com coverage < 30, buscar substitutos do mesmo tipo
substitutes = {}
for a in ALERTS:
    if a["regime"] == "commodity" and a["coverage"] < 30:
        # Buscar outros produtos com mesmo des_produto (primeira palavra do nome)
        base_name = a["name"].split("-")[0].strip() if "-" in a["name"] else a["name"].split()[0]
        candidates = []
        for a2 in ALERTS:
            if a2["id"] != a["id"] and a2["cat"] == a["cat"] and a2["regime"] == "commodity":
                base2 = a2["name"].split("-")[0].strip() if "-" in a2["name"] else a2["name"].split()[0]
                if base_name[:4] == base2[:4] or base_name.split()[0] == base2.split()[0]:
                    candidates.append(a2)
        if candidates:
            substitutes[a["id"]] = {
                "product": a["name"],
                "substitutes": sorted(candidates, key=lambda x: abs(x.get("unitCost", 0) - a.get("unitCost", 0)))[:3]
            }

# Dados para o JS
total_suppliers = len(supplier_orders)
total_with_min = sum(1 for s in supplier_orders if s["meets_minimum"])
total_critical = sum(1 for s in supplier_orders if s["urgency"] == "CRITICAL")
total_value = sum(s["total_cost"] for s in supplier_orders)

js_suppliers = json.dumps(supplier_orders, ensure_ascii=False)
js_substitutes = json.dumps(substitutes, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Compras por Fornecedor</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--v:#7B2D4E;--d:#C9A84C;--w:#FAF8F5;--t:#2D1B24;--m:#8C7A86;--r:#DC3545;--h:#FD7E14;--g:#28A745}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:var(--w);color:var(--t);font-size:14px}}
h1,h2,h3{{font-family:Cormorant Garamond,serif;font-weight:600}}
.banner{{background:#FFF3CD;color:#856404;text-align:center;font-size:0.75rem;padding:3px 0}}
.top{{background:linear-gradient(135deg,#5C1F3A,#7B2D4E);color:#fff;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
.c{{max-width:1440px;margin:0 auto;padding:10px 16px}}
.card{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(123,45,78,0.08);margin-bottom:14px}}
.card-sm{{padding:10px 14px;margin-bottom:8px;background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(123,45,78,0.06);border-left:4px solid var(--d)}}
.card-sm.crit{{border-left-color:var(--r)}}
.card-sm.high{{border-left-color:var(--h)}}
table{{width:100%;border-collapse:collapse;font-size:0.78rem}}
th{{background:var(--v);color:#fff;padding:7px 8px;text-align:left;font-weight:600;white-space:nowrap}}
td{{padding:6px 8px;border-bottom:1px solid #E8E0DA;white-space:nowrap}}
tr:hover{{background:#F8F4F0}}
.b{{display:inline-block;font-size:0.6rem;font-weight:700;padding:2px 7px;border-radius:20px;color:#fff}}
.b-CRITICAL{{background:var(--r)}}.b-HIGH{{background:var(--h)}}
.b-MEDIUM{{background:#FFC107;color:#7B5A00}}.b-LOW{{background:var(--g)}}
.wrap{{overflow-x:auto}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:14px}}
.kp{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(123,45,78,0.08);border-left:4px solid var(--d)}}
.kp .l{{font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;color:var(--m)}}
.kp .v{{font-size:1.4rem;font-weight:700;color:var(--v)}}
.kp .s{{font-size:0.7rem}}
.kp.crit{{border-left-color:var(--r)}}
.kp.crit .v{{color:var(--r)}}
.f{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}}
.f label{{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.3px;color:var(--m)}}
.f select{{padding:4px 8px;border:1px solid #ccc;border-radius:6px;font-family:Inter;font-size:0.8rem}}
.fc{{font-size:0.8rem;color:var(--m);background:#F0EBE6;padding:4px 10px;border-radius:20px}}
.info{{font-size:0.75rem;color:var(--m);padding:8px 12px;background:#F0EBE6;border-radius:6px;margin-bottom:12px}}
.det{{display:none;padding:10px 0 0 16px}}
.det.show{{display:block}}
.bt{{padding:4px 12px;border:1px solid var(--v);border-radius:6px;background:transparent;color:var(--v);cursor:pointer;font-size:0.75rem}}
.bt:hover{{background:var(--v);color:#fff}}
.extrato{{background:#fff;border:2px solid var(--d);border-radius:10px;padding:16px;margin:20px 0;font-size:0.82rem;display:none}}
.extrato.show{{display:block}}
.extrato h3{{color:var(--v);margin-bottom:8px}}
@media(max-width:640px){{.k{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="banner">MOCK - Dados de simulacao. Compras manuais por fornecedor. Minimo R$10k. Cobertura alvo 120d. Max 1 pedido/mes.</div>
<div class="top"><h1>Chez Violeta - Compras por Fornecedor</h1><div class="fc" id="hdr">-</div></div>
<div class="c" id="app"></div>
<script>
var SUPPLIERS = {js_suppliers};
var SUBSTITUTES = {js_substitutes};

document.getElementById('hdr').innerHTML = 'Fornecedores c/ alerta: <b>' + SUPPLIERS.length + '</b> | Criticos: <b style=color:#DC3545>' + SUPPLIERS.filter(function(s){{return s.urgency==='CRITICAL'}}).length + '</b> | Valor total: <b>R$ ' + SUPPLIERS.reduce(function(s,o){{return s+o.total_cost}},0).toLocaleString('pt-BR',{{minimumFractionDigits:2}}) + '</b>';

function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}

function toggleDet(id) {{
  var el = document.getElementById('det-' + id);
  if (el) el.classList.toggle('show');
}}

function showExtrato(id) {{
  var ext = document.getElementById('ext-' + id);
  if (ext) ext.classList.toggle('show');
}}

function render() {{
  var filtro = (document.getElementById('ff')||{{}}).value||'todos';
  var busca = (document.getElementById('fb')||{{}}).value||'';

  var filtered = SUPPLIERS.filter(function(s){{
    if (filtro === 'crit' && s.urgency !== 'CRITICAL') return false;
    if (filtro === 'min' && !s.meets_minimum) return false;
    if (filtro === 'ok' && s.meets_minimum && s.urgency !== 'CRITICAL') return false;
    if (busca && s.name.toLowerCase().indexOf(busca.toLowerCase()) < 0) return false;
    return true;
  }});

  var cards = filtered.map(function(s, i){{
    var extId = 'ext-' + i;
    var detId = 'det-' + i;
    var critClass = s.urgency === 'CRITICAL' ? 'crit' : (s.urgency === 'HIGH' ? 'high' : '');
    var minOk = s.meets_minimum ? '<span style=color:#28A745>Atinge R$10k</span>' : '<span style=color:#DC3545>Abaixo do minimo R$10k</span>';
    if (s.categories.indexOf('BIJU') >= 0) minOk = '<span style=color:#C9A84C>Bijuterias - compra manual</span>';
    
    var products = s.products.slice(0, 20).map(function(p){{
      return '<tr><td>' + esc(p.name) + '</td><td>' + p.code + '</td><td>' + p.cat + '</td><td>' + p.qty + '</td><td>' + p.coverage + 'd</td><td><span class="b b-' + p.risk + '">' + p.risk + '</span></td><td>R$' + p.cost.toFixed(0) + '</td></tr>';
    }}).join('');

    return '<div class="card-sm ' + critClass + '">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">' +
        '<div><strong>' + esc(s.name) + '</strong> <span class="b b-' + s.urgency + '">' + s.urgency + '</span> <span style="font-size:0.7rem;color:var(--m)">Compliance: ' + s.compliance + '%</span></div>' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
          '<span style="font-size:0.8rem">' + s.n_skus + ' produtos | R$' + s.total_cost.toFixed(0) + '</span>' +
          '<span style="font-size:0.75rem">' + minOk + '</span>' +
          '<button class=bt onclick="toggleDet(' + i + ')">Detalhes</button>' +
          '<button class=bt onclick="showExtrato(' + i + ')">Extrato</button>' +
        '</div>' +
      '</div>' +

      '<div class=det id="' + detId + '">' +
        '<div style="font-size:0.75rem;color:var(--m);margin-bottom:6px">' +
          'Cobertura min: ' + s.min_coverage + 'd | Categorias: ' + s.categories.join(', ') +
          ' | Cobertura alvo: 120d | Max 1 pedido/mes, 4/ano' +
        '</div>' +
        '<div class=wrap><table><thead><tr>' +
          '<th>Produto</th><th>Cod</th><th>Categoria</th><th>Qtd</th><th>Cobertura</th><th>Risco</th><th>Custo</th>' +
        '</tr></thead><tbody>' + products + '</tbody></table></div>' +
        (s.products.length > 20 ? '<div style="font-size:0.7rem;color:var(--m);text-align:center;padding:4px">+ ' + (s.products.length-20) + ' produtos (total ' + s.products.length + ')</div>' : '') +
      '</div>' +

      '<div class=extrato id="' + extId + '">' +
        '<h3>Extrato de Compra - ' + esc(s.name) + '</h3>' +
        '<p style="font-size:0.75rem;color:var(--m);margin-bottom:8px">Pedido sugerido para cobertura de 120 dias.</p>' +
        '<table><thead><tr><th>Codigo</th><th>Produto</th><th>Categoria</th><th>Qtd</th><th>Cobertura Atual</th><th>Qtd p/ 120d</th><th>Custo Unit</th><th>Total</th></tr></thead><tbody>' +
          s.products.map(function(p){{
            var qtd120 = Math.ceil(p.qty * (120 / Math.max(p.coverage, 1)));
            return '<tr><td>' + p.code + '</td><td>' + esc(p.name) + '</td><td>' + p.cat + '</td><td>' + p.qty + '</td><td>' + p.coverage + 'd</td><td>' + qtd120 + '</td><td>R$' + (p.qty > 0 ? (p.cost / p.qty).toFixed(2) : '0.00') + '</td><td>R$' + (qtd120 * (p.qty > 0 ? p.cost / p.qty : 0)).toFixed(0) + '</td></tr>';
          }}).join('') +
        '</tbody></table>' +
        '<div style="margin-top:8px;font-weight:600;text-align:right">Total estimado: R$ ' + s.products.reduce(function(sum, p){{return sum + Math.ceil(p.qty * (120 / Math.max(p.coverage, 1))) * (p.qty > 0 ? p.cost / p.qty : 0)}}, 0).toFixed(2) + '</div>' +
      '</div>' +
    '</div>';
  }}).join('');

  document.getElementById('app').innerHTML =
    '<div class=k>' +
      '<div class=kp><div class=l>Fornecedores c/ Alerta</div><div class=v>' + SUPPLIERS.length + '</div><div class=s>Total de fornecedores</div></div>' +
      '<div class=kp crit><div class=l>Atendem Minimo R$10k</div><div class=v>' + SUPPLIERS.filter(function(s){{return s.meets_minimum}}).length + '</div><div class=s>Podem receber pedido</div></div>' +
      '<div class=kp><div class=l>Valor Total Alertas</div><div class=v>R$' + SUPPLIERS.reduce(function(s,o){{return s+o.total_cost}},0).toFixed(0) + '</div><div class=s>Necessario para comprar</div></div>' +
      '<div class=kp crit><div class=l>Criticos</div><div class=v>' + SUPPLIERS.filter(function(s){{return s.urgency==='CRITICAL'}}).length + '</div><div class=s>Acao imediata necessaria</div></div>' +
    '</div>' +

    '<div class=info>' +
      '<b>Regras de Compra:</b> ' +
      'Max 1 pedido/mes por fornecedor (4/ano). ' +
      'Minimo R$10k (exceto bijuterias - compra manual). ' +
      'Cobertura alvo: 120 dias. ' +
      'Pedidos MANUAIS - o dashboard apenas alerta. ' +
      'Substitutos: produtos mesmo tipo +-20% preco.' +
    '</div>' +

    '<div class=f>' +
      '<label>Filtro</label><select id=ff onchange=render()>' +
        '<option value=todos>Todos fornecedores</option>' +
        '<option value=crit>Apenas Criticos</option>' +
        '<option value=ok>Atende minimo</option>' +
        '<option value=min>Abaixo do minimo</option>' +
      '</select>' +
      '<label>Busca</label><input id=fb onkeyup=render() placeholder="Nome fornecedor..." style="padding:4px 8px;border:1px solid #ccc;border-radius:6px;font-size:0.8rem">' +
      '<span class=fc>' + filtered.length + ' fornecedores</span>' +
    '</div>' +

    '<div id="cards">' + cards + '</div>';
}}

render();
</script>
</body>
</html>'''

out_path = BASE + "/artifacts/design/dashboard-comprador/index.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard v4 gerado: {out_path} ({os.path.getsize(out_path):,} bytes)")
print(f"Fornecedores com alerta: {total_suppliers}")
print(f"Atendem minimo R$10k: {total_with_min}")
print(f"Criterios: {total_critical}")
print(f"Valor total: R$ {total_value:,.2f}")
print(f"Grupos de substitutos identificados: {len(substitutes)}")
