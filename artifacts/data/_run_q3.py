import duckdb
con = duckdb.connect('F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb')

# Check fato_compras columns
print("=== fato_compras columns ===")
for row in con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'gold' AND table_name = 'fato_compras' ORDER BY ordinal_position").fetchall():
    print(f"  {row[0]} ({row[1]})")

print("\n=== dim_fornecedor columns ===")
for row in con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'gold' AND table_name = 'dim_fornecedor' ORDER BY ordinal_position").fetchall():
    print(f"  {row[0]} ({row[1]})")

# Check distinct cod_tipo_pedido
print("\n=== Pedido types ===")
for row in con.execute("SELECT DISTINCT cod_tipo_pedido FROM gold.fato_compras").fetchall():
    print(f"  {row[0]}")

# Check some sample pedidos with multiple products
q_check = """
SELECT fc.num_pedido, fc.cod_tipo_pedido, COUNT(DISTINCT fc.id_produto) as skus
FROM gold.fato_compras fc
JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
WHERE dp.des_categoria IN ('UNDERWARE', 'FITNESS')
  AND dp.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
GROUP BY fc.num_pedido, fc.cod_tipo_pedido
HAVING COUNT(DISTINCT fc.id_produto) > 3
ORDER BY skus DESC
LIMIT 20
"""
print("\n=== Pedidos with multiple commodity SKUs ===")
rows = con.execute(q_check).fetchall()
print(f"{'Pedido':15s} {'Tipo':12s} {'SKUs':>5s}")
print("-" * 35)
for r in rows:
    print(f"{str(r[0]):15s} {str(r[1]):12s} {r[2]:5d}")

# Check if dim_fornecedor has the link
print("\n=== dim_fornecedor sample ===")
for row in con.execute("SELECT * FROM gold.dim_fornecedor LIMIT 10").fetchall():
    print(f"  {row}")

# Check pedido details - what products share a pedido
q_detail = """
SELECT fc.num_pedido, dp.des_produto, dp.des_linha, dp.cod_fornecedor, COUNT(*) as qtd
FROM gold.fato_compras fc
JOIN gold.dim_produto dp ON fc.id_produto = dp.id_produto
WHERE dp.des_categoria IN ('UNDERWARE', 'FITNESS')
  AND dp.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
  AND fc.num_pedido IN (
    SELECT fc2.num_pedido
    FROM gold.fato_compras fc2
    JOIN gold.dim_produto dp2 ON fc2.id_produto = dp2.id_produto
    WHERE dp2.des_categoria IN ('UNDERWARE', 'FITNESS')
      AND dp2.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
    GROUP BY fc2.num_pedido
    HAVING COUNT(DISTINCT dp2.des_produto) >= 2
    LIMIT 5
  )
GROUP BY fc.num_pedido, dp.des_produto, dp.des_linha, dp.cod_fornecedor
ORDER BY fc.num_pedido, dp.des_produto
"""
print("\n=== Sample pedidos with multiple product types ===")
rows = con.execute(q_detail).fetchall()
print(f"{'Pedido':15s} {'Produto':20s} {'Linha':12s} {'Fornec':12s} {'Qtd':>4s}")
print("-" * 68)
for r in rows:
    print(f"{str(r[0]):15s} {str(r[1]):20s} {str(r[2]):12s} {str(r[3]):12s} {r[4]:4d}")

con.close()
