# Chez Violeta — Mapeamento Fonte → Gold Layer

## Convenções

- **Tipo fonte:** Todos os dados no PostgreSQL são TEXT — o CAST para tipo apropriado
  acontece no pipeline silver → gold.
- **Sem PK/FK:** O source não tem constraints. As chaves são inferidas por convenção de nomes.
- **PII:** Colunas com PII (nome_cliente, email, celular, telefone, num_cnpj) não passam para gold.

---

## Dimensões

### dim_produto

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold | Cast |
|-------------|------------------|-------------|-----------|------|
| cod_artigo | artigos_modelos.cod_artigo | VARCHAR | direto |
| des_artigo | artigos_modelos.des_artigo | VARCHAR | direto |
| cod_cor | artigos_variantes.cod_cor | VARCHAR | direto |
| des_cor | atrv_cores.des_cor | VARCHAR | LEFT JOIN |
| cod_tamanho | artigos_variantes.cod_tamanho | VARCHAR | direto |
| des_tamanho | atrv_tamanhos.des_tamanho | VARCHAR | LEFT JOIN |
| cod_barra | artigos_variantes.cod_barra | VARCHAR | direto |
| cod_fornecedor | artigos_modelos.cod_fornecedor | VARCHAR | direto |
| des_produto | atr_produtos.des_produto | VARCHAR | JOIN via artigos_modelos.at_cod_produto |
| des_categoria | atr_categorias.des_categoria | VARCHAR | JOIN via artigos_modelos.at_cod_categoria |
| des_linha | atr_linhas.des_linha | VARCHAR | JOIN via artigos_modelos.at_cod_linha |
| des_modelagem | atr_modelagens.des_modelagem | VARCHAR | JOIN via artigos_modelos.at_cod_modelagem |
| des_material | atr_materiais.des_material | VARCHAR | JOIN via artigos_modelos.at_cod_material |
| des_colecao | atrv_colecoes.des_colecao | VARCHAR | JOIN via artigos_variantes.at_cod_colecao |
| des_status | atr_status.des_status | VARCHAR | JOIN via artigos_variantes.at_cod_status |
| des_grade | atr_grades.des_grade | VARCHAR | JOIN via artigos_modelos.at_cod_grade |
| cod_ncm | artigos_modelos.cod_ncm | VARCHAR | direto |
| des_publico | artigos_modelos.des_publico | VARCHAR | direto |
| des_estilo | artigos_modelos.des_estilo | VARCHAR | direto |
| val_custo_inicial | artigos_modelos.val_custo_inicial | DECIMAL | CAST(val_custo_inicial AS DECIMAL(12,2)) |
| dat_cadastramento | artigos_modelos.dat_cadastramento | DATE | CAST(dat_cadastramento AS DATE) |

**Business key:** (cod_artigo, cod_cor, cod_tamanho)
**SCD2:** Mudanças em des_artigo, des_produto, des_categoria, etc. geram nova versão.
**Hash SCD2:** MD5(CONCAT(des_artigo, des_produto, des_categoria, des_linha, ...))

### dim_tempo

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold | Cast |
|-------------|------------------|-------------|-----------|------|
| dat_dia | datas.dat_dia | DATE | CAST(dat_dia AS DATE) |
| num_dia_semana | datas.num_dia_semana | INTEGER | CAST(num_dia_semana AS INTEGER) |
| des_dia_semana | datas.des_dia_semana | VARCHAR | direto |
| num_dia_mes | datas.num_dia_mes | INTEGER | CAST(num_dia_mes AS INTEGER) |
| num_mes_ano | datas.num_mes_ano | INTEGER | CAST(num_mes_ano AS INTEGER) |
| des_mes_ano | datas.des_mes_ano | VARCHAR | direto |
| num_ano | datas.num_ano | INTEGER | CAST(num_ano AS INTEGER) |
| id_ano_mes | datas.id_ano_mes | INTEGER | CAST |
| num_semana | datas.num_sem | INTEGER | CAST |
| id_ano_sem | datas.id_ano_sem | INTEGER | CAST |
| flg_feriado | datas.ind_feriado | BOOLEAN | CASE WHEN ind_feriado = 'S' THEN TRUE ELSE FALSE END |

**Surrogate key:** (ano * 10000 + mes * 100 + dia) como INTEGER

### dim_loja

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| cod_estabelecimento | estabelecimentos.cod_estabelecimento | VARCHAR |
| des_estabelecimento | estabelecimentos.des_estabelecimento | VARCHAR |
| nom_razao_social | estabelecimentos.nom_razao_social | VARCHAR |
| nom_municipio | estabelecimentos.nom_municipio | VARCHAR |
| cod_uf | estabelecimentos.cod_uf | VARCHAR |

**PII excluído:** estabelecimentos.num_cnpj, estabelecimentos.num_cnpj_2

### dim_fornecedor

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| cod_fornecedor | fornecedores.cod_fornecedor | VARCHAR |
| cod_ncm | fornecedores.cod_ncm | VARCHAR |
| sts_compra | fornecedores.sts_compra | VARCHAR |

### dim_cliente

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| codigo_cliente | clientes.codigo_cliente | VARCHAR |
| sexo | clientes.sexo | VARCHAR |
| idade | clientes.idade | INTEGER | CAST(idade AS INTEGER) |
| dat_cadastramento | clientes.dat_cadastramento | DATE | CAST |
| tip_cliente | clientes.tip_cliente | VARCHAR |
| flg_whatsapp | clientes.flg_whatsapp | BOOLEAN | CASE WHEN flg_whatsapp IN ('S','1') THEN TRUE ELSE FALSE END |
| flg_email_valido | clientes.flg_email_valido | BOOLEAN | CASE WHEN flg_email_valido IN ('S','1') THEN TRUE ELSE FALSE END |

**PII excluído:** nome_cliente, email, ddd_celular, celular, ddd, telefone

### dim_vendedor

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| cod_vendedor | vendas_cupons.cod_vendedor (distinct values) | VARCHAR |
| id_func | rh_funcs.id_func | VARCHAR |
| nom_funcionaria | rh_funcs.nom_funcionaria | VARCHAR |
| des_cargo | rh_cargos.des_cargo | VARCHAR | JOIN rh_funcs.id_cargo → rh_cargos.id_cargo |
| dat_inicio_trabalho | rh_funcs.dat_inicio_trabalho | DATE | CAST |
| flg_alocado_cd | rh_funcs.flg_alocado_cd | BOOLEAN | CASE WHEN flg_alocado_cd IN ('S','1') THEN TRUE ELSE FALSE END |

---

## Fatos

### fato_vendas

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| id_data | vendas_cupons.dat_venda | → dim_tempo.id_data | CAST para DATE → lookup |
| id_loja | vendas_cupons.cod_estabelecimento | → dim_loja.id_loja |
| id_produto | brax_itens_cupons (cod_artigo, cod_cor, cod_tamanho) | → dim_produto.id_produto |
| id_cliente | vendas_cupons.cod_cliente | → dim_cliente.id_cliente |
| id_vendedor | vendas_cupons.cod_vendedor | → dim_vendedor.id_vendedor |
| num_ticket | vendas_cupons.num_ticket | VARCHAR |
| num_item | brax_itens_cupons.num_item | VARCHAR |
| qtd_pecas | brax_itens_cupons.qtd_pecas | INTEGER | CAST |
| val_venda_cadastro | brax_itens_cupons.val_venda_liquida | DECIMAL | CAST (corrigir: na tabela itens, val_venda_liquida = valor do item) |
| val_desconto | brax_itens_cupons.val_desconto | DECIMAL | CAST |
| val_venda_liquida | brax_itens_cupons.val_venda_liquida | DECIMAL | CAST |
| val_custo | vendas_cupons.val_venda_custo | DECIMAL | CAST |
| val_pagamento | vendas_cupons.val_pagamento | DECIMAL | CAST |

**JOIN key:** vendas_cupons.(cod_estabelecimento, num_ticket) = brax_itens_cupons.(cod_estabelecimento, num_ticket)

### fato_estoque_diario

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| id_data | estoques_diarios.dat_dia | → dim_tempo.id_data | CAST |
| id_loja | estoques_diarios.cod_estabelecimento | → dim_loja |
| id_produto | estoques_diarios (cod_artigo, cod_cor, cod_tamanho) | → dim_produto |
| qtd_estoque | estoques_diarios.qtd_estoque | INTEGER | CAST |
| qtd_estoque_inicial | estoques_diarios.qtd_estoque_inicial | INTEGER | CAST |
| qtd_venda | estoques_diarios.qtd_venda | INTEGER | CAST |
| qtd_entrada_nota | estoques_diarios.qtd_entrada_nota | INTEGER | CAST |
| qtd_troca | estoques_diarios.qtd_troca | INTEGER | CAST |
| qtd_transf_entrada | estoques_diarios.qtd_transf_entrada | INTEGER | CAST |
| qtd_transf_saida | estoques_diarios.qtd_transf_saida | INTEGER | CAST |
| qtd_ajuste_positivo | estoques_diarios.qtd_ajuste_positivo | INTEGER | CAST |
| qtd_ajuste_negativo | estoques_diarios.qtd_ajuste_negativo | INTEGER | CAST |
| qtd_inventario | estoques_diarios.qtd_inventario | INTEGER | CAST |

### fato_compras

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| id_data_pedido | compras.dat_pedido | → dim_tempo | CAST |
| id_loja | compras.cod_estabelecimento | → dim_loja |
| id_fornecedor | compras.cod_fornecedor | → dim_fornecedor |
| id_produto | compras_variantes (cod_artigo, cod_cor, cod_tamanho) | → dim_produto |
| num_pedido | compras.num_pedido | VARCHAR |
| cod_tipo_pedido | compras.cod_tipo_pedido | VARCHAR |
| qtd_pecas | compras_variantes.qtd_pecas | INTEGER | CAST |
| val_bruto | compras_variantes.val_uni_bruto | DECIMAL | CAST |
| val_desconto | compras.val_desconto | DECIMAL | CAST (rateado por item) |
| val_liquido | compras_variantes.val_uni_bruto * qtd - rateio desconto | DECIMAL | computado |
| val_imposto | compras.val_imposto | DECIMAL | CAST (rateado) |

**JOIN:** compras.num_pedido → compras_modelos.num_pedido (+ cod_artigo) → compras_variantes.num_pedido (+ cod_artigo + cod_cor + cod_tamanho)

### fato_trocas

| Gold Column | PostgreSQL Source | Table.Column | Tipo Gold |
|-------------|------------------|-------------|-----------|
| id_data | trocas.dat_troca | → dim_tempo | CAST |
| id_loja | trocas.cod_estabelecimento | → dim_loja |
| id_produto_devolvido | trocas_itens_devolvidos (cod_artigo, cod_cor, cod_tamanho) | → dim_produto |
| id_produto_substituto | trocas_itens_substitutos (cod_artigo, cod_cor, cod_tamanho) | → dim_produto |
| tip_troca | 'DEVOLVIDO' ou 'SUBSTITUTO' | VARCHAR | constante |
| qtd_pecas | trocas_itens_*.qtd_pecas | INTEGER | CAST |
| val_venda_liquida | trocas_itens_*.val_venda_liquida | DECIMAL | CAST |
| val_venda_cadastro | trocas_itens_*.val_venda_cadastro | DECIMAL | CAST |
| val_desconto | trocas_itens_*.val_desconto | DECIMAL | CAST |
| flg_defeito | trocas_itens_devolvidos.flg_defeito | BOOLEAN |

**Nota:** trocas_itens_devolvidos e trocas_itens_substitutos são carregados como linhas separadas,
identificadas pelo campo `tip_troca`. O cabeçalho (trocas) fornece loja, data e vendedora.
**JOIN:** trocas.(cod_estabelecimento, dat_troca) → trocas_itens_devolvidos.(cod_estabelecimento, dat_troca)
