# Risk Analysis Methodology — Chez Violeta Purchase Alerts

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

Source: `daily_pending_detail.json` (360 days of simulation, 198310 pending entries)

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

- **compliance_rate** = `on_time / total_orders`
- **on_time** = deliveries where `delay_days == 0` (no delay)
- **avg_delay_days** = mean delay days only for deliveries WITH delay
- **estimated_lead_time_mean** = standard contracted lead time in days
- Suppliers with `total_orders = 0` show `compliance_rate = 1.0` (no data, assumed compliant)

## 6. Data Freshness

All data is sourced from the simulation output v2 (360-day simulation, seed=42).

| Dataset | Rows | Freshness |
|---------|------|-----------|
| product_lookup.csv | 35258 | Current (dat_fim_vigencia IS NULL) |
| stock_by_store.csv | 45050 | Last simulation day (20191130) |
| purchase_alerts_enriched.csv | 7111 | 2019-12-01 to 2020-11-24 |
| supplier_performance.csv | 178 | 178 suppliers tracked |
| daily_pending_detail.json | 198310 entries | 360 days of pending orders |
