# ADR-001: Star Schema para Chez Violeta

## Contexto

A Chez Violeta possui 98 tabelas em PostgreSQL com 13.6M+ linhas,
armazenadas integralmente como tipo TEXT (sem constraints PK/FK).
O schema fonte é um dump do ERP Oracle DMP GAVARNIE, refletindo
a modelagem transacional do ERP. Para análises de vendas, estoque,
compras e trocas, precisamos de um modelo dimensional (star schema)
que:

- Seja compreensível por analistas de negócio
- Suporte consultas analíticas rápidas (OLAP)
- Permita SCD Tipo 2 para atributos de produto
- Exclua PII (dados pessoais) da camada gold pública

## Decisão

Adotar **Star Schema** (Kimball) com 6 dimensões e 4 fatos,
implementado em DuckDB (gold layer). O modelo segue os princípios:

1. **Grain declarado** — cada fato tem grain explícito (linha = item, dia+SKU+loja, etc.)
2. **Surrogate keys** — cada dimensão usa chave auto-incremental (SERIAL) para referência dos fatos
3. **SCD Tipo 2 em dim_produto** — tracking de mudanças em atributos de produto
4. **Camada gold em DuckDB** — materializada a partir de staging (silver) com tipagem forte
5. **PII excluído** — dim_cliente não contém nome_cliente, email, celular

## Dimensões

| Dimensão | Grain | SCD | Fonte | Observação |
|----------|-------|-----|-------|------------|
| dim_produto | SKU (artigo+cor+tamanho) por vigência | Tipo 2 | artigos_modelos + artigos_variantes + atr_* | Atributos descritivos tracking |
| dim_tempo | dia | — | datas | Granularidade diária, 20 anos |
| dim_loja | loja | Tipo 1 | estabelecimentos | 28 lojas, sem PII (CNPJ excluído) |
| dim_fornecedor | fornecedor | Tipo 1 | fornecedores | 188 fornecedores |
| dim_cliente | cliente | Tipo 1 | clientes | SEM nome/email/celular (PII) |
| dim_vendedor | vendedor | Tipo 1 | rh_funcs | 221 funcionários |

## Fatos

| Fato | Grain | Medidas | Fontes | Est. linhas |
|------|-------|---------|--------|-------------|
| fato_vendas | item de venda (loja+ticket+item) | qtd, valor líquido, desconto, custo | vendas_cupons + brax_itens_cupons | 528K |
| fato_estoque_diario | SKU+loja+dia | qtd_estoque, qtd_venda, qtd_entrada, qtd_transf | estoques_diarios | 10.1M |
| fato_compras | item de compra (pedido+artigo) | qtd, valor bruto, valor líquido | compras + compras_modelos + compras_variantes | 188K |
| fato_trocas | item trocado (devolvido ou substituto) | qtd, valor | trocas + trocas_itens_devolvidos + trocas_itens_substitutos | 258K |

## Alternativas Consideradas

1. **Data Vault** — rejeitado por overkill para o volume (13.6M linhas) e time-to-value
2. **Single Large Table** — rejeitado por dificultar manutenção e entendimento do negócio
3. **Modelagem 3NF** — rejeitado por performance insuficiente em consultas analíticas

## Consequências

- Positivas: modelo intuitivo para negócio, queries simples (JOIN com 1 dimensão por fato),
  performance excelente em DuckDB (colunar), fácil de estender com novos fatos
- Negativas: SCD Tipo 2 aumenta complexidade do ETL (precisa detectar mudanças),
  dimensão produto com SCD2 pode crescer ao longo do tempo
- Riscos: DuckDB não suporta UPDATE otimizado — SCD2 será implementado via INSERT + window function

## Compliance

- PII Policy: dim_cliente tem apenas codigo_cliente + atributos demográficos não-identificadores (sexo, idade)
- Gold layer: sem dados brutos de clientes (nome, email, celular, telefone)
- Acesso à camada silver (com PII) restrito ao pipeline
