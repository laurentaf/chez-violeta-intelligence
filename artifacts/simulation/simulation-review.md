# Review: Motor de Simulação de Estoque — Chez Violeta

**Task:** data-architect implementação do Motor de Simulação
**Date:** 2026-07-08
**Engine version:** 1.0.0

---

## Artifacts Created

### 1. `artifacts/simulation/simulation_engine.py`
Motor principal de simulação. 1,237 linhas. Funcionalidades implementadas:

| Feature | Status | Details |
|---------|--------|---------|
| Extração DuckDB | ✅ | Lê dim_produto, dim_fornecedor, fato_estoque_diario, fato_vendas, fato_compras |
| Classificação de regime | ✅ | `classify_regime()` baseada em categoria/linha/coleção |
| Simulação dia-a-dia | ✅ | `simulate_day()` — Poisson com sazonalidade, dia-da-semana, temperatura |
| Ponto de reabastecimento | ✅ | Commodity 90d, Fashion 14d, Seasonal 180d targets |
| Lead time de fornecedor | ✅ | Média + std por fornecedor; ~178 fornecedores estimados |
| Alertas de compra | ✅ | CRITICAL ≤7d, HIGH ≤14d, MEDIUM ≤30d |
| Produtos substitutos | ✅ | Mesma categoria+linha+preço ±20%, top 5 |
| Produtos lentos | ✅ | 60+ dias sem venda → desconto 10/20/30% |
| Processo de entrada | ✅ | Lead time expiry + tagging time (1-2 dias) |
| CLI | ✅ | `--days`, `--seed`, `--verbose`, `--db-path`, `--output` |

### 2. `artifacts/simulation/simulation_config.json`
Parâmetros configuráveis — 150 linhas:
- Regime params (commodity/fashion/seasonal)
- Sales model por categoria (8 categorias)
- Temperature by month
- Regime classification rules
- Simulation config (discount tiers, slow mover threshold, etc.)

### 3. Outputs em `artifacts/simulation/output/`

| File | Rows | Description |
|------|------|-------------|
| `daily_log.csv` | 30 | Log dia-a-dia: estoque total, vendas, rupturas, alertas |
| `stockouts.csv` | 1,456 | Produtos que zeraram durante simulação |
| `purchase_alerts.csv` | 739 | Alertas de compra gerados (CRITICAL/HIGH/MEDIUM/LOW) |
| `supplier_performance.csv` | 178 | Compliance de fornecedores |
| `slow_movers.csv` | 898 | Produtos lentos com sugestão de desconto |
| `summary.json` | 31 linhas | Resumo completo da simulação |

### 4. `artifacts/simulation/dashboard/simulation_dashboard.html`
Dashboard visual auto-contido (338 linhas) com Chart.js via CDN:
- Gráfico linha: estoque total vs vendas diárias
- Gráfico pizza: distribuição de regimes
- Tabela: top 10 alertas de compra
- Tabela: top 5 fornecedores pior compliance
- Cards resumo: vendas, receita, rupturas, alertas, lentos

## Simulation Results

| Metric | Value |
|--------|-------|
| Days simulated | 30 |
| Period | 2019-12-01 → 2019-12-30 |
| Products tracked | 9,525 (com stock inicial) |
| Total stock (initial) | 22,556 units |
| Total stock (final) | 19,886 units (-11.8%) |
| Sales (units) | 2,670 |
| Revenue | R$ 88,143.87 |
| Products stocked out | 1,456 |
| Purchase alerts | 739 |
| Slow movers | 898 unique products |
| Regime distribution | 4,858 commodity / 3,795 fashion / 872 seasonal |

## Data Sources

- DuckDB: `F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb`
- Sales model: Learned from `params_learned.json` (8 categorias: UNDERWARE, MODA_PRAIA, LINHA_NOITE, VESTUARIO, FITNESS, BIJU/JOIAS, EROTICA, ACESSORIOS)
- Suppliers: 178 fornecedores reais com lead time estimado por volume de pedidos
- Latest stock date: 2019-11-30

## Limitations (v1)

1. **Zero receipts in 30 days** — lead times (20-75 dias) > simulation horizon. Realistic for short runs.
2. **Unit cost for some products is R$ 0** — ~60% of products have NULL val_custo_inicial. Fallback price (R$ 29.99) used for sales.
3. **No multi-store simulation** — aggregated across all stores.
4. **No seasonal reorder trigger** — `sell_through > 70%` check for seasonal not implemented.
5. **Dashboard requires HTTP server** — `python -m http.server` to serve the fetch() calls.

## How to Re-run

```bash
cd F:/projects/chez-violeta-intelligence
uv run python artifacts/simulation/simulation_engine.py --days 30 --verbose
uv run python artifacts/simulation/simulation_engine.py --days 90 --seed 123

# For dashboard:
cd artifacts/simulation/dashboard
python -m http.server 8080
# Open http://localhost:8080/simulation_dashboard.html
```

## File Sizes

```
artifacts/simulation/simulation_engine.py        1,237 lines
artifacts/simulation/simulation_config.json        150 lines
artifacts/simulation/dashboard/simulation_dashboard.html  338 lines
artifacts/simulation/output/daily_log.csv          30 rows
artifacts/simulation/output/stockouts.csv       1,456 rows
artifacts/simulation/output/purchase_alerts.csv   739 rows
artifacts/simulation/output/supplier_performance.csv  178 rows
artifacts/simulation/output/slow_movers.csv       898 rows
artifacts/simulation/output/summary.json         31 lines
```
