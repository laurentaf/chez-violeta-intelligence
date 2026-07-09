# Dashboard do Comprador — Chez Violeta

Dashboard self-contained para consulta diária de compras, gerado a
partir dos dados da simulação de 360 dias (output-360d-v2).

## Como usar

Abra `index.html` diretamente no navegador. Nenhum servidor necessário
— todos os dados estão embutidos no HTML.

## Funcionalidades

1. **KPI Cards** — 4 indicadores no topo:
   - Total em alertas pendentes (R$)
   - Alertas CRITICAL no último dia
   - Fornecedores com pior compliance
   - Produtos em risco de ruptura (cobertura ≤ 5 dias)

2. **Tabela de Alertas** — filtrável por:
   - Dia (dropdown com todos os dias do período)
   - Urgência (CRITICAL / HIGH / MEDIUM / LOW)
   - Fornecedor
   - Categoria

3. **Gráficos:**
   - Linha: Vendas (R$) vs Estoque ao longo dos 360 dias
   - Pizza: Distribuição de alertas por categoria
   - Barra horizontal: Top 10 fornecedores por valor de alerta

4. **Performance de Fornecedores** — ranking de compliance com
   barras visuais, ordenável por qualquer coluna

5. **Produtos Lentos (Slow Movers)** — ordenável por dias sem venda
   ou quantidade em estoque, com desconto sugerido e badge visual

## Design System

- **Paleta:** Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5
- **Tipografia:** Cormorant Garamond (títulos), Inter (corpo)
- **Fonte:** Google Fonts (carregada via CDN)
- **Gráficos:** Chart.js 4.4.4 (carregado via CDN)
- **Responsivo:** Adaptável para desktop e mobile

## Dados

Fonte: `artifacts/simulation/output-360d-v2/`

| Dataset | Registros | Uso |
|---------|-----------|-----|
| daily_log.csv | 361 dias | Gráfico vendas vs estoque |
| supplier_performance.csv | 178 fornecedores | Tabela de compliance |
| slow_movers.csv | Top 100 | Tabela de produtos lentos |
| purchase_alerts.csv | Últimos 30 dias | Tabela de alertas + KPIs |

## Marcadores de Compliance

O dashboard é marcado como `MOCK — Dados de simulação, não para produção`
conforme a política de dados sintéticos (Hard Rule #11).

## Referência

- `source.md` — DESIGN.md de referência
- `generate.py` — Script gerador do HTML
- `template.html` — Template HTML usado pelo gerador
- `index.html` — Dashboard final (self-contained)
