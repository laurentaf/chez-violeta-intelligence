-- ============================================================================
-- schema-gold.sql — Gold Layer DDL for Chez Violeta (DuckDB)
-- Star Schema: 6 dimensions + 4 fact tables
--
-- Dialect: DuckDB (compatible with PostgreSQL syntax)
-- Source: PostgreSQL 16 / localhost:5433/chez_violeta
-- Target: DuckDB gold layer
--
-- PII excluded:
--   - dim_cliente: no NOME_CLIENTE, EMAIL, CELULAR, TELEFONE, DDD
--   - dim_loja: no NUM_CNPJ
-- ============================================================================

-- ============================================================================
-- 1. DIMENSIONS
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1.1 dim_tempo — Date dimension
-- Grain: one row per calendar day
-- Refresh: initial full load, then annual append
-- Source: datas table in PostgreSQL
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_tempo START 1;

CREATE TABLE IF NOT EXISTS gold.dim_tempo (
    id_data         INTEGER PRIMARY KEY,        -- YYYYMMDD surrogate key
    dat_dia         DATE NOT NULL,
    num_dia_semana  INTEGER,                    -- 1=Sunday, 2=Monday...
    des_dia_semana  VARCHAR(20),
    num_dia_mes     INTEGER,                    -- 1-31
    num_mes_ano     INTEGER,                    -- 1-12
    des_mes_ano     VARCHAR(20),
    num_ano         INTEGER,
    id_ano_mes      INTEGER,                    -- YYYYMM
    num_semana      INTEGER,                    -- week number
    id_ano_sem      INTEGER,                    -- year + week number
    flg_feriado     BOOLEAN                     -- TRUE if holiday
);

COMMENT ON TABLE gold.dim_tempo IS 'Date dimension — calendar days from the datas table';
COMMENT ON COLUMN gold.dim_tempo.id_data IS 'Surrogate key: YYYYMMDD';


-- --------------------------------------------------------------------------
-- 1.2 dim_produto — Product dimension (SCD Type 2)
-- Grain: one row per SKU (article + color + size) per validity period
-- Refresh: daily incremental (INSERT new versions via SCD2)
-- Source: artigos_modelos + artigos_variantes + atr_* lookup tables
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_produto START 1;

CREATE TABLE IF NOT EXISTS gold.dim_produto (
    id_produto          INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_produto'),
    -- Business keys
    cod_artigo          VARCHAR(20) NOT NULL,
    cod_cor             VARCHAR(10) NOT NULL,
    cod_tamanho         VARCHAR(10) NOT NULL,
    -- Identifiers
    cod_barra           VARCHAR(30),
    cod_fornecedor      VARCHAR(30),
    -- Descriptive attributes
    des_artigo          VARCHAR(200),
    des_cor             VARCHAR(50),
    des_tamanho         VARCHAR(20),
    des_produto         VARCHAR(50),        -- atr_produtos
    des_categoria       VARCHAR(50),        -- atr_categorias
    des_linha           VARCHAR(50),        -- atr_linhas
    des_modelagem       VARCHAR(50),        -- atr_modelagens
    des_material        VARCHAR(50),        -- atr_materiais
    des_colecao         VARCHAR(50),        -- atrv_colecoes
    des_status          VARCHAR(50),        -- atr_status
    des_grade           VARCHAR(50),        -- atr_grades
    des_publico         VARCHAR(100),
    des_estilo          VARCHAR(100),
    cod_ncm             VARCHAR(20),
    val_custo_inicial   DECIMAL(12,2),
    dat_cadastramento   DATE,
    -- SCD2 validity period
    dat_inicio_vigencia DATE NOT NULL,
    dat_fim_vigencia    DATE,               -- NULL = current version
    flg_ativo           BOOLEAN DEFAULT TRUE,
    -- SCD2 hash for change detection
    dc_hash             VARCHAR(64),
    -- Metadata
    dat_carga           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.dim_produto IS 'Product dimension with SCD Type 2 — tracks changes to product attributes';
COMMENT ON COLUMN gold.dim_produto.id_produto IS 'Surrogate key';
COMMENT ON COLUMN gold.dim_produto.dat_inicio_vigencia IS 'SCD2 validity start date';
COMMENT ON COLUMN gold.dim_produto.dat_fim_vigencia IS 'SCD2 validity end date (NULL = current)';
COMMENT ON COLUMN gold.dim_produto.dc_hash IS 'MD5/SHA256 hash of all descriptive attributes for change detection';

-- Index for SCD2 lookup
CREATE INDEX IF NOT EXISTS idx_dim_produto_bk
    ON gold.dim_produto (cod_artigo, cod_cor, cod_tamanho, flg_ativo);

CREATE INDEX IF NOT EXISTS idx_dim_produto_cod_barra
    ON gold.dim_produto (cod_barra);


-- --------------------------------------------------------------------------
-- 1.3 dim_loja — Store dimension
-- Grain: one row per store
-- Refresh: weekly full reload
-- Source: estabelecimentos
-- PII: NUM_CNPJ excluded
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_loja START 1;

CREATE TABLE IF NOT EXISTS gold.dim_loja (
    id_loja                 INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_loja'),
    cod_estabelecimento     VARCHAR(10) NOT NULL UNIQUE,
    des_estabelecimento     VARCHAR(100),
    nom_razao_social        VARCHAR(200),
    nom_municipio           VARCHAR(100),
    cod_uf                  VARCHAR(2)
);

COMMENT ON TABLE gold.dim_loja IS 'Store dimension — PII-safe (CNPJ excluded)';
COMMENT ON COLUMN gold.dim_loja.id_loja IS 'Surrogate key';
COMMENT ON COLUMN gold.dim_loja.cod_estabelecimento IS 'Business key from ERP';


-- --------------------------------------------------------------------------
-- 1.4 dim_fornecedor — Supplier dimension
-- Grain: one row per supplier
-- Refresh: weekly full reload
-- Source: fornecedores + fornecedores_categorias
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_fornecedor START 1;

CREATE TABLE IF NOT EXISTS gold.dim_fornecedor (
    id_fornecedor       INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_fornecedor'),
    cod_fornecedor      VARCHAR(30) NOT NULL UNIQUE,
    cod_ncm             VARCHAR(20),
    des_categoria       VARCHAR(100),       -- from fornecedores_categorias
    sts_compra          VARCHAR(10)
);

COMMENT ON TABLE gold.dim_fornecedor IS 'Supplier dimension';


-- --------------------------------------------------------------------------
-- 1.5 dim_cliente — Customer dimension (PII-safe)
-- Grain: one row per customer
-- Refresh: weekly full reload
-- Source: clientes (WITHOUT nome_cliente, email, celular, telefone, ddd)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_cliente START 1;

CREATE TABLE IF NOT EXISTS gold.dim_cliente (
    id_cliente          INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_cliente'),
    codigo_cliente      VARCHAR(20) NOT NULL UNIQUE,
    sexo                VARCHAR(1),
    idade               INTEGER,
    dat_cadastramento   DATE,
    tip_cliente         VARCHAR(20),
    flg_whatsapp        BOOLEAN,
    flg_email_valido    BOOLEAN
);

COMMENT ON TABLE gold.dim_cliente IS 'Customer dimension — PII-safe (no name, email, phone)';
COMMENT ON COLUMN gold.dim_cliente.codigo_cliente IS 'Customer code (CPF) — hash if privacy needed';


-- --------------------------------------------------------------------------
-- 1.6 dim_vendedor — Seller dimension
-- Grain: one row per seller
-- Refresh: weekly full reload
-- Source: rh_funcs + rh_cargos
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_vendedor START 1;

CREATE TABLE IF NOT EXISTS gold.dim_vendedor (
    id_vendedor         INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_vendedor'),
    cod_vendedor        VARCHAR(10) NOT NULL UNIQUE,
    id_func             VARCHAR(10),
    nom_funcionaria     VARCHAR(100),
    des_cargo           VARCHAR(50),
    dat_inicio_trabalho DATE,
    flg_alocado_cd      BOOLEAN
);

COMMENT ON TABLE gold.dim_vendedor IS 'Seller dimension';


-- ============================================================================
-- 2. FACT TABLES
-- ============================================================================

-- --------------------------------------------------------------------------
-- 2.1 fato_vendas — Sales facts
-- Grain: one row per item sold (store + ticket + item)
-- Refresh: daily incremental by dat_venda
-- Source: vendas_cupons (header) + brax_itens_cupons (items)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fato_vendas START 1;

CREATE TABLE IF NOT EXISTS gold.fato_vendas (
    id_venda            INTEGER PRIMARY KEY DEFAULT nextval('seq_fato_vendas'),
    -- Foreign keys
    id_data             INTEGER NOT NULL REFERENCES gold.dim_tempo(id_data),
    id_loja             INTEGER NOT NULL REFERENCES gold.dim_loja(id_loja),
    id_produto          INTEGER NOT NULL REFERENCES gold.dim_produto(id_produto),
    id_cliente          INTEGER REFERENCES gold.dim_cliente(id_cliente),
    id_vendedor         INTEGER REFERENCES gold.dim_vendedor(id_vendedor),
    -- Business identifiers
    num_ticket          VARCHAR(20),
    num_item            VARCHAR(10),
    -- Measures
    qtd_pecas           INTEGER,
    val_venda_cadastro  DECIMAL(12,2),
    val_desconto        DECIMAL(12,2),
    val_venda_liquida   DECIMAL(12,2),
    val_custo           DECIMAL(12,2),
    val_pagamento       DECIMAL(12,2),
    -- Metadata
    dat_carga           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.fato_vendas IS 'Sales fact — one row per item sold';

-- Indexes for analytical queries
CREATE INDEX IF NOT EXISTS idx_fato_vendas_data
    ON gold.fato_vendas (id_data);
CREATE INDEX IF NOT EXISTS idx_fato_vendas_loja
    ON gold.fato_vendas (id_loja);
CREATE INDEX IF NOT EXISTS idx_fato_vendas_produto
    ON gold.fato_vendas (id_produto);


-- --------------------------------------------------------------------------
-- 2.2 fato_estoque_diario — Daily inventory facts
-- Grain: one row per SKU + store + day
-- Refresh: daily incremental (DELETE + INSERT by dat_dia)
-- Source: estoques_diarios (10.1M rows)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fato_estoque_diario START 1;

CREATE TABLE IF NOT EXISTS gold.fato_estoque_diario (
    id_estoque_diario   INTEGER PRIMARY KEY DEFAULT nextval('seq_fato_estoque_diario'),
    -- Foreign keys
    id_data             INTEGER NOT NULL REFERENCES gold.dim_tempo(id_data),
    id_loja             INTEGER NOT NULL REFERENCES gold.dim_loja(id_loja),
    id_produto          INTEGER NOT NULL REFERENCES gold.dim_produto(id_produto),
    -- Measures
    qtd_estoque             INTEGER,
    qtd_estoque_inicial     INTEGER,
    qtd_venda               INTEGER,
    qtd_entrada_nota        INTEGER,
    qtd_troca               INTEGER,
    qtd_transf_entrada      INTEGER,
    qtd_transf_saida        INTEGER,
    qtd_ajuste_positivo     INTEGER,
    qtd_ajuste_negativo     INTEGER,
    qtd_inventario          INTEGER,
    -- Metadata
    dat_carga           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.fato_estoque_diario IS 'Daily inventory fact — one row per SKU+store+day';

-- Composite unique constraint for upsert (prevent duplicates)
CREATE UNIQUE INDEX IF NOT EXISTS uq_fato_estoque_diario
    ON gold.fato_estoque_diario (id_data, id_loja, id_produto);

CREATE INDEX IF NOT EXISTS idx_fato_estoque_diario_data
    ON gold.fato_estoque_diario (id_data);
CREATE INDEX IF NOT EXISTS idx_fato_estoque_diario_produto
    ON gold.fato_estoque_diario (id_produto);


-- --------------------------------------------------------------------------
-- 2.3 fato_compras — Purchase facts
-- Grain: one row per purchased item (order + article + color + size)
-- Refresh: daily incremental by order date
-- Source: compras + compras_modelos + compras_variantes
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fato_compras START 1;

CREATE TABLE IF NOT EXISTS gold.fato_compras (
    id_compra           INTEGER PRIMARY KEY DEFAULT nextval('seq_fato_compras'),
    -- Foreign keys
    id_data_pedido      INTEGER NOT NULL REFERENCES gold.dim_tempo(id_data),
    id_loja             INTEGER NOT NULL REFERENCES gold.dim_loja(id_loja),
    id_fornecedor       INTEGER NOT NULL REFERENCES gold.dim_fornecedor(id_fornecedor),
    id_produto          INTEGER NOT NULL REFERENCES gold.dim_produto(id_produto),
    -- Business identifiers
    num_pedido          VARCHAR(20),
    cod_tipo_pedido     VARCHAR(10),
    -- Measures
    qtd_pecas           INTEGER,
    val_bruto           DECIMAL(12,2),
    val_desconto        DECIMAL(12,2),
    val_liquido         DECIMAL(12,2),
    val_imposto         DECIMAL(12,2),
    -- Metadata
    dat_carga           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.fato_compras IS 'Purchase fact — one row per purchased item';

CREATE INDEX IF NOT EXISTS idx_fato_compras_data
    ON gold.fato_compras (id_data_pedido);
CREATE INDEX IF NOT EXISTS idx_fato_compras_fornecedor
    ON gold.fato_compras (id_fornecedor);


-- --------------------------------------------------------------------------
-- 2.4 fato_trocas — Exchange/return facts
-- Grain: one row per exchanged item (returned or substitute)
-- Refresh: daily incremental by exchange date
-- Source: trocas + trocas_itens_devolvidos + trocas_itens_substitutos
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fato_trocas START 1;

CREATE TABLE IF NOT EXISTS gold.fato_trocas (
    id_troca                INTEGER PRIMARY KEY DEFAULT nextval('seq_fato_trocas'),
    -- Foreign keys
    id_data                 INTEGER NOT NULL REFERENCES gold.dim_tempo(id_data),
    id_loja                 INTEGER NOT NULL REFERENCES gold.dim_loja(id_loja),
    id_produto_devolvido    INTEGER NOT NULL REFERENCES gold.dim_produto(id_produto),
    id_produto_substituto   INTEGER REFERENCES gold.dim_produto(id_produto),
    -- Type
    tip_troca               VARCHAR(20),    -- 'DEVOLVIDO' or 'SUBSTITUTO'
    cod_vendedora           VARCHAR(10),
    -- Measures
    qtd_pecas               INTEGER,
    val_venda_liquida       DECIMAL(12,2),
    val_venda_cadastro      DECIMAL(12,2),
    val_desconto            DECIMAL(12,2),
    flg_defeito             BOOLEAN,
    -- Metadata
    dat_carga               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.fato_trocas IS 'Exchange/return fact — one row per exchanged item';

CREATE INDEX IF NOT EXISTS idx_fato_trocas_data
    ON gold.fato_trocas (id_data);
CREATE INDEX IF NOT EXISTS idx_fato_trocas_produto_devolvido
    ON gold.fato_trocas (id_produto_devolvido);


-- ============================================================================
-- 3. DQ VIEWS — Data quality monitoring
-- ============================================================================

-- Orphan check: sales without valid product
CREATE OR REPLACE VIEW gold.dq_vendas_sem_produto AS
SELECT fv.*
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_produto dp ON fv.id_produto = dp.id_produto
WHERE dp.id_produto IS NULL;

-- Orphan check: inventory without valid product
CREATE OR REPLACE VIEW gold.dq_estoque_sem_produto AS
SELECT fe.*
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
WHERE dp.id_produto IS NULL;

-- Negative inventory check
CREATE OR REPLACE VIEW gold.dq_estoque_negativo AS
SELECT id_data, id_loja, id_produto, qtd_estoque
FROM gold.fato_estoque_diario
WHERE qtd_estoque < 0;

-- Future-dated sales check
CREATE OR REPLACE VIEW gold.dq_vendas_futuras AS
SELECT fv.*, td.dat_dia
FROM gold.fato_vendas fv
JOIN gold.dim_tempo td ON fv.id_data = td.id_data
WHERE td.dat_dia > CURRENT_DATE;
