# Fonte de Design — Dashboard do Comprador Chez Violeta

**DESIGN.md de referência:** O presente dashboard segue o design system
Chez Violeta definido no brief do projeto:

- **Paleta:** Vinho #7B2D4E, Dourado #C9A84C, Off-white #FAF8F5
- **Tipografia:** Cormorant Garamond (headings), Inter/System (body)
- **Projeto:** chez-violeta-intelligence
- **Needs:** dashboard
- **Capabilities:** ladesign
- **Data policy:** `synthetic: true` (dados de simulação de 360 dias)
- **granted_by:** project_yaml (simulação aprovada no escopo do projeto)
- **granted_at:** 2026-07-08
- **reason:** dados da simulação output-360d-v2 previamente executada

## Fontes de dados

CSVs da simulação em `artifacts/simulation/output-360d-v2/`:
- `purchase_alerts.csv` — alertas de compra por data/produto/fornecedor
- `daily_log.csv` — log diário de estoque, vendas, rupturas
- `supplier_performance.csv` — performance de fornecedores (compliance, atrasos)
- `slow_movers.csv` — produtos com baixa rotatividade e descontos sugeridos

## Artefato

- `dashboard-comprador/index.html` — Dashboard self-contained
- `dashboard-comprador/README.md` — Documentação do dashboard
