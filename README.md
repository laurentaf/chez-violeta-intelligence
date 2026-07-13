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

## Por que Prophet (e nao OLS, Regressao ou ML)

### Contexto da decisao

O projeto comecou com uma regressao OLS semanal (`vendas ~ categoria + trimestre + tendencia`, R²=0.726), mas dois fatores motivaram a evolucao:

**1. Dados incompletos na primeira extracao**
- Usavamos `fato_vendas` (10.476 linhas) — apenas 1 dos 2 sistemas de registro
- O dado real de vendas estava em `fato_estoque_diario.qtd_venda` (676.630 linhas)
- Com 64x mais dados, o cenario mudou completamente

**2. Modelagem de feriados e datas comerciais brasileiras**
- O OLS com dummies de trimestre nao captura dia especifico algum
- Prophet captura feriados oficiais BR, mas datas comerciais (12/06, Black Friday) precisam ser adicionadas manualmente

### Arvore de decisao completa

```
Quantos meses de dados historicos continuos temos?
  ├── 0-6 meses   → Media movel simples (dados insuficientes para qualquer modelo)
  ├── 6-12 meses  → Regressao OLS com dummies de mes (poucos dados, evitar overfitting)
  ├── 12-24 meses → Prophet (ideal: minimo de 1 ciclo sazonal completo)  ← ESTAMOS AQUI
  ├── 24-36 meses → Prophet ou SARIMA (ambos viaveis com 2+ ciclos)
  └── 36+ meses   → Prophet, SARIMA ou XGBoost (dados suficientes para ML)

Quantas observacoes (linhas de venda)?
  ├── < 1.000     → Regressao simples (evitar qualquer modelo complexo)
  ├── 1.000-50.000 → OLS com dummies (suficiente para 10-20 parametros)
  ├── 50.000-500.000 → Prophet (ideal para este volume)  ← ESTAMOS AQUI (676k)
  └── 500.000+    → Prophet ou XGBoost (ML comeca a ser viavel)

Precisamos capturar feriados e datas comerciais?
  ├── SIM, feriados oficiais → Prophet.add_country_holidays('BR')
  │    (Natal, Ano Novo, Tiradentes, 7 Setembro, 15 Novembro, etc.)
  ├── SIM, datas comerciais → Prophet.add_regressor() manual
  │    (12/06 - Dia dos Namorados, Black Friday, Dias das Maes/Pais)
  │    NOTA: Dia das Maes e Dia dos Pais NAO sao feriados nacionais brasileiros
  └── NAO → OLS ou SARIMA (sazonalidade fixa basta)

O comprador precisa entender o "por que" da previsao?
  ├── SIM → Prophet (componentes sazonais plotaveis) ou OLS (coeficientes)
  └── NAO → XGBoost/LightGBM (maior precisao possivel, menor explicabilidade)
  
As vendas tem sazonalidade multipla (ano + mes + dia da semana)?
  ├── SIM → Prophet (multiplas sazonalidades nativas)  ← ESTAMOS AQUI
  └── NAO → OLS ou SARIMA (sazonalidade unica)
```

### Feriados vs Datas Comerciais no Brasil

O Prophet `add_country_holidays('BR')` inclui **apenas feriados nacionais oficiais**:

| Feriado | Data | Prophet captura? | Impacto vendas |
|---------|:----:|:----------------:|:--------------:|
| Confraternizacao Universal | 01/Jan | ✅ | Medio |
| Carnaval | movel | **Nao** (precisa add manual) | Alto |
| Sexta-Feira Santa | movel | ✅ | Baixo |
| Tiradentes | 21/Abr | ✅ | Baixo |
| Dia do Trabalho | 01/Mai | ✅ | Medio |
| **Dia das Maes** | **2º dom Maio** | **NAO** 🔴 | **Altissimo** |
| Corpo de Deus | movel | ✅ | Baixo |
| **Dia dos Namorados** | **12/Jun** | **NAO** 🔴 | **Muito Alto** |
| Independencia | 07/Set | ✅ | Medio |
| **Dia das Criancas** | **12/Out** | ✅ | Alto |
| Finados | 02/Nov | ✅ | Baixo |
| Proclamacao da Republica | 15/Nov | ✅ | Medio |
| **Black Friday** | **nov (variavel)** | **NAO** 🔴 | **Altissimo** |
| **Dia dos Pais** | **2º dom Ago** | **NAO** 🔴 | **Alto** |
| Natal | 25/Dez | ✅ | **Altissimo** |
| Reveillon | 31/Dez | ✅ | Alto |

**⚠️ Importante:** O Prophet `add_country_holidays('BR')` usa a biblioteca `holidays` do Python, que inclui apenas feriados federais. **Dia das Maes, Dia dos Pais, Dia dos Namorados e Black Friday NAO sao feriados nacionais** e precisam ser adicionados manualmente como regressores.

Para este projeto, os dados historicos (2017-2019) tem apenas **2 ocorrencias** de cada data comercial — insuficiente para o Prophet aprender o efeito sozinho. A solucao adotada foi:
- Usar **sazonalidade anual multiplicativa** (captura o padrao geral por epoca do ano)
- As datas comerciais ficam "embutidas" na curva sazonal (ex: Dezembro tem +38% em UNDERWARE = Natal + Reveillon + confraternizacoes)
- Conforme mais dados forem acumulados, adicionar regressores especificos para cada data comercial

### Comparacao detalhada

| Aspecto | OLS com dummies | Prophet | Random Forest / XGBoost |
|---------|:--------------:|:-------:|:-----------------------:|
| **Dados necessarios (linhas)** | 50+ | **1.000 - 500.000** (temos 676k) | 5.000+ |
| **Dados necessarios (temporal)** | 6+ meses | **12-24 meses** (temos 24) | 24+ meses |
| **Sazonalidade anual** | Dummy de mes/trimestre | **Nativa** (Fourier, suave) | Nao captura sozinha |
| **Multiplas sazonalidades** | Manual (2 sets de dummies) | **Nativa** (ano + semana + dia) | Feature engineering |
| **Feriados oficiais BR** | Feature engineering manual | **`add_country_holidays('BR')`** | Feature engineering |
| **Datas comerciais BR** | Feature engineering manual | **Manual** (regressor) | Feature engineering |
| **Tendencia nao-linear** | Polynomial features | **Changepoints nativos** | Captura |
| **Incerteza** (IC) | Nao nativa | **Intervalos de confianca** | Nao nativa |
| **Interpretabilidade** | Coeficientes (claros) | Componentes + plot | SHAP (aproximado) |
| **Overfitting com 676k pts** | Baixo | Baixo (regularizacao) | **Alto** (100+ arvores) |
| **Instalacao** | statsmodels (ok) | **`pip install prophet`** | sklearn (ok) |
| **Tempo de treino** | Milissegundos | 2-5 segundos por modelo | Segundos |

### Veredito

**Prophet foi a escolha certa porque:**
1. Temos **exatamente 24 meses** de dados — o minimo que o Prophet precisa para sazonalidade anual, e o maximo que temos disponivel
2. **676.634 registros** de venda — volume ideal para Prophet (acima de 500k ML comeca a ser viavel, mas ainda arriscado sem feature engineering)
3. Os **feriados oficiais sao capturados automaticamente** — Natal e Ano Novo (dez/jan) sao os maiores picos
4. As **datas comerciais** (12/06, Black Friday, Dia das Maes) ficam embutidas na curva sazonal anual, mas idealmente deveriam ser regressores manuais quando houver mais dados
5. O **comprador precisa entender** "por que comprar agora?" — os graficos de componentes do Prophet mostram visualmente o pico de cada mes
6. Com **676 mil registros e apenas 24 meses**, ML como XGBoost sofreria overfitting por ter mais arvores que ciclos sazonais completos
7. OLS com dummies de semana exigiria ~60 parametros para capturar 52 semanas — Prophet faz isso com ~20 termos de Fourier, mais estavel

### Quando reavaliar

| Cenario | Modelo recomendado | Gatilho |
|---------|-------------------|---------|
| Acumular 36+ meses de dados | Prophet ou SARIMA | 2021 |
| Acumular 5+ anos de dados | XGBoost/LightGBM | 2023+ |
| Incluir features externas (clima, preco) | Prophet ou XGBoost | Quando disponivel |
| Precisao > 95% exigida | XGBoost | Quando houver 50k+ obs por categoria |
| Sem comprador (compra automatica) | XGBoost + regras | Quando houver 3+ anos de dados |

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
