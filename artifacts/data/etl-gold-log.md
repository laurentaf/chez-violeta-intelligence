# ETL Gold Layer — Carga Log

**Date:** 2026-07-02 20:12:17 UTC
**Source:** PostgreSQL localhost:5433/chez_violeta
**Target:** DuckDB chez_gold.duckdb
**Status:** SUCCESS

## Summary

| Table | Rows Loaded |
|-------|-------------|
| dim_tempo | 7,306 |
| dim_produto | 35,258 |
| dim_loja | 29 |
| dim_fornecedor | 189 |
| dim_cliente | 1,086 |
| dim_vendedor | 221 |
| fato_vendas | 10,435 |
| fato_estoque_diario | 10,124,888 |
| fato_compras | 187,935 |
| fato_trocas | 300,827 |
| **Total** | **10,668,174** |

## Step Log

| Time | Step | Detail |
|------|------|--------|
| 20:10:47 | Step 1 | Creating DuckDB database + gold schema
| 20:10:47 |   Cleanup | Removed existing chez_gold.duckdb
| 20:10:47 |   Extensions | postgres scanner installed & loaded
| 20:10:47 |   Schema | gold schema created
| 20:10:47 | Step 2 | Executing DDL from schema-gold.sql
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_tempo IS 'Date dimension — calendar days from the data
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_tempo.id_data IS 'Surrogate key: YYYYMMDD';
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_produto IS 'Product dimension with SCD Type 2 — tracks
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_produto.id_produto IS 'Surrogate key';
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_produto.dat_inicio_vigencia IS 'SCD2 validity start d
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_produto.dat_fim_vigencia IS 'SCD2 validity end date (
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_produto.dc_hash IS 'MD5/SHA256 hash of all descriptiv
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_loja IS 'Store dimension — PII-safe (CNPJ excluded)';
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_loja.id_loja IS 'Surrogate key';
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_loja.cod_estabelecimento IS 'Business key from ERP';
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_fornecedor IS 'Supplier dimension';
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_cliente IS 'Customer dimension — PII-safe (no name, em
| 20:10:47 |   Skipping COMMENT | COMMENT ON COLUMN gold.dim_cliente.codigo_cliente IS 'Customer code (CPF) — hash
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.dim_vendedor IS 'Seller dimension';
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.fato_vendas IS 'Sales fact — one row per item sold';
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.fato_estoque_diario IS 'Daily inventory fact — one row per
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.fato_compras IS 'Purchase fact — one row per purchased ite
| 20:10:47 |   Skipping COMMENT | COMMENT ON TABLE gold.fato_trocas IS 'Exchange/return fact — one row per exchang
| 20:10:47 |   DDL: -- =============================================== OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- Index for SCD2 lookup
CREATE INDEX IF NOT EXIST OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_dim_produto_cod_barra
    ON gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- =============================================== OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- Indexes for analytical queries
CREATE INDEX IF  OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_vendas_loja
    ON gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_vendas_produto
    ON gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: -- Composite unique constraint for upsert (prevent OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_estoque_diario_data
    ON gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_estoque_diario_produto
    ON gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_compras_data
    ON gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_compras_fornecedor
    ON gold OK | 0.0s
| 20:10:47 |   DDL: -- ----------------------------------------------- OK | 0.0s
| 20:10:47 |   DDL: CREATE TABLE IF NOT EXISTS gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_trocas_data
    ON gold OK | 0.0s
| 20:10:47 |   DDL: CREATE INDEX IF NOT EXISTS idx_fato_trocas_produto_devolvido
    ON gold OK | 0.0s
| 20:10:47 |   DDL: -- =============================================== OK | 0.0s
| 20:10:47 |   DDL: -- Orphan check: inventory without valid product
C OK | 0.0s
| 20:10:47 |   DDL: -- Negative inventory check
CREATE OR REPLACE VIEW OK | 0.0s
| 20:10:47 |   DDL: -- Future-dated sales check
CREATE OR REPLACE VIEW OK | 0.0s
| 20:10:47 |   DDL Complete | 36 statements executed
| 20:10:47 |   Tables created | dim_cliente, dim_fornecedor, dim_loja, dim_produto, dim_tempo, dim_vendedor, fato_compras, fato_estoque_diario, fato_trocas, fato_vendas, dq_estoque_negativo, dq_estoque_sem_produto, dq_vendas_futuras, dq_vendas_sem_produto
| 20:10:47 | Step 3 | Attaching PostgreSQL
| 20:10:48 |   ATTACH PostgreSQL OK | 0.0s
| 20:10:48 |   PostgreSQL tables found | 98
| 20:10:48 | Step 4 | Loading dimensions
| 20:10:48 |   0 Unknown placeholders | Inserting N/A records for FK integrity
| 20:10:48 |   4.1 dim_tempo | Loading from datas table
| 20:10:48 |   dim_tempo INSERT OK | 0.0s
| 20:10:48 |   dim_tempo rows: 7306
| 20:10:48 |   4.2 dim_produto | Loading from artigos_modelos + artigos_variantes + lookups (SCD2 initial)
| 20:10:48 |   dim_produto INSERT OK | 0.4s
| 20:10:48 |   dim_produto rows: 35258
| 20:10:48 |   4.3 dim_loja | Loading from estabelecimentos (PII-safe: no CNPJ)
| 20:10:48 |   dim_loja INSERT OK | 0.0s
| 20:10:48 |   dim_loja rows: 29
| 20:10:48 |   4.4 dim_fornecedor | Loading from fornecedores
| 20:10:48 |   dim_fornecedor INSERT OK | 0.0s
| 20:10:48 |   dim_fornecedor rows: 189
| 20:10:48 |   4.5 dim_cliente | Loading from clientes (PII-safe: no nome, email, phone)
| 20:10:48 |   dim_cliente INSERT OK | 0.0s
| 20:10:48 |   dim_cliente rows: 1086
| 20:10:48 |   4.6 dim_vendedor | Loading from rh_funcs (id_cargo FK not found in rh_funcs)
| 20:10:48 |   dim_vendedor INSERT OK | 0.0s
| 20:10:48 |   dim_vendedor rows: 221
| 20:10:48 | Step 5 | Loading fact tables
| 20:10:48 |   5.1 fato_vendas | Loading from vendas_cupons + brax_itens_cupons
| 20:10:49 |   fato_vendas INSERT OK | 0.6s
| 20:10:49 |   fato_vendas rows: 10435
| 20:10:49 |   5.2 fato_estoque_diario | Loading from estoques_diarios (10.1M rows)
| 20:10:49 |   fato_estoque_diario DROP INDEX OK | 0.0s
| 20:12:11 |   fato_estoque_diario INSERT OK | 82.6s
| 20:12:11 |   fato_estoque_diario SKIP unique index re-creation | source has genuine duplicates; dedup needed before re-creating
| 20:12:11 |   fato_estoque_diario rows: 10124888
| 20:12:11 |   5.3 fato_compras | Loading from compras + compras_modelos + compras_variantes
| 20:12:13 |   fato_compras INSERT OK | 1.6s
| 20:12:13 |   fato_compras rows: 187935
| 20:12:13 |   5.4 fato_trocas | Loading from trocas + trocas_itens_devolvidos + trocas_itens_substitutos
| 20:12:13 |   fato_trocas INSERT (devolvidos) OK | 0.5s
| 20:12:17 |   fato_trocas INSERT (substitutos) OK | 3.2s
| 20:12:17 |   fato_trocas rows: 300827
| 20:12:17 | Step 6 | Creating DQ monitoring views
| 20:12:17 |   dq_vendas_sem_produto OK | 0.0s
| 20:12:17 |   dq_estoque_sem_produto OK | 0.0s
| 20:12:17 |   dq_estoque_negativo OK | 0.0s
| 20:12:17 |   dq_vendas_futuras OK | 0.0s
| 20:12:17 |   DQ views created | 4 views
| 20:12:17 | Step 7 | Summary & validation
| 20:12:17 |   gold.dim_tempo | 7,306 rows
| 20:12:17 |   gold.dim_produto | 35,258 rows
| 20:12:17 |   gold.dim_loja | 29 rows
| 20:12:17 |   gold.dim_fornecedor | 189 rows
| 20:12:17 |   gold.dim_cliente | 1,086 rows
| 20:12:17 |   gold.dim_vendedor | 221 rows
| 20:12:17 |   gold.fato_vendas | 10,435 rows
| 20:12:17 |   gold.fato_estoque_diario | 10,124,888 rows
| 20:12:17 |   gold.fato_compras | 187,935 rows
| 20:12:17 |   gold.fato_trocas | 300,827 rows
| 20:12:17 | ETL Complete | Total time: 89.3s

## Notes

- All data loaded via DuckDB postgres scanner extension
- DuckDB version: 1.5.3
- PII columns excluded: dim_cliente (nome, email, celular, telefone), dim_loja (CNPJ)
- All source columns stored as TEXT in PostgreSQL; CAST to appropriate type on load
- dim_produto uses SCD2: initial full load, dat_inicio_vigencia = dat_cadastramento
- Dimensions loaded before facts for FK integrity
- DQ views created for monitoring: orphan checks, negative inventory, future-dated sales
