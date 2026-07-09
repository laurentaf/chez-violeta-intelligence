# Sales Generator ARIMA — Detailed Results

**Task ID**: sales-generator-2026-07-08
**Date**: 2026-07-08
**Agent**: data-architect

## Summary

Created synthetic sales data generator using SARIMA with seasonality learned from Chez Violeta Gold Layer DuckDB.

## Artifacts Produced

| File | Size | Description |
|------|------|-------------|
| `artifacts/data/sales-generator-spec.md` | 5,680 B | Methodology spec in Portuguese |
| `artifacts/data/sales-generator.py` | 37,513 B | Self-contained Python script |
| `artifacts/data/params_learned.json` | 8,340 B | SARIMA parameters learned from DuckDB |

## Data Source Explored

**DB**: `chez_gold.duckdb` (10,435 rows, 2017-11-21 to 2020-05-28)

Tables used:
- `gold.fato_vendas` — 10,435 sales transactions
- `gold.dim_tempo` — 7,306 days (dense calendar)
- `gold.dim_produto` — 35,258 SKUs

Categories extracted (8): ACESSORIOS, BIJU / JOIAS, EROTICA, FITNESS, LINHA NOITE, MODA PRAIA, UNDERWARE, VESTUARIO

## Key Patterns Learned

- **UNDERWARE** dominates: ~580/month avg, 22.97 avg price
- **LINHA NOITE** second: ~320/month, 53.81 avg price
- **MODA PRAIA** peaks summer (Dec-Feb), trough winter (Jun-Aug)
- **Day-of-week**: Saturday strongest, Monday/Sunday weakest
- **Temperatures**: sinusoidal model (summer ~30°C, winter ~15°C)

## Validation

- Default mode (embedded params): ✅ 38 rows / 7 days
- Learn mode (DuckDB + SARIMA): ✅ 1,851 rows / 365 days, R$ 1.22M
- --help CLI: ✅ All flags documented
- --verbose: ✅ Progress output working

## Known Limitations

1. **Sparse real data**: May 2020 = 52% of rows, SARIMA params smoothed
2. **No promotion modeling**: Discounts/holidays not captured
3. **No cross-category correlation**: Categories generated independently
4. **No stock-out simulation**: Generator does not model inventory
5. **statsmodels dependency**: Auto-installed via `uv pip install` on --learn
