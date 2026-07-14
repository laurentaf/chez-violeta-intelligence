#!/usr/bin/env python3
"""Explore prophet forecast data"""
import duckdb
import pandas as pd

con = duckdb.connect('artifacts/data/chez_gold.duckdb')

# Prophet dates and categories
pf = con.execute("""
SELECT MIN(ds) as min_ds, MAX(ds) as max_ds, 
       COUNT(*) as rows, categoria,
       ROUND(SUM(yhat), 1) as total_yhat
FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv') 
GROUP BY categoria
""").fetchdf()
print("Prophet forecast:")
print(pf.to_string())

# Check what categories in dim_produto are NOT in prophet
print("\n=== Categories in dim_produto not in prophet ===")
cats_not_in_prophet = con.execute("""
SELECT DISTINCT p.des_categoria
FROM gold.dim_produto p
WHERE p.dat_fim_vigencia IS NULL 
  AND p.des_categoria NOT IN (SELECT DISTINCT categoria FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv'))
  AND p.des_categoria IS NOT NULL
""").fetchdf()
print(cats_not_in_prophet.to_string())

# Check what categories in prophet are NOT in dim_produto
print("\n=== Categories in prophet not in dim_produto ===")
cats_not_in_dim = con.execute("""
SELECT DISTINCT categoria
FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv')
WHERE categoria NOT IN (SELECT DISTINCT des_categoria FROM gold.dim_produto WHERE des_categoria IS NOT NULL)
""").fetchdf()
print(cats_not_in_dim.to_string())

# Count products by category with stock > 0
print("\n=== Products with stock > 0 by category ===")
stock_cat = con.execute("""
SELECT p.des_categoria, COUNT(DISTINCT p.id_produto) as qtd_com_estoque
FROM gold.dim_produto p
JOIN gold.fato_estoque_diario fe ON p.id_produto = fe.id_produto
WHERE p.dat_fim_vigencia IS NULL AND fe.qtd_estoque > 0
GROUP BY p.des_categoria ORDER BY qtd_com_estoque DESC
""").fetchdf()
print(stock_cat.to_string())

con.close()
