# Relatório de Regressão — Previsão Semanal de Vendas

## 1. Resumo do Modelo

| Métrica | Valor |
|---------|-------|
| **R²** | 0.7260 |
| **R² Ajustado** | 0.6942 |
| **AIC** | 277.2 |
| **BIC** | 305.5 |
| **N (observações)** | 97 |
| **K (parâmetros)** | 11 |
| **Fórmula** | `qtd_log ~ C(categoria) + C(quarter) + t` |

### Interpretação do R²

O R² de **72.60%** significa que o modelo explica 72.6% da variância 
do log das vendas semanais usando apenas categoria, trimestre e tendência linear. 
O R² ajustado de **69.42%** penaliza pela quantidade de parâmetros, 
dando uma estimativa mais realista do poder explicativo.

**Limitação:** Com apenas 97 observações e 11 parâmetros, 
há risco de overfitting. Recomenda-se reavaliar o modelo conforme mais dados 
de vendas forem acumulados.

---

## 2. Top 20 Coeficientes

| Termo | Coeficiente | p-valor | Sig. |
|-------|-------------|---------|------|
| `C(categoria)[T.UNDERWARE]` | +4.3714 | 0.0000 | *** |
| `C(categoria)[T.LINHA NOITE]` | +3.2638 | 0.0000 | *** |
| `C(categoria)[T.VESTUARIO]` | +3.0286 | 0.0000 | *** |
| `C(categoria)[T.MODA PRAIA]` | +2.7003 | 0.0000 | *** |
| `C(quarter)[T.Q3]` | -1.2312 | 0.0095 | *** |
| `Intercept` | +0.9607 | 0.2217 |  |
| `C(categoria)[T.FITNESS]` | +0.6539 | 0.2933 |  |
| `C(categoria)[T.BIJU / JOIAS]` | +0.6378 | 0.3879 |  |
| `C(categoria)[T.EROTICA]` | +0.4231 | 0.4954 |  |
| `C(quarter)[T.Q4]` | -0.4226 | 0.3138 |  |
| `t` | +0.0072 | 0.3072 |  |

*(Significância: *** p<0.01, ** p<0.05, * p<0.1)*

---

## 3. Sazonalidade Identificada

### Efeitos de Trimestre

- Q3: -1.23 (p=0.0095) (significativo)
- Q4: -0.42 (p=0.3138)

Os coeficientes de trimestre indicam o desvio nas vendas (em log) em relação ao trimestre de referência (Q1).

- **Q2 (Abr-Jun):** Período de lançamentos de moda praia e coleção outono-inverno.
- **Q3 (Jul-Set):** Preparação para coleção primavera-verão.
- **Q4 (Out-Dez):** Alta sazonalidade com Black Friday e Natal.

### Sazonalidade por Categoria

As categorias com maior coeficiente positivo na regressão indicam maior volume relativo:

| Categoria | Coeficiente | Significância |
|-----------|-------------|---------------|
| BIJU / JOIAS | +0.64 | ⚠️ (p=0.3879) |
| EROTICA | +0.42 | ⚠️ (p=0.4954) |
| FITNESS | +0.65 | ⚠️ (p=0.2933) |
| LINHA NOITE | +3.26 | ✅ (p=0.0000) |
| MODA PRAIA | +2.70 | ✅ (p=0.0000) |
| UNDERWARE | +4.37 | ✅ (p=0.0000) |
| VESTUARIO | +3.03 | ✅ (p=0.0000) |

---

## 4. Tendência

**TENDENCIA NAO SIGNIFICATIVA**

O coeficiente de tendencia (t=0.0072, p=0.3072) nao e estatisticamente significativo a 5%.

Interpretação prática: se a tendência é crescente, os pedidos de compra devem
considerar volumes maiores ao longo do tempo. Se decrescente, revisar mix de produtos.

---

## 5. Previsão para as Próximas Compras (120 dias)

Abaixo, a previsão de vendas para cobrir **18 semanas (~120 dias)** à frente,
por categoria. Use estes valores como referência para pedidos de compra.

| Categoria | Previsão 120d | Mínimo | Máximo |
|-----------|--------------|--------|--------|
| UNDERWARE | 6,277 un. | 3,120 | 12,904 |
| LINHA NOITE | 2,062 un. | 1,021 | 4,241 |
| VESTUARIO | 1,626 un. | 805 | 3,341 |
| MODA PRAIA | 1,166 un. | 544 | 2,547 |
| FITNESS | 135 un. | 59 | 294 |
| BIJU / JOIAS | 132 un. | 42 | 378 |
| EROTICA | 103 un. | 44 | 230 |
| ACESSORIOS | 62 un. | 8 | 269 |

**Nota:** Os valores mínimos e máximos representam o intervalo de confiança de 95% da previsão.
Compre acima do valor previsto para evitar ruptura, considerando lead time de reposição.

---

## 6. Exemplo Prático

### "Se comprar na Semana 10 de 2026, quanto pedir de UNDERWARE para cobrir até a Semana 27?"

O modelo não utiliza semana como variável categórica (devido à esparsidade dos dados),
então a resposta depende da **tendência linear** e do **trimestre** da semana em questão.

Para calcular:

1. **Localizar o trimestre:** Semana 10 ~ meados de março → **Q1**
2. **Cobertura (Semana 10 → Semana 27 = 17 semanas):**
   - Previsão total ≈ previsão_semanal_média × 17

3. **Recomendação prática:**
   - Pedir **6,277 unidades** de UNDERWARE para cobrir 120 dias
   - Com margem de segurança, considerar até **12,904 unidades**
   - Consulte `weekly_predictions.csv` para a previsão detalhada semana a semana

> **Ação sugerida:** Quantidade recomendada para próximo pedido de UNDERWARE:
> **6,277 unidades** (margem de segurança: 12,904)

---

## 7. Notas Técnicas

### Limitações do Modelo

1. **Dados esparsos:** Apenas 16 semanas com vendas entre 2018-2020. O modelo usou
   trimestre (Q1-Q4) em vez de semana individual para capturar sazonalidade.
2. **Sem interação categoria × semana:** Com 97 observações, incluir interações
   adicionaria muitos parâmetros sem dados suficientes.
3. **Quebra temporal:** Houve gaps grandes sem vendas (dez/2018-set/2019, out/2019-abr/2020),
   possivelmente devido a sazonalidade operacional ou pandemia.
4. **Dados limitados para previsão:** Prever 26 semanas com base em 16 semanas de
   dados históricos tem alta incerteza — usar com cautela.

### Recomendações

1. **Acumular mais dados:** A cada mês de operação, re-treinar o modelo com os
   novos dados de vendas para melhorar a precisão.
2. **Modelo hierárquico futuro:** Com >200 observações, migrar para um modelo
   com efeitos mistos (categoria como grupo aleatório) e sazonalidade semanal via
   componentes Fourier.
3. **Validação:** Comparar previsões com vendas reais após 4 semanas para calibrar.

---

*Relatório gerado automaticamente em 12/07/2026 13:33*
*Fonte: chez_gold.duckdb | Modelo: statsmodels OLS*
