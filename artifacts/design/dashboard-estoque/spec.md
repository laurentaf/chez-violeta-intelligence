---
synthetic: false
kind: spec
label: "Dashboard Spec — Estoque"
design_system: artifacts/design/design-system.md
data_source: gold.fato_estoque_diario, gold.dim_produto, gold.dim_loja, gold.dim_tempo
---

# Dashboard de Estoque — Spec

## 1. Objetivo

Monitorar o inventário atual, giro, cobertura e rupturas na rede
Chez Violeta. Identificar produtos com estoque crítico antes que
afetem vendas.

**Público:** Gerente de estoque, compras, diretoria operacional.

---

## 2. KPIs Principais

| KPI | Fórmula | Fonte | Frequência |
|-----|---------|-------|------------|
| **Valor Total em Estoque** | `SUM(qtd_estoque * val_custo_inicial)` | fato_estoque_diario + dim_produto | Diária |
| **Giro de Estoque** | `SUM(qtd_venda) / AVG(qtd_estoque)` | fato_estoque_diario | Acumulado (anual) |
| **Cobertura Média** | `AVG(qtd_estoque) / AVG(qtd_venda) * 30` | fato_estoque_diario | Dias |
| **Produtos em Ruptura** | `COUNT(qtd_estoque = 0)` | fato_estoque_diario | Diária |

### Derivados

| Métrica | Aplicação |
|---------|-----------|
| Δ Valor estoque vs. mês anterior | KPI card |
| Δ Giro vs. período anterior | KPI card |
| Δ Cobertura vs. mês anterior | KPI card |
| Δ Ruptura vs. mês anterior | KPI card (atenção: quanto maior, pior) |
| Top 10 produtos por valor | Bar chart horizontal |
| Giro por categoria | Horizontal bar chart |
| Evolução estoque × vendas | Dual line chart |
| Cobertura por categoria | Color-coded bar chart |
| Produtos críticos | Data table com status e progresso |

---

## 3. Filtros

| Filtro | Tipo | Default | Comportamento |
|--------|------|---------|---------------|
| Período | Date range (mês) | Últimos 12 meses | Filtra `dim_tempo.dat_dia` |
| Loja | Multi-select | Todas | Filtra `dim_loja.id_loja` |
| Categoria | Multi-select | Todas | Filtra `dim_produto.des_categoria` |
| Nível Estoque | Single-select | Todos | Filtra por faixa de cobertura (crítico/atenção/ok) |

---

## 4. Layout (1920×1080)

```
┌──────────────────────────────────────────────────────────┐
│ Header: Logo + "Estoque" + nav tabs (Vendas, Compras…)   │
├──────────────────────────────────────────────────────────┤
│ Filter Bar: Período | Loja | Categoria | Nível Estq |    │
├──────────┬───────────────┬──────────┬────────────────────┤
│ Valor    │ Giro de       │ Cobertura│ Ruptura            │
│ Estoque  │ Estoque       │ Média    │ 342 produtos       │
│ R$ 30,2M │ 59.181×       │ 47 dias  │ ⚠ +28 vs. mês     │
│ ▼ 2,1%   │ ▲ 8,3%        │ ▼ 5 dias │ Crítico: 127       │
├──────────┴───────────┬────┴──────────┴────────────────────┤
│ Top 10 Produtos por  │ Giro por Categoria                 │
│ Valor Estoque (bar)  │ (horizontal bar)                   │
├──────────────────────┴──────────────────────────────────-┤
│ Evolução Estoque × Vendas (dual line chart)              │
├──────────────────────┬────────────────────────────────────┤
│ Cobertura por        │                                    │
│ Categoria (color-    │                                    │
│ coded bars)          │                                    │
├──────────────────────┴────────────────────────────────────┤
│ Produtos com Estoque Crítico (data table com status)      │
│ Produto | Categoria | Estoque | Vendas | Cobertura | Bar │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Queries

### KPIs Agregados

```sql
SELECT
  SUM(e.qtd_estoque * COALESCE(p.val_custo_inicial, 0)) AS valor_estoque_total,
  SUM(e.qtd_venda) / NULLIF(AVG(e.qtd_estoque), 0) AS giro_estoque,
  AVG(e.qtd_estoque) / NULLIF(AVG(e.qtd_venda), 0) * 30 AS cobertura_dias,
  SUM(CASE WHEN e.qtd_estoque = 0 THEN 1 ELSE 0 END) AS ruptura_count
FROM gold.fato_estoque_diario e
JOIN gold.dim_produto p ON e.id_produto = p.id_produto
WHERE e.id_data = :data_ultima
```

### Top Produtos por Valor Estoque

```sql
SELECT
  p.des_produto,
  p.des_categoria,
  SUM(e.qtd_estoque) AS total_estoque,
  SUM(e.qtd_estoque * COALESCE(p.val_custo_inicial, 0)) AS val_estoque
FROM gold.fato_estoque_diario e
JOIN gold.dim_produto p ON e.id_produto = p.id_produto
WHERE e.qtd_estoque > 0
GROUP BY p.des_produto, p.des_categoria
ORDER BY val_estoque DESC
LIMIT 10
```

### Giro por Categoria

```sql
SELECT
  p.des_categoria,
  SUM(e.qtd_venda) AS total_vendido,
  AVG(e.qtd_estoque) AS estoque_medio,
  CASE
    WHEN AVG(e.qtd_estoque) > 0
    THEN SUM(e.qtd_venda) / AVG(e.qtd_estoque)
    ELSE 0
  END AS giro
FROM gold.fato_estoque_diario e
JOIN gold.dim_produto p ON e.id_produto = p.id_produto
GROUP BY p.des_categoria
ORDER BY giro DESC
```

### Produtos Críticos

```sql
SELECT
  p.des_produto,
  p.des_categoria,
  e.qtd_estoque,
  e.qtd_venda AS vendas_mes,
  CASE
    WHEN e.qtd_venda > 0
    THEN e.qtd_estoque / e.qtd_venda * 30
    ELSE 999
  END AS cobertura_dias
FROM gold.fato_estoque_diario e
JOIN gold.dim_produto p ON e.id_produto = p.id_produto
WHERE e.qtd_estoque <= 10
ORDER BY cobertura_dias ASC
LIMIT 20
```

---

## 6. Interações Planejadas

- **Clique em barra de produto** → abre histórico de estoque do produto
- **Clique em produto crítico** → sugestão de reabastecimento
- **Hover em série** → tooltip com valor
- **Ordenação de tabela** por qualquer coluna
- **Export CSV** dos produtos críticos
- **Link para pedido de compra** (integração com fornecedor)

---

## 7. Regras de Cobertura

| Faixa | Label | Cor | Ação |
|-------|-------|-----|------|
| < 30 dias | Crítico | 🔴 Vermelho | Reabastecimento urgente |
| 30–60 dias | Atenção | 🟡 Laranja | Programar compra |
| > 60 dias | OK | 🟢 Verde | Monitorar |

---

## 8. Notas Técnicas

- **Engine:** Power BI (pbix) ou web app (HTML+Chart.js)
- **Data refresh:** Diário via pipeline n8n
- **Volume:** ~4.5M registros de estoque diário
- **Fonte:** Dados reais de 2018–2020

---

## 9. Estado Atual

- [x] Wireframe HTML produzido
- [ ] Design system tokens integrados
- [ ] Implementação Power BI
- [ ] Testes de acesso e performance
- [ ] Revisão de acessibilidade (WCAG 2.1 AA)
