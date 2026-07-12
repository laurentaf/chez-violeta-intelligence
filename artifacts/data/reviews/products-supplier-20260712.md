# Task: Extrair produtos ativos por fornecedor com estoque e cobertura

**Date:** 2026-07-12
**Task ID:** products-supplier-20260712

## Summary

Executed 2 queries on `chez_gold.duckdb` to extract active products by supplier with stock and coverage data.

## Query Adjustment

**Problem identified during execution:**
Original queries used `dt.dat_dia >= (SELECT MAX(dat_dia) - INTERVAL '90 days' FROM gold.dim_tempo)`. The `dim_tempo` table contains future dates up to **2030-12-31**, so the 90-day window (2030-10-02 to 2030-12-31) fell entirely after actual sales data (which ends at 2020-05-28). This caused all `velocidade_diaria` values to be NULL and all `coverage_days` to be 0.

**Fix applied:**
Changed the 90-day window subquery to compute from actual sales dates:
```sql
dt.dat_dia >= (SELECT MAX(dt2.dat_dia) FROM gold.fato_vendas fv2 
               JOIN gold.dim_tempo dt2 ON fv2.id_data = dt2.id_data) 
             - INTERVAL '90 days'
```
Resulting window: **2020-02-28 to 2020-05-28**

## Output Files

### `artifacts/data/products_by_supplier.csv`
- **5,838 rows**, 15 columns
- One row per active product with positive stock
- Columns: supplier_code, supplier_name_code, supplier_category, id_produto, cod_artigo, des_artigo, des_produto, product_category, des_linha, des_colecao, val_custo_inicial, qtd_estoque, ultima_venda, velocidade_diaria, coverage_days

### `artifacts/data/supplier_summary.csv`
- **84 rows** (suppliers with ≥ 3 active products in stock), 6 columns
- Columns: supplier, supplier_cat, n_products, total_stock, avg_coverage, stock_value
- Sorted by stock_value DESC

## Key Findings

| Metric | Value |
|--------|-------|
| Active products with stock | 5,838 |
| Products with sales in last 90 days | 1,241 |
| Suppliers (≥3 products) | 84 |
| Top supplier by stock value | CLASS (R$ 92,083) |
| Top by stock coverage | RIVANNA (avg 7,234 days) |

### Data Quality Notes
- Only 1,522 of 5,838 products (26%) have non-null `val_custo_inicial` → `stock_value` underreported for most suppliers
- Coverage days calculated only for products with sales velocity (1,241 products); others show 0
- Coverage days range from 90 to 35,010 days (high values likely from slow-moving items with very low daily velocity)
