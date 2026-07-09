# Contrato — Chez Violeta Operations Intelligence Platform

## Brief
Plataforma de inteligência operacional para a Chez Violeta,
loja de joias e acessórios. Unifica dados de vendas, estoque,
compras, financeiro e RH em um único data warehouse analítico,
com dashboards operacionais, modelo de precificação e previsão
de estoque.

## Needs
data, dashboard, econometrics, predictive-modeling, automation, etl, data-quality, design

## Capabilities
- latade: SQL, DuckDB, modelagem dimensional
- ladesign: dashboards, design system
- laecon: econometria, elasticidade, previsão
- lan8n: automação de pipelines

## Deliverables
1. **data-model** — Star schema dimensional (gold layer)
2. **dashboards** — Dashboards de vendas e estoque
3. **pricing-model** — Elasticidade-preço e recomendações
4. **table-relationships** — Validação de integridade referencial
5. **goods-receipt-process** — Documentação do processo de entrada de mercadorias
6. **sales-generator** — Gerador de vendas sintéticas ARIMA
7. **automation** — Pipelines n8n (pending)
8. **deck** — Apresentação executiva (pending)

## Data Sources
Oracle DMP → PostgreSQL (localhost:5433/chez_violeta)
100 tabelas, 13.6M rows
PII: CLIENTES.NOME_CLIENTE, EMAIL, CELULAR; ESTABELECIMENTOS.NUM_CNPJ

## Repository
github.com/laurentaf/chez-violeta-intelligence
