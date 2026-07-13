"""Explore the sales data from fato_estoque_diario."""
import duckdb
import pandas as pd

conn = duckdb.connect('artifacts/data/chez_gold.duckdb')

# Vendas > 0
res = conn.execute("""
    SELECT COUNT(*) as total_vendas,
           MIN(dt.dat_dia) as min_data,
           MAX(dt.dat_dia) as max_data,
           COUNT(DISTINCT fe.id_loja) as n_lojas,
           COUNT(DISTINCT dp.des_categoria) as n_categorias
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data
    JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
    WHERE fe.qtd_venda > 0
""").fetchdf()
print("=== RESUMO VENDAS (qtd_venda > 0) ===")
print(res.to_string())
print()

# Lojas com vendas
lojas = conn.execute("""
    SELECT l.id_loja, l.des_estabelecimento, COUNT(*) as n_registros, SUM(fe.qtd_venda) as total_vendas
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_loja l ON fe.id_loja = l.id_loja
    WHERE fe.qtd_venda > 0
    GROUP BY l.id_loja, l.des_estabelecimento
    ORDER BY SUM(fe.qtd_venda) DESC
""").fetchdf()
print("=== LOJAS ===")
print(lojas.to_string())
print()

# Categorias
cats = conn.execute("""
    SELECT dp.des_categoria, COUNT(*) as n_registros, SUM(fe.qtd_venda) as total_vendas
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
    WHERE fe.qtd_venda > 0
    GROUP BY dp.des_categoria
    ORDER BY SUM(fe.qtd_venda) DESC
""").fetchdf()
print("=== CATEGORIAS ===")
print(cats.to_string())
print()

# Vendas mensais agregadas
monthly = conn.execute("""
    SELECT 
        dt.num_ano,
        dt.des_mes_ano,
        SUM(fe.qtd_venda) as vendas_mes
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data
    WHERE fe.qtd_venda > 0
    GROUP BY dt.num_ano, dt.des_mes_ano, dt.id_ano_mes
    ORDER BY dt.id_ano_mes
""").fetchdf()
print("=== VENDAS MENSAIS ===")
print(monthly.to_string())
