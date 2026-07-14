#!/usr/bin/env python3
"""Explore data for dashboard fix"""
import duckdb

con = duckdb.connect('artifacts/data/chez_gold.duckdb')

print("=== Categories with custo medio ===")
cats = con.execute("""
SELECT des_categoria, 
       ROUND(AVG(CASE WHEN val_custo_inicial > 0 THEN val_custo_inicial END), 2) as custo_medio,
       COUNT(*) as qtd
FROM gold.dim_produto WHERE dat_fim_vigencia IS NULL 
GROUP BY des_categoria ORDER BY qtd DESC
""").fetchdf()
print(cats.to_string())

print("\n=== Prophet forecast ===")
pf = con.execute("""
SELECT categoria, ROUND(SUM(yhat), 1) as total_120d, COUNT(*) as rows
FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv') 
GROUP BY categoria
""").fetchdf()
print(pf.to_string())

print("\n=== VESTUARIO with cod_fornecedor ===")
vest = con.execute("""
SELECT cod_fornecedor, COUNT(*) as qtd
FROM gold.dim_produto 
WHERE des_categoria = 'VESTUARIO' AND dat_fim_vigencia IS NULL
AND cod_fornecedor IS NOT NULL AND cod_fornecedor != ''
GROUP BY cod_fornecedor ORDER BY qtd DESC LIMIT 10
""").fetchdf()
print(vest.to_string())

vest_total = con.execute("""
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN cod_fornecedor IS NOT NULL AND cod_fornecedor != '' THEN 1 ELSE 0 END) as com_forn,
  SUM(CASE WHEN cod_fornecedor IS NULL OR cod_fornecedor = '' THEN 1 ELSE 0 END) as sem_forn
FROM gold.dim_produto 
WHERE des_categoria = 'VESTUARIO' AND dat_fim_vigencia IS NULL
""").fetchdf()
print(vest_total.to_string())

print("\n=== Total distinct dates ===")
print("Total:", con.execute("SELECT COUNT(DISTINCT id_data) FROM gold.fato_estoque_diario").fetchone()[0])
print("Com venda:", con.execute("SELECT COUNT(DISTINCT id_data) FROM gold.fato_estoque_diario WHERE qtd_venda > 0").fetchone()[0])

print("\n=== Sample product velocity issue ===")
sample = con.execute("""
WITH 
vendas AS (
    SELECT id_produto, SUM(qtd_venda) as total_vendas,
           COUNT(DISTINCT id_data) as dias_com_venda
    FROM gold.fato_estoque_diario
    WHERE qtd_venda > 0
    GROUP BY id_produto
)
SELECT p.des_produto, p.des_categoria, v.total_vendas, v.dias_com_venda,
       ROUND(v.total_vendas * 1.0 / v.dias_com_venda, 4) as vel_antiga,
       ROUND(v.total_vendas * 1.0 / 632, 4) as vel_nova,
       ROUND(v.total_vendas * 1.0 / v.dias_com_venda * 120, 0) as prev_antiga,
       ROUND(v.total_vendas * 1.0 / 632 * 120, 0) as prev_nova
FROM vendas v
JOIN gold.dim_produto p ON v.id_produto = p.id_produto
WHERE v.total_vendas BETWEEN 1 AND 20 AND v.dias_com_venda BETWEEN 1 AND 10
ORDER BY v.total_vendas DESC LIMIT 15
""").fetchdf()
print(sample.to_string())

con.close()
