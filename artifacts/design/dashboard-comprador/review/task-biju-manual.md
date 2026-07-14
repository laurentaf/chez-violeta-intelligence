# Review: BIJU / JOIAS como Compra Manual

## Task
Separar BIJU/JOIAS para compra manual por produto, assim como VESTUARIO.

## Arquivo alterado
`generate.py` — gerador do dashboard do comprador.

## O que mudou

### Separação de categorias
Antes:
- `forn_df` = tudo exceto VESTUARIO (incluía BIJU/JOIAS com fornecedores)
- `vest_df` = só VESTUARIO

Depois:
- `CAT_MANUAL = {'VESTUARIO', 'BIJU / JOIAS'}`
- `forn_df` = categorias com fornecedor (excluindo MANUAL)
- `manual_df` = VESTUARIO + BIJU / JOIAS
- `vest_df`, `biju_df` = subdivisões do manual

### Agrupamento BIJU / JOIAS
- Group by `des_produto` (ANEL, BRINCO, COLAR, CHOCKER, CONJUNTO, EARCUFF, INDEFINIDO, PONTO DE LUZ, PRESILHA, PULSEIRA)
- Within each type: list SKUs by `cod_artigo` + `cod_tamanho` with stock, forecast, to-buy
- Max 20 most urgent product types

### UI
- Tab "Vestuário por Tamanho" → "Compra Manual" (abriga VESTUARIO + BIJU/JOIAS)
- BIJU section with info header: "Compra Manual — sem fornecedor"
- Each BIJU product type labeled with ` <span class="bc">BIJU</span> ` badge
- Overview KPIs include BIJU counts & value

## Resultados da geração

| Métrica | Antes | Depois |
|---------|-------|--------|
| Fornecedores | 20 | 20 |
| Vestuario tipos (limite) | 30 | 30 |
| Bijuterias tipos | N/A (ia para fornecedor) | 10 |
| Total itens manual | 22.753 vest | 23.072 (22.753 vest + 319 biju) |
| Valor manual | R$ 654.381,72 | R$ 659.797,57 |
| Tamanho HTML | ~124 KB | **123.9 KB** (< 500KB ✅) |

## Dados de BIJU / JOIAS
- **Total produtos ativos**: 388
- **Com estoque/precisa comprar**: 305 produtos
- **Tipos de produto**: ANEL (20), BRINCO (79), CHOCKER (2), COLAR (64), CONJUNTO (12), EARCUFF (6), INDEFINIDO (168), PONTO DE LUZ (1), PRESILHA (2), PULSEIRA (34)
- **Valor total a comprar**: R$ 5.415,85
