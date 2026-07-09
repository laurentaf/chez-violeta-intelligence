# Task: Simular 360 dias + Validar vendas vs histórico

**Task ID:** `sim-360d-validate-20260708`
**Data:** 2026-07-08
**Subagente:** data-architect

## Resultados

### 1. Simulação 360 dias — CONCLUÍDA

Comando executado:
```
uv run python artifacts/simulation/simulation_engine.py --days 360 --seed 42 --verbose --output artifacts/simulation/output-360d
```

**Resumo:**
- Dias simulados: 360 (2019-12-01 a 2020-11-24)
- Vendas totais: 15.696 unidades
- Receita total: R$ 505.971,67
- Média diária: 43,6 un/dia
- Rupturas: 7.983 produtos (84% do estoque inicial)
- Alertas de compra: 2.592
- Slow movers: 3.492 produtos
- Estoque final: 6.860 unidades (1.542 produtos)

### 2. Extração de vendas históricas — CONCLUÍDA

Dados extraídos do DuckDB gold layer (`gold.fato_vendas` + `gold.dim_produto` + `gold.dim_tempo`).

**Cobertura histórica:** 59 registros (mês-categoria), 2017-2020
- 2017: nov-dez (2 meses, parcial)
- 2018: out-dez (3 meses, mais completo)
- 2019: set-out (2 meses, limitado)
- 2020: abr-mai (2 meses, maio com pico atípico)

### 3. Comparação Simulado vs Histórico — CONCLUÍDA

**Principais achados:**

| Aspecto | Status | Detalhe |
|---------|--------|---------|
| Ordem de grandeza | ✅ | Sim 44 un/dia vs Hist 2018 36 un/dia (~22% dif) |
| Receita média/dia | ✅ | R$ 1.405 (sim) vs R$ 1.410 (hist 2018) |
| Sazonalidade MODA PRAIA | ✅ | Pico verão correto |
| Sazonalidade LINHA NOITE | ⚠️ | Pico parcial (maio hist vs junho sim) |
| Reabastecimento | ❌ | Zero recebimentos em 360 dias (possível bug) |
| Pico maio/2020 | ⚠️ | Histórico mostra 5.408 un (Dia das Mães?) vs sim 1.242 |

### 4. Arquivos gerados

Todos em `artifacts/simulation/output-360d/`:
- `daily_log.csv` — Log diário (360 linhas)
- `stockouts.csv` — Rupturas (7.983)
- `purchase_alerts.csv` — Alertas (2.592)
- `supplier_performance.csv` — Fornecedores (178)
- `slow_movers.csv` — Lentos (3.492)
- `summary.json` — Resumo
- `historical_comparison.csv` — Tabela mensal comparativa
- `comparison_summary.json` — Resumo da comparação

Relatório completo: `artifacts/simulation/validation-report.md`
