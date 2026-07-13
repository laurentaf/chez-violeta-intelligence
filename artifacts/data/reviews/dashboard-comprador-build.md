# Dashboard Comprador - Build Review

**Task:** Dashboard de Pedidos por Fornecedor  
**Date:** 2026-07-13  
**Status:** CONCLUIDO

## Deliverables

| File | Size | Description |
|------|------|-------------|
| `artifacts/design/dashboard-comprador/index.html` | 5.8 MB | Dashboard HTML self-contained |
| `artifacts/design/dashboard-comprador/purchase_data.json` | 8.5 MB | Raw extracted data for reproducibility |
| `artifacts/data/_build_purchase_dashboard.py` | Main generator script | |

## Data Sources

- **DuckDB:** `artifacts/data/chez_gold.duckdb` (gold schema: fato_estoque_diario, dim_produto, dim_fornecedor)
- **Prophet Forecast:** `artifacts/data/prophet_forecast_future.csv` (182 days per category)
- **Latest stock date:** 2019-11-30
- **Sales days:** 614 days

## Metrics

| Metric | Value |
|--------|-------|
| Total products analyzed | 15,469 |
| Products needing purchase | 9,623 |
| Suppliers needing purchase | 113 |
| Vestuario types with needs | 30 |
| Total a comprar (qtd) | 9,769,403 units |
| Total a comprar (R$) | R$ 119,167,374.50 |
| Total estoque atual | 112,145 units |
| Categorias criticas | 5 |

## Dashboard Structure

### Visão Geral (home)
- 4 summary cards (fornecedores, total valor, categorias criticas, estoque)
- Supplier table sorted by total value (desc)
- Category filter dropdown
- Category summary table

### Página por Fornecedor (113 suppliers)
- Each supplier has its own section accessed via dropdown or "Ver Pedido" link
- Supplier header: name, compliance, categories, product count, stock
- Product table: name, code, category, size, stock, forecast 120d, coverage (tag), qty to order, unit value, total
- Sorted by coverage ratio (lowest first)
- Total row at bottom
- BIJU suppliers marked with gold badge

### Página Vestuário (30 product types)
- Grouped by product type (BLUSA MC, CALCA JEANS, etc.)
- Within each type: variants by size (P, M, G, GG, etc.)
- Table: product, code, size, stock, forecast, qty to order, unit price

## Forecast Logic
- Products with vel_diaria > 0: forecast_120d = vel_diaria × 120
- Products without sales: uses Prophet category average (10% of daily avg × 120)
- Purchase need = max(0, forecast_120d - estoque)
- Coverage ratio = estoque / forecast_120d (tagged: Critico < 50%, OK 50-150%, Excedente > 150%)

## Category Mapping
| dim_produto | Prophet |
|-------------|---------|
| ACESSORIOS | OUTROS |
| BIJU / JOIAS | OUTROS |
| EROTICA | OUTROS |
| FITNESS | OUTROS |
| LINHA NOITE | LINHA NOITE |
| MODA PRAIA | MODA PRAIA |
| UNDERWARE | UNDERWARE |
| VESTUARIO | VESTUARIO |

## Known Issues
- ~66% of products have zero/null cost in DuckDB → treated as R$ 0.00 in totals
- Total value (R$119M) reflects only products with known cost
- HTML is 5.8MB due to embedded data — opens directly in browser via file://
