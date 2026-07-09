# Chez Violeta — Modelo Dimensional (Star Schema)

## Visão Geral

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  dim_tempo  │     │   dim_produto    │     │  dim_loja    │
│  PK: id_data│────>│   PK: id_produto │────>│  PK: id_loja │
└──────┬──────┘     └────────┬─────────┘     └──────┬───────┘
       │                     │                       │
       ▼                     ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│                      fato_vendas                          │
│  FK: id_data, id_produto, id_loja, id_cliente,           │
│      id_vendedor                                          │
│  Measures: qtd_pecas, val_venda_liquida, val_desconto,   │
│            val_venda_cadastro, val_custo, val_pagamento   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   fato_estoque_diario                     │
│  FK: id_data, id_produto, id_loja                        │
│  Measures: qtd_estoque, qtd_venda, qtd_entrada_nota,     │
│            qtd_troca, qtd_transf_entrada, qtd_ajuste      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     fato_compras                          │
│  FK: id_data, id_produto, id_loja, id_fornecedor         │
│  Measures: qtd_pecas, val_bruto, val_liquido,            │
│            val_desconto, val_imposto                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                      fato_trocas                          │
│  FK: id_data, id_produto, id_loja                        │
│  Measures: qtd_pecas_devolvidas, val_devolvido,           │
│            qtd_pecas_substitutas, val_substituto           │
└──────────────────────────────────────────────────────────┘
```

---

## Status
- **Versão:** 1.0
- **Última atualização:** 2026-07-02
- **Proprietário:** Laurent (data-architect)
- **Cadência de atualização:** Diária (incremental)

---

## 1. Dimensões

### 1.1 dim_produto (SCD Tipo 2)
**Grain:** Um registro por SKU (artigo + cor + tamanho) por período de vigência.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_produto | INTEGER PK | auto-increment | Surrogate key (SERIAL) |
| cod_artigo | VARCHAR | artigos_modelos.cod_artigo | Código do artigo (modelo) |
| des_artigo | VARCHAR | artigos_modelos.des_artigo | Descrição / nome do artigo |
| cod_cor | VARCHAR | artigos_variantes.cod_cor | Código da cor |
| des_cor | VARCHAR | atrv_cores.des_cor | Nome da cor |
| cod_tamanho | VARCHAR | artigos_variantes.cod_tamanho | Código do tamanho |
| des_tamanho | VARCHAR | atrv_tamanhos.des_tamanho | Descrição do tamanho |
| cod_barra | VARCHAR | artigos_variantes.cod_barra | Código de barras (EAN) |
| cod_fornecedor | VARCHAR | artigos_modelos.cod_fornecedor | Código do fornecedor do artigo |
| des_produto | VARCHAR | atr_produtos.des_produto | Tipo de produto (ex: ANEL, BRINCO) |
| des_categoria | VARCHAR | atr_categorias.des_categoria | Categoria (ex: ACESSORIOS) |
| des_linha | VARCHAR | atr_linhas.des_linha | Linha (ex: BASICO) |
| des_modelagem | VARCHAR | atr_modelagens.des_modelagem | Modelagem (ex: 1/2 MANGA) |
| des_material | VARCHAR | atr_materiais.des_material | Material (ex: ACETINADO) |
| des_colecao | VARCHAR | atrv_colecoes.des_colecao | Coleção (ex: CONTINUO) |
| des_status | VARCHAR | atr_status.des_status | Status do artigo |
| des_grade | VARCHAR | atr_grades.des_grade | Grade de tamanhos |
| cod_ncm | VARCHAR | artigos_modelos.cod_ncm | NCM fiscal |
| des_publico | VARCHAR | artigos_modelos.des_publico | Público-alvo |
| des_estilo | VARCHAR | artigos_modelos.des_estilo | Estilo |
| val_custo_inicial | DECIMAL(12,2) | artigos_modelos.val_custo_inicial | Custo inicial |
| dat_cadastramento | DATE | artigos_modelos.dat_cadastramento | Data de cadastro |
| dat_inicio_vigencia | DATE | — | Início da vigência SCD2 |
| dat_fim_vigencia | DATE | — | Fim da vigência SCD2 (NULL = atual) |
| flg_ativo | BOOLEAN | — | TRUE = registro vigente |

**Partitioning:** Por cod_artigo (HASH, 8 partições)
**Refresh:** Full reload semanal, incremental diário

### 1.2 dim_tempo
**Grain:** Um registro por dia.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_data | INTEGER PK | YYYYMMDD (surrogate) | Chave no formato AAAAMMDD |
| dat_dia | DATE | datas.dat_dia | Data calendário |
| num_dia_semana | INTEGER | datas.num_dia_semana | 1=domingo, 2=segunda, ... |
| des_dia_semana | VARCHAR | datas.des_dia_semana | Nome do dia (DOMINGO, SEGUNDA...) |
| num_dia_mes | INTEGER | datas.num_dia_mes | Dia do mês (1-31) |
| num_mes_ano | INTEGER | datas.num_mes_ano | Mês (1-12) |
| des_mes_ano | VARCHAR | datas.des_mes_ano | Nome do mês (JANEIRO...) |
| num_ano | INTEGER | datas.num_ano | Ano |
| id_ano_mes | INTEGER | datas.id_ano_mes | AAAAMM |
| num_semana | INTEGER | datas.num_sem | Número da semana do ano |
| id_ano_sem | INTEGER | datas.id_ano_sem | Ano + semana |
| flg_feriado | BOOLEAN | datas.ind_feriado | TRUE se feriado (S/N) |

**Partitioning:** Por num_ano (RANGE, 1 partição por ano)
**Refresh:** Uma vez (carga inicial completa), depois anual

### 1.3 dim_loja
**Grain:** Um registro por estabelecimento.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_loja | INTEGER PK | auto-increment | Surrogate key |
| cod_estabelecimento | VARCHAR | estabelecimentos.cod_estabelecimento | Código da loja |
| des_estabelecimento | VARCHAR | estabelecimentos.des_estabelecimento | Nome fantasia |
| nom_razao_social | VARCHAR | estabelecimentos.nom_razao_social | Razão social |
| nom_municipio | VARCHAR | estabelecimentos.nom_municipio | Cidade |
| cod_uf | VARCHAR | estabelecimentos.cod_uf | Estado (UF) |

**Nota:** CNPJ (NUM_CNPJ) excluído por política PII.
**Refresh:** Semanal

### 1.4 dim_fornecedor
**Grain:** Um registro por fornecedor.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_fornecedor | INTEGER PK | auto-increment | Surrogate key |
| cod_fornecedor | VARCHAR | fornecedores.cod_fornecedor | Código do fornecedor |
| cod_ncm | VARCHAR | fornecedores.cod_ncm | NCM principal |
| sts_compra | VARCHAR | fornecedores.sts_compra | Status de compra |

**Refresh:** Semanal

### 1.5 dim_cliente (sem PII)
**Grain:** Um registro por cliente.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_cliente | INTEGER PK | auto-increment | Surrogate key |
| codigo_cliente | VARCHAR | clientes.codigo_cliente | Código do cliente (CPF) |
| sexo | VARCHAR | clientes.sexo | Sexo (M/F) |
| idade | INTEGER | clientes.idade | Idade |
| dat_cadastramento | DATE | clientes.dat_cadastramento | Data de cadastro |
| tip_cliente | VARCHAR | clientes.tip_cliente | Tipo de cliente |
| flg_whatsapp | BOOLEAN | clientes.flg_whatsapp | Possui WhatsApp |
| flg_email_valido | BOOLEAN | clientes.flg_email_valido | Email válido |

**PII excluído:** NOME_CLIENTE, EMAIL, CELULAR, DDD_CELULAR, TELEFONE, DDD
**Refresh:** Semanal

### 1.6 dim_vendedor
**Grain:** Um registro por vendedor.

| Coluna | Tipo | Fonte | Descrição |
|--------|------|-------|-----------|
| id_vendedor | INTEGER PK | auto-increment | Surrogate key |
| cod_vendedor | VARCHAR | vendas_cupons.cod_vendedor | Código do vendedor |
| id_func | VARCHAR | rh_funcs.id_func | ID do funcionário |
| nom_funcionaria | VARCHAR | rh_funcs.nom_funcionaria | Nome (apenas para gold interna) |
| des_cargo | VARCHAR | rh_cargos.des_cargo | Cargo |
| dat_inicio_trabalho | DATE | rh_funcs.dat_inicio_trabalho | Data de início |
| flg_alocado_cd | BOOLEAN | rh_funcs.flg_alocado_cd | Alocado ao centro de distribuição |

**Refresh:** Semanal

---

## 2. Fatos

### 2.1 fato_vendas
**Grain:** Um registro por item vendido (loja + ticket + item).
**Fonte:** vendas_cupons (cabeçalho) + brax_itens_cupons (itens)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id_venda | INTEGER PK | Surrogate key |
| id_data | INTEGER FK | → dim_tempo (dat_venda) |
| id_loja | INTEGER FK | → dim_loja |
| id_produto | INTEGER FK | → dim_produto |
| id_cliente | INTEGER FK | → dim_cliente (nullable) |
| id_vendedor | INTEGER FK | → dim_vendedor |
| num_ticket | VARCHAR | Número do ticket/cupom |
| num_item | VARCHAR | Número do item no cupom |
| qtd_pecas | INTEGER | Quantidade de peças |
| val_venda_cadastro | DECIMAL(12,2) | Valor de venda cadastrado |
| val_desconto | DECIMAL(12,2) | Valor do desconto |
| val_venda_liquida | DECIMAL(12,2) | Valor líquido da venda |
| val_custo | DECIMAL(12,2) | Custo da venda (val_venda_custo) |
| val_pagamento | DECIMAL(12,2) | Valor recebido |

**Partitioning:** Por id_data (RANGE mensal)
**Refresh:** Diário incremental

### 2.2 fato_estoque_diario
**Grain:** Um registro por SKU + loja + dia.
**Fonte:** estoques_diarios (10.1M registros)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id_estoque_diario | INTEGER PK | Surrogate key |
| id_data | INTEGER FK | → dim_tempo |
| id_loja | INTEGER FK | → dim_loja |
| id_produto | INTEGER FK | → dim_produto |
| dat_dia | DATE | Data do estoque |
| qtd_estoque | INTEGER | Estoque final do dia |
| qtd_estoque_inicial | INTEGER | Estoque inicial do dia |
| qtd_venda | INTEGER | Quantidade vendida no dia |
| qtd_entrada_nota | INTEGER | Entrada por nota fiscal |
| qtd_troca | INTEGER | Entrada/saída por troca |
| qtd_transf_entrada | INTEGER | Entrada por transferência |
| qtd_transf_saida | INTEGER | Saída por transferência |
| qtd_ajuste_positivo | INTEGER | Ajuste positivo |
| qtd_ajuste_negativo | INTEGER | Ajuste negativo |
| qtd_inventario | INTEGER | Quantidade de inventário |

**Partitioning:** Por id_data (RANGE trimestral)
**Refresh:** Diário incremental (UPSERT pelo dia+SKU+loja)

### 2.3 fato_compras
**Grain:** Um registro por item de compra (pedido + artigo + cor + tamanho).
**Fonte:** compras (cabeçalho) + compras_modelos (item-article) + compras_variantes (item-SKU)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id_compra | INTEGER PK | Surrogate key |
| id_data_pedido | INTEGER FK | → dim_tempo (dat_pedido) |
| id_loja | INTEGER FK | → dim_loja |
| id_fornecedor | INTEGER FK | → dim_fornecedor |
| id_produto | INTEGER FK | → dim_produto |
| num_pedido | VARCHAR | Número do pedido de compra |
| cod_tipo_pedido | VARCHAR | Tipo do pedido |
| qtd_pecas | INTEGER | Quantidade pedida |
| val_bruto | DECIMAL(12,2) | Valor bruto do item |
| val_desconto | DECIMAL(12,2) | Valor do desconto |
| val_liquido | DECIMAL(12,2) | Valor líquido (bruto - desconto) |
| val_imposto | DECIMAL(12,2) | Valor do imposto |

**Partitioning:** Por id_data_pedido (RANGE trimestral)
**Refresh:** Diário incremental

### 2.4 fato_trocas
**Grain:** Um registro por item devolvido ou substituto em uma troca.
**Fonte:** trocas (cabeçalho) + trocas_itens_devolvidos + trocas_itens_substitutos

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id_troca | INTEGER PK | Surrogate key |
| id_data | INTEGER FK | → dim_tempo (dat_troca) |
| id_loja | INTEGER FK | → dim_loja |
| id_produto_devolvido | INTEGER FK | → dim_produto |
| id_produto_substituto | INTEGER FK | → dim_produto (nullable) |
| cod_vendedora | VARCHAR | Vendedora que realizou a troca |
| tip_troca | VARCHAR | 'DEVOLVIDO' ou 'SUBSTITUTO' |
| qtd_pecas | INTEGER | Quantidade de peças |
| val_venda_liquida | DECIMAL(12,2) | Valor líquido |
| val_venda_cadastro | DECIMAL(12,2) | Valor de cadastro |
| val_desconto | DECIMAL(12,2) | Desconto |
| flg_defeito | BOOLEAN | TRUE se troca por defeito |

**Partitioning:** Por id_data (RANGE trimestral)
**Refresh:** Diário incremental

---

## 3. Source Lineage

| Gold Table | Silver Source | Bronze Source | Transformações |
|-----------|--------------|---------------|----------------|
| dim_produto | stg_produto | artigos_modelos, artigos_variantes, atrv_cores, atrv_tamanhos, atr_produtos, atr_categorias, atr_linhas, atr_modelagens, atr_materiais, atrv_colecoes, atr_status, atr_grades | JOINs + CAST tipagem + SCD2 window |
| dim_tempo | stg_tempo | datas | CAST dat_dia → DATE |
| dim_loja | stg_loja | estabelecimentos | CAST + remover CNPJ (PII) |
| dim_fornecedor | stg_fornecedor | fornecedores, fornecedores_categorias | JOIN |
| dim_cliente | stg_cliente | clientes | Excluir colunas PII |
| dim_vendedor | stg_vendedor | rh_funcs, rh_cargos | JOIN |
| fato_vendas | stg_vendas | vendas_cupons + brax_itens_cupons | JOIN cupom + itens + CAST |
| fato_estoque_diario | stg_estoque | estoques_diarios | CAST + dedup |
| fato_compras | stg_compras | compras + compras_modelos + compras_variantes | JOIN cabeçalho + modelo + SKU |
| fato_trocas | stg_trocas | trocas + trocas_itens_devolvidos + trocas_itens_substitutos | UNION devolvidos + substitutos |

---

## 4. Estratégia de Refresh

| Tabela | Cadência | Estratégia |
|--------|----------|------------|
| dim_tempo | Única + anual | FULL LOAD (só cresce) |
| dim_loja, dim_fornecedor, dim_cliente, dim_vendedor | Semanal | FULL LOAD (poucas linhas) |
| dim_produto | Diário | INCREMENTAL via SCD2 (INSERT se mudou) |
| fato_vendas | Diário | INCREMENTAL por dat_venda |
| fato_estoque_diario | Diário | INCREMENTAL por dat_dia (DELETE + INSERT do dia) |
| fato_compras | Diário | INCREMENTAL por dat_pedido |
| fato_trocas | Diário | INCREMENTAL por dat_troca |

---

## 5. Data Quality Baseline

| Regra | Tabela | Severidade | Descrição |
|-------|--------|------------|-----------|
| PK única | Todas as dimensões | BLOCK | Surrogate key deve ser única |
| FK referencial | Todos os fatos | BLOCK | FK deve existir na dimensão |
| qtd_pecas > 0 | fato_vendas, fato_estoque_diario | WARN | Quantidades negativas são exceção |
| val_venda_liquida >= 0 | fato_vendas | WARN | Valor líquido negativo = possível erro |
| dat_venda <= hoje | fato_vendas | WARN | Vendas no futuro são raras |
| Estoque não-negativo | fato_estoque_diario | WARN | qtd_estoque final < 0 = ruptura ou erro |
| Correspondência cupom-item | fato_vendas | BLOCK | Todo item tem cupom válido |
