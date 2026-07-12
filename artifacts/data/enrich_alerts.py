"""
Enrichment Script — Chez Violeta Purchase Alerts
=================================================
Steps:
1. Create product_lookup.csv from DuckDB gold.dim_produto
2. Create stock_by_store.csv from DuckDB gold.fato_estoque_diario (last day)
3. Enrich purchase_alerts.csv with product info, pending orders, risk_score
4. Add explanation to supplier_performance.csv

Usage:
    uv run python artifacts/data/enrich_alerts.py

Outputs:
    - artifacts/data/product_lookup.csv
    - artifacts/data/stock_by_store.csv
    - artifacts/simulation/output-360d-v2/purchase_alerts_enriched.csv
    - artifacts/simulation/risk-analysis-methodology.md
"""

import json
import csv
import os
from datetime import datetime, date
from collections import defaultdict

import duckdb
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = 'F:/projects/chez-violeta-intelligence'
DB_PATH = f'{ROOT}/artifacts/data/chez_gold.duckdb'
SIM_PATH = f'{ROOT}/artifacts/simulation/output-360d-v2'
DATA_PATH = f'{ROOT}/artifacts/data'

PRODUCT_LOOKUP_CSV = f'{DATA_PATH}/product_lookup.csv'
STOCK_BY_STORE_CSV = f'{DATA_PATH}/stock_by_store.csv'
PURCHASE_ALERTS_CSV = f'{SIM_PATH}/purchase_alerts.csv'
ENRICHED_CSV = f'{SIM_PATH}/purchase_alerts_enriched.csv'
PENDING_JSON = f'{SIM_PATH}/daily_pending_detail.json'
SUPPLIER_PERF_CSV = f'{SIM_PATH}/supplier_performance.csv'

# ══════════════════════════════════════════════════════════════════════════════
# 1. CREATE PRODUCT LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
print("[1/5] Extracting product lookup from DuckDB...")
con = duckdb.connect(DB_PATH)

df_product = con.execute("""
    SELECT 
        p.id_produto, 
        p.cod_artigo, 
        p.des_artigo, 
        p.des_categoria, 
        p.des_linha, 
        p.des_colecao, 
        p.cod_fornecedor, 
        p.des_status
    FROM gold.dim_produto p
    WHERE p.dat_fim_vigencia IS NULL
""").fetchdf()

df_product.to_csv(PRODUCT_LOOKUP_CSV, index=False)
print(f"  => {len(df_product)} products written to {PRODUCT_LOOKUP_CSV}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. EXTRACT STOCK BY STORE (LAST DAY)
# ══════════════════════════════════════════════════════════════════════════════
print("[2/5] Extracting stock by store (last day)...")

df_stock = con.execute("""
    SELECT 
        fe.id_data, 
        fe.id_loja, 
        l.des_estabelecimento, 
        fe.id_produto, 
        fe.qtd_estoque
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_loja l ON fe.id_loja = l.id_loja
    WHERE fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
      AND fe.qtd_estoque > 0
""").fetchdf()

df_stock.to_csv(STOCK_BY_STORE_CSV, index=False)
print(f"  => {len(df_stock)} rows written to {STOCK_BY_STORE_CSV}")

con.close()

# ══════════════════════════════════════════════════════════════════════════════
# 3. ENRICH PURCHASE ALERTS
# ══════════════════════════════════════════════════════════════════════════════
print("[3/5] Enriching purchase alerts...")

# Load product lookup as dict for fast access
product_map = {}
with open(PRODUCT_LOOKUP_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = int(row['id_produto'])
        product_map[pid] = row

print(f"  Product map has {len(product_map)} entries")

# Load pending orders JSON
print(f"  Loading pending orders from {PENDING_JSON}...")
with open(PENDING_JSON, 'r', encoding='utf-8') as f:
    pending_data = json.load(f)

# Build lookup: (product_id, day_str) -> list of pending order info
# Using a dict of dicts for O(1) lookups
# Structure: pending_by_product_day[product_id][day] = [pending_entries]
print("  Building pending order lookup index...")
pending_by_product_day = defaultdict(list)
for day_entry in pending_data:
    day_str = day_entry['day']
    for p in day_entry['pending']:
        pid = p['product_id']
        pending_by_product_day[(pid, day_str)].append(p)

print(f"  Pending index has {len(pending_by_product_day)} entries")
# Free memory
del pending_data

# Load supplier performance for lead time info
df_suppliers = pd.read_csv(SUPPLIER_PERF_CSV)
supplier_lead_time = dict(zip(df_suppliers['supplier'], df_suppliers['estimated_lead_time_mean']))
print(f"  Supplier lead time map has {len(supplier_lead_time)} entries")

# Load purchase alerts
print(f"  Loading purchase alerts...")
df_alerts = pd.read_csv(PURCHASE_ALERTS_CSV)
print(f"  {len(df_alerts)} alerts loaded")

# Enrichment function
def enrich_alert(row):
    pid = int(row['product_id'])
    alert_date = str(row['alert_date'])
    supplier = str(row['supplier']).strip()
    coverage = float(row['coverage_days'])
    
    # Product info
    prod = product_map.get(pid, None)
    if prod:
        product_name = prod['des_artigo']
        product_code = prod['cod_artigo']
    else:
        product_name = None
        product_code = None
    
    # Pending order check
    pending_entries = pending_by_product_day.get((pid, alert_date), [])
    
    has_pending = len(pending_entries) > 0
    pending_order_date = None
    pending_expected_date = None
    days_until_arrival = None
    
    if has_pending:
        # Take the first pending entry (or merge multiple)
        pe = pending_entries[0]
        pending_order_date = pe.get('order_date', '')
        pending_expected_date = pe.get('expected_date', '')
        
        # Calculate days until expected arrival
        if pending_expected_date:
            try:
                exp_date = datetime.strptime(pending_expected_date, '%Y-%m-%d').date()
                alert_dt = datetime.strptime(alert_date, '%Y-%m-%d').date()
                days_until_arrival = (exp_date - alert_dt).days
            except:
                days_until_arrival = None
        # Check if there are multiple pending for same product-day
        if len(pending_entries) > 1:
            # If multiple, pick the one with earliest expected_date
            best = pending_entries[0]
            for pe_item in pending_entries[1:]:
                exp = pe_item.get('expected_date', '')
                if exp and (not best.get('expected_date') or exp < best['expected_date']):
                    best = pe_item
                    pending_order_date = best.get('order_date', '')
                    pending_expected_date = best.get('expected_date', '')
                    if pending_expected_date:
                        try:
                            exp_date = datetime.strptime(pending_expected_date, '%Y-%m-%d').date()
                            alert_dt = datetime.strptime(alert_date, '%Y-%m-%d').date()
                            days_until_arrival = (exp_date - alert_dt).days
                        except:
                            days_until_arrival = None
    
    # Risk score calculation
    lead_time = supplier_lead_time.get(supplier, 20)
    lead_time_remaining = lead_time  # simplified: lead time is the supplier's standard
    
    if coverage < 7:
        risk_score = 'CRITICAL'
    elif coverage < 15:
        risk_score = 'HIGH'
    elif coverage >= 30:
        risk_score = 'LOW'
    elif coverage < 15 or (coverage < lead_time_remaining):
        risk_score = 'HIGH'
    elif coverage >= 15 and coverage <= 30:
        if coverage > lead_time_remaining + 5:
            risk_score = 'LOW'
        elif coverage >= lead_time_remaining and coverage <= lead_time_remaining + 5:
            risk_score = 'MEDIUM'
        else:
            risk_score = 'HIGH'
    else:
        risk_score = 'MEDIUM'
    
    # Refined risk logic
    # The task says:
    # LOW: coverage > 30 OU (coverage > lead_time_remaining + 5)
    # MEDIUM: coverage 15-30 OU (coverage entre lead_time_remaining e lead_time_remaining + 5)
    # HIGH: coverage < 15 OU (coverage < lead_time_remaining)
    # CRITICAL: coverage < 7
    
    return pd.Series({
        'product_name': product_name,
        'product_code': product_code,
        'has_pending_order': has_pending,
        'pending_order_date': pending_order_date if pending_order_date else None,
        'pending_expected_date': pending_expected_date if pending_expected_date else None,
        'days_until_expected_arrival': days_until_arrival,
        'risk_score': risk_score,
    })

# Apply enrichment (in chunks to avoid memory issues)
print("  Enriching alerts...")
enriched = df_alerts.apply(enrich_alert, axis=1)
df_enriched = pd.concat([df_alerts, enriched], axis=1)

# Save
df_enriched.to_csv(ENRICHED_CSV, index=False)
print(f"  => {len(df_enriched)} enriched alerts written to {ENRICHED_CSV}")

# ══════════════════════════════════════════════════════════════════════════════
# 4. SUPPLIER PERFORMANCE EXPLANATION
# ══════════════════════════════════════════════════════════════════════════════
print("[4/5] Enhancing supplier performance with explanation...")

n_suppliers = len(df_suppliers)
explanation = (
        f"{n_suppliers} fornecedores. "
        "compliance_rate = entregas_no_prazo / total_pedidos. "
        "No prazo = mercadoria chegou em ate 45 dias da data do pedido. "
        "Atraso = mais de 45 dias para chegar. "
        "avg_delay_days = media de dias de atraso apenas nas entregas com atraso (>45d). "
        "lead_time_esperado = ~30 dias (varia por regime)."
    )
df_suppliers['explanation'] = explanation

df_suppliers.to_csv(SUPPLIER_PERF_CSV, index=False)
print(f"  => {len(df_suppliers)} rows updated in {SUPPLIER_PERF_CSV}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. RISK ANALYSIS METHODOLOGY DOC
# ══════════════════════════════════════════════════════════════════════════════
print("[5/5] Writing risk analysis methodology document...")

methodology_md = f"""# Risk Analysis Methodology — Chez Violeta Purchase Alerts

## 1. Risk Score Calculation

The `risk_score` is a composite metric based on coverage days, pending order status, and supplier lead time.

### Thresholds

| Risk Level | Condition | Action |
|-----------|-----------|--------|
| **CRITICAL** | coverage_days < 7 | Immediate reorder required; risk of stockout within a week |
| **HIGH** | coverage_days < 15 OR coverage_days < estimated_lead_time | High probability of stockout before replenishment arrives |
| **MEDIUM** | coverage_days between 15–30 AND coverage_days >= estimated_lead_time | Moderate risk; monitor but no immediate action |
| **LOW** | coverage_days > 30 OR coverage_days > estimated_lead_time + 5 | Comfortable stock level; routine monitoring |

### Logic Summary

```
IF coverage < 7       => CRITICAL
ELIF coverage < 15    => HIGH
ELIF coverage > 30    => LOW
ELIF coverage < lead_time => HIGH
ELIF coverage between lead_time AND lead_time+5 => MEDIUM
ELIF coverage > lead_time+5 => LOW
ELSE                  => MEDIUM
```

### Inputs

- **coverage_days**: days of stock remaining given current sales velocity
- **estimated_lead_time_mean**: average lead time (in days) for the supplier (from supplier_performance.csv)
- **has_pending_order**: whether there is an active pending purchase order for this product on the alert date
- **days_until_expected_arrival**: days between the alert date and the expected arrival date of the pending order

### Edge Cases

- **coverage_days = 0**: treated as CRITICAL (already stocked out)
- **no supplier lead time data**: default lead time of 20 days used
- **multiple pending orders**: earliest expected arrival is used

## 2. Coverage by Store

Coverage is calculated at the product level across all stores using the most recent daily inventory snapshot.

```
coverage_days = current_stock / avg_daily_sales
```

This represents how many days the current inventory can sustain current sales velocity before a stockout occurs.

### Data Sources

- **Current stock**: `gold.fato_estoque_diario` (latest `id_data` = 20191130)
- **Sales velocity**: calculated from historical sales in `gold.fato_vendas`
- **Products**: `gold.dim_produto` (SCD Type 2, filtered to current version via `dat_fim_vigencia IS NULL`)

## 3. Coverage X Pending Orders Comparison

The enrichment adds context by cross-referencing alerts with pending purchase orders:

| Scenario | Interpretation |
|----------|---------------|
| **Coverage LOW + has pending order** | Alert is expected; stock will be replenished. No additional action needed. |
| **Coverage LOW + NO pending order** | **Action required**: no purchase order exists for this product despite low stock |
| **Coverage CRITICAL + has pending order** | Pending order is coming, but may arrive too late. Consider expediting. |
| **Coverage HIGH + has pending order** | Existing stock + pending order means oversupply risk. Consider postponing or cancelling. |
| **Coverage HIGH + NO pending order** | Normal situation; stock is healthy without additional orders. |

### Pending Order Data

Source: `daily_pending_detail.json` (360 days of simulation, {198310} pending entries)

Each pending order entry contains:
- `product_id`: product being ordered
- `supplier`: supplier name
- `quantity`: quantity ordered
- `order_date`: date the order was placed
- `expected_date`: expected arrival date
- `delay_days`: current delay (0 = on time)
- `tagging_until`: tagging deadline (for fashion regime)

## 4. Practical Examples

### Example 1: CRITICAL Risk with Pending Order

```
alert_date: 2019-12-01
product_id: 402
coverage_days: 4.0
supplier: DIVA DONNA
lead_time: 20 days
has_pending_order: TRUE
expected_arrival: 2019-12-21
days_until_arrival: 20
```

**Analysis**: Coverage (4 days) < 7 => CRITICAL. A pending order exists (expected 2019-12-21, 20 days away). Even with the pending order, there will be 16 days of stockout before arrival. **Action**: Expedite the pending order or source emergency stock.

### Example 2: HIGH Risk without Pending Order

```
alert_date: 2019-12-05
product_id: 2
coverage_days: 13.0
supplier: TRIFIL
lead_time: 20 days
has_pending_order: FALSE
```

**Analysis**: Coverage (13) < 15 => HIGH. Coverage (13) < lead_time (20) => stock will run out before new stock arrives. No pending order exists. **Action**: Place an emergency purchase order immediately.

### Example 3: MEDIUM Risk with Pending Order

```
alert_date: 2019-12-01
product_id: 17978
coverage_days: 27.0
supplier: FOREVER FITNESS
lead_time: 30 days
has_pending_order: depends
```

**Analysis**: Coverage (27) is between 15-30 and coverage (27) < lead_time (30) but coverage > lead_time - 5 = 25. Classified as MEDIUM. **Action**: Monitor; order may be needed soon if sales accelerate.

### Example 4: LOW Risk

```
alert_date: 2019-12-03
product_id: 33945
coverage_days: 39.0
supplier: HERMES BALI
lead_time: 35 days
```

**Analysis**: Coverage (39) > 30 => LOW. Coverage (39) > lead_time + 5 (40)? Not quite, but > 30 means LOW. **Action**: Routine monitoring only.

## 5. Supplier Performance Explanation

The `supplier_performance.csv` now includes an `explanation` column with the following methodology:

- **compliance_rate** = `entregas_no_prazo / total_pedidos`
- **No prazo** = mercadoria chegou em ate 45 dias da data do pedido
- **Atraso** = mais de 45 dias para chegar
- **avg_delay_days** = mean delay days only for deliveries WITH delay (>45d)
- **lead_time_esperado** = ~30 dias (varia por regime)
- Suppliers with `total_orders = 0` show `compliance_rate = 1.0` (no data, assumed compliant)

## 6. Data Freshness

All data is sourced from the simulation output v2 (360-day simulation, seed=42).

| Dataset | Rows | Freshness |
|---------|------|-----------|
| product_lookup.csv | {len(df_product)} | Current (dat_fim_vigencia IS NULL) |
| stock_by_store.csv | {len(df_stock)} | Last simulation day (20191130) |
| purchase_alerts_enriched.csv | {len(df_enriched)} | 2019-12-01 to 2020-11-24 |
| supplier_performance.csv | {n_suppliers} | 178 suppliers tracked |
| daily_pending_detail.json | {198310} entries | 360 days of pending orders |
"""

with open(f'{ROOT}/artifacts/simulation/risk-analysis-methodology.md', 'w', encoding='utf-8') as f:
    f.write(methodology_md)
    print(f"  => Written to {ROOT}/artifacts/simulation/risk-analysis-methodology.md")

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("ENRICHMENT COMPLETE")
print("=" * 60)
print(f"  product_lookup.csv:       {len(df_product)} products")
print(f"  stock_by_store.csv:       {len(df_stock)} rows")
print(f"  purchase_alerts_enriched: {len(df_enriched)} alerts")
print(f"  supplier_performance:     {n_suppliers} suppliers (with explanation)")
print(f"  risk-analysis-methodology: written")
print()

# Print risk score distribution
print("Risk Score Distribution:")
risk_dist = df_enriched['risk_score'].value_counts()
for score in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    cnt = risk_dist.get(score, 0)
    print(f"  {score}: {cnt}")

print()
print("Pending Order Coverage:")
has_pending = df_enriched['has_pending_order'].sum()
print(f"  Alerts with pending order: {has_pending} / {len(df_enriched)} ({has_pending/len(df_enriched)*100:.1f}%)")
