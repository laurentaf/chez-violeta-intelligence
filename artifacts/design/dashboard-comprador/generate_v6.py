#!/usr/bin/env python3
"""Generate dashboard v6 - Duas visoes + previsao, self-contained HTML."""
import json
import os

DATA_PATH = "F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/data_v6.json"
OUTPUT_PATH = "F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html"

with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

kpi = data["kpi"]
v1 = data["visao1_vestuario"]
v1stats = data["visao1_stats"]
v2 = data["visao2_fornecedores"]
v2stats = data["visao2_stats"]
v3 = data["visao3_forecast"]
semanas = data["forecast_semanas"]

# Build VISAO 1 table rows
v1_rows = []
for item in v1:
    acao_cls = "acao-comprar" if item["acao"] == "COMPRAR" else "acao-ok"
    v1_rows.append(f"""<tr class="{acao_cls}">
    <td>{item['produto']}</td>
    <td>{item['tamanho']}</td>
    <td class="num">{item['estoque']}</td>
    <td class="num">{item['necessidade']}</td>
    <td class="num">{item['diferenca']:+,d}</td>
    <td><span class="badge-{item['acao'].lower()}">{item['acao']}</span></td>
</tr>""")

v1_comprar = [i for i in v1 if i["acao"] == "COMPRAR"]

# Build VISAO 2 table rows
v2_rows = []
for f in v2:
    ating_cls = "atinge-sim" if f["atinge_10k"] == "SIM" else "atinge-nao"
    v2_rows.append(f"""<tr class="{ating_cls}">
    <td><strong>{f['fornecedor']}</strong></td>
    <td class="num">{f['n_produtos']}</td>
    <td class="num">{f['cobertura_media']:.1f}</td>
    <td class="num">R$ {f['valor_estimado']:,.0f}</td>
    <td><span class="badge-{'sim' if f['atinge_10k']=='SIM' else 'nao'}">{f['atinge_10k']}</span></td>
</tr>""")

# Build VISAO 3 forecast table
v3_rows = []
for c in v3:
    bar_pct = min(c["media_semanal"] / max(x["media_semanal"] for x in v3) * 100, 100)
    v3_rows.append(f"""<tr>
    <td>{c['categoria']}</td>
    <td class="num">{c['media_semanal']:,.0f}</td>
    <td class="num">{c['previsao_26s']:,.0f}</td>
    <td><div class="bar-container"><div class="bar" style="width:{bar_pct:.0f}%"></div></div></td>
</tr>""")

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chez Violeta - Comprador v6</title>
<style>
:root{{--v:#7B2D4E;--d:#C9A84C;--w:#FAF8F5;--t:#2D1B24;--m:#8C7A86;--r:#DC3545;--h:#FD7E14;--g:#28A745;--b:#E8E0DA}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:var(--w);color:var(--t);font-size:14px;line-height:1.5}}
h1,h2,h3{{font-family:'Cormorant Garamond',serif;font-weight:700;color:var(--v)}}
h1{{font-size:1.5rem}}h2{{font-size:1.2rem;margin:16px 0 8px;border-bottom:2px solid var(--d);padding-bottom:4px}}
h3{{font-size:1rem;margin:12px 0 6px}}

/* Header */
.header{{background:linear-gradient(135deg,#5C1F3A,#7B2D4E);color:#fff;padding:12px 16px}}
.header h1{{color:#fff;font-size:1.3rem}}
.kpi-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0;max-width:800px}}
.kpi-card{{background:rgba(255,255,255,0.1);border-radius:8px;padding:10px 14px;text-align:center}}
.kpi-card .label{{font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;opacity:0.8}}
.kpi-card .value{{font-size:1.4rem;font-weight:700;font-family:'Cormorant Garamond',serif}}

/* Content */
.container{{max-width:1400px;margin:0 auto;padding:10px 16px}}

/* Cards */
.card{{background:#fff;border-radius:8px;padding:14px;margin-bottom:12px;box-shadow:0 1px 4px rgba(123,45,78,0.08)}}
.card-explicativo{{background:#F8F4F0;border-left:3px solid var(--d);padding:8px 12px;margin:6px 0 10px;font-size:0.8rem;color:var(--m);border-radius:0 4px 4px 0}}
.card-explicativo strong{{color:var(--t)}}

/* Tabs */
.tabs{{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}}
.tab-btn{{padding:6px 14px;border:1px solid var(--v);background:transparent;color:var(--v);border-radius:4px;cursor:pointer;font-family:Inter;font-size:0.75rem;font-weight:500;transition:all 0.2s}}
.tab-btn.active{{background:var(--v);color:#fff}}
.tab-btn:hover{{background:var(--v);color:#fff;opacity:0.9}}
.tab-content{{display:none}}
.tab-content.active{{display:block}}

/* Tables */
.table-wrap{{overflow-x:auto;max-height:500px;overflow-y:auto}}
table{{width:100%;border-collapse:collapse;font-size:0.75rem}}
th{{background:var(--v);color:#fff;padding:6px 8px;text-align:left;font-weight:600;font-size:0.7rem;white-space:nowrap;position:sticky;top:0;z-index:1}}
td{{padding:4px 8px;border-bottom:1px solid var(--b);white-space:nowrap}}
tr:hover{{background:#F8F4F0}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}

/* Badges */
.badge-comprar,.badge-ok,.badge-sim,.badge-nao{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:0.65rem;font-weight:600;color:#fff}}
.badge-comprar,.badge-nao{{background:var(--r)}}
.badge-ok,.badge-sim{{background:var(--g)}}

/* Action classes */
.acao-comprar{{background:#FFF5F5}}
.acao-ok{{background:#F5FFF5}}

/* Supplier classes */
.atinge-sim{{}}
.atinge-nao{{background:#FFF8F0}}

/* Forecast bar */
.bar-container{{background:var(--b);height:12px;border-radius:6px;overflow:hidden;min-width:80px}}
.bar{{height:100%;background:linear-gradient(90deg,var(--v),var(--d));border-radius:6px;transition:width 0.5s}}

/* Cards grid */
.card-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}}

@media(max-width:640px){{
.kpi-row{{grid-template-columns:1fr}}
.card-grid{{grid-template-columns:1fr}}
}}

/* Summary cards */
.summary-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}}
.summary-item{{background:var(--w);border:1px solid var(--b);border-radius:6px;padding:6px 12px;font-size:0.75rem}}
.summary-item .num{{font-weight:700;color:var(--v);font-size:0.9rem}}
</style>
</head>
<body>

<div class="header">
    <h1>&#9670; Chez Violeta &mdash; Gestao de Compras v6</h1>
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="label">Fornecedores p/ comprar</div>
            <div class="value">{kpi['fornecedores_comprar']}</div>
        </div>
        <div class="kpi-card">
            <div class="label">Itens de vestuario em falta</div>
            <div class="value">{kpi['itens_vestuario_falta']:,d}</div>
        </div>
        <div class="kpi-card">
            <div class="label">Valor total estimado</div>
            <div class="value">R$ {kpi['valor_total_estimado']:,.0f}</div>
        </div>
    </div>
</div>

<div class="container">

<div class="tabs">
    <button class="tab-btn active" onclick="showTab('v1')">Vestuario</button>
    <button class="tab-btn" onclick="showTab('v2')">Demais Categorias</button>
    <button class="tab-btn" onclick="showTab('v3')">Previsao</button>
</div>

<!-- ========== VISAO 1 ========== -->
<div id="tab-v1" class="tab-content active">
    <h2>&#128083; Visao 1 &mdash; Vestuario (roupas)</h2>
    <div class="card-explicativo">
        <strong>O que e esta tela?</strong> Produtos de vestuario sem fornecedor definido.
        A coluna <strong>Necessidade (120d)</strong> calcula quantas pecas seriam necessarias
        para cobrir 120 dias de venda, com base na media historica das ultimas 52 semanas.
        Itens marcados como <strong>COMPRAR</strong> estao abaixo da cobertura ideal.
    </div>

    <div class="summary-row">
        <div class="summary-item">Total de itens: <span class="num">{v1stats['total_itens']}</span></div>
        <div class="summary-item">Precisam comprar: <span class="num" style="color:var(--r)">{v1stats['itens_comprar']}</span></div>
        <div class="summary-item">Cobertura OK: <span class="num" style="color:var(--g)">{v1stats['itens_ok']}</span></div>
    </div>

    <div class="card">
        <div class="table-wrap">
        <table>
            <thead><tr>
                <th>Produto</th><th>Tamanho</th><th class="num">Estoque Atual</th>
                <th class="num">Necessidade 120d</th><th class="num">Diferenca</th><th>Acao</th>
            </tr></thead>
            <tbody>
                {chr(10).join(v1_rows)}
            </tbody>
        </table>
        </div>
    </div>

    <h3>Itens criticos (precisam comprar)</h3>
    <div class="card-grid">
"""

# Cards for items that need buying
for item in v1_comprar:
    html += f"""        <div class="card" style="border-left:3px solid var(--r)">
            <div style="font-weight:600;font-size:0.85rem">{item['produto']}</div>
            <div style="font-size:0.7rem;color:var(--m)">
                Tamanho: {item['tamanho']} |
                Estoque: <strong>{item['estoque']}</strong> |
            </div>
            <div style="font-size:0.7rem;color:var(--m)">
                Necessario: <strong>{item['necessidade']}</strong> |
                Diferenca: <strong style="color:var(--r)">{item['diferenca']:+,d}</strong>
            </div>
        </div>
"""

html += f"""    </div>
</div>

<!-- ========== VISAO 2 ========== -->
<div id="tab-v2" class="tab-content">
    <h2>&#128230; Visao 2 &mdash; Demais Categorias por Fornecedor</h2>
    <div class="card-explicativo">
        <strong>O que e esta tela?</strong> Fornecedores de categorias nao-vestuario
        (commodities, moda praia, underwear, linha noite, etc). A coluna
        <strong>Valor Estimado</strong> considera o estoque atual x custo unitario.
        Fornecedores com <strong>R$10k+</strong> sao prioridade de compra.
    </div>

    <div class="summary-row">
        <div class="summary-item">Total fornecedores: <span class="num">{v2stats['total_fornecedores']}</span></div>
        <div class="summary-item">Atingem R$10k: <span class="num" style="color:var(--g)">{v2stats['atingem_10k']}</span></div>
        <div class="summary-item">Abaixo de R$10k: <span class="num" style="color:var(--h)">{v2stats['total_fornecedores'] - v2stats['atingem_10k']}</span></div>
    </div>

    <div class="card">
        <div class="table-wrap">
        <table>
            <thead><tr>
                <th>Fornecedor</th><th class="num">N Produtos</th><th class="num">Cobertura Media</th>
                <th class="num">Valor Estimado</th><th>Atinge R$10k?</th>
            </tr></thead>
            <tbody>
                {chr(10).join(v2_rows)}
            </tbody>
        </table>
        </div>
    </div>
</div>

<!-- ========== VISAO 3 ========== -->
<div id="tab-v3" class="tab-content">
    <h2>&#128200; Visao 3 &mdash; Previsao de Vendas (26 semanas)</h2>
    <div class="card-explicativo">
        <strong>O que e esta tela?</strong> Projecao de vendas para as proximas 26 semanas
        baseada na media movel das vendas das ultimas 52 semanas por categoria.
        O grafico de barras mostra a forca relativa de cada categoria.
    </div>

    <div class="card">
        <div class="table-wrap">
        <table>
            <thead><tr>
                <th>Categoria</th><th class="num">Media Semanal</th><th class="num">Previsao 26 Semanas</th><th>Forca Relativa</th>
            </tr></thead>
            <tbody>
                {chr(10).join(v3_rows)}
            </tbody>
        </table>
        </div>
    </div>

    <div class="card">
        <h3>Semanas projetadas</h3>
        <div style="display:flex;flex-wrap:wrap;gap:3px">
"""

for s in semanas:
    html += f'            <span style="background:var(--w);border:1px solid var(--b);border-radius:3px;padding:1px 5px;font-size:0.65rem">{s}</span>\n'

html += """        </div>
    </div>

    <div class="card-explicativo">
        <strong>Nota:</strong> Esta previsao usa media movel simples.
        O modelo de regressao OLS (R²=0.726) mostra que UNDERWARE e LINHA NOITE
        sao as categorias mais fortes. Q3 (inverno) tem efeito negativo.
        Consulte o README para detalhes do modelo.
    </div>
</div>

</div><!-- .container -->

<script>
function showTab(id) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + id).classList.add('active');
    document.querySelector('[onclick="showTab(\\'' + id + '\\')"]').classList.add('active');
}
</script>

</body>
</html>"""

with open(OUTPUT_PATH, 'w', newline='\n', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard v6 generated: {OUTPUT_PATH}")
print(f"  {len(html)} bytes")
print(f"  V1: {len(v1)} linhas, {v1stats['itens_comprar']} comprar")
print(f"  V2: {len(v2)} fornecedores")
print(f"  V3: {len(v3)} categorias, {len(semanas)} semanas")
