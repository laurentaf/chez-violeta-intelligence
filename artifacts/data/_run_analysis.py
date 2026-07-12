import duckdb
con = duckdb.connect('F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb')

# ============================================================================
# QUERY 1: Perfil de produtos commodities por tipo
# ============================================================================
print("=" * 80)
print("QUERY 1: Product Profile (commodities por tipo)")
print("=" * 80)

q1 = """
SELECT 
    des_produto,
    des_categoria,
    des_linha,
    COUNT(DISTINCT id_produto) as n_skus,
    COUNT(DISTINCT cod_fornecedor) as n_fornecedores,
    CAST(AVG(val_custo_inicial) AS DECIMAL(10,2)) as custo_medio,
    CAST(MIN(val_custo_inicial) AS DECIMAL(10,2)) as custo_min,
    CAST(MAX(val_custo_inicial) AS DECIMAL(10,2)) as custo_max
FROM gold.dim_produto
WHERE dat_fim_vigencia IS NULL
  AND des_categoria IN ('UNDERWARE', 'FITNESS')
  AND des_status = 'ATIVO'
  AND des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
GROUP BY des_produto, des_categoria, des_linha
ORDER BY n_skus DESC
"""
rows = con.execute(q1).fetchall()
print(f"{'Produto':25s} {'Cat':12s} {'Linha':12s} {'SKUs':>5s} {'Forn':>4s} {'CustoMed':>8s} {'Range':>25s}")
print("-" * 95)
q1_results = []
for r in rows:
    line = f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2]):12s} {r[3]:5d} {r[4]:4d} {str(r[5] if r[5] else 'NULL'):>8s} [{str(r[6] if r[6] else '?'):>7s}-{str(r[7] if r[7] else '?'):>7s}]"
    print(line)
    q1_results.append(r)
print(f"Total rows: {len(rows)}")

# ============================================================================
# QUERY 2: Grupos de substitutos por fornecedor
# ============================================================================
print()
print("=" * 80)
print("QUERY 2: Substitute groups by fornecedor")
print("=" * 80)

q2 = """
SELECT 
    p.des_produto,
    p.des_categoria,
    p.des_linha,
    p.cod_fornecedor,
    COALESCE(f.des_categoria, 'S/FORNECEDOR') as fornecedor_cat,
    COUNT(p.id_produto) as n_skus,
    CAST(AVG(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_medio,
    CAST(MIN(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_min,
    CAST(MAX(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_max
FROM gold.dim_produto p
LEFT JOIN gold.dim_fornecedor f ON p.cod_fornecedor = f.cod_fornecedor
WHERE p.dat_fim_vigencia IS NULL
  AND p.des_status = 'ATIVO'
  AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
  AND p.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
GROUP BY p.des_produto, p.des_categoria, p.des_linha, p.cod_fornecedor, f.des_categoria
ORDER BY p.des_produto, p.des_linha, p.cod_fornecedor
"""
rows = con.execute(q2).fetchall()
print(f"{'Produto':25s} {'Cat':12s} {'Linha':12s} {'Fornec':12s} {'FornCat':12s} {'SKUs':>5s} {'CustoMed':>8s} {'Range':>25s}")
print("-" * 115)
q2_results = []
for r in rows:
    line = f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2]):12s} {str(r[3]):12s} {str(r[4]):12s} {r[5]:5d} {str(r[6] if r[6] else 'NULL'):>8s} [{str(r[7] if r[7] else '?'):>7s}-{str(r[8] if r[8] else '?'):>7s}]"
    print(line)
    q2_results.append(r)
print(f"Total rows: {len(rows)}")

# ============================================================================
# QUERY 3: Co-purchase analysis (mesmo pedido - fato_compras)
# ============================================================================
print()
print("=" * 80)
print("QUERY 3: Co-purchase analysis (same pedido)")
print("=" * 80)

q3 = """
WITH pedido_produtos AS (
    SELECT 
        fc.num_pedido,
        dp.des_produto,
        dp.des_categoria,
        dp.des_linha,
        dp.cod_fornecedor,
        COUNT(DISTINCT fc.id_produto) as skus_no_pedido
    FROM gold.fato_compras fc
    JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
    WHERE dp.dat_fim_vigencia IS NULL
      AND dp.des_status = 'ATIVO'
      AND dp.des_categoria IN ('UNDERWARE', 'FITNESS')
      AND dp.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
    GROUP BY fc.num_pedido, dp.des_produto, dp.des_categoria, dp.des_linha, dp.cod_fornecedor
),
pares AS (
    SELECT 
        a.des_produto as prod_a,
        a.des_linha as linha_a,
        a.des_categoria as cat_a,
        a.cod_fornecedor as forn_a,
        b.des_produto as prod_b,
        b.des_linha as linha_b,
        b.des_categoria as cat_b,
        b.cod_fornecedor as forn_b,
        COUNT(DISTINCT a.num_pedido) as pedidos_juntos
    FROM pedido_produtos a
    JOIN pedido_produtos b ON a.num_pedido = b.num_pedido
        AND (a.des_produto < b.des_produto 
             OR (a.des_produto = b.des_produto AND a.cod_fornecedor < b.cod_fornecedor))
    GROUP BY a.des_produto, a.des_linha, a.des_categoria, a.cod_fornecedor,
             b.des_produto, b.des_linha, b.des_categoria, b.cod_fornecedor
)
SELECT *
FROM pares
WHERE prod_a = prod_b
  AND forn_a <> forn_b
ORDER BY pedidos_juntos DESC
LIMIT 30
"""
rows = con.execute(q3).fetchall()
print(f"{'Produto':20s} {'Linha':12s} {'Forn_A':12s} {'Forn_B':12s} {'PedidosJuntos':>13s}")
print("-" * 75)
for r in rows:
    print(f"{str(r[0]):20s} {str(r[1]):12s} {str(r[3]):12s} {str(r[7]):12s} {r[8]:13d}")
print(f"Total rows: {len(rows)}")

# Same product, different fornecedor, same pedido - summary stats
q3b = """
SELECT 
    p.des_produto,
    p.des_linha,
    p.des_categoria,
    COUNT(DISTINCT fc.num_pedido) as pedidos_com_substitutos,
    COUNT(DISTINCT fc.cod_fornecedor) as fornecedores_distintos,
    COUNT(DISTINCT fc.id_produto) as skus_distintos
FROM gold.fato_compras fc
JOIN gold.dim_produto p ON fc.id_produto = p.id_produto
WHERE p.dat_fim_vigencia IS NULL
  AND p.des_status = 'ATIVO'
  AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
  AND p.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
GROUP BY p.des_produto, p.des_linha, p.des_categoria
ORDER BY pedidos_com_substitutos DESC
LIMIT 20
"""
print()
print("-- Co-purchase summary by product type --")
rows = con.execute(q3b).fetchall()
print(f"{'Produto':25s} {'Linha':12s} {'Cat':12s} {'Pedidos':>8s} {'Forn':>5s} {'SKUs':>5s}")
print("-" * 72)
for r in rows:
    print(f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2]):12s} {r[3]:8d} {r[4]:5d} {r[5]:5d}")

# ============================================================================
# QUERY 4: Preco medio de venda por des_produto
# ============================================================================
print()
print("=" * 80)
print("QUERY 4: Average sale price by product type")
print("=" * 80)

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
print(f"{'Produto':25s} {'Cat':12s} {'VendaMed':>8s} {'CustoMed':>8s} {'SKUsVend':>8s} {'TotalVend':>10s}")
print("-" * 75)
q4_results = []
for r in rows:
    line = f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2] if r[2] else 'NULL'):>8s} {str(r[3] if r[3] else 'NULL'):>8s} {r[4]:8d} {r[5]:10d}"
    print(line)
    q4_results.append(r)
print(f"Total rows: {len(rows)}")

# ============================================================================
# EXTRA: Fornecedores que competem no mesmo segmento
# ============================================================================
print()
print("=" * 80)
print("EXTRA: Fornecedor competition by segment")
print("=" * 80)

q5 = """
SELECT 
    p.des_produto,
    p.des_linha,
    p.cod_fornecedor,
    f.des_categoria as fornecedor_cat,
    COUNT(p.id_produto) as n_skus,
    CAST(AVG(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_medio
FROM gold.dim_produto p
LEFT JOIN gold.dim_fornecedor f ON p.cod_fornecedor = f.cod_fornecedor
WHERE p.dat_fim_vigencia IS NULL
  AND p.des_status = 'ATIVO'
  AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
  AND p.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
  AND p.val_custo_inicial > 0
GROUP BY p.des_produto, p.des_linha, p.cod_fornecedor, f.des_categoria
HAVING COUNT(p.id_produto) >= 5
ORDER BY p.des_produto, p.des_linha, n_skus DESC
"""
rows = con.execute(q5).fetchall()
print(f"{'Produto':25s} {'Linha':12s} {'Fornec':12s} {'FornCat':15s} {'SKUs':>5s} {'CustoMed':>8s}")
print("-" * 82)
for r in rows:
    print(f"{str(r[0]):25s} {str(r[1]):12s} {str(r[2]):12s} {str(r[3]):15s} {r[4]:5d} {str(r[5] if r[5] else 'NULL'):>8s}")
print(f"Total rows: {len(rows)}")

# Save all results for later use
import json
results = {
    "q1": [[str(c) for c in r] for r in q1_results],
    "q4": [[str(c) for c in r] for r in q4_results],
}
with open("F:/projects/chez-violeta-intelligence/artifacts/data/_query_results.json", "w") as f:
    json.dump(results, f, indent=2)

con.close()
print("\nDone!")
