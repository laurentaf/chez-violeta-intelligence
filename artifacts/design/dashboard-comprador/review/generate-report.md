# Dashboard do Comprador - Relatório de Geração

**Data:** 2026-07-13
**Fonte:** DuckDB `chez_gold.duckdb` (snapshot 2019-11-30)

## Processamento

1. **Query** de 15.469 produtos ativos com estoque do gold.dim_produto
2. **Cálculo** de velocidade diária por produto (média de vendas / dias com venda; fallback para média da categoria)
3. **Previsão** de 120 dias: `vel_diaria * 120`
4. **Necessidade**: `max(0, previsao_120d - estoque)`, arredondado para cima
5. **Filtro**: apenas produtos com `precisa > 0`

## Separação

- **Fornecedores** (com `cod_fornecedor` preenchido): 122 fornecedores, limitado aos 20 mais urgentes
- **Vestuário** (`des_categoria = 'VESTUARIO'`): 1.434 tipos, limitado aos 30 com maior necessidade

## Agregação

- Fornecedores: agregado por `(fornecedor, des_artigo, cod_tamanho)` para reduzir linhas
- Vestuário: agregado por `(des_artigo, cod_tamanho)`, sem informação de fornecedor

## Arquivo de saída

- **Path**: `artifacts/design/dashboard-comprador/index.html`
- **Tamanho**: ~51 KB (bem abaixo do limite de 500 KB)
- **Dados**: embutidos como arrays JavaScript diretos (não JSON.parse)
- **Estilo**: Chez Violeta (vinho/dourado)
- **Abas**: Pedidos por Fornecedor / Vestuário por Tamanho

## Estrutura do HTML

```
<div class="hdr">          → Cabeçalho Chez Violeta
<div class="tabs">         → 2 abas navegáveis
<div id="tab-forn">        → AB1: Cards de fornecedores
  .ov (overview cards)     → 3 cards: Fornecedores, Itens, Valor
  .sc (supplier cards)     → Lista expansível de fornecedores
    .sh (header)           → Nome, stats, badge de urgência
    .sb (body)             → Tabela de produtos do fornecedor
<div id="tab-vest">        → AB2: Vestuário
  .ov (overview cards)     → 3 cards: Tipos, Itens, Valor
  .vg (grupos)             → Por artigo + tabela de tamanhos
```

## Observações

- `BIJU` detectado por nome do fornecedor (Amor Biju, Karisma Biju, etc.) e exibido com tag
- Urgência: < 30d = URGENTE (vermelho), 30-60d = ATENÇÃO (amarelo), > 60d = OK (verde)
- Total de itens a comprar de fornecedores: ~R$ 16,7M
- Total de itens a comprar de vestuário: ~R$ 13,2M
