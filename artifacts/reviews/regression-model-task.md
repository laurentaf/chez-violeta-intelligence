# Task Review: Regressão Semanal para Previsão de Compras

**Status:** ✅ COMPLETE
**Date:** 2026-07-12
**Agent:** data-architect

## Summary

Modelo de regressão OLS treinado para previsão semanal de vendas por categoria. 
R² = 0.726 (72.6% da variância explicada). Previsões para 26 semanas e recomendações
de compra para 120 dias geradas e integradas ao dashboard do comprador.

## Deliverables

| # | File | Size | Status |
|---|------|------|--------|
| 1 | `artifacts/data/regression_model_results.json` | 2,677 B | ✅ |
| 2 | `artifacts/data/weekly_predictions.csv` | 9,992 B | ✅ |
| 3 | `artifacts/data/regression-report.md` | 5,885 B | ✅ |
| 4 | `artifacts/design/dashboard-comprador/index.html` | 323 KB | ✅ |

## Model Details

- **Method:** OLS (statsmodels)
- **Formula:** `qtd_log ~ C(categoria) + C(quarter) + t`
- **R²:** 0.7260 | **Adj. R²:** 0.6942
- **N:** 97 observations | **K:** 11 parameters
- **AIC:** 277.2 | **BIC:** 305.5
- **Trend:** +0.0072 (p=0.307, não significativo)

### Adaptation from Original Spec

The user requested `C(categoria):C(num_semana)` interactions, but with only 97 observations
and 16 unique weeks, a full interaction model would have more parameters than data points.
**Adapted to quarter-level seasonality** (Q1-Q4) instead of individual week dummies:

| Approach | Params | Viable? |
|----------|--------|---------|
| Category × Week interactions | ~400+ | ❌ Overfitted |
| Week dummies alone | ~60+ | ❌ Sparse |
| Quarter dummies + Category + Trend | 11 | ✅ Used |

### Top 3 Categories by Volume (26-week forecast)

1. **UNDERWARE:** 7,397 un. — largest volume
2. **LINHA NOITE:** 2,426 un.
3. **VESTUARIO:** 1,912 un.

### Dashboard Updates

- Added "Previsao" tab alongside existing "Fornecedores" tab
- Tab shows: weekly forecast table (filterable by category), 120-day purchase recommendations, R² notice
- All predictions data embedded as JS variable (no external API calls)

### Data Caveats

- Sales data spans 2017-2020 with only 16 populated weeks
- Gap between Dec 2018 and Sep 2019, and Oct 2019 to Apr 2020
- `num_semana` and `id_ano_sem` columns in dim_tempo are entirely NULL — used `WEEK(dat_dia)` instead
- 3 categories (ACESSORIOS, BIJU/JOIAS, EROTICA) have very low volume (<50 units total)

## Artifacts Produced

- `artifacts/data/_weekly_regression.py` — main modeling script
- `artifacts/data/_update_dashboard.py` — dashboard updater script
