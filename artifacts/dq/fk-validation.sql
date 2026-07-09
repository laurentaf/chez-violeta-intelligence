-- ============================================================================
-- fk-validation.sql — Chez Violeta Gold Layer Referential Integrity Checks
-- ============================================================================
-- Dialect: DuckDB
-- Target: F:\projects\chez-violeta-intelligence\artifacts\data\chez_gold.duckdb
-- Schema: gold
-- Author: data-architect (LAOS)
-- Date: 2026-07-08
-- ============================================================================
-- Usage: duckdb <path-to-db> < fk-validation.sql
-- Or paste sections into your SQL client.
-- ============================================================================

-- ============================================================================
-- 0. RECORD COUNTS — All tables
-- ============================================================================
SELECT '=== RECORD COUNTS ===' AS section;
SELECT 'dim_tempo' AS tabela, COUNT(*) AS linhas FROM gold.dim_tempo
UNION ALL
SELECT 'dim_produto', COUNT(*) FROM gold.dim_produto
UNION ALL
SELECT 'dim_loja', COUNT(*) FROM gold.dim_loja
UNION ALL
SELECT 'dim_fornecedor', COUNT(*) FROM gold.dim_fornecedor
UNION ALL
SELECT 'dim_cliente', COUNT(*) FROM gold.dim_cliente
UNION ALL
SELECT 'dim_vendedor', COUNT(*) FROM gold.dim_vendedor
UNION ALL
SELECT 'fato_vendas', COUNT(*) FROM gold.fato_vendas
UNION ALL
SELECT 'fato_estoque_diario', COUNT(*) FROM gold.fato_estoque_diario
UNION ALL
SELECT 'fato_compras', COUNT(*) FROM gold.fato_compras
UNION ALL
SELECT 'fato_trocas', COUNT(*) FROM gold.fato_trocas
ORDER BY tabela;

-- ============================================================================
-- 1. PK UNIQUENESS — Every dimension's surrogate key is unique
-- ============================================================================
SELECT '=== PK UNIQUENESS ===' AS section;

-- 1.1 dim_tempo
SELECT 'dim_tempo.id_data' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_data) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_data) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_tempo;

-- 1.2 dim_produto
SELECT 'dim_produto.id_produto' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_produto) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_produto) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_produto;

-- 1.3 dim_loja
SELECT 'dim_loja.id_loja' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_loja) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_loja) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_loja;

-- 1.4 dim_fornecedor
SELECT 'dim_fornecedor.id_fornecedor' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_fornecedor) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_fornecedor) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_fornecedor;

-- 1.5 dim_cliente
SELECT 'dim_cliente.id_cliente' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_cliente) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_cliente) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_cliente;

-- 1.6 dim_vendedor
SELECT 'dim_vendedor.id_vendedor' AS pk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT id_vendedor) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT id_vendedor) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_vendedor;

-- 1.7 Business key uniqueness (where applicable)
SELECT 'dim_loja.cod_estabelecimento' AS bk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT cod_estabelecimento) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT cod_estabelecimento) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_loja;

SELECT 'dim_fornecedor.cod_fornecedor' AS bk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT cod_fornecedor) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT cod_fornecedor) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_fornecedor;

SELECT 'dim_cliente.codigo_cliente' AS bk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT codigo_cliente) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT codigo_cliente) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_cliente;

SELECT 'dim_vendedor.cod_vendedor' AS bk_check,
       COUNT(*) AS total,
       COUNT(DISTINCT cod_vendedor) AS distinct_values,
       CASE WHEN COUNT(*) = COUNT(DISTINCT cod_vendedor) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_vendedor;

-- dim_produto unique composite (cod_artigo, cod_cor, cod_tamanho, flg_ativo) business key
-- SCD2 allows same BK at different validity periods, but only 1 active per BK
SELECT 'dim_produto SCD2 (cod_artigo, cod_cor, cod_tamanho, flg_ativo=TRUE)' AS bk_check,
       COUNT(*) AS total,
       COUNT(*) AS active_rows,
       CASE WHEN COUNT(*) = COUNT(DISTINCT (cod_artigo, cod_cor, cod_tamanho)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.dim_produto
WHERE flg_ativo = TRUE;

-- ============================================================================
-- 2. FK REFERENTIAL INTEGRITY — Fact FK values exist in referenced dimensions
-- ============================================================================
SELECT '=== FK REFERENTIAL INTEGRITY ===' AS section;

-- 2.1 fato_vendas → dim_tempo
SELECT 'fato_vendas.id_data → dim_tempo.id_data' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fv.id_data) AS distinct_fk_values,
       SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_tempo dt ON fv.id_data = dt.id_data;

-- 2.2 fato_vendas → dim_loja
SELECT 'fato_vendas.id_loja → dim_loja.id_loja' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fv.id_loja) AS distinct_fk_values,
       SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_loja dl ON fv.id_loja = dl.id_loja;

-- 2.3 fato_vendas → dim_produto
SELECT 'fato_vendas.id_produto → dim_produto.id_produto' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fv.id_produto) AS distinct_fk_values,
       SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_produto dp ON fv.id_produto = dp.id_produto;

-- 2.4 fato_vendas → dim_cliente (nullable FK)
SELECT 'fato_vendas.id_cliente → dim_cliente.id_cliente (nullable)' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fv.id_cliente) AS distinct_fk_values,
       SUM(CASE WHEN fv.id_cliente IS NULL THEN 1 ELSE 0 END) AS null_fks,
       SUM(CASE WHEN fv.id_cliente IS NOT NULL AND dc.id_cliente IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN fv.id_cliente IS NOT NULL AND dc.id_cliente IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_cliente dc ON fv.id_cliente = dc.id_cliente;

-- 2.5 fato_vendas → dim_vendedor (nullable FK)
SELECT 'fato_vendas.id_vendedor → dim_vendedor.id_vendedor (nullable)' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fv.id_vendedor) AS distinct_fk_values,
       SUM(CASE WHEN fv.id_vendedor IS NULL THEN 1 ELSE 0 END) AS null_fks,
       SUM(CASE WHEN fv.id_vendedor IS NOT NULL AND dv.id_vendedor IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN fv.id_vendedor IS NOT NULL AND dv.id_vendedor IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_vendedor dv ON fv.id_vendedor = dv.id_vendedor;

-- 2.6 fato_estoque_diario → dim_tempo
SELECT 'fato_estoque_diario.id_data → dim_tempo.id_data' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fe.id_data) AS distinct_fk_values,
       SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data;

-- 2.7 fato_estoque_diario → dim_loja
SELECT 'fato_estoque_diario.id_loja → dim_loja.id_loja' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fe.id_loja) AS distinct_fk_values,
       SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_loja dl ON fe.id_loja = dl.id_loja;

-- 2.8 fato_estoque_diario → dim_produto
SELECT 'fato_estoque_diario.id_produto → dim_produto.id_produto' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fe.id_produto) AS distinct_fk_values,
       SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto;

-- 2.9 fato_compras → dim_tempo (via id_data_pedido)
SELECT 'fato_compras.id_data_pedido → dim_tempo.id_data' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fc.id_data_pedido) AS distinct_fk_values,
       SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_compras fc
LEFT JOIN gold.dim_tempo dt ON fc.id_data_pedido = dt.id_data;

-- 2.10 fato_compras → dim_loja
SELECT 'fato_compras.id_loja → dim_loja.id_loja' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fc.id_loja) AS distinct_fk_values,
       SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_compras fc
LEFT JOIN gold.dim_loja dl ON fc.id_loja = dl.id_loja;

-- 2.11 fato_compras → dim_fornecedor
SELECT 'fato_compras.id_fornecedor → dim_fornecedor.id_fornecedor' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fc.id_fornecedor) AS distinct_fk_values,
       SUM(CASE WHEN df.id_fornecedor IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN df.id_fornecedor IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_compras fc
LEFT JOIN gold.dim_fornecedor df ON fc.id_fornecedor = df.id_fornecedor;

-- 2.12 fato_compras → dim_produto
SELECT 'fato_compras.id_produto → dim_produto.id_produto' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT fc.id_produto) AS distinct_fk_values,
       SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_compras fc
LEFT JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto;

-- 2.13 fato_trocas → dim_tempo
SELECT 'fato_trocas.id_data → dim_tempo.id_data' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT ft.id_data) AS distinct_fk_values,
       SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dt.id_data IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_tempo dt ON ft.id_data = dt.id_data;

-- 2.14 fato_trocas → dim_loja
SELECT 'fato_trocas.id_loja → dim_loja.id_loja' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT ft.id_loja) AS distinct_fk_values,
       SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dl.id_loja IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_loja dl ON ft.id_loja = dl.id_loja;

-- 2.15 fato_trocas → dim_produto (devolvido)
SELECT 'fato_trocas.id_produto_devolvido → dim_produto.id_produto' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT ft.id_produto_devolvido) AS distinct_fk_values,
       SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN dp.id_produto IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_produto dp ON ft.id_produto_devolvido = dp.id_produto;

-- 2.16 fato_trocas → dim_produto (substituto, nullable)
SELECT 'fato_trocas.id_produto_substituto → dim_produto.id_produto (nullable)' AS fk_check,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT ft.id_produto_substituto) AS distinct_fk_values,
       SUM(CASE WHEN ft.id_produto_substituto IS NULL THEN 1 ELSE 0 END) AS null_fks,
       SUM(CASE WHEN ft.id_produto_substituto IS NOT NULL AND dp.id_produto IS NULL THEN 1 ELSE 0 END) AS orphans,
       CASE WHEN SUM(CASE WHEN ft.id_produto_substituto IS NOT NULL AND dp.id_produto IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_produto dp ON ft.id_produto_substituto = dp.id_produto;

-- ============================================================================
-- 3. NULL FK VALUES — Fact rows with null dimension keys
-- ============================================================================
SELECT '=== NULL FK VALUES ===' AS section;

SELECT 'fato_vendas.id_cliente' AS null_check,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN id_cliente IS NULL THEN 1 ELSE 0 END) AS null_count,
       ROUND(100.0 * SUM(CASE WHEN id_cliente IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS null_pct
FROM gold.fato_vendas;

SELECT 'fato_vendas.id_vendedor' AS null_check,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN id_vendedor IS NULL THEN 1 ELSE 0 END) AS null_count,
       ROUND(100.0 * SUM(CASE WHEN id_vendedor IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS null_pct
FROM gold.fato_vendas;

SELECT 'fato_trocas.id_produto_substituto' AS null_check,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN id_produto_substituto IS NULL THEN 1 ELSE 0 END) AS null_count,
       ROUND(100.0 * SUM(CASE WHEN id_produto_substituto IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS null_pct
FROM gold.fato_trocas;

-- ============================================================================
-- 4. DATE RANGES — All fact dates fall within dim_tempo range
-- ============================================================================
SELECT '=== DATE RANGES ===' AS section;

-- dim_tempo range
SELECT 'dim_tempo' AS tabela,
       MIN(dat_dia) AS min_date,
       MAX(dat_dia) AS max_date,
       COUNT(*) AS total_days
FROM gold.dim_tempo;

-- fato_vendas date range vs dim_tempo
SELECT 'fato_vendas' AS tabela,
       MIN(dt.dat_dia) AS min_data,
       MAX(dt.dat_dia) AS max_data,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN dt.dat_dia < (SELECT MIN(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS before_dim,
       SUM(CASE WHEN dt.dat_dia > (SELECT MAX(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS after_dim
FROM gold.fato_vendas fv
JOIN gold.dim_tempo dt ON fv.id_data = dt.id_data;

-- fato_estoque_diario date range vs dim_tempo
SELECT 'fato_estoque_diario' AS tabela,
       MIN(dt.dat_dia) AS min_data,
       MAX(dt.dat_dia) AS max_data,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN dt.dat_dia < (SELECT MIN(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS before_dim,
       SUM(CASE WHEN dt.dat_dia > (SELECT MAX(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS after_dim
FROM gold.fato_estoque_diario fe
JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data;

-- fato_compras date range vs dim_tempo
SELECT 'fato_compras' AS tabela,
       MIN(dt.dat_dia) AS min_data,
       MAX(dt.dat_dia) AS max_data,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN dt.dat_dia < (SELECT MIN(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS before_dim,
       SUM(CASE WHEN dt.dat_dia > (SELECT MAX(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS after_dim
FROM gold.fato_compras fc
JOIN gold.dim_tempo dt ON fc.id_data_pedido = dt.id_data;

-- fato_trocas date range vs dim_tempo
SELECT 'fato_trocas' AS tabela,
       MIN(dt.dat_dia) AS min_data,
       MAX(dt.dat_dia) AS max_data,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN dt.dat_dia < (SELECT MIN(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS before_dim,
       SUM(CASE WHEN dt.dat_dia > (SELECT MAX(dat_dia) FROM gold.dim_tempo) THEN 1 ELSE 0 END) AS after_dim
FROM gold.fato_trocas ft
JOIN gold.dim_tempo dt ON ft.id_data = dt.id_data;

-- ============================================================================
-- 5. ORPHAN DETAILS — List specific orphan FK values if any found
-- ============================================================================
SELECT '=== ORPHAN DETAILS ===' AS section;

-- fato_vendas orphans by dimension
SELECT 'fato_vendas' AS fact_table, 'id_tempo' AS fk_name, fv.id_data AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_tempo dt ON fv.id_data = dt.id_data
WHERE dt.id_data IS NULL
GROUP BY fv.id_data
ORDER BY fv.id_data;

SELECT 'fato_vendas' AS fact_table, 'id_loja' AS fk_name, fv.id_loja AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_loja dl ON fv.id_loja = dl.id_loja
WHERE dl.id_loja IS NULL
GROUP BY fv.id_loja;

SELECT 'fato_vendas' AS fact_table, 'id_produto' AS fk_name, fv.id_produto AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_produto dp ON fv.id_produto = dp.id_produto
WHERE dp.id_produto IS NULL
GROUP BY fv.id_produto;

SELECT 'fato_vendas' AS fact_table, 'id_cliente_orphans' AS fk_name, fv.id_cliente AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_cliente dc ON fv.id_cliente = dc.id_cliente
WHERE fv.id_cliente IS NOT NULL AND dc.id_cliente IS NULL
GROUP BY fv.id_cliente;

SELECT 'fato_vendas' AS fact_table, 'id_vendedor_orphans' AS fk_name, fv.id_vendedor AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_vendas fv
LEFT JOIN gold.dim_vendedor dv ON fv.id_vendedor = dv.id_vendedor
WHERE fv.id_vendedor IS NOT NULL AND dv.id_vendedor IS NULL
GROUP BY fv.id_vendedor;

-- fato_estoque_diario orphans
SELECT 'fato_estoque_diario' AS fact_table, 'id_tempo' AS fk_name, fe.id_data AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data
WHERE dt.id_data IS NULL
GROUP BY fe.id_data;

SELECT 'fato_estoque_diario' AS fact_table, 'id_loja' AS fk_name, fe.id_loja AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_loja dl ON fe.id_loja = dl.id_loja
WHERE dl.id_loja IS NULL
GROUP BY fe.id_loja;

SELECT 'fato_estoque_diario' AS fact_table, 'id_produto' AS fk_name, fe.id_produto AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_estoque_diario fe
LEFT JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
WHERE dp.id_produto IS NULL
GROUP BY fe.id_produto;

-- fato_compras orphans
SELECT 'fato_compras' AS fact_table, 'id_data_pedido' AS fk_name, fc.id_data_pedido AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_compras fc
LEFT JOIN gold.dim_tempo dt ON fc.id_data_pedido = dt.id_data
WHERE dt.id_data IS NULL
GROUP BY fc.id_data_pedido;

SELECT 'fato_compras' AS fact_table, 'id_loja' AS fk_name, fc.id_loja AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_compras fc
LEFT JOIN gold.dim_loja dl ON fc.id_loja = dl.id_loja
WHERE dl.id_loja IS NULL
GROUP BY fc.id_loja;

SELECT 'fato_compras' AS fact_table, 'id_fornecedor' AS fk_name, fc.id_fornecedor AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_compras fc
LEFT JOIN gold.dim_fornecedor df ON fc.id_fornecedor = df.id_fornecedor
WHERE df.id_fornecedor IS NULL
GROUP BY fc.id_fornecedor;

SELECT 'fato_compras' AS fact_table, 'id_produto' AS fk_name, fc.id_produto AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_compras fc
LEFT JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
WHERE dp.id_produto IS NULL
GROUP BY fc.id_produto;

-- fato_trocas orphans
SELECT 'fato_trocas' AS fact_table, 'id_data' AS fk_name, ft.id_data AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_tempo dt ON ft.id_data = dt.id_data
WHERE dt.id_data IS NULL
GROUP BY ft.id_data;

SELECT 'fato_trocas' AS fact_table, 'id_loja' AS fk_name, ft.id_loja AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_loja dl ON ft.id_loja = dl.id_loja
WHERE dl.id_loja IS NULL
GROUP BY ft.id_loja;

SELECT 'fato_trocas' AS fact_table, 'id_produto_devolvido' AS fk_name, ft.id_produto_devolvido AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_produto dp ON ft.id_produto_devolvido = dp.id_produto
WHERE dp.id_produto IS NULL
GROUP BY ft.id_produto_devolvido;

SELECT 'fato_trocas' AS fact_table, 'id_produto_substituto' AS fk_name, ft.id_produto_substituto AS fk_value, COUNT(*) AS occurrences
FROM gold.fato_trocas ft
LEFT JOIN gold.dim_produto dp ON ft.id_produto_substituto = dp.id_produto
WHERE ft.id_produto_substituto IS NOT NULL AND dp.id_produto IS NULL
GROUP BY ft.id_produto_substituto;

-- ============================================================================
-- 6. DIMENSIONAL COVERAGE — Which dimension records are unused
-- ============================================================================
SELECT '=== UNUSED DIMENSIONS ===' AS section;

-- Products not in any fact
SELECT 'dim_produto sem fato_vendas' AS check_name, COUNT(*) AS unused_count
FROM gold.dim_produto dp
LEFT JOIN (SELECT DISTINCT id_produto FROM gold.fato_vendas) fv ON dp.id_produto = fv.id_produto
LEFT JOIN (SELECT DISTINCT id_produto FROM gold.fato_estoque_diario) fe ON dp.id_produto = fe.id_produto
LEFT JOIN (SELECT DISTINCT id_produto FROM gold.fato_compras) fc ON dp.id_produto = fc.id_produto
LEFT JOIN (SELECT DISTINCT id_produto_devolvido AS id_produto FROM gold.fato_trocas) ft1 ON dp.id_produto = ft1.id_produto
LEFT JOIN (SELECT DISTINCT id_produto_substituto AS id_produto FROM gold.fato_trocas) ft2 ON dp.id_produto = ft2.id_produto
WHERE fv.id_produto IS NULL AND fe.id_produto IS NULL
  AND fc.id_produto IS NULL AND ft1.id_produto IS NULL AND ft2.id_produto IS NULL;

-- Stores not in any fact
SELECT 'dim_loja sem fato_vendas' AS check_name, COUNT(*) AS unused_count
FROM gold.dim_loja dl
LEFT JOIN (SELECT DISTINCT id_loja FROM gold.fato_vendas) fv ON dl.id_loja = fv.id_loja
LEFT JOIN (SELECT DISTINCT id_loja FROM gold.fato_estoque_diario) fe ON dl.id_loja = fe.id_loja
LEFT JOIN (SELECT DISTINCT id_loja FROM gold.fato_compras) fc ON dl.id_loja = fc.id_loja
WHERE fv.id_loja IS NULL AND fe.id_loja IS NULL AND fc.id_loja IS NULL;

-- Customers never bought
SELECT 'dim_cliente sem fato_vendas' AS check_name, COUNT(*) AS unused_count
FROM gold.dim_cliente dc
LEFT JOIN (SELECT DISTINCT id_cliente FROM gold.fato_vendas) fv ON dc.id_cliente = fv.id_cliente
WHERE fv.id_cliente IS NULL;
