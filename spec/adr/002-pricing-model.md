# ADR-002: Escolha Metodológica para Modelo de Elasticidade-Preço

## Status
Accepted (2026-07-02)

## Context

Precisamos estimar a elasticidade-preço da demanda dos produtos Chez Violeta. O gold layer (DuckDB) contém 10.435 linhas de vendas com 3.546 produtos únicos.

O desafio central é: **90,3% dos produtos foram vendidos a um único preço**. Sem variação de preço intra-produto, a elasticidade não pode ser estimada em nível de SKU.

Três abordagens foram avaliadas, cada uma com trade-offs diferentes dada a natureza dos dados.

## Decision

**Abordagem selecionada: Regressão Log-Log Agregada por (Categoria, Mês).**

```math
ln(Q_{c,m}) = \alpha_c + \beta_c \cdot ln(P_{c,m}) + \varepsilon_{c,m}
```

O modelo estima elasticidades separadas por categoria (efeitos fixos) usando 59 observações (categoria-mês) de 7 categorias com dados suficientes. A regressão foi executada via DuckDB (funções `regr_slope`, `regr_intercept`, `regr_r2`).

**Motivação:**
- É a única abordagem que produz estimativas com os dados disponíveis (não requer variação intra-SKU)
- A agregação mensal suaviza ruído de vendas diárias e captura tendências de preço/mix
- DuckDB suporta regressão linear nativa (sem dependências externas como scikit-learn ou statsmodels)

**Limitação documentada:** O coeficiente β captura tanto elasticidade-preço verdadeira quanto efeito-composição (mudança no mix de SKUs dentro da categoria). Categorias com alta sazonalidade e sortimento variado (UNDERWARE, LINHA NOITE) apresentam β > 0 — sinal de que o efeito-composição domina.

## Alternatives

### A) Regressão Log-Log intra-SKU com efeitos fixos de produto (DESCARTADA)

Modelo ideal: `ln(qty_{i,t}) = β·ln(price_{i,t}) + γ_i + δ_t + ε`

**Descartada porque:** 90,3% dos produtos têm apenas 1 preço distinto (sem variância intra-SKU para identificar β). Dos 344 produtos multi-preço, apenas 15 têm ≥50 transações. E mesmo estes 15 têm variação de centavos (ex: R$19,99 vs R$19,56), insuficiente para estimação confiável. Seriam necessários 2-3 anos de dados com mudanças sistemáticas de preço para viabilizar esta abordagem.

### B) Abordagem de Séries Temporais (VAR / Cointegração) (DESCARTADA)

Modelo multivariado com preços e quantidades como sistema endógeno.

**Descartada porque:** Requer séries longas e contínuas (idealmente ≥36 meses). Temos no máximo 9 meses por categoria (2017-11 a 2020-05, com gaps). Além disso, exigiria dependências externas (statsmodels) não disponíveis no ambiente atual.

### C) Abordagem de Painel com Efeitos Fixos de SKU e Loja (DESCARTADA, futura)

Modelo em painel usando variação de preço entre lojas para o mesmo SKU.

**Descartada porque:** Não há evidência de que o mesmo SKU tenha preços diferentes entre lojas nos dados atuais. Mas é a abordagem recomendada para o futuro, caso o processo de dados inclua precificação por loja.

## Consequences

+ **Positivo:** O modelo é executável com os recursos disponíveis (DuckDB, zero dependências externas). Produz estimativas numéricas para 7 categorias.
+ **Positivo:** Os resultados de MODA PRAIA (β = -3,66) e VESTUARIO (β = -3,42) são economicamente plausíveis e acionáveis — apontam para oportunidade de redução de preço.
+ **Positivo:** A documentação explícita da limitação (efeito-composição) evita uso ingênuo dos coeficientes positivos.
- **Negativo:** Elasticidades positivas de UNDERWARE e LINHA NOITE não são acionáveis — não sabemos se o efeito é preço ou mix.
- **Negativo:** O R² baixo (0,02–0,30) indica que o preço explica pouco da variação de demanda nestes dados. Outros fatores (sazonalidade, promoções, sortimento) dominam.
- **Negativo:** Com 6–9 observações por categoria, os intervalos de confiança são grandes e a significância estatística é baixa (não estimamos p-valores formalmente).
- **Negativo:** A causalidade é presumida (preço → quantidade), mas pode haver reversa (alta demanda → preços mais altos por remarcação).

## Recomendação para próxima iteração

1. Criar tabela de histórico de preços (preço de tabela por SKU com vigência) — permitiria intra-SKU elasticity com efeitos fixos
2. Conduzir experimento A/B controlado em MODA PRAIA e VESTUARIO para validar a elasticidade estimada
3. Incluir loja como efeito fixo quando houver precificação diferenciada por loja
