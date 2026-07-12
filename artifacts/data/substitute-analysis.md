# Análise de Substitutos — Produtos Commodities

**Base:** `chez_gold.duckdb` (gold layer)  
**Data da análise:** 2026-07-12  
**Escopo:** UNDERWARE + FITNESS | Linhas: BASICO, MEIA, SHAPEWARE, MATERNITY, MASCULINO  
**Filtro:** Produtos ATIVOS, sem fim de vigência (`dat_fim_vigencia IS NULL`, `des_status = 'ATIVO'`)

---

## 1. Perfil Geral das Commodities

| Produto | Categoria | Linha | SKUs | Fornecedores | Custo Médio | Faixa de Custo |
|---|---|---|---|---|---|---|
| SOUTIEN | UNDERWARE | BASICO | 629 | 11 | R$ 10,39 | R$ 0,00–39,96 |
| CALCINHA | UNDERWARE | BASICO | 627 | 10 | R$ 5,04 | R$ 0,00–15,74 |
| CUECA | UNDERWARE | MASCULINO | 281 | 4 | R$ 9,72 | R$ 0,00–13,86 |
| BODY | UNDERWARE | SHAPEWARE | 114 | 3 | R$ 10,31 | R$ 0,00–26,28 |
| SOUTIEN | UNDERWARE | MATERNITY | 96 | 3 | R$ 16,16 | R$ 13,20–20,70 |
| MEIA-CALCA | UNDERWARE | MEIA | 92 | 2 | R$ 7,90 | R$ 0,00–13,45 |
| CALCINHA | UNDERWARE | SHAPEWARE | 78 | 6 | R$ 13,71 | R$ 0,00–18,55 |
| REGATA FINA | FITNESS | BASICO | 56 | 1 | — | — |
| BERMUDA | UNDERWARE | SHAPEWARE | 50 | 5 | R$ 5,64 | R$ 0,00–20,07 |
| TOP | FITNESS | BASICO | 34 | 3 | — | — |
| CALCINHA | UNDERWARE | MATERNITY | 30 | 3 | R$ 7,70 | R$ 7,40–7,80 |
| INDEFINIDO | UNDERWARE | SHAPEWARE | 27 | 2 | R$ 27,02 | R$ 0,00–52,00 |
| CALCA | FITNESS | BASICO | 24 | 2 | — | — |
| BERMUDA | FITNESS | BASICO | 22 | 2 | — | — |
| REGATA FINA | UNDERWARE | BASICO | 21 | 1 | R$ 12,16 | R$ 12,16–12,16 |
| BODY | UNDERWARE | BASICO | 20 | 2 | — | — |
| SHORTS | FITNESS | BASICO | 20 | 2 | — | — |
| SHORTS | UNDERWARE | SHAPEWARE | 16 | 2 | R$ 12,91 | R$ 8,09–20,29 |
| CALECON | UNDERWARE | BASICO | 16 | 1 | — | — |
| CAMISETE | UNDERWARE | BASICO | 13 | 1 | R$ 10,07 | R$ 10,07–10,07 |
| MEIA | UNDERWARE | MEIA | 10 | 2 | R$ 3,77 | R$ 0,00–8,84 |
| CALCA-CINTA | UNDERWARE | BASICO | 10 | 2 | — | — |
| FAIXA | UNDERWARE | BASICO | 8 | 1 | R$ 5,93 | R$ 5,93–5,93 |
| TOP | UNDERWARE | BASICO | 8 | 1 | — | — |
| BODY | UNDERWARE | MATERNITY | 7 | 1 | R$ 22,59 | R$ 22,59–22,59 |

**Total:** 27 grupos produto-linha | ~1.700 SKUs commodities

---

## 2. Grupos de Substitutos por Fornecedor

### 2.1 CALCINHA BASICO (UNDERWARE) — 4 fornecedores competindo

| Fornecedor | SKUs | Custo Médio | IQR (P25–P75) | Posição |
|---|---|---|---|---|
| **DIVA DONNA** | 300 | R$ 4,19 | R$ 3,45–4,55 | Líder em SKUs, preço baixo |
| **ZEE RUCCI** | 65 | R$ 5,21 | R$ 4,92–5,70 | Preço similar, menor sortimento |
| **TRIFIL** | 37 | R$ 12,66 | R$ 6,24–15,74 | Preço mais alto, maior var. |
| **VI LINGERIE** | 37 | R$ 4,39 | R$ 4,22–4,59 | Preço baixo, faixa estreita |

**Substitutos diretos:** DIVA DONNA ↔ ZEE RUCCI ↔ VI LINGERIE (todos na faixa R$ 3,45–5,70)  
**Substituto parcial:** TRIFIL (apenas na faixa R$ 6,24–15,74 sobrepõe com a faixa alta dos demais)

### 2.2 SOUTIEN BASICO (UNDERWARE) — 5 fornecedores competindo

| Fornecedor | SKUs | Custo Médio | IQR (P25–P75) |
|---|---|---|---|
| **VI LINGERIE** | 168 | R$ 15,00 | R$ 11,61–19,13 |
| **ZEE RUCCI** | 87 | R$ 14,18 | R$ 10,47–12,24 |
| **TRIFIL** | 20 | R$ 19,60 | R$ 14,51–14,51 |
| **JULIA MORAES** | 12 | R$ 18,55 | R$ 18,55–18,55 |
| **CLASS** | 4 | R$ 16,43 | R$ 16,43–16,43 |

**Substitutos diretos:** VI LINGERIE ↔ ZEE RUCCI (sobreposição em R$ 11,61–12,24)  
**Substitutos parciais:** TRIFIL, JULIA MORAES, CLASS (preço mais alto, segmento superior)

### 2.3 CUECA MASCULINO (UNDERWARE) — 3 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **MASH** | 231 | R$ 10,43 | R$ 7,88–11,86 |
| **ZEE RUCCI** | 4 | R$ 4,33 | R$ 4,33–4,33 |
| **CONFECCOES CANAA** | 4 | R$ 3,65 | R$ 3,65–3,65 |

**Substitutos diretos:** Nenhum (faixas não se sobrepõem — MASH é premium, ZEE RUCCI e CANAA são econômicos)  
**Nota:** MASH domina com 231 SKUs; ZEE RUCCI e CANAA atuam em faixa de entrada.

### 2.4 MEIA-CALCA MEIA (UNDERWARE) — 2 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **TRIFIL** | 53 | R$ 8,61 | R$ 6,39–12,16 |
| **LUPO** | 31 | R$ 7,70 | R$ 5,70–11,51 |

**Substitutos diretos:** TRIFIL ↔ LUPO (sobreposição completa em R$ 6,39–11,51)

### 2.5 CALCINHA SHAPEWARE (UNDERWARE) — 3 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **VI LINGERIE** | 41 | R$ 16,07 | R$ 11,65–17,92 |
| **ZEE RUCCI** | 11 | R$ 9,77 | R$ 9,12–10,92 |
| **TRIFIL** | 9 | R$ 13,87 | R$ 13,87–13,87 |

**Substitutos diretos:** VI LINGERIE ↔ TRIFIL (sobreposição ~ R$ 13,87)  
**Nota:** ZEE RUCCI é faixa mais baixa, não sobrepõe.

### 2.6 BODY SHAPEWARE (UNDERWARE) — 2 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **VI LINGERIE** | 32 | R$ 23,61 | R$ 19,86–26,28 |
| **TRIFIL** | 4 | R$ 17,45 | R$ 17,45–17,45 |

**Substitutos parciais:** TRIFIL está abaixo do P25 da VI LINGERIE. Sobreposição marginal.

### 2.7 BERMUDA SHAPEWARE (UNDERWARE) — 2 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **TRIFIL** | 9 | R$ 11,85 | R$ 8,91–14,20 |
| **LUPO** | 8 | R$ 16,27 | R$ 12,48–20,07 |

**Substitutos parciais:** Sobreposição parcial em R$ 12,48–14,20.

### 2.8 SHORTS SHAPEWARE (UNDERWARE) — 2 fornecedores

| Fornecedor | SKUs | Custo Médio | IQR |
|---|---|---|---|
| **TRIFIL** | 8 | R$ 10,13 | R$ 8,09–12,16 |
| **LUPO** | 8 | R$ 15,69 | R$ 11,08–20,29 |

**Substitutos parciais:** Sobreposição parcial em R$ 11,08–12,16.

### 2.9 Monofornecedores (sem substituto)

Estes grupos têm apenas 1 fornecedor com ≥ 3 SKUs — **sem substituto direto disponível**:

| Produto | Linha | Fornecedor | SKUs | Custo |
|---|---|---|---|---|
| BODY | MATERNITY | VI LINGERIE | 7 | R$ 22,59 |
| CALCINHA | MATERNITY | VI LINGERIE | 16 | R$ 7,70 |
| CAMISETE | BASICO | TRIFIL | 13 | R$ 10,07 |
| FAIXA | BASICO | TRIFIL | 8 | R$ 5,93 |
| INDEFINIDO | SHAPEWARE | ESBELT | 19 | R$ 38,39 |
| MEIA | MEIA | TRIFIL | 6 | R$ 5,03 |
| REGATA FINA | BASICO | ZEE RUCCI | 21 | R$ 12,16 |
| SOUTIEN | MATERNITY | VI LINGERIE | 48 | R$ 16,16 |

---

## 3. Regra de Substituição Proposta

### Definição

> **Produtos A e B são substitutos perfeitos** se compartilham o mesmo par `(des_produto, des_linha)` E seus custos de aquisição (`val_custo_inicial`) estão dentro de uma faixa de **±20% da média** do grupo produto-linha.

### Implementação sugerida

```sql
WITH group_stats AS (
    SELECT 
        des_produto,
        des_linha,
        AVG(val_custo_inicial) AS custo_medio_grupo,
        STDDEV(val_custo_inicial) AS custo_std_grupo
    FROM gold.dim_produto
    WHERE des_status = 'ATIVO' AND dat_fim_vigencia IS NULL
    GROUP BY des_produto, des_linha
)
SELECT 
    p.id_produto,
    p.cod_artigo,
    p.des_produto,
    p.des_linha,
    p.cod_fornecedor,
    p.val_custo_inicial,
    g.custo_medio_grupo,
    s.id_produto AS substituto_id,
    s.cod_artigo AS substituto_artigo,
    s.cod_fornecedor AS substituto_fornecedor,
    s.val_custo_inicial AS substituto_custo,
    ROUND(
        ABS(p.val_custo_inicial - s.val_custo_inicial) / NULLIF(g.custo_medio_grupo, 0) * 100, 1
    ) AS diff_pct
FROM gold.dim_produto p
JOIN group_stats g ON p.des_produto = g.des_produto AND p.des_linha = g.des_linha
JOIN gold.dim_produto s ON p.des_produto = s.des_produto 
    AND p.des_linha = s.des_linha
    AND p.id_produto <> s.id_produto
    AND ABS(p.val_custo_inicial - s.val_custo_inicial) <= g.custo_medio_grupo * 0.20
WHERE p.des_status = 'ATIVO' AND p.dat_fim_vigencia IS NULL
  AND s.des_status = 'ATIVO' AND s.dat_fim_vigencia IS NULL
  AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
```

### Thresholds e ajustes

| Grupo | Faixa de Substituição (custo) | Observação |
|---|---|---|
| CALCINHA BASICO | R$ 3,45–5,70 | ±20% cobre bem DIVA DONNA / ZEE RUCCI / VI LINGERIE |
| SOUTIEN BASICO | R$ 10,47–18,84 | ±20% cobre parcialmente; sugerir ±25% ou faixa por cluster |
| CUECA MASCULINO | R$ 7,88–11,86 | ±20% só cobre MASH; ZEE RUCCI e CANAA ficam fora |
| MEIA-CALCA | R$ 5,70–12,16 | ±20% cobre TRIFIL e LUPO perfeitamente |

### Regra por segmento de preço (recomendada)

Em vez de um percentual fixo, sugere-se **bandas por cluster**:

- **Econômico** (custo < R$ 6,00): ±25% (absorve variação de commodities de baixo custo)
- **Médio** (R$ 6,00–15,00): ±20%
- **Premium** (> R$ 15,00): ±15%

---

## 4. Fornecedores que Competem no Mesmo Segmento

### Mesmo produto-linha, faixas de preço sobrepostas

| Segmento | Concorrentes | Natureza da Competição |
|---|---|---|
| **CALCINHA BASICO econômico** | DIVA DONNA, VI LINGERIE, ZEE RUCCI | **Direta** — mesma faixa R$ 3,45–5,70 |
| **CALCINHA BASICO médio** | TRIFIL | Monopólio na faixa R$ 6,24–15,74 |
| **SOUTIEN BASICO médio** | VI LINGERIE, ZEE RUCCI | **Direta** — sobreposição R$ 10,47–12,24 |
| **SOUTIEN BASICO premium** | TRIFIL, JULIA MORAES, CLASS | **Direta** — todos acima de R$ 14,50 |
| **CUECA MASCULINO econômico** | ZEE RUCCI, CONFECCOES CANAA | **Direta** — ambos ~R$ 4,00 |
| **CUECA MASCULINO premium** | MASH | **Monopólio** — 231 SKUs, sem concorrência direta |
| **MEIA-CALCA** | TRIFIL, LUPO | **Direta** — sobreposição total |
| **CALCINHA SHAPEWARE** | VI LINGERIE, TRIFIL | **Parcial** — TRIFIL é faixa única R$ 13,87 |
| **BERMUDA SHAPEWARE** | TRIFIL, LUPO | **Parcial** — sobreposição R$ 12,48–14,20 |
| **SHORTS SHAPEWARE** | TRIFIL, LUPO | **Parcial** — sobreposição R$ 11,08–12,16 |

### Mapa de concentração de fornecedor por categoria

| Fornecedor | Categorias onde domina (>50% SKUs) |
|---|---|
| **VI LINGERIE** | SOUTIEN BASICO (53%), BODY SHAPEWARE (93%), SOUTIEN MATERNITY (72%), BODY MATERNITY (100%), CALCINHA MATERNITY (100%) |
| **DIVA DONNA** | CALCINHA BASICO (68%) |
| **MASH** | CUECA MASCULINO (82%) |
| **FOREVER FITNESS** | REGATA FINA FITNESS BASICO (100%), CALCA FITNESS BASICO (88%), TOP FITNESS BASICO (71%) |
| **TRIFIL** | MEIA-CALCA MEIA (58%), CAMISETE BASICO (100%), FAIXA BASICO (100%) |
| **ESBELT** | INDEFINIDO SHAPEWARE (100%) |

---

## 5. Co-compra (Cross-sell via Pedidos)

A análise de `fato_compras` mostra que **pedidos de compra são mono-fornecedor** — não há ocorrência de mesmo produto de fornecedores diferentes no mesmo pedido. No entanto, há **forte cross-sell** de produtos complementares no mesmo pedido:

### Top 10 pares de produtos comprados juntos

| Produto A | Linha | Fornecedor | Produto B | Linha | Pedidos Juntos |
|---|---|---|---|---|---|
| CALCINHA | SHAPEWARE | VI LINGERIE | SOUTIEN | BASICO | 155 |
| BODY | SHAPEWARE | VI LINGERIE | SOUTIEN | BASICO | 151 |
| CALCINHA | SHAPEWARE | VI LINGERIE | SOUTIEN | MATERNITY | 148 |
| BODY | SHAPEWARE | VI LINGERIE | SOUTIEN | MATERNITY | 144 |
| BODY | SHAPEWARE | VI LINGERIE | CALCINHA | SHAPEWARE | 143 |
| CALCINHA | BASICO | ZEE RUCCI | SOUTIEN | BASICO | 116 |
| CALCINHA | BASICO | VI LINGERIE | SOUTIEN | BASICO | 115 |
| BODY | MATERNITY | VI LINGERIE | SOUTIEN | BASICO | 114 |
| BODY | MATERNITY | VI LINGERIE | CALCINHA | SHAPEWARE | 109 |
| BODY | MATERNITY | VI LINGERIE | SOUTIEN | MATERNITY | 108 |

**Insight:** VI LINGERIE domina o cross-sell. O par SOUTIEN + CALCINHA (BASICO) é o mais frequente. Toda compra de BODY SHAPEWARE vem acompanhada de SOUTIEN ou CALCINHA.

### Implicação para substituição

Ao substituir um produto em falta, priorizar fornecedores que já aparecem no mesmo pedido — pois a logística já está consolidada. Exemplo: se VI LINGERIE falta SOUTIEN BASICO, substituir por ZEE RUCCI (116 pedidos juntos) é preferível a TRIFIL (91 pedidos juntos).

---

## 6. Preço de Venda vs. Custo (Margem por Tipo)

| Produto | Categoria | Preço Venda Médio | Custo Médio | Margem Bruta |
|---|---|---|---|---|
| CALCINHA | UNDERWARE | R$ 14,99 | R$ 4,87 | **67,5%** |
| SOUTIEN | UNDERWARE | R$ 35,71 | R$ 9,33 | **73,9%** |
| CUECA | UNDERWARE | R$ 14,10 | R$ 7,07 | **49,9%** |
| CALECON | UNDERWARE | R$ 19,79 | — | — |
| MEIA | UNDERWARE | R$ 18,20 | R$ 0,24 | **98,7%** |
| MEIA-CALCA | UNDERWARE | R$ 16,00 | R$ 6,69 | **58,2%** |
| BODY | UNDERWARE | R$ 84,13 | R$ 7,94 | **90,6%** |
| BERMUDA | UNDERWARE | R$ 60,03 | R$ 0,72 | **98,8%** |
| CAMISETE | UNDERWARE | R$ 29,90 | R$ 10,07 | **66,3%** |
| TOP | UNDERWARE | R$ 31,84 | — | — |
| INDEFINIDO | UNDERWARE | R$ 87,11 | R$ 41,97 | **51,8%** |
| CONJUNTO | UNDERWARE | R$ 25,03 | — | — |
| TOP | FITNESS | R$ 28,22 | — | — |
| CALCA | FITNESS | R$ 48,97 | — | — |

**Nota:** Margens altas (>65%) em CALCINHA, SOUTIEN, BODY, CAMISETE — substitutos com custo similar mantêm a rentabilidade. MEIA e BERMUDA têm custo virtualmente zero no cadastro (distorção ou custo alocado em outra etapa).

---

## 7. Recomendações

### 7.1 Regra de substituição automática

Criar uma tabela de substituição `gold.dim_substituto` com base na regra:

```
Substituto = mesmo (des_produto, des_linha) 
           AND ABS(custo_A - custo_B) <= custo_medio_grupo * 0.20
```

**Prioridade de substituição:**

1. Mesmo fornecedor, produto similar (cross-sell histórico)
2. Mesmo segmento de preço, fornecedor diferente (concorrente direto)
3. Mesmo segmento de preço, monofornecedor (sem substituto — escalar)

### 7.2 Alertas de compra sem substituto

Produtos sem substituto (±20%) que precisam de atenção em ruptura:

- **CUECA MASCULINO** — MASH é premium (R$ 10,43); ZEE RUCCI (R$ 4,33) e CONFECCOES CANAA (R$ 3,65) são faixa muito inferior
- **INDEFINIDO SHAPEWARE** — ESBELT é único fornecedor
- **BODY MATERNITY** — VI LINGERIE é único fornecedor
- **CALCINHA MATERNITY** — VI LINGERIE domina; ZEE RUCCI e LOVE SECRET têm poucos SKUs
- **REGATA FINA FITNESS** — FOREVER FITNESS é único fornecedor
- **TOP FITNESS** — FOREVER FITNESS domina

### 7.3 Expansão de sortimento

Segmentos com concorrência limitada onde faz sentido buscar novos fornecedores:

| Segmento | Problema | Oportunidade |
|---|---|---|
| CUECA MASCULINO | MASH tem 82% dos SKUs, sem concorrente na faixa | Novo fornecedor na faixa R$ 7–12 |
| SOUTIEN MATERNITY | VI LINGERIE domina, ZEE RUCCI marginal | LOVE SECRET poderia expandir |
| BODY SHAPEWARE | VI LINGERIE tem 93% dos SKUs | TRIFIL poderia aumentar sortimento |
| CALCINHA BASICO | TRIFIL é único na faixa R$ 6–16 | DIVA DONNA ou ZEE RUCCI poderiam entrar |

### 7.4 Dashboard de monitoramento (sugestão)

- **Cobertura de substitutos**: % de SKUs com ≥ 1 substituto dentro de ±20%
- **Concentração por fornecedor**: HHI por (produto, linha)
- **Ruptura sem substituto**: alerta quando produto sem substituto fica abaixo do estoque mínimo
- **Margem do substituto**: se substituto tem custo >10% maior, acionar revisão de preço

---

## 8. SQL de Materialização (Tabela de Substitutos)

```sql
-- Tabela gold de substitutos para consulta em BI e alertas
CREATE OR REPLACE TABLE gold.dim_substituto AS
WITH group_stats AS (
    SELECT 
        des_produto,
        des_linha,
        AVG(val_custo_inicial) AS custo_medio_grupo
    FROM gold.dim_produto
    WHERE des_status = 'ATIVO' 
      AND dat_fim_vigencia IS NULL
      AND des_categoria IN ('UNDERWARE', 'FITNESS')
    GROUP BY des_produto, des_linha
    HAVING AVG(val_custo_inicial) > 0
),
substitutos AS (
    SELECT 
        p.id_produto,
        p.des_produto,
        p.des_linha,
        p.cod_fornecedor,
        p.cod_artigo,
        p.val_custo_inicial,
        g.custo_medio_grupo,
        ROUND(ABS(p.val_custo_inicial - g.custo_medio_grupo) / NULLIF(g.custo_medio_grupo, 0) * 100, 1) AS diff_pct_media,
        s.id_produto AS substituto_id,
        s.cod_artigo AS substituto_artigo,
        s.cod_fornecedor AS substituto_fornecedor,
        s.val_custo_inicial AS substituto_custo,
        s.des_status AS substituto_status,
        ROUND(ABS(p.val_custo_inicial - s.val_custo_inicial) / NULLIF(g.custo_medio_grupo, 0) * 100, 1) AS diff_pct
    FROM gold.dim_produto p
    JOIN group_stats g ON p.des_produto = g.des_produto AND p.des_linha = g.des_linha
    JOIN gold.dim_produto s ON p.des_produto = s.des_produto 
        AND p.des_linha = s.des_linha
        AND p.id_produto <> s.id_produto
    WHERE p.des_status = 'ATIVO' AND p.dat_fim_vigencia IS NULL
      AND s.des_status = 'ATIVO' AND s.dat_fim_vigencia IS NULL
      AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
)
SELECT *,
    CASE 
        WHEN diff_pct <= 20 THEN 'SUBSTITUTO_DIRETO'
        WHEN diff_pct <= 35 THEN 'SUBSTITUTO_PROXIMO'
        ELSE 'SUBSTITUTO_DISTANTE'
    END AS grau_substituicao
FROM substitutos
WHERE diff_pct <= 35;
```

---

## 9. Resumo Executivo

- **8 grupos** com 2+ fornecedores competindo → substituição viável
- **8 grupos** monofornecedor → sem substituto direto
- **Maior concorrência:** CALCINHA BASICO (4 forns) e SOUTIEN BASICO (5 forns)
- **Maior concentração:** VI LINGERIE domina SOUTIEN, BODY, MATERNITY; MASH domina CUECA MASCULINO
- **Regra proposta:** ±20% do custo médio do grupo como threshold de substituição
- **Próximo passo:** validar com equipe de compras se thresholds estão adequados à realidade operacional
