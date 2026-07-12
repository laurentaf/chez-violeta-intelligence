import duckdb
con = duckdb.connect('F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb')

# Q3 proper: co-purchase analysis via same pedido
# fato_compras.id_fornecedor -> dim_fornecedor.id_fornecedor -> cod_fornecedor
q3 = """
WITH pedido_produtos AS (
    SELECT 
        fc.num_pedido,
        dp.des_produto,
        dp.des_linha,
        dp.des_categoria,
        df.cod_fornecedor,
        dp.id_produto
    FROM gold.fato_compras fc
    JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
    LEFT JOIN gold.dim_fornecedor df ON fc.id_fornecedor = df.id_fornecedor
    WHERE dp.dat_fim_vigencia IS NULL
      AND dp.des_status = 'ATIVO'
      AND dp.des_categoria IN ('UNDERWARE', 'FITNESS')
      AND dp.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
),
pares AS (
    SELECT 
        a.des_produto as prod_a,
        a.des_linha as linha_a,
        a.cod_fornecedor as forn_a,
        b.des_produto as prod_b,
        b.des_linha as linha_b,
        b.cod_fornecedor as forn_b,
        COUNT(DISTINCT a.num_pedido) as pedidos_juntos
    FROM pedido_produtos a
    JOIN pedido_produtos b ON a.num_pedido = b.num_pedido
        AND (a.des_produto < b.des_produto 
             OR (a.des_produto = b.des_produto AND a.cod_fornecedor < b.cod_fornecedor))
    GROUP BY a.des_produto, a.des_linha, a.cod_fornecedor,
             b.des_produto, b.des_linha, b.cod_fornecedor
)
-- Same product, different fornecedores in same pedido
SELECT prod_a as produto, linha_a as linha, forn_a, forn_b, pedidos_juntos
FROM pares
WHERE prod_a = prod_b
  AND forn_a <> forn_b
ORDER BY pedidos_juntos DESC
LIMIT 30
"""
rows = con.execute(q3).fetchall()
print("=== Q3: Same product, different forns, same pedido ===")
print(f"{'Produto':20s} {'Linha':12s} {'Forn_A':20s} {'Forn_B':20s} {'Pedidos':>8s}")
print("-" * 85)
if len(rows) == 0:
    print("  (no results - pedidos typically single-fornecedor)")
else:
    for r in rows:
        print(f"{str(r[0]):20s} {str(r[1]):12s} {str(r[2]):20s} {str(r[3]):20s} {r[4]:8d}")

# Different products in same pedido (cross-sell)
q3b = """
WITH pedido_produtos AS (
    SELECT 
        fc.num_pedido,
        dp.des_produto,
        dp.des_linha,
        dp.des_categoria,
        df.cod_fornecedor,
        dp.id_produto
    FROM gold.fato_compras fc
    JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
    LEFT JOIN gold.dim_fornecedor df ON fc.id_fornecedor = df.id_fornecedor
    WHERE dp.dat_fim_vigencia IS NULL
      AND dp.des_status = 'ATIVO'
      AND dp.des_categoria IN ('UNDERWARE', 'FITNESS')
      AND dp.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
),
pares AS (
    SELECT 
        a.des_produto as prod_a,
        a.des_linha as linha_a,
        a.cod_fornecedor as forn_a,
        b.des_produto as prod_b,
        b.des_linha as linha_b,
        b.cod_fornecedor as forn_b,
        COUNT(DISTINCT a.num_pedido) as pedidos_juntos
    FROM pedido_produtos a
    JOIN pedido_produtos b ON a.num_pedido = b.num_pedido
        AND a.des_produto < b.des_produto
    GROUP BY a.des_produto, a.des_linha, a.cod_fornecedor,
             b.des_produto, b.des_linha, b.cod_fornecedor
)
SELECT prod_a, linha_a, forn_a, prod_b, linha_b, forn_b, pedidos_juntos
FROM pares
ORDER BY pedidos_juntos DESC
LIMIT 20
"""
print("\n=== Q3b: Cross-sell pairs (different products, same pedido) ===")
rows = con.execute(q3b).fetchall()
print(f"{'Prod_A':20s} {'Linha_A':12s} {'Forn':20s} {'Prod_B':20s} {'Linha_B':12s} {'Forn_B':20s} {'Juntos':>6s}")
print("-" * 115)
for r in rows:
    print(f"{str(r[0]):20s} {str(r[1]):12s} {str(r[2]):20s} {str(r[3]):20s} {str(r[4]):12s} {str(r[5]):20s} {r[6]:6d}")

# Q4: Average sale price by product type
print("\n\n=== QUERY 4: Sale price by product type ===")
q4 = """
SELECT 
    dp.des_produto,
    dp.des_categoria,
    CAST(AVG(fv.val_venda_liquida / NULLIF(fv.qtd_pecas, 0)) AS DECIMAL(10,2)) as preco_venda_medio,
    CAST(AVG(dp.val_custo_inicial) AS DECIMAL(10,2)) as custo_medio,
    COUNT(DISTINCT fv.id_produto) as skus_vendidos,
    SUM(fv.qtd_pecas) as total_vendido
FROM gold.fato_vendas fv
JOIN gold.dim_produto dp ON fv.id_produto = dp.id_produto
WHERE dp.dat_fim_vigencia IS NULL
  AND dp.des_status = 'ATIVO'
GROUP BY dp.des_produto, dp.des_categoria
HAVING COUNT(DISTINCT fv.id_produto) > 5
ORDER BY total_vendido DESC
"""
rows = con.execute(q4).fetchall()
print(f"{'Produto':25s} {'Cat':12s} {'VendaMed':>8s} {'CustoMed':>8s} {'SKUs':>5s} {'TotalVend':>10s}")
print("-" * 72)
for r in rows:
    v = str(r[2]) if r[2] else 'NULL'
    c = str(r[3]) if r[3] else 'NULL'
    print(f"{str(r[0]):25s} {str(r[1]):12s} {v:>8s} {c:>8s} {r[4]:5d} {r[5]:10d}")

# EXTRA: Price bands for substitute rules
print("\n\n=== EXTRA: Price distribution by (product, linha) ===")
q5 = """
SELECT 
    des_produto,
    des_linha,
    des_categoria,
    CAST(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val_custo_inicial) AS DECIMAL(10,2)) as p25,
    CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY val_custo_inicial) AS DECIMAL(10,2)) as p50,
    CAST(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val_custo_inicial) AS DECIMAL(10,2)) as p75,
    COUNT(DISTINCT cod_fornecedor) as n_forn,
    COUNT(DISTINCT id_produto) as n_skus
FROM gold.dim_produto
WHERE dat_fim_vigencia IS NULL
  AND des_status = 'ATIVO'
  AND des_categoria IN ('UNDERWARE', 'FITNESS')
  AND des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
  AND val_custo_inicial > 0
GROUP BY des_produto, des_linha, des_categoria
HAVING COUNT(DISTINCT id_produto) >= 5
ORDER BY des_categoria, des_produto
"""
rows = con.execute(q5).fetchall()
print(f"{'Produto':25s} {'Linha':12s} {'Cat':12s} {'P25':>8s} {'P50':>8s} {'P75':>8s} {'Forn':>4s} {'SKUs':>5s}")
print("-" * 87)
for r in rows:
    print(f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2]):12s} {str(r[3]):>8s} {str(r[4]):>8s} {str(r[5]):>8s} {r[6]:4d} {r[7]:5d}")

con.close()
