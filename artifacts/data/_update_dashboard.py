"""
Update dashboard-index.html with regression predictions tab.
Adds a "Previsao" tab showing weekly forecast + 120-day purchase recommendations.
"""
import json
import pandas as pd

# ============================================================
# 1. Read existing dashboard
# ============================================================
with open('F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html', 'r', encoding='utf-8') as f:
    original = f.read()

print(f"Original dashboard: {len(original):,} bytes")

# Split at script boundaries
si = original.find('<script>')
ei = original.find('</script>')

before = original[:si+8]    # includes <script>
after = original[ei:]        # includes </script>
existing_js = original[si+8:ei]

# ============================================================
# 2. Load predictions data
# ============================================================
pred = pd.read_csv('F:/projects/chez-violeta-intelligence/artifacts/data/weekly_predictions.csv')
pred_json = json.dumps(pred.to_dict(orient='records'), ensure_ascii=False)

rec = pred.groupby('categoria').agg(
    previsao_120d=('previsao_media', lambda x: round(x.head(18).sum(), 1)),
    previsao_min_120d=('previsao_min', lambda x: round(x.head(18).sum(), 1)),
    previsao_max_120d=('previsao_max', lambda x: round(x.head(18).sum(), 1))
).reset_index().sort_values('previsao_120d', ascending=False)
rec_json = json.dumps(rec.to_dict(orient='records'), ensure_ascii=False)

# Load R² from model results
with open('F:/projects/chez-violeta-intelligence/artifacts/data/regression_model_results.json', 'r') as f:
    mr = json.load(f)
r2 = mr['r2']

print(f"Predictions data: {len(pred_json):,} chars")
print(f"Recommendations: {len(rec_json):,} chars")
print(f"R²: {r2}")

# ============================================================
# 3. Build new JS with predictions view
# ============================================================
new_js = existing_js + f"""

// ===== PREVISAO SEMANAL (regression model) =====
var PREDICTIONS = {pred_json};
var RECOMMENDATIONS = {rec_json};

function renderPrevisao(){{
  var catHtml = RECOMMENDATIONS.map(function(r){{
    return '<tr><td>'+r.categoria+'</td><td style=text-align:right>'+r.previsao_120d.toFixed(0)+'</td><td style=text-align:right>'+r.previsao_min_120d.toFixed(0)+'</td><td style=text-align:right>'+r.previsao_max_120d.toFixed(0)+'</td></tr>';
  }}).join('');

  var catSel = '<select id=pred-cat onchange=renderPrevisao() style="padding:2px 5px;border:1px solid #ccc;border-radius:3px;font-family:Inter;font-size:0.7rem">'+
    '<option value=TODAS>Todas as categorias</option>'+
    RECOMMENDATIONS.map(function(r){{return '<option value="'+esc(r.categoria)+'">'+r.categoria+'</option>';}}).join('')+
    '</select>';

  var selCat = (document.getElementById('pred-cat')||{{}}).value || 'TODAS';
  var weekData = selCat === 'TODAS' 
    ? PREDICTIONS 
    : PREDICTIONS.filter(function(p){{ return p.categoria === selCat; }});

  var weekRows = weekData.map(function(w){{
    return '<tr><td>'+esc(w.categoria)+'</td><td>'+w.data_inicio+'</td><td>W'+w.num_semana+'</td><td style=text-align:right>'+w.previsao_media.toFixed(0)+'</td><td style=text-align:right>'+w.previsao_min.toFixed(0)+'</td><td style=text-align:right>'+w.previsao_max.toFixed(0)+'</td></tr>';
  }}).join('');

  var total = weekData.reduce(function(s,w){{return s+w.previsao_media;}},0);
  var nWeeks = weekData.length > 0 ? 26 : 0;
  var nCats = weekData.length > 0 ? new Set(weekData.map(function(w){{return w.categoria;}})).size : 0;

  document.getElementById('app').innerHTML =
    '<div class=k>'+
      '<div class=kp><div class=l>Categorias</div><div class=v>'+RECOMMENDATIONS.length+'</div><div class=s>Com previsao</div></div>'+
      '<div class=kp><div class=l>Previsao 120d</div><div class=v>'+RECOMMENDATIONS.reduce(function(s,r){{return s+r.previsao_120d;}},0).toFixed(0)+'</div><div class=s>Unidades totais</div></div>'+
      '<div class=kp><div class=l>Semanas previstas</div><div class=v>'+nWeeks+'</div><div class=s>Por linha</div></div>'+
      '<div class=kp><div class=l>Categorias ativas</div><div class=v>'+nCats+'</div><div class=s>Na selecao</div></div>'+
    '</div>'+
    '<div style="margin-bottom:8px;font-size:0.85rem;font-weight:600;color:var(--v);font-family:Cormorant Garamond,serif">Previsao Semanal de Vendas por Categoria</div>'+
    '<div class=f><label>Categoria</label>'+catSel+'<span class=fc>'+(selCat==='TODAS'?'Todas':selCat)+' | '+weekData.length+' semanas</span></div>'+
    '<div style=max-height:400px;overflow-y:auto;margin-bottom:16px>'+
    '<table><thead><tr><th>Categoria</th><th>Data Inicio</th><th>Semana</th><th style=text-align:right>Prev.Media</th><th style=text-align:right>Prev.Min</th><th style=text-align:right>Prev.Max</th></tr></thead>'+
    '<tbody>'+weekRows+'</tbody></table></div>'+
    '<div style="margin-top:12px;margin-bottom:8px;font-size:0.85rem;font-weight:600;color:var(--v);font-family:Cormorant Garamond,serif">Recomendacao de Compra - 120 dias (18 semanas)</div>'+
    '<table><thead><tr><th>Categoria</th><th style=text-align:right>Prev. 120d</th><th style=text-align:right>Minimo</th><th style=text-align:right>Maximo</th></tr></thead>'+
    '<tbody>'+catHtml+'</tbody></table>'+
    '<div style="margin-top:12px;padding:8px;background:#FFF3CD;border-radius:4px;font-size:0.7rem">'+
      '<strong>Nota:</strong> Previsoes baseadas em modelo de regressao OLS (R²='+{r2}+'). '+
      'Dados historicos limitados (2018-2020, 97 obs). Usar com cautela. Re-treinar a cada mes.</div>';
}}

// View switching
var currentView = 'compra';

function switchView(view){{
  currentView = view;
  var tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(function(t){{t.style.background='transparent';t.style.color='#fff';t.style.border='1px solid rgba(255,255,255,0.3)';}});
  var active = document.getElementById('tab-'+view);
  if(active){{active.style.background='rgba(255,255,255,0.2)';active.style.border='1px solid rgba(255,255,255,0.1)';}}
  if(view==='compra') render();
  else renderPrevisao();
}}
"""

# ============================================================
# 4. Create complete HTML with navigation tabs
# ============================================================
html = before + '\n' + new_js + '\n' + after

# Add navigation tabs to the top bar
old_top = '<div class=top><h1>Chez Violeta - Compra por Fornecedor</h1><div class=fc id=hdr>-</div></div>'
new_top = '''<div class=top>
  <h1>Chez Violeta - Gestao de Compras</h1>
  <div style=display:flex;gap:4px;align-items:center>
    <button class=tab-btn id=tab-compra onclick=switchView("compra") style="background:rgba(255,255,255,0.2);color:#fff;border:1px solid rgba(255,255,255,0.1);padding:2px 10px;border-radius:3px;cursor:pointer;font-size:0.65rem">Fornecedores</button>
    <button class=tab-btn id=tab-previsao onclick=switchView("previsao") style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,0.3);padding:2px 10px;border-radius:3px;cursor:pointer;font-size:0.65rem">Previsao</button>
  </div>
  <div class=fc id=hdr>-</div>
</div>'''

html = html.replace(old_top, new_top)

# ============================================================
# 5. Write updated dashboard
# ============================================================
with open('F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Updated dashboard: {len(html):,} bytes")
print("Tabs: Fornecedores | Previsao")
print("Done!")
