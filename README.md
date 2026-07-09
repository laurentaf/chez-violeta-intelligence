# Chez Violeta — Operations Intelligence Platform

## O que é
Plataforma de inteligência operacional para a Chez Violeta,
loja de joias e acessórios. Unifica dados de vendas, estoque,
compras, financeiro e RH em um único data warehouse analítico.

## Como rodar
1. PostgreSQL em Docker: `docker run -d --name chez-pg -p 5433:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chez_violeta postgres:16`
2. Acessar dados: `psql postgresql://postgres:postgres@localhost:5433/chez_violeta`
3. Gold layer DuckDB em `artifacts/data/chez_gold.duckdb`
4. Para reproduzir o gold layer: `python artifacts/data/etl_gold.py`

## Onde está o quê
| Path | Conteúdo |
|------|----------|
| `spec/` | SDD — Constitution, TODO, ADRs, specs |
| `spec/adr/` | Architecture Decision Records (001-star-schema, 002-pricing-model) |
| `spec/specs/000-bootstrap/` | Spec de bootstrap do projeto |
| `contract.md` | Contrato do projeto (brief, needs, deliverables) |
| `artifacts/simulation/` | Motor de Simulação de Estoque + outputs 360 dias |
| `artifacts/simulation/output-360d-v2/` | 360 dias simulados (CSVs, relatórios do comprador) |
| `artifacts/simulation/output-360d-v2/buyer_reports/` | 360 relatórios diários para o comprador |
| `artifacts/design/dashboard-comprador/` | Dashboard visual do comprador (HTML) |
| `artifacts/design/chatbot-loja/` | Chatbot de processos para lojas (HTML) |
| `artifacts/design/processo-entrada-mercadorias.md` | Documentação do processo de entrada |
| `artifacts/data/sales-generator.py` | Gerador de vendas sintéticas (ARIMA) |

## Status
Stage 0 (SDD Scaffold) ✅ | Stage 1 (Data Model) ✅ | Stage 2 (Dashboards + Pricing) ✅ | Stage 2b (Integridade + Processo + Gerador) ✅ | Stage 2c (Simulação 360 dias) ✅ | Stage 3 (parcial: Dashboard Comprador + Chatbot ✅, Pipeline automatizado pendente) | Stage 4 (Deck Executivo pendente)

## Como rodar a simulação
```bash
cd F:/projects/chez-violeta-intelligence
uv run python artifacts/simulation/simulation_engine.py --days 30 --verbose
uv run python artifacts/simulation/simulation_engine.py --days 360 --seed 42
```

## Como abrir os dashboards
- **Dashboard do Comprador**: Abrir `artifacts/design/dashboard-comprador/index.html` no navegador
- **Chatbot da Loja**: Abrir `artifacts/design/chatbot-loja/index.html` no navegador
| `artifacts/data/` | Modelo dimensional, DDL gold layer, pricing model |
| `artifacts/data/chez_gold.duckdb` | Gold layer DuckDB (10M+ linhas) |
| `artifacts/design/` | Design system, wireframes de dashboards |
| `artifacts/dq/` | Data quality checks |

## Schema de dados
100 tabelas de negócio (~13.6M linhas) extraídas do sistema GAVARNIE
(Oracle Export 10.01.00, 2020-05-29). Domínios: vendas, estoque,
compras, financeiro, RH, logística.

## Status
Stage 0 (SDD Scaffold) completo. Pronto para Stage 1 (Data Model).
