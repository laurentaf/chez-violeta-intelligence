#!/usr/bin/env python3
"""
Dashboard v5 fix - com medias por categoria para produtos sem dados de venda
"""
import json, os, csv
from collections import defaultdict

BASE = "F:/projects/chez-violeta-intelligence"

# Carregar produtos
products = []
with open(BASE + "/artifacts/data/products_by_supplier.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        products.append(row)

# Calcular velocidades e custos medios por categoria
cat_velocity = defaultdict(list)
cat_cost = defaultdict(list)
for p in products:
    v = p.get("velocidade_diaria", "")
    c = p.get("val_custo_inicial", "")
    cat = p.get("product_category", "OUTROS") or "OUTROS"
    if v and float(v) > 0:
        cat_velocity[cat].append(float(v))
    if c and float(c) > 0:
        cat_cost[cat].append(float(c))

cat_avg_vel = {k: sum(v)/len(v) for k, v in cat_velocity.items() if v}
cat_avg_cost = {k: sum(v)/len(v) for k, v in cat_cost.items() if v}
GLOBAL_AVG_VEL = sum(cat_avg_vel.values()) / len(cat_avg_vel) if cat_avg_vel else 0.02
GLOBAL_AVG_COST = sum(cat_avg_cost.values()) / len(cat_avg_cost) if cat_avg_cost else 20

# Agrupar por fornecedor
sup_products = defaultdict(list)
for p in products:
    sup = p.get("supplier_name_code", "") or p.get("supplier_code", "") or "DESC"
    sup_products[sup].append(p)

# Carregar alertas
with open(BASE + "/artifacts/design/dashboard-comprador/data.json") as f:
    DATA = json.load(f)
ALERTS = DATA["alerts"]
SUPPLIERS = DATA["suppliers"]
alert_suppliers = set(a["supplier"] for a in ALERTS)
sup_compliance = {s["name"]: s["compliancePct"] for s in SUPPLIERS}

# Construir pedidos
COBERTURAS = [120, 150, 180]
MINIMO = 10000

supplier_orders = []
for sup_name in sorted(alert_suppliers):
    if sup_name not in sup_products:
        continue
    
    sup_alerts = [a for a in ALERTS if a["supplier"] == sup_name]
    max_urg = max((a["urgency"] for a in sup_alerts), key=lambda u: {"LOW":0,"MEDIUM":1,"HIGH":2,"CRITICAL":3}.get(u,0))
    min_cov = min(a["coverage"] for a in sup_alerts) if sup_alerts else 999
    categories = list(set(a["cat"] for a in sup_alerts))
    is_biju = "BIJU" in str(categories).upper()
    
    for target_days in COBERTURAS:
        total_cost = 0
        items = []
        
        for p in sup_products[sup_name]:
            stock = int(float(p.get("qtd_estoque", 0) or 0))
            if stock <= 0:
                continue
            
            cat = p.get("product_category", "OUTROS") or "OUTROS"
            
            # Velocidade: usar do dado, ou fallback para media da categoria, ou global
            vel_str = p.get("velocidade_diaria", "")
            if vel_str and float(vel_str) > 0:
                velocity = float(vel_str)
            else:
                velocity = cat_avg_vel.get(cat, GLOBAL_AVG_VEL)
            
            # Custo: usar do dado, ou fallback para media da categoria, ou global
            cost_str = p.get("val_custo_inicial", "")
            if cost_str and float(cost_str) > 0:
                unit_cost = float(cost_str)
            else:
                unit_cost = cat_avg_cost.get(cat, GLOBAL_AVG_COST)
            
            if velocity <= 0:
                velocity = GLOBAL_AVG_VEL
            
            # Cobertura atual
            coverage = stock / velocity if velocity > 0 else 999
            
            if coverage >= target_days:
                continue  # Ja tem cobertura suficiente
            
            days_needed = target_days - coverage
            qty = max(1, int(days_needed * velocity + 0.5))  # Arredondar
            cost = qty * unit_cost
            
            items.append({
                "name": p.get("des_artigo", "") or p.get("des_produto", "Sem nome"),
                "code": p.get("cod_artigo", ""),
                "cat": cat,
                "stock": stock,
                "velocity": round(velocity, 4),
                "coverage": round(coverage, 0),
                "qty": qty,
                "unit_cost": round(unit_cost, 2),
                "cost": round(cost, 2),
                "target_days": target_days
            })
            total_cost += cost
        
        if not items:
            continue
        
        if total_cost >= MINIMO or target_days == COBERTURAS[-1]:
            supplier_orders.append({
                "name": sup_name,
                "n_total_products": len(sup_products[sup_name]),
                "n_items": len(items),
                "n_alertas": len(sup_alerts),
                "urgency": max_urg,
                "min_coverage": min_cov,
                "categories": categories,
                "is_biju": is_biju,
                "total_cost": round(total_cost, 2),
                "total_qty": sum(i["qty"] for i in items),
                "target_days": target_days,
                "meets_minimum": total_cost >= MINIMO,
                "compliance": sup_compliance.get(sup_name, 100),
                "items": items
            })
            break

# Ordenar
supplier_orders.sort(key=lambda s: (
    0 if s["urgency"] == "CRITICAL" else 1 if s["urgency"] == "HIGH" else 2,
    s["min_coverage"]
))

js_orders = json.dumps(supplier_orders, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Compra por Fornecedor</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--v:#7B2D4E;--d:#C9A84C;--w:#FAF8F5;--t:#2D1B24;--m:#8C7A86;--r:#DC3545;--h:#FD7E14;--g:#28A745}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:var(--w);color:var(--t);font-size:14px}}
h1{{font-family:Cormorant Garamond,serif;font-weight:600;font-size:1.2rem}}
.banner{{background:#FFF3CD;color:#856404;text-align:center;font-size:0.7rem;padding:2px 0}}
.top{{background:linear-gradient(135deg,#5C1F3A,#7B2D4E);color:#fff;padding:8px 12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px}}
.c{{max-width:1400px;margin:0 auto;padding:6px 10px}}
.card{{background:#fff;border-radius:6px;padding:10px;margin-bottom:8px;box-shadow:0 1px 4px rgba(123,45,78,0.06)}}
.card.crit{{border-left:3px solid var(--r)}}
table{{width:100%;border-collapse:collapse;font-size:0.7rem}}
th{{background:var(--v);color:#fff;padding:4px 5px;text-align:left;font-weight:600;font-size:0.65rem;white-space:nowrap}}
td{{padding:3px 5px;border-bottom:1px solid #E8E0DA;white-space:nowrap;font-size:0.7rem}}
tr:hover{{background:#F8F4F0}}
.b{{display:inline-block;font-size:0.5rem;font-weight:700;padding:1px 5px;border-radius:8px;color:#fff}}
.b-CRITICAL{{background:var(--r)}}.b-HIGH{{background:var(--h)}}
.b-MEDIUM{{background:#FFC107;color:#5A3F00}}.b-LOW{{background:var(--g)}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px;margin-bottom:8px}}
.kp{{background:#fff;border-radius:6px;padding:8px;box-shadow:0 1px 3px rgba(123,45,78,0.04);border-left:3px solid var(--d)}}
.kp .l{{font-size:0.55rem;text-transform:uppercase;letter-spacing:0.3px;color:var(--m)}}
.kp .v{{font-size:1.1rem;font-weight:700;color:var(--v)}}
.kp .s{{font-size:0.6rem}}
.f{{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:6px}}
.f label{{font-size:0.6rem;font-weight:600;text-transform:uppercase;color:var(--m)}}
.f select,.f input{{padding:2px 5px;border:1px solid #ccc;border-radius:3px;font-family:Inter;font-size:0.7rem}}
.fc{{font-size:0.7rem;color:var(--m);background:#F0EBE6;padding:2px 6px;border-radius:10px}}
.det{{display:none;padding:6px 0 0 8px}}
.det.show{{display:block}}
.bt{{padding:2px 8px;border:1px solid var(--v);border-radius:3px;background:transparent;color:var(--v);cursor:pointer;font-size:0.65rem}}
.bt:hover{{background:var(--v);color:#fff}}
@media(max-width:640px){{.k{{grid-template-columns:1fr 1fr}}}}
</style></head>
<body>
<div class=banner>MOCK - Compra TOTAL por fornecedor. Cobertura 120d (150/180 se < R$10k). Velocidade media por categoria para produtos sem venda.</div>
<div class=top><h1>Chez Violeta - Compra por Fornecedor</h1><div class=fc id=hdr>-</div></div>
<div class=c id=app></div>
<script>
var ORDERS = {js_orders};
document.getElementById('hdr').innerHTML = ORDERS.length + ' fornecedores | R$' + ORDERS.reduce(function(s,o){{return s+o.total_cost}},0).toFixed(0) + ' | ' + ORDERS.filter(function(o){{return o.meets_minimum}}).length + ' atingem R$10k';

function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}
function toggle(id){{var e=document.getElementById('d-'+id);if(e)e.classList.toggle('show')}}

function render(){{
  var f=(document.getElementById('ff')||{{}}).value||'todos';
  var filtered=ORDERS.filter(function(o){{
    if(f==='crit'&&o.urgency!=='CRITICAL')return false;
    if(f==='min'&&!o.meets_minimum)return false;
    return true;
  }});
  var cards=filtered.map(function(o,i){{
    var cls=o.urgency==='CRITICAL'?'card crit':'card';
    var minTxt=o.meets_minimum?'<span style=color:#28A745>OK R$10k</span>':'<span style=color:#DC3545>Abaixo (cob.'+o.target_days+'d)</span>';
    if(o.is_biju)minTxt='<span style=color:#C9A84C>Bijuterias</span>';
    var rows=o.items.map(function(p){{return '<tr><td>'+esc(p.name)+'</td><td>'+p.code+'</td><td>'+p.cat+'</td><td>'+p.stock+'</td><td>'+p.coverage+'d</td><td>'+p.qty+'</td><td>R$'+p.cost.toFixed(0)+'</td></tr>'}}).join('');
    return '<div class="'+cls+'"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">'+
      '<div><strong>'+esc(o.name)+'</strong> <span class="b b-'+o.urgency+'">'+o.urgency+'</span> <span style=font-size:0.6rem;color:var(--m)>'+o.compliance+'% | '+o.n_total_products+' prod</span></div>'+
      '<div style=display:flex;gap:4px;align-items:center>'+
        '<span style=font-size:0.7rem><b>'+o.n_items+'</b> itens | <b>R$'+o.total_cost.toFixed(0)+'</b></span>'+
        '<span style=font-size:0.65rem>'+minTxt+'</span>'+
        '<button class=bt onclick=toggle('+i+')>Itens</button></div></div>'+
      '<div style=font-size:0.6rem;color:var(--m);margin-top:2px>'+
        'Cob.alvo: '+o.target_days+'d | Min.alerta: '+o.min_coverage+'d | '+o.n_alertas+' alertas | '+o.total_qty+' un | '+o.categories.join(', ')+
      '</div>'+
      '<div class=det id="d-'+i+'"><div style=max-height:300px;overflow-y:auto><table><thead><tr><th>Produto</th><th>Cod</th><th>Cat</th><th>Estq</th><th>Cob</th><th>Pedir</th><th>Custo</th></tr></thead><tbody>'+rows+'</tbody></table></div></div></div>';
  }}).join('');
  document.getElementById('app').innerHTML=
    '<div class=k>'+
      '<div class=kp><div class=l>Fornecedores</div><div class=v>'+ORDERS.length+'</div><div class=s>Com alertas</div></div>'+
      '<div class=kp><div class=l>Valor Total</div><div class=v>R$'+ORDERS.reduce(function(s,o){{return s+o.total_cost}},0).toFixed(0)+'</div><div class=s>Cob.'+ORDERS[0].target_days+'d</div></div>'+
      '<div class=kp><div class=l>Atende R$10k</div><div class=v>'+ORDERS.filter(function(o){{return o.meets_minimum}}).length+'</div><div class=s>Podem pedir</div></div>'+
      '<div class=kp><div class=l>Itens Total</div><div class=v>'+ORDERS.reduce(function(s,o){{return s+o.n_items}},0)+'</div></div>'+
    '</div>'+
    '<div class=f><label>Filtro</label><select id=ff onchange=render()>'+
      '<option value=todos>Todos</option><option value=crit>Criticos</option><option value=min>Atende R$10k</option></select>'+
      '<span class=fc>'+filtered.length+' fornecedores</span></div>'+
    '<div id=cards>'+cards+'</div>';
}}
render();
</script></body></html>'''

out_path = BASE + "/artifacts/design/dashboard-comprador/index.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

tot = sum(s["total_cost"] for s in supplier_orders)
ok = sum(1 for s in supplier_orders if s["meets_minimum"])
print(f"Dashboard v5: {os.path.getsize(out_path):,} bytes")
print(f"Fornecedores: {len(supplier_orders)} | Valor: R$ {tot:,.2f} | Atende R$10k: {ok}")
