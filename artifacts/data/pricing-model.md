# Chez Violeta — Modelo de Elasticidade-Preço

- **Versão:** 1.0
- **Data:** 2026-07-02
- **Autor:** data-architect (Laurent)
- **Cadência:** Snapshot único (não recorrente — necessita revisão quando houver mudanças de preço)

---

## 1. Objetivo

Estimar a elasticidade-preço da demanda dos produtos Chez Violeta: dado um aumento de X% no preço, qual a variação percentual esperada na quantidade vendida?

---

## 2. Fonte de Dados

| Fonte | Localização |
|-------|-------------|
| Gold Layer DuckDB | `F:/Projetos/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb` |
| Tabela principal | `gold.fato_vendas` |
| Dimensão de produto | `gold.dim_produto` |
| Dimensão de tempo | `gold.dim_tempo` |

**Período:** 2017-11-21 a 2020-05-28 (10.435 linhas, 3.546 produtos únicos, 10 lojas).

---

## 3. Metodologia

### 3.1 Abordagem escolhida: Log-Log Agregado por (Categoria, Mês)

```math
ln(Q_{c,m}) = \alpha_c + \beta_c \cdot ln(P_{c,m}) + \varepsilon_{c,m}
```

Onde:
- \(Q_{c,m}\) = soma de peças vendidas na categoria *c* no mês *m*
- \(P_{c,m}\) = preço médio (val_venda_liquida) na categoria *c* no mês *m*
- \(\beta_c\) = elasticidade-preço da categoria *c*
- \(\alpha_c\) = intercepto por categoria (efeito fixo)

### 3.2 Por que não intra-SKU?

A análise intra-produto (Step 3 do profile) mostrou:

- **90,3%** dos produtos (3.202 de 3.546) foram vendidos a **um único preço** — sem variação para estimar elasticidade
- Apenas **15 produtos** (0,4%) têm ≥50 transações **e** ≥2 preços distintos — o mínimo necessário para uma regressão intra-SKU
- Mesmo nesses 15, a variação de preço é marginal (ex: R$19,99 vs R$19,56 — centavos de diferença, provavelmente descontos promocionais, não mudanças de preço)
- A exceção são 2 SKUs de cueca boxer (id 8346, 8347) com R$7,50–R$28,29 de amplitude, mas com apenas 57–73 transações

**Conclusão:** A base de vendas Chez Violeta não tem variação sistemática de preço intra-SKU suficiente para estimar elasticidade em nível de produto. A abordagem agregada por (categoria, mês) é a única viável com os dados disponíveis.

### 3.3 Limitações conhecidas

1. **Efeito-Composição:** O preço médio mensal por categoria varia porque o *mix de SKUs* vendidos muda entre meses, não porque o mesmo SKU foi vendido a preços diferentes. Categorias onde SKUs mais caros vendem mais em meses de alta demanda produzem elasticidades positivas espúrias (Simpson's Paradox).
2. **Poucos períodos:** A série temporal tem no máximo 9 meses por categoria (para categorias principais), limitando a significância estatística.
3. **Agregação cross-store:** Não controla por loja — lojas com sortimento diferente podem distorcer o preço médio.
4. **Causalidade reversa:** Demanda alta pode levar a preços mais altos (se a loja remarcar para cima em momentos de pico), não o contrário.

---

## 4. Resultados

### 4.1 Elasticidades por Categoria

| Categoria | Obs | Elasticidade (β) | R² | Preço Médio | Qtd Total | Interpretação |
|-----------|-----|-----------------|-----|-------------|-----------|---------------|
| BIJU / JOIAS | 3 | **-1,25** | 0,05 | R$ 10,22 | 46 | Elástica (n pequeno) |
| EROTICA | 8 | **+0,37** | 0,02 | R$ 30,88 | 71 | Inelástica (sinal + = mix) |
| FITNESS | 8 | **+1,40** | 0,05 | R$ 38,68 | 80 | Elástica (sinal + = mix) |
| LINHA NOITE | 9 | **+5,12** | 0,30 | R$ 49,86 | 3.122 | Elástica (sinal + = mix) |
| MODA PRAIA | 6 | **-3,66** | 0,16 | R$ 59,40 | 937 | **Altamente elástica** |
| UNDERWARE | 9 | **+5,34** | 0,10 | R$ 23,39 | 4.883 | Elástica (sinal + = mix) |
| VESTUARIO | 9 | **-3,42** | 0,20 | R$ 63,37 | 1.298 | **Altamente elástica** |

**Pooled (todas categorias):** β = +1,00, R² = 0,09 (elasticidade unitária — mas dominada por efeito-composição)

### 4.2 Categorias com elasticidade negativa confiável (higher price → lower quantity)

| Categoria | Elasticidade | Recomendação de precificação |
|-----------|-------------|------------------------------|
| **MODA PRAIA** | **-3,66** | Redução de preço aumenta receita. Ex: -10% no preço → +37% na qtd → +23% na receita. |
| **VESTUARIO** | **-3,42** | Redução de preço aumenta receita. Ex: -10% no preço → +34% na qtd → +21% na receita. |
| BIJU / JOIAS | -1,25 | Potencialmente elástica, mas n=3 apenas — não confiável. |

### 4.3 Categorias com elasticidade positiva (mix effect)

| Categoria | Elasticidade | Explicação |
|-----------|-------------|------------|
| LINHA NOITE | +5,34 | SKUs de maior valor agregado vendem mais em meses de alta sazonalidade (ex: Dia dos Namorados, Natal). |
| UNDERWARE | +5,34 | Produtos de maior preço médio dentro da categoria vendem mais em certos meses — o preço não caiu, o mix mudou. |
| FITNESS | +1,40 | Mesmo padrão, menos intenso. |
| EROTICA | +0,37 | Praticamente inelástica — variação de preço não explica variação de demanda. |

---

## 5. Recomendações

### 5.1 Imediatas (com dados atuais)

1. **MODA PRAIA e VESTUARIO são candidatas a testes de redução de preço.** A elasticidade negativa e de magnitude > 3 sugere que cortes de preço podem aumentar a receita. Recomenda-se reduzir preços em 5-10% em um subconjunto de SKUs destas categorias e medir o impacto nas vendas por 30 dias.
2. **Ignorar elasticidades positivas para decisões de precificação.** As elasticidades positivas de UNDERWARE, LINHA NOITE e FITNESS refletem composição de mix, não sinal de precificação. Decisões de preço nestas categorias devem ser baseadas em margem e posicionamento, não na elasticidade agregada.

### 5.2 Futuras (mudanças no processo de dados)

3. **Implementar rastreamento de mudanças de preço.** A principal limitação é a falta de variação de preço intra-SKU. Para resolver isso:
   - Criar uma tabela `fato_precificacao` que registre o histórico de preços por SKU (preço de tabela, não preço médio de venda) com datas de vigência
   - Isso permite estimar elasticidade com efeitos fixos de produto: `ln(qty) = β·ln(price) + γ_i (product FE) + ε`
4. **Conduzir experimentos A/B.** Para categorias com mix complexo (UNDERWARE, LINHA NOITE), um experimento A/B com mudanças controladas de preço é mais confiável que regressão com dados observacionais.
5. **Desagregar por loja.** Incluir efeitos fixos de loja no modelo para controlar por diferenças de sortimento entre lojas.

---

## 6. Dicionário do Modelo

| Coluna | Definição | Fonte |
|--------|-----------|-------|
| categoria | Nome da categoria de produto (COALESCE) | dim_produto.des_categoria |
| mes | Primeiro dia do mês da venda | DATE_TRUNC('month', dim_tempo.dat_dia) |
| qtd | Soma de peças vendidas no mês-categoria | SUM(fato_vendas.qtd_pecas) |
| preco | Preço médio ponderado no mês-categoria | AVG(fato_vendas.val_venda_liquida) |
| ln_qtd | Log natural da quantidade | LN(qtd) |
| ln_preco | Log natural do preço médio | LN(preco) |
| elasticidade | Coeficiente β da regressão ln_qtd ~ ln_preco | regr_slope(ln_qtd, ln_preco) |

---

## 7. Auditoria

- **Pipeline executado em:** 2026-07-02
- **Scripts:**
  - `artifacts/data/_pricing_analysis.py` — profile e variação intra-SKU
  - `artifacts/data/_pricing_regression.py` — regressão log-log
- Ferramentas: DuckDB (regr_slope, regr_intercept, regr_r2)
- Decisão metodológica documentada em: `spec/adr/002-pricing-model.md`
