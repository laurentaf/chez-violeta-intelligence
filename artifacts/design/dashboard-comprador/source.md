---
synthetic: true
kind: dashboard
label: "mock, not for production"
granted_by: project_yaml
granted_at: 2026-07-08T10:00:00Z
reason: "dados da simulação output-360d-v2 previamente executada (seed=42, 360 dias)"
---

# Fonte de Design — Dashboard do Comprador Chez Violeta v2

**DESIGN.md de referência:** O presente dashboard segue o design system
Chez Violeta definido no brief do projeto:

- **Paleta:** Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5
- **Tipografia:** Cormorant Garamond (headings), Inter/System (body)
- **Projeto:** chez-violeta-intelligence
- **Needs:** dashboard
- **Capabilities:** ladesign
- **Data policy:** `synthetic: true` (dados de simulação de 360 dias)

## Fontes de dados

CSVs da simulação em `artifacts/simulation/output-360d-v2/`:
- `purchase_alerts_enriched.csv` — 7.111 alertas enriquecidos com dados de pedido pendente
- `supplier_performance.csv` — 178 fornecedores (compliance, atrasos)
- `stock_by_store.csv` — 45.050 registros de estoque por loja
- `slow_movers.csv` — produtos com baixa rotatividade
- `daily_log.csv` — log diário de estoque, vendas e rupturas
- `risk-analysis-methodology.md` — metodologia de classificação de risco

## Versão 2 — Melhorias

vs versão anterior (`index.html` original):

1. ✅ **Tabela de alertas completamente interativa** — ordenação por qualquer coluna, 13 colunas com dados enriquecidos
2. ✅ **Colunas novas:** Tem Pedido?, Previsão Chegada, Chega Antes da Ruptura?, Risco
3. ✅ **Destaque vermelho** em linhas que NÃO chegam antes da ruptura
4. ✅ **Seção "Cobertura por Loja"** — estoque por loja para produtos em alerta
5. ✅ **Seção "Risco de Ruptura vs Pedidos"** — cards explicativos + tabela
6. ✅ **Seção "Performance de Fornecedores"** — ordenável, com nota A-D + explicação
7. ✅ **KPIs no topo** — total, % alto/crítico, ruptura antes do pedido, pior fornecedor
8. ✅ **Gráficos** — distribuição de risco (rosca), alertas por categoria (barras), top fornecedores
9. ✅ **Design system Chez Violeta** — vinho, dourado, off-white
10. ✅ **Responsivo** — adapta a mobile
11. ✅ **MOCK banner** no topo
12. ✅ **Self-contained** — HTML único com dados embutidos em JSON, Chart.js via CDN

## Artefatos

- `dashboard-comprador/index.html` — Dashboard self-contained (231 KB)
- `dashboard-comprador/README.md` — Documentação do dashboard
- `dashboard-comprador/source.md` — Este arquivo (fonte de design)
- `dashboard-comprador/data.json` — Dados extraídos em JSON (intermediário)
- `dashboard-comprador/extract_data.py` — Script de extração de dados
- `dashboard-comprador/generate_dashboard.py` — Gerador do HTML final

## Dados embutidos

- 200 alertas mais recentes (dos 7.111 totais)
- 178 fornecedores
- Estoque por loja para produtos em alerta (~1.008 registros)
- Resumo estatístico completo

## Notas Técnicas

- Chart.js 4.4.4 via CDN (requer internet na primeira carga)
- Google Fonts (Cormorant Garamond + Inter) via CDN
- Navegador: Chrome, Firefox, Edge (moderno)
- Abertura local: `file:///F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html`
