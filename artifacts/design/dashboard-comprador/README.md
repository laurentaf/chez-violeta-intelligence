# Dashboard do Comprador — Chez Violeta v2

## Visão Geral

Dashboard operacional para o time de compras da Chez Violeta, focado em:
- Alertas de compra com priorização por risco de ruptura
- Análise de cobertura por loja
- Performance de fornecedores
- Risco de ruptura vs pedidos pendentes

Este dashboard consome dados da simulação de 360 dias (output-360d-v2).

## Seções

### 1. Resumo (KPIs)
Cards no topo com:
- Total de alertas no período
- % com risco ALTO ou CRÍTICO (99.1%)
- Produtos que vão romper ANTES do pedido chegar
- Fornecedor com pior compliance

### 2. Tabela de Alertas de Compra (Interativa)
- **Ordenação** por qualquer coluna (clicar no cabeçalho)
- **Filtros**: Urgência, Categoria, Fornecedor, Risco
- Colunas: Produto, Código, Categoria, Regime, Fornecedor, Cobertura, Qtd Sugerida, Urgência, Risco, Tem Pedido?, Previsão Chegada, Chega Antes da Ruptura?, Custo Total
- Destaque vermelho em linhas onde NÃO chega antes da ruptura

### 3. Distribuição de Risco + Alertas por Categoria (Gráficos)
- Gráfico de rosca: distribuição dos níveis de risco
- Gráfico de barras: alertas por categoria de produto

### 4. Risco de Ruptura vs Pedidos
- Cards explicativos dos 4 níveis de risco (Baixo/Médio/Alto/Crítico)
- Tabela ordenada por cobertura (menor primeiro)

### 5. Cobertura por Loja
- Tabela de estoque por loja para produtos em alerta
- Destaque vermelho para cobertura < 7 dias

### 6. Performance de Fornecedores
- Tabela ordenável por qualquer coluna
- Métricas: Pedidos, No Prazo, Atrasados, % Compliance, Nota (A-D), Atraso Médio
- Coluna de explicação da metodologia de cálculo

## Metodologia de Risco

| Risco | Condição | Ação |
|-------|----------|------|
| **⚫ Crítico** | cobertura < 7 dias | Ruptura iminente |
| **🔴 Alto** | cobertura < 15 OU cobertura < lead_time | Rompe antes de chegar |
| **🟡 Médio** | cobertura 15-30 E cobertura >= lead_time | Monitorar |
| **🟢 Baixo** | cobertura > 30 | Confortável |

## Design System

- **Paleta**: Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5
- **Tipografia**: Cormorant Garamond (headings), Inter (body)
- **Framework**: Chart.js 4.4.4 (via CDN)
- **Ícones**: Unicode (emoji)

## Como Abrir

O dashboard é self-contained (HTML único com dados embutidos em JSON).
Abra no navegador:

```
file:///F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html
```

## Fonte dos Dados

Os dados são da simulação `output-360d-v2` (seed=42, 360 dias):
- `purchase_alerts_enriched.csv` — 7.111 alertas enriquecidos
- `supplier_performance.csv` — 178 fornecedores
- `stock_by_store.csv` — estoque por loja (45.050 registros)
- `risk-analysis-methodology.md` — metodologia de risco

**⚠ Importante:** Dados de simulação, não para produção.
