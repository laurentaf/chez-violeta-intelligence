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
- **Dashboard do Comprador (v6)**: Abrir `artifacts/design/dashboard-comprador/index.html` no navegador
- **Chatbot da Loja**: Abrir `artifacts/design/chatbot-loja/index.html` no navegador

| Path | Conteúdo |
|------|----------|
| `artifacts/data/` | Modelo dimensional, DDL gold layer, pricing model |
| `artifacts/data/chez_gold.duckdb` | Gold layer DuckDB (10M+ linhas) |
| `artifacts/design/` | Design system, wireframes de dashboards |
| `artifacts/dq/` | Data quality checks |

## Schema de dados
100 tabelas de negócio (~13.6M linhas) extraídas do sistema GAVARNIE
(Oracle Export 10.01.00, 2020-05-29). Domínios: vendas, estoque,
compras, financeiro, RH, logística.

## Modelo de Previsao (Prophet)

| Metrica | Valor |
|---------|-------|
| Modelo | Prophet 1.3.0 (Facebook) |
| Fonte | `fato_estoque_diario.qtd_venda` |
| Periodo historico | 2017-12-01 a 2019-11-30 |
| Registros | 619,289 vendas (qtd_venda > 0 de 11 lojas) |
| Categorias | 5 modelos (UNDERWARE, MODA PRAIA, VESTUARIO, LINHA NOITE, OUTROS) |
| Horizonte | 26 semanas (182 dias) |
| Sazonalidade | Anual (multiplicativa) |
| Feriados | BR (11 feriados nacionais) |

### Previsao 26 semanas por Categoria

| Categoria | Previsao Total | Media Diaria | Pico |
|-----------|---------------|--------------|------|
| UNDERWARE | 55,862 | 306.9/dia | 25/Dez |
| VESTUARIO | 26,125 | 143.5/dia | 22/Dez |
| MODA PRAIA | 15,035 | 82.6/dia | 25/Dez |
| LINHA NOITE | 14,247 | 78.3/dia | 19/Mai |
| OUTROS | 715 | 3.9/dia | 20/Dez |

### Insights Sazonais

- **UNDERWARE** — Pico em Dez (+38%), vale em Fev (-29%). Sazonalidade media-alta.
- **MODA PRAIA** — Altissima sazonalidade: Nov/Dez +121%/+110%, Jun/Jul -89%/-87%. Biquini vende muito no verao, quase nada no inverno.
- **VESTUARIO** — Pico em Dez (+53%), vale em Abr (-40%). Mais estavel que MODA PRAIA.
- **LINHA NOITE** — Pico em Ago (+56%) e Mai (+42%). Padrao diferente - possivel correlacao com Dias dos Namorados (Jun) e inverno.
- A maioria das categorias tem pico na **ultima semana do ano** (Natal), consistente com presenteismo e confraternizacoes.

### Estoque Recomendado (120 dias)

| Categoria | Previsao 120d | Estoque Recomendado |
|-----------|--------------|-------------------|
| UNDERWARE | 36,811 | 44,172 |
| MODA PRAIA | 14,041 | 16,848 |
| VESTUARIO | 17,998 | 21,597 |
| LINHA NOITE | 7,837 | 9,404 |
| OUTROS | 524 | 628 |
| **TOTAL** | | **92,649** |

*Margem de seguranca: 20%.*

### Outputs

| Arquivo | Conteudo |
|---------|----------|
| `artifacts/data/prophet_models.pkl` | 5 modelos serializados (Prophet JSON) |
| `artifacts/data/prophet_forecast.csv` | Previsao completa (3.974 linhas, historico + futuro) |
| `artifacts/data/prophet_forecast_future.csv` | Apenas futuro (910 linhas, 182 dias x 5 categorias) |
| `artifacts/data/prophet_components.png` | Grafico previsao vs historico |
| `artifacts/data/prophet_report.md` | Relatorio completo com recomendacao de compra |
