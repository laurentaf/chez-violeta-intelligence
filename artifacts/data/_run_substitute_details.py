import duckdb
con = duckdb.connect('F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb')

# Per (produto, linha) - which fornecedors compete with overlapping price ranges
q = """
WITH stats AS (
    SELECT 
        p.des_produto,
        p.des_linha,
        p.des_categoria,
        p.cod_fornecedor,
        COALESCE(f.des_categoria, 'N/D') as fornecedor_cat,
        COUNT(p.id_produto) as n_skus,
        CAST(MIN(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_min,
        CAST(MAX(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_max,
        CAST(AVG(p.val_custo_inicial) AS DECIMAL(10,2)) as custo_medio,
        CAST(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY p.val_custo_inicial) AS DECIMAL(10,2)) as p25,
        CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY p.val_custo_inicial) AS DECIMAL(10,2)) as p50,
        CAST(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY p.val_custo_inicial) AS DECIMAL(10,2)) as p75
    FROM gold.dim_produto p
    LEFT JOIN gold.dim_fornecedor f ON p.cod_fornecedor = f.cod_fornecedor
    WHERE p.dat_fim_vigencia IS NULL
      AND p.des_status = 'ATIVO'
      AND p.des_categoria IN ('UNDERWARE', 'FITNESS')
      AND p.des_linha IN ('BASICO', 'MEIA', 'SHAPEWARE', 'MATERNITY', 'MASCULINO')
      AND p.val_custo_inicial > 0
    GROUP BY p.des_produto, p.des_linha, p.des_categoria, p.cod_fornecedor, f.des_categoria
    HAVING COUNT(p.id_produto) >= 3
)
SELECT 
    des_produto,
    des_linha,
    des_categoria,
    STRING_AGG(cod_fornecedor, ', ' ORDER BY n_skus DESC) as fornecedores,
    STRING_AGG(fornecedor_cat, ', ' ORDER BY n_skus DESC) as fornecedor_cats,
    STRING_AGG(CAST(n_skus AS VARCHAR), ', ' ORDER BY n_skus DESC) as skus_por_forn,
    STRING_AGG(CAST(custo_medio AS VARCHAR), ', ' ORDER BY n_skus DESC) as custo_por_forn,
    STRING_AGG(CAST(p25 AS VARCHAR) || '-' || CAST(p75 AS VARCHAR), ', ' ORDER BY n_skus DESC) as iqr_por_forn,
    SUM(n_skus) as total_skus,
    COUNT(*) as n_fornecedores
FROM stats
GROUP BY des_produto, des_linha, des_categoria
HAVING COUNT(*) >= 2
ORDER BY total_skus DESC
"""
rows = con.execute(q).fetchall()
print("=== COMPETITIVE SUBSTITUTE GROUPS (2+ fornecedors) ===")
print(f"{'Produto':20s} {'Linha':12s} {'Cat':12s} {'Forns':>5s} {'TotalSKU':>7s} {'Fornecedores':>80s}")
print("-" * 140)
for r in rows:
    print(f"{str(r[0]):20s} {str(r[1]):12s} {str(r[2]):12s} {r[9]:5d} {r[8]:7d}")
    print(f"{'':44s} Fornecedores: {str(r[3])}")
    print(f"{'':44s} Categorias:   {str(r[4])}")
    print(f"{'':44s} SKUs:         {str(r[5])}")
    print(f"{'':44s} Custos med:   {str(r[6])}")
    print(f"{'':44s} IQR range:    {str(r[7])}")
    print()

con.close()
