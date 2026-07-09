---
synthetic: false
kind: spec
label: "Dashboard Spec — Vendas"
design_system: artifacts/design/design-system.md
data_source: gold.fato_vendas, gold.dim_loja, gold.dim_produto, gold.dim_tempo, gold.dim_vendedor, gold.dim_cliente
---

# Dashboard de Vendas — Spec

## 1. Objetivo

Monitorar a performance de vendas da rede Chez Violeta com visão
agregada (receita, volume, ticket médio) e drill-down por loja,
produto, mês e sazonalidade.

**Público:** Gerentes de loja, diretoria comercial.

---

## 2. KPIs Principais

| KPI | Fórmula | Fonte | Frequência |
|-----|---------|-------|------------|
| **Receita Total** | `SUM(val_venda_liquida)` | fato_vendas | Diária |
| **Volume de Vendas** | `SUM(qtd_pecas)` | fato_vendas | Diária |
| **Ticket Médio** | `SUM(val_venda_liquida) / COUNT(DISTINCT num_ticket)` | fato_vendas | Diária |
| **Margem Média** | `(SUM(val_venda_liquida) - SUM(val_custo)) / SUM(val_venda_liquida)` | fato_vendas | Diária |

### Variações & Derivados

| Métrica | Aplicação |
|---------|-----------|
| Δ Receita vs. período anterior | KPI card sparkline |
| Δ Volume vs. período anterior | KPI card |
| Δ Ticket médio vs. período anterior | KPI card |
| Δ Margem (pp) vs. período anterior | KPI card |
| Receita por loja | Bar chart + data table |
| Receita por mês | Line chart |
| Sazonalidade (dia da semana) | Bar chart |
| Distribuição por categoria | Donut chart |
| Top produtos por volume | Table |

---

## 3. Filtros

| Filtro | Tipo | Default | Comportamento |
|--------|------|---------|---------------|
| Período | Date range | Todo o histórico | Filtra `dim_tempo.dat_dia` |
| Loja | Multi-select | Todas | Filtra `dim_loja.id_loja` |
| Categoria | Multi-select | Todas | Filtra `dim_produto.des_categoria` |
| Linha | Multi-select | Todas | Filtra `dim_produto.des_linha` |
| Vendedor | Multi-select | Todos | Filtra `dim_vendedor.id_vendedor` |

---

## 4. Layout (1920×1080)

```
┌──────────────────────────────────────────────────────────┐
│ Header: Logo + "Vendas" + nav tabs (Estoque, Compras…)  │
├──────────────────────────────────────────────────────────┤
│ Filter Bar: Período | Loja | Categoria | [Limpar]        │
│ Applied filters as pills                                 │
├──────────┬──────────┬──────────┬──────────┤
│ Receita  │ Volume   │ Ticket   │ Margem   │
│ R$ 442k  │ 10.596   │ R$41,73  │ 54,2%    │
│ ▲ 12,3%  │ ▲ 8,7%   │ ▲ 3,2%   │ ▼ 1,1pp  │
├──────────┴──────────┴──────────┴──────────┤
│ Receita Mensal (line chart, full width)    │
├─────────────────────┬──────────────────────┤
│ Vendas por Loja     │ Sazonalidade         │
│ (bar chart)         │ (bar chart por mês)   │
├─────────────────────┴──────────────────────┤
│ Vendas por Dia da Semana (bar chart)       │
├──────────┬─────────────────────────────────┤
│ Top Prod │ Categoria (donut)               │
├──────────┴─────────────────────────────────┤
│ Data Table: Detalhamento por Loja          │
│ (sortable columns)                         │
└──────────────────────────────────────────────┘
```

### Responsivo

| Breakpoint | Layout | Notas |
|------------|--------|-------|
| ≥ 1280px | 4-col KPI, 2-col charts | Desktop padrão |
| 768–1279px | 2-col KPI, 1-col charts | Tablet |
| < 768px | 1-col tudo empilhado | Mobile |

---

## 5. Queries

### KPI Aggregation

```sql
SELECT
  SUM(f.val_venda_liquida) AS receita_total,
  SUM(f.qtd_pecas) AS volume_vendas,
  SUM(f.val_venda_liquida) / NULLIF(COUNT(DISTINCT f.num_ticket), 0) AS ticket_medio,
  (SUM(f.val_venda_liquida) - SUM(f.val_custo)) / NULLIF(SUM(f.val_venda_liquida), 0) AS margem_media
FROM gold.fato_vendas f
WHERE f.id_data BETWEEN :data_ini AND :data_fim
```

### Receita por Mês

```sql
SELECT
  t.num_ano,
  t.num_mes_ano,
  t.des_mes_ano,
  SUM(f.val_venda_liquida) AS receita
FROM gold.fato_vendas f
JOIN gold.dim_tempo t ON f.id_data = t.id_data
GROUP BY t.num_ano, t.num_mes_ano, t.des_mes_ano
ORDER BY t.num_ano, t.num_mes_ano
```

### Vendas por Loja

```sql
SELECT
  l.des_estabelecimento,
  COUNT(*) AS num_vendas,
  SUM(f.qtd_pecas) AS qtd_total,
  SUM(f.val_venda_liquida) AS receita,
  AVG(f.val_venda_liquida) AS ticket_medio
FROM gold.fato_vendas f
JOIN gold.dim_loja l ON f.id_loja = l.id_loja
GROUP BY l.des_estabelecimento
ORDER BY receita DESC
```

### Sazonalidade (Dia da Semana)

```sql
SELECT
  t.des_dia_semana,
  t.num_dia_semana,
  COUNT(*) AS num_vendas,
  SUM(f.val_venda_liquida) AS receita
FROM gold.fato_vendas f
JOIN gold.dim_tempo t ON f.id_data = t.id_data
GROUP BY t.des_dia_semana, t.num_dia_semana
ORDER BY t.num_dia_semana
```

---

## 6. Interações Planejadas

- **Clique em barra do gráfico** → filtra data table abaixo
- **Drill-down em loja** → abre visão detalhada da loja (novo dashboard ou modal)
- **Hover em série do gráfico** → tooltip com valor exato
- **Clique em cabeçalho de tabela** → ordena ascendente/descendente
- **Exportar dados** → botão de download CSV no canto superior direito da table

---

## 7. Notas Técnicas

- **Engine:** Power BI (pbix) ou web app estático (HTML+Chart.js)
- **Data refresh:** Diário via pipeline n8n
- **Snapshot:** gold.fato_vendas materializado no DuckDB
- **Fonte:** Dados reais de 2017–2020 (~10.596 vendas, 15 lojas)

---

## 8. Estado Atual

- [x] Wireframe HTML produzido
- [ ] Design system tokens integrados
- [ ] Implementação Power BI
- [ ] Testes de acesso e performance
- [ ] Revisão de acessibilidade (WCAG 2.1 AA)
