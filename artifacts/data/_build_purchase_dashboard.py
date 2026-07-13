#!/usr/bin/env python3
"""
Build purchase dashboard for Chez Violeta:
1. Extract data from DuckDB + Prophet forecast
2. Calculate purchase needs per product
3. Output purchase_data.json and index.html
"""

import duckdb
import pandas as pd
import numpy as np
import json

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)
import os
import math
from collections import defaultdict

# ─── Paths ───────────────────────────────────────────────────────
DB_PATH = 'F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb'
FORECAST_PATH = 'F:/projects/chez-violeta-intelligence/artifacts/data/prophet_forecast_future.csv'
OUTPUT_DIR = 'F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador'
JSON_PATH = os.path.join(OUTPUT_DIR, 'purchase_data.json')
HTML_PATH = os.path.join(OUTPUT_DIR, 'index.html')

os.makedirs(OUTPUT_DIR, exist_ok=True)

con = duckdb.connect(DB_PATH)

# ─── 1. Get latest stock date ────────────────────────────────────
latest_stock_date = con.execute("""
    SELECT MAX(id_data) FROM gold.fato_estoque_diario
""").fetchone()[0]
print(f"Latest stock date: {latest_stock_date}")

# Count sales days
sales_days = con.execute("""
    SELECT COUNT(DISTINCT id_data) 
    FROM gold.fato_estoque_diario 
    WHERE qtd_venda > 0
""").fetchone()[0]
print(f"Sales days: {sales_days}")

# ─── 2. Get product data with stock and velocity ────────────────
products = con.execute(f"""
    SELECT 
        p.id_produto,
        p.des_produto,
        p.des_artigo,
        p.cod_artigo,
        p.cod_tamanho,
        p.des_tamanho,
        p.des_categoria,
        p.des_linha,
        COALESCE(p.cod_fornecedor, 'VESTUARIO') as fornecedor,
        p.val_custo_inicial,
        COALESCE(fe.qtd_estoque, 0) as estoque,
        COALESCE(sales.qtd_venda_total, 0) as qtd_venda_total,
        COALESCE(sales.vel_diaria, 0.0) as vel_diaria
    FROM gold.dim_produto p
    LEFT JOIN (
        SELECT id_produto, SUM(qtd_estoque) as qtd_estoque
        FROM gold.fato_estoque_diario
        WHERE id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
        GROUP BY id_produto
    ) fe ON p.id_produto = fe.id_produto
    LEFT JOIN (
        SELECT 
            id_produto, 
            SUM(qtd_venda) as qtd_venda_total,
            SUM(qtd_venda)::float / {sales_days} as vel_diaria
        FROM gold.fato_estoque_diario
        WHERE qtd_venda > 0
        GROUP BY id_produto
    ) sales ON p.id_produto = sales.id_produto
    WHERE p.dat_fim_vigencia IS NULL
      AND p.des_status = 'ATIVO'
      AND p.des_categoria IS NOT NULL
      AND p.id_produto > 0
      AND (fe.qtd_estoque > 0 OR fe.qtd_estoque IS NOT NULL)
    ORDER BY p.des_categoria, p.des_produto, p.cod_tamanho
""").fetchdf()

print(f"Total active products with stock: {len(products)}")
print(f"Categories: {list(products['des_categoria'].unique())}")

# ─── 3. Load Prophet forecast ────────────────────────────────────
forecast = pd.read_csv(FORECAST_PATH)
forecast['ds'] = pd.to_datetime(forecast['ds'])

# 120-day total forecast per Prophet category
prophet_by_category = {}
for cat in forecast['categoria'].unique():
    cat_df = forecast[forecast['categoria'] == cat]
    total = cat_df['yhat'].sum()
    prophet_by_category[cat] = {
        'total_120d': total,
        'daily_avg': total / len(cat_df),
        'days': len(cat_df)
    }
    print(f"  Prophet {cat}: {total:.0f} total over {len(cat_df)} days ({total/len(cat_df):.1f}/day)")

# dim_produto -> Prophet category mapping
CATEGORY_MAP = {
    'ACESSORIOS': 'OUTROS',
    'BIJU / JOIAS': 'OUTROS',
    'EROTICA': 'OUTROS',
    'FITNESS': 'OUTROS',
    'LINHA NOITE': 'LINHA NOITE',
    'MODA PRAIA': 'MODA PRAIA',
    'UNDERWARE': 'UNDERWARE',
    'VESTUARIO': 'VESTUARIO',
}

# ─── 4. Calculate purchase needs ─────────────────────────────────
products['cat_prophet'] = products['des_categoria'].map(CATEGORY_MAP).fillna('OUTROS')
cat_vel_total = products.groupby('cat_prophet')['vel_diaria'].sum().to_dict()
cat_product_count = products.groupby('cat_prophet').size().to_dict()

BIJU_SUPPLIERS = {'AMOR BIJU', 'ENOQUE BIJU', 'INTER BIJU', 'KARISMA BIJU',
                   'MAURO BIJU', 'MROS', 'RELUZ BIJU', 'ZORIK'}

results = []
for idx, row in products.iterrows():
    cat_p = row['cat_prophet']
    estoque = float(row['estoque'])
    vel = float(row['vel_diaria'])
    
    if math.isnan(vel) or math.isinf(vel):
        vel = 0.0
    
    if vel > 0:
        forecast_120d = vel * 120
    else:
        cat_fc = prophet_by_category.get(cat_p, prophet_by_category.get('OUTROS', {}))
        cat_total_fc = cat_fc.get('total_120d', 0)
        cat_total_vel = cat_vel_total.get(cat_p, 0)
        
        if cat_total_vel > 0:
            min_daily = cat_fc.get('daily_avg', 1) * 0.1
            forecast_120d = min_daily * 120
        else:
            count = cat_product_count.get(cat_p, 1)
            forecast_120d = max(1, cat_total_fc / count)
    
    forecast_120d = max(0, forecast_120d)
    precisa = max(0, forecast_120d - estoque)
    
    results.append({
        'id_produto': int(row['id_produto']),
        'des_produto': str(row['des_produto'] or ''),
        'des_artigo': str(row['des_artigo'] or ''),
        'cod_artigo': str(row['cod_artigo'] or ''),
        'cod_tamanho': str(row['cod_tamanho'] or ''),
        'des_tamanho': str(row['des_tamanho'] or ''),
        'des_categoria': str(row['des_categoria'] or ''),
        'des_linha': str(row['des_linha'] or ''),
        'fornecedor': str(row['fornecedor'] or 'VESTUARIO'),
        'val_custo_inicial': float(row['val_custo_inicial']) if pd.notna(row['val_custo_inicial']) and float(row['val_custo_inicial']) > 0 else 0.0,
        'estoque': round(estoque, 0),
        'vel_diaria': round(vel, 4),
        'forecast_120d': round(forecast_120d, 1),
        'qtd_a_pedir': max(0, round(precisa, 0)),
        'precisa': bool(precisa > 1),
    })

print(f"\nTotal product-variants analyzed: {len(results)}")
products_with_need = [r for r in results if r['precisa']]
print(f"Products needing purchase: {len(products_with_need)}")

# ─── 5. Build supplier data ──────────────────────────────────────
supplier_products = defaultdict(list)
for r in results:
    supplier_products[r['fornecedor']].append(r)

suppliers_df = con.execute("""
    SELECT DISTINCT cod_fornecedor
    FROM gold.dim_fornecedor
    WHERE cod_fornecedor != 'N/A'
    ORDER BY cod_fornecedor
""").fetchdf()
all_suppliers = set(suppliers_df['cod_fornecedor'].tolist())

supplier_data = []
for sup_name in sorted(supplier_products.keys()):
    prods = supplier_products[sup_name]
    needs = [p for p in prods if p['precisa']]
    categories = sorted(set(p['des_categoria'] for p in prods))
    total_pedido = sum(p['qtd_a_pedir'] * p['val_custo_inicial'] for p in needs)
    total_pedido_qtd = sum(p['qtd_a_pedir'] for p in needs)
    total_estoque = sum(p['estoque'] for p in prods)
    compliance = 'A'
    is_biju = sup_name in BIJU_SUPPLIERS or 'BIJU' in sup_name.upper()
    
    supplier_data.append({
        'nome': sup_name,
        'compliance': compliance,
        'categorias': categories,
        'total_produtos': len(prods),
        'total_a_comprar': round(total_pedido, 2),
        'total_a_comprar_qtd': int(total_pedido_qtd),
        'total_estoque': int(total_estoque),
        'is_biju': is_biju,
        'precisa_comprar': len(needs) > 0,
        'produtos': sorted([{
            'des_produto': p['des_produto'],
            'cod_artigo': p['cod_artigo'],
            'des_artigo': p['des_artigo'],
            'cod_tamanho': p['cod_tamanho'],
            'des_tamanho': p['des_tamanho'],
            'des_categoria': p['des_categoria'],
            'des_linha': p['des_linha'],
            'estoque': int(p['estoque']),
            'forecast_120d': p['forecast_120d'],
            'qtd_a_pedir': int(p['qtd_a_pedir']),
            'val_custo_inicial': p['val_custo_inicial'],
            'precisa': p['precisa'],
            'vel_diaria': p['vel_diaria'],
        } for p in needs], key=lambda x: (
            0 if x['forecast_120d'] - x['estoque'] <= 0
            else (x['estoque'] / max(x['forecast_120d'], 1)),
            -x['qtd_a_pedir']
        ))
    })

print(f"Suppliers with products: {len(supplier_data)}")
print(f"Suppliers needing purchase: {sum(1 for s in supplier_data if s['precisa_comprar'])}")

# ─── 6. Build VESTUARIO section ──────────────────────────────────
vestuario_prods = [r for r in results if r['des_categoria'] == 'VESTUARIO']
vestuario_by_type = defaultdict(list)
for r in vestuario_prods:
    vestuario_by_type[r['des_produto']].append(r)

vestuario_data = []
for prod_type in sorted(vestuario_by_type.keys()):
    variants = vestuario_by_type[prod_type]
    needs = [v for v in variants if v['precisa']]
    variants_sorted = sorted(variants, key=lambda x: (
        int(x['estoque']) / max(float(x['forecast_120d']), 1) if float(x['forecast_120d']) > 0 else 999,
        -x['qtd_a_pedir'],
        x['cod_tamanho']
    ))
    
    vestuario_data.append({
        'tipo': prod_type,
        'total_variants': len(variants),
        'needs_purchase': len(needs),
        'variants': [{
            'des_produto': v['des_produto'],
            'cod_artigo': v['cod_artigo'],
            'des_artigo': v['des_artigo'],
            'cod_tamanho': v['cod_tamanho'],
            'des_tamanho': v['des_tamanho'],
            'estoque': int(v['estoque']),
            'forecast_120d': v['forecast_120d'],
            'qtd_a_pedir': int(v['qtd_a_pedir']),
            'val_custo_inicial': v['val_custo_inicial'],
            'precisa': v['precisa'],
            'fornecedor': v['fornecedor'],
        } for v in variants_sorted],
    })

# ─── 7. Build category overview ──────────────────────────────────
categories_overview = defaultdict(lambda: {'total_estoque': 0, 'total_forecast': 0,
                                             'total_pedir': 0, 'total_valor': 0, 'qtd_produtos': 0})
for r in results:
    cat = r['des_categoria']
    categories_overview[cat]['total_estoque'] += r['estoque']
    categories_overview[cat]['total_forecast'] += r['forecast_120d']
    categories_overview[cat]['qtd_produtos'] += 1
    if r['precisa']:
        categories_overview[cat]['total_pedir'] += r['qtd_a_pedir']
        categories_overview[cat]['total_valor'] += r['qtd_a_pedir'] * r['val_custo_inicial']

categories_list = [{'nome': k, **v} for k, v in sorted(categories_overview.items())]

# ─── 8. Build final data structure ───────────────────────────────
total_all_estoque = sum(r['estoque'] for r in results)
total_all_pedir = sum(r['qtd_a_pedir'] for r in results if r['precisa'])
total_all_valor = sum(r['qtd_a_pedir'] * max(0, r['val_custo_inicial']) for r in results if r['precisa'])
total_fornecedores = sum(1 for s in supplier_data if s['precisa_comprar'])
total_categorias_criticas = sum(1 for c in categories_list if c['total_forecast'] > c['total_estoque'] * 2)

dashboard_data = {
    'meta': {
        'generated_at': pd.Timestamp.now().isoformat(),
        'latest_stock_date': str(latest_stock_date),
        'total_products_analyzed': len(results),
        'total_products_needing_purchase': len(products_with_need),
    },
    'overview': {
        'total_fornecedores': total_fornecedores,
        'total_a_comprar_valor': round(total_all_valor, 2),
        'total_a_comprar_qtd': int(total_all_pedir),
        'categorias_criticas': total_categorias_criticas,
        'total_estoque': int(total_all_estoque),
        'categories': categories_list,
    },
    'suppliers': [s for s in supplier_data if s['precisa_comprar']],
    'vestuario': vestuario_data,
}

# ─── 9. Write JSON ───────────────────────────────────────────────
with open(JSON_PATH, 'w', newline='\n', encoding='utf-8') as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    print(f"\nJSON written to: {JSON_PATH}")
print(f"JSON size: {os.path.getsize(JSON_PATH) / 1024:.1f} KB")

# ─── 10. Generate HTML ──────────────────────────────────────────
vest_badge_count = sum(1 for v in vestuario_data if v['needs_purchase'] > 0)
print(f"Vestuario types needing purchase: {vest_badge_count}")

data_json = json.dumps(dashboard_data, ensure_ascii=False, cls=NumpyEncoder)
stock_date_str = pd.Timestamp(str(latest_stock_date)).strftime('%d/%m/%Y')

# Read the HTML template and inject data
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard de Compras - Chez Violeta</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --vinho: #7B2D4E;
    --vinho-light: #9E4D6E;
    --vinho-dark: #5B1D3A;
    --dourado: #C9A84C;
    --dourado-light: #E0C86E;
    --off-white: #FAF8F5;
    --bg: #F5F2ED;
    --card-bg: #FFFFFF;
    --text: #2D2D2D;
    --text-light: #6B6B6B;
    --border: #E8E4DE;
    --green: #2E7D32;
    --red: #C62828;
    --orange: #E65100;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
}
h1, h2, h3, h4 {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 700;
}
h1 { font-size: 2rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.2rem; }
h4 { font-size: 1.1rem; }

.header {
    background: linear-gradient(135deg, var(--vinho) 0%, var(--vinho-dark) 100%);
    color: white;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.header h1 {
    font-size: 1.8rem;
    letter-spacing: 0.5px;
}
.header .subtitle {
    font-size: 0.85rem;
    opacity: 0.8;
    font-weight: 300;
}

.tabs {
    display: flex;
    gap: 0.25rem;
    background: var(--off-white);
    padding: 0.5rem 2rem;
    border-bottom: 2px solid var(--border);
    overflow-x: auto;
    flex-wrap: nowrap;
}
.tab-btn {
    padding: 0.6rem 1.2rem;
    border: none;
    background: transparent;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-light);
    white-space: nowrap;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    border-radius: 4px 4px 0 0;
}
.tab-btn:hover {
    color: var(--vinho);
    background: rgba(123,45,78,0.05);
}
.tab-btn.active {
    color: var(--vinho);
    border-bottom-color: var(--vinho);
    background: white;
}
.tab-btn .badge {
    display: inline-block;
    background: var(--vinho);
    color: white;
    font-size: 0.7rem;
    padding: 0.1rem 0.5rem;
    border-radius: 10px;
    margin-left: 0.3rem;
}

.content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem 2rem;
}
.section { display: none; }
.section.active { display: block; }

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}
.card {
    background: var(--card-bg);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border: 1px solid var(--border);
}
.card .card-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-light);
    margin-bottom: 0.3rem;
}
.card .card-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--vinho);
}
.card .card-sub {
    font-size: 0.8rem;
    color: var(--text-light);
    margin-top: 0.2rem;
}

.table-container {
    overflow-x: auto;
    margin-bottom: 1.5rem;
}
table {
    width: 100%;
    border-collapse: collapse;
    background: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 0.85rem;
}
th {
    background: var(--vinho);
    color: white;
    padding: 0.7rem 0.8rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
td {
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(123,45,78,0.03); }
tr.high-need td { background: rgba(198,40,40,0.04); }

tr.total-row td {
    background: var(--vinho);
    color: white;
    font-weight: 700;
    border-top: 2px solid var(--vinho-dark);
}

.filter-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    align-items: center;
}
.filter-bar select, .filter-bar input {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    background: white;
    color: var(--text);
}
.filter-bar select:focus, .filter-bar input:focus {
    outline: none;
    border-color: var(--vinho);
}

.supplier-header {
    background: linear-gradient(135deg, var(--vinho) 0%, var(--vinho-light) 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
}
.supplier-header h2 { font-size: 1.8rem; margin-bottom: 0.3rem; }
.supplier-header .meta {
    display: flex;
    gap: 2rem;
    font-size: 0.85rem;
    opacity: 0.9;
    flex-wrap: wrap;
}
.supplier-header .badge {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-biju {
    background: var(--dourado);
    color: var(--vinho-dark);
}

.vest-type-section { margin-bottom: 2rem; }
.vest-type-header {
    background: linear-gradient(135deg, var(--vinho-light) 0%, var(--vinho-dark) 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.vest-type-header h3 { margin: 0; font-size: 1.3rem; }
.vest-type-header .count { font-size: 0.85rem; opacity: 0.9; }

.tag {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
}
.tag-low { background: #C8E6C9; color: #2E7D32; }
.tag-mid { background: #FFF3E0; color: #E65100; }
.tag-high { background: #FFEBEE; color: #C62828; }
.tag-biju { background: #FFF8E1; color: #C9A84C; }

@media (max-width: 768px) {
    .header { padding: 1rem; flex-direction: column; text-align: center; gap: 0.5rem; }
    .tabs { padding: 0.5rem 1rem; }
    .content { padding: 1rem; }
    .card-grid { grid-template-columns: repeat(2, 1fr); }
    .supplier-header .meta { flex-direction: column; gap: 0.5rem; }
}
</style>
</head>
<body>

<div class="header">
    <div>
        <h1>Chez Violeta &#9825; Compras</h1>
        <div class="subtitle">Dashboard de Pedidos por Fornecedor</div>
    </div>
    <div style="text-align:right;font-size:0.8rem;opacity:0.8;">
        <div>Estoque: STOCK_DATE</div>
        <div id="generated-date"></div>
    </div>
</div>

<nav class="tabs" id="main-tabs">
    <button class="tab-btn active" data-tab="home" onclick="showTab('home')">Visao Geral</button>
    <button class="tab-btn" data-tab="vestuario" onclick="showTab('vestuario')">Vestuario <span class="badge">VEST_BADGE</span></button>
    <div style="flex:1;min-width:0.5rem;"></div>
    <button class="tab-btn dropdown-toggle" onclick="toggleSupplierDropdown()" style="position:relative;">Fornecedores &#9660;</button>
</nav>

<div id="supplier-dropdown" style="display:none;position:fixed;top:auto;background:white;border:1px solid var(--border);border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);max-height:400px;overflow-y:auto;z-index:200;min-width:280px;"></div>

<div class="content">

<div id="section-home" class="section active">
    <div class="card-grid" id="overview-cards">
        <div class="card">
            <div class="card-label">Fornecedores</div>
            <div class="card-value" id="ov-total-fornecedores">&mdash;</div>
            <div class="card-sub">precisam comprar</div>
        </div>
        <div class="card">
            <div class="card-label">Total a Comprar</div>
            <div class="card-value" id="ov-total-valor">&mdash;</div>
            <div class="card-sub" id="ov-total-qtd"></div>
        </div>
        <div class="card">
            <div class="card-label">Categorias Criticas</div>
            <div class="card-value" id="ov-cat-criticas">&mdash;</div>
            <div class="card-sub">estoque &lt; 50% da previsao</div>
        </div>
        <div class="card">
            <div class="card-label">Estoque Total</div>
            <div class="card-value" id="ov-total-estoque">&mdash;</div>
            <div class="card-sub">unidades em todas as lojas</div>
        </div>
    </div>

    <div class="filter-bar">
        <label style="font-weight:500;font-size:0.85rem;">Filtrar por categoria:</label>
        <select id="cat-filter" onchange="filterByCategory()">
            <option value="">Todas as categorias</option>
        </select>
        <span style="margin-left:auto;font-size:0.8rem;color:var(--text-light);" id="supplier-count"></span>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Fornecedor</th>
                    <th>Compliance</th>
                    <th>Categorias</th>
                    <th>Produtos</th>
                    <th>Estoque</th>
                    <th>A Comprar (qtd)</th>
                    <th>Total Pedido (R$)</th>
                    <th></th>
                </tr>
            </thead>
            <tbody id="supplier-table-body"></tbody>
        </table>
    </div>

    <div style="margin-top:2rem;">
        <h3>Categorias</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Categoria</th>
                        <th>Produtos</th>
                        <th>Estoque Total</th>
                        <th>Previsao 120d</th>
                        <th>A Comprar</th>
                        <th>Valor (R$)</th>
                    </tr>
                </thead>
                <tbody id="category-table-body"></tbody>
            </table>
        </div>
    </div>
</div>

<div id="section-vestuario" class="section">
    <div style="margin-bottom:1rem;">
        <h2>Compras Vestuario</h2>
        <p style="color:var(--text-light);font-size:0.9rem;">Produtos sem fornecedor definido &mdash; compra presencial por tipo e tamanho</p>
    </div>
    <div id="vestuario-content"></div>
</div>

<div id="supplier-sections"></div>

</div>

<script id="data-json" type="application/json">DATA_JSON_PLACEHOLDER</script>
<script>
var DATA = JSON.parse(document.getElementById('data-json').textContent);

function fmt(n) {
    if (n == null || isNaN(n)) return '\u2014';
    return Number(n).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function fmtMoney(n) {
    if (n == null || isNaN(n)) return '\u2014';
    return 'R$ ' + Number(n).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function coverageClass(est, fc) {
    var r = fc > 0 ? est / fc : 999;
    if (r >= 1.5) return 'tag-high';
    if (r >= 0.5) return 'tag-mid';
    return 'tag-low';
}
function coverageLabel(est, fc) {
    var r = fc > 0 ? est / fc : 999;
    if (r >= 1.5) return 'Excedente';
    if (r >= 0.5) return 'OK';
    return 'Critico';
}

function showTab(tabId) {
    document.querySelectorAll('.section').forEach(function(s) { s.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.getElementById('section-' + tabId).classList.add('active');
    var btn = document.querySelector('.tab-btn[data-tab="' + tabId + '"]');
    if (btn) btn.classList.add('active');
    document.getElementById('supplier-dropdown').style.display = 'none';
}

function toggleSupplierDropdown() {
    var dd = document.getElementById('supplier-dropdown');
    if (dd.style.display === 'block') { dd.style.display = 'none'; return; }
    var html = '<div style="padding:0.5rem 0;">';
    DATA.suppliers.forEach(function(s) {
        var slug = s.nome.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
        html += '<a href="#" onclick="showSupplier(\\'' + slug + '\\');return false;" style="display:block;padding:0.5rem 1rem;text-decoration:none;color:var(--text);border-bottom:1px solid var(--border);">';
        html += '<strong>' + s.nome + '</strong>';
        html += ' <span style="color:var(--text-light);font-size:0.8rem;">' + fmt(s.total_a_comprar_qtd) + ' un / ' + fmtMoney(s.total_a_comprar) + '</span>';
        if (s.is_biju) html += ' <span style="background:#FFF8E1;color:#C9A84C;font-size:0.7rem;padding:0.1rem 0.4rem;border-radius:3px;">BIJU</span>';
        html += '</a>';
    });
    html += '</div>';
    dd.innerHTML = html;
    var btn = document.querySelector('.dropdown-toggle');
    var rect = btn.getBoundingClientRect();
    dd.style.top = (rect.bottom + 4) + 'px';
    dd.style.left = Math.max(10, rect.right - 280) + 'px';
    dd.style.display = 'block';
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown-toggle') && !e.target.closest('#supplier-dropdown')) {
        document.getElementById('supplier-dropdown').style.display = 'none';
    }
});

function showSupplier(slug) {
    document.querySelectorAll('.section').forEach(function(s) { s.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.getElementById('section-sup-' + slug).classList.add('active');
    document.getElementById('supplier-dropdown').style.display = 'none';
}

function filterByCategory() {
    var cat = document.getElementById('cat-filter').value;
    var rows = document.querySelectorAll('#supplier-table-body tr');
    var visible = 0;
    rows.forEach(function(row) {
        var cats = row.getAttribute('data-categories') || '';
        if (!cat || cats.indexOf(cat) >= 0) {
            row.style.display = '';
            visible++;
        } else {
            row.style.display = 'none';
        }
    });
    document.getElementById('supplier-count').textContent = visible + ' fornecedores';
}

function renderOverview() {
    var o = DATA.overview;
    document.getElementById('ov-total-fornecedores').textContent = fmt(o.total_fornecedores);
    document.getElementById('ov-total-valor').textContent = fmtMoney(o.total_a_comprar_valor);
    document.getElementById('ov-total-qtd').textContent = fmt(o.total_a_comprar_qtd) + ' unidades';
    document.getElementById('ov-cat-criticas').textContent = fmt(o.categorias_criticas);
    document.getElementById('ov-total-estoque').textContent = fmt(o.total_estoque);

    var sel = document.getElementById('cat-filter');
    o.categories.forEach(function(c) {
        var opt = document.createElement('option');
        opt.value = c.nome;
        opt.textContent = c.nome + ' (' + fmt(c.qtd_produtos) + ' produtos)';
        sel.appendChild(opt);
    });

    var tbody = document.getElementById('supplier-table-body');
    var html = '';
    DATA.suppliers.sort(function(a,b) { return b.total_a_comprar_valor - a.total_a_comprar_valor; });
    DATA.suppliers.forEach(function(s) {
        var slug = s.nome.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
        html += '<tr data-categories="' + (s.categorias || []).join(',') + '">';
        html += '<td><strong>' + s.nome + '</strong>' + (s.is_biju ? ' <span class="tag tag-biju">BIJU</span>' : '') + '</td>';
        html += '<td>' + (s.compliance || '\u2014') + '</td>';
        html += '<td>' + (s.categorias || []).join(', ') + '</td>';
        html += '<td>' + fmt(s.total_a_comprar_qtd) + ' / ' + fmt(s.total_produtos) + '</td>';
        html += '<td>' + fmt(s.total_estoque) + '</td>';
        html += '<td>' + fmt(s.total_a_comprar_qtd) + '</td>';
        html += '<td>' + fmtMoney(s.total_a_comprar_valor) + '</td>';
        html += '<td><a href="#" onclick="showSupplier(\\'' + slug + '\\');return false;" style="color:var(--vinho);text-decoration:none;font-weight:600;white-space:nowrap;">Ver Pedido &rarr;</a></td>';
        html += '</tr>';
    });
    tbody.innerHTML = html;
    document.getElementById('supplier-count').textContent = DATA.suppliers.length + ' fornecedores';

    var cath = '';
    o.categories.sort(function(a,b) { return b.total_pedir - a.total_pedir; });
    o.categories.forEach(function(c) {
        cath += '<tr>';
        cath += '<td><strong>' + c.nome + '</strong></td>';
        cath += '<td>' + fmt(c.qtd_produtos) + '</td>';
        cath += '<td>' + fmt(c.total_estoque) + '</td>';
        cath += '<td>' + fmt(c.total_forecast) + '</td>';
        cath += '<td>' + fmt(c.total_pedir) + '</td>';
        cath += '<td>' + fmtMoney(c.total_valor) + '</td>';
        cath += '</tr>';
    });
    document.getElementById('category-table-body').innerHTML = cath;
}

function renderVestuario() {
    var container = document.getElementById('vestuario-content');
    var html = '';
    DATA.vestuario.forEach(function(vt) {
        if (vt.needs_purchase === 0) return;
        html += '<div class="vest-type-section">';
        html += '<div class="vest-type-header">';
        html += '<h3>' + vt.tipo + '</h3>';
        html += '<div class="count">' + vt.needs_purchase + ' de ' + vt.total_variants + ' variantes precisam compra</div>';
        html += '</div><div class="table-container"><table>';
        html += '<thead><tr><th>Produto</th><th>Codigo</th><th>Tamanho</th><th>Estoque</th><th>Previsao 120d</th><th>A Comprar</th><th>Valor Un.</th></tr></thead><tbody>';
        vt.variants.forEach(function(v) {
            if (!v.precisa) return;
            var isCrit = v.forecast_120d > 0 && v.estoque / v.forecast_120d < 0.3;
            html += '<tr' + (isCrit ? ' class="high-need"' : '') + '>';
            html += '<td>' + v.des_produto + '<br><span style="font-size:0.75rem;color:var(--text-light);">' + (v.des_artigo || '') + '</span></td>';
            html += '<td>' + (v.cod_artigo || '') + '</td>';
            html += '<td><strong>' + v.cod_tamanho + '</strong>' + (v.des_tamanho ? ' (' + v.des_tamanho + ')' : '') + '</td>';
            html += '<td>' + fmt(v.estoque) + '</td>';
            html += '<td>' + fmt(v.forecast_120d) + '</td>';
            html += '<td><strong>' + fmt(v.qtd_a_pedir) + '</strong></td>';
            html += '<td>' + fmtMoney(v.val_custo_inicial) + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
    });
    container.innerHTML = html;
}

function renderSuppliers() {
    var container = document.getElementById('supplier-sections');
    var html = '';
    DATA.suppliers.sort(function(a,b) { return b.total_a_comprar_valor - a.total_a_comprar_valor; });
    DATA.suppliers.forEach(function(s) {
        var slug = s.nome.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
        html += '<div id="section-sup-' + slug + '" class="section">';
        html += '<div class="supplier-header">';
        html += '<h2>' + s.nome + '</h2>';
        html += '<div class="meta">';
        html += '<span>Compliance: <strong>' + (s.compliance || 'N/A') + '</strong></span>';
        html += '<span>Categorias: <strong>' + (s.categorias || []).join(', ') + '</strong></span>';
        html += '<span>Produtos: <strong>' + fmt(s.total_produtos) + '</strong></span>';
        html += '<span>Estoque atual: <strong>' + fmt(s.total_estoque) + '</strong></span>';
        if (s.is_biju) html += '<span class="badge badge-biju">&#9825; Compra Manual (BIJU)</span>';
        html += '</div></div>';

        var prods = s.produtos || [];
        var totalQtd = 0, totalValor = 0;
        prods.forEach(function(p) { totalQtd += p.qtd_a_pedir; totalValor += p.qtd_a_pedir * p.val_custo_inicial; });

        html += '<div class="table-container"><table>';
        html += '<thead><tr><th>Produto</th><th>Codigo</th><th>Categoria</th><th>Tamanho</th><th>Estoque</th><th>Previsao 120d</th><th>Cobertura</th><th>A Comprar</th><th>Valor Un.</th><th>Total</th></tr></thead><tbody>';
        prods.forEach(function(p) {
            var ratio = p.forecast_120d > 0 ? (p.estoque / p.forecast_120d) : 999;
            var cls = coverageClass(p.estoque, p.forecast_120d);
            var lbl = coverageLabel(p.estoque, p.forecast_120d);
            var isCrit = ratio < 0.3;
            html += '<tr' + (isCrit ? ' class="high-need"' : '') + '>';
            html += '<td><strong>' + p.des_produto + '</strong><br><span style="font-size:0.75rem;color:var(--text-light);">' + (p.des_artigo || '') + '</span></td>';
            html += '<td>' + (p.cod_artigo || '') + '</td>';
            html += '<td>' + (p.des_categoria || '') + '<br><span style="font-size:0.7rem;color:var(--text-light);">' + (p.des_linha || '') + '</span></td>';
            html += '<td>' + p.cod_tamanho + (p.des_tamanho ? ' (' + p.des_tamanho + ')' : '') + '</td>';
            html += '<td>' + fmt(p.estoque) + '</td>';
            html += '<td>' + fmt(p.forecast_120d) + '</td>';
            html += '<td><span class="tag ' + cls + '">' + lbl + '</span></td>';
            html += '<td><strong>' + fmt(p.qtd_a_pedir) + '</strong></td>';
            html += '<td>' + fmtMoney(p.val_custo_inicial) + '</td>';
            html += '<td>' + fmtMoney(p.qtd_a_pedir * p.val_custo_inicial) + '</td>';
            html += '</tr>';
        });
        html += '<tr class="total-row"><td colspan="7"><strong>Total do Pedido</strong></td>';
        html += '<td><strong>' + fmt(totalQtd) + '</strong></td><td></td>';
        html += '<td><strong>' + fmtMoney(totalValor) + '</strong></td></tr>';
        html += '</tbody></table></div></div>';
    });
    container.innerHTML = html;
}

document.getElementById('generated-date').textContent = 'Gerado: ' + new Date().toLocaleString('pt-BR');
renderOverview();
renderVestuario();
renderSuppliers();
</script>
</body>
</html>"""

html = (HTML_TEMPLATE
    .replace('DATA_JSON_PLACEHOLDER', data_json)
    .replace('STOCK_DATE', stock_date_str)
    .replace('VEST_BADGE', str(vest_badge_count))
)

with open(HTML_PATH, 'w', newline='\n', encoding='utf-8') as f:
    f.write(html)

print(f"HTML written to: {HTML_PATH}")
print(f"HTML size: {os.path.getsize(HTML_PATH) / 1024:.1f} KB")

con.close()
print("\nDone!")
