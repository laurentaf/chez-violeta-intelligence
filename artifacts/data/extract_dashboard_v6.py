#!/usr/bin/env python3
"""Extract DuckDB data for dashboard v6, save as JSON for embedding."""
import duckdb
import pandas as pd
import json
import os

DB = "F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
OUT = "F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/data_v6.json"
con = duckdb.connect(DB)

# ── KPI: Total fornecedores ativos (com produtos ativos) ──
kpi_fornecedores = con.execute("""
    SELECT COUNT(DISTINCT p.cod_fornecedor) as total
    FROM gold.dim_produto p
    WHERE p.des_status = 'ATIVO' AND p.dat_fim_vigencia IS NULL
      AND p.cod_fornecedor IS NOT NULL
""").fetchone()[0]

# ── KPI: Itens de vestuario em falta (estoque = 0 ou negativo) ──
kpi_vestuario_falta = con.execute("""
    SELECT COUNT(DISTINCT p.id_produto)
    FROM gold.dim_produto p
    LEFT JOIN gold.fato_estoque_diario fe ON p.id_produto = fe.id_produto
        AND fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
    WHERE p.des_categoria = 'VESTUARIO'
      AND p.des_status = 'ATIVO'
      AND p.dat_fim_vigencia IS NULL
      AND (fe.qtd_estoque IS NULL OR fe.qtd_estoque <= 0)
""").fetchone()[0]

# ── KPI: Valor total estimado de compras (soma custo * necessidade) ──
kpi_valor_estimado = con.execute("""
    SELECT ROUND(SUM(
        COALESCE(fe.qtd_estoque, 0) * COALESCE(p.val_custo_inicial, 0)
    ), 0) as total
    FROM gold.dim_produto p
    LEFT JOIN gold.fato_estoque_diario fe ON p.id_produto = fe.id_produto
        AND fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
    WHERE p.des_status = 'ATIVO' AND p.dat_fim_vigencia IS NULL
""").fetchone()[0]

# ── VISAO 1: VESTUARIO ──
vestuario_df = con.execute("""
    SELECT 
        p.des_produto,
        COALESCE(p.cod_tamanho, 'UN') as tamanho,
        COALESCE(SUM(fe.qtd_estoque), 0) as estoque_atual,
        ROUND(COALESCE(SUM(fv.qtd_pecas) * 17.0 / 52, 0)) as necessidade_120d
    FROM gold.dim_produto p
    LEFT JOIN gold.fato_estoque_diario fe ON p.id_produto = fe.id_produto 
        AND fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
    LEFT JOIN gold.fato_vendas fv ON p.id_produto = fv.id_produto
    WHERE p.des_categoria = 'VESTUARIO'
      AND p.dat_fim_vigencia IS NULL
      AND p.des_status = 'ATIVO'
    GROUP BY p.des_produto, p.cod_tamanho
    HAVING SUM(fe.qtd_estoque) > 0 OR SUM(fv.qtd_pecas) > 0
    ORDER BY p.des_produto, p.cod_tamanho
""").fetchdf()

# Transform to list of dicts
vestuario_itens = []
for _, r in vestuario_df.iterrows():
    diff = r['estoque_atual'] - r['necessidade_120d']
    acao = "OK" if diff >= 0 else "COMPRAR"
    vestuario_itens.append({
        "produto": r['des_produto'],
        "tamanho": r['tamanho'],
        "estoque": int(r['estoque_atual']),
        "necessidade": int(r['necessidade_120d']),
        "diferenca": int(diff),
        "acao": acao
    })

# ── VISAO 2: DEMAIS CATEGORIAS POR FORNECEDOR ──
# Link products to suppliers, compute cobertura media and estimated value
outras_categorias = con.execute("""
    SELECT 
        COALESCE(f.cod_fornecedor, 'SEM FORNECEDOR') as fornecedor,
        COUNT(DISTINCT p.id_produto) as n_produtos,
        ROUND(AVG(COALESCE(fe.qtd_estoque, 0)), 1) as cobertura_media,
        ROUND(SUM(COALESCE(fe.qtd_estoque, 0) * COALESCE(p.val_custo_inicial, 0)), 0) as valor_estimado
    FROM gold.dim_produto p
    LEFT JOIN gold.dim_fornecedor f ON p.cod_fornecedor = f.cod_fornecedor
    LEFT JOIN gold.fato_estoque_diario fe ON p.id_produto = fe.id_produto
        AND fe.id_data = (SELECT MAX(id_data) FROM gold.fato_estoque_diario)
    WHERE p.des_categoria != 'VESTUARIO'
      AND p.des_status = 'ATIVO'
      AND p.dat_fim_vigencia IS NULL
    GROUP BY f.cod_fornecedor
    HAVING COUNT(DISTINCT p.id_produto) > 0
    ORDER BY valor_estimado DESC
""").fetchdf()

fornecedores_visao = []
for _, r in outras_categorias.iterrows():
    atinge_10k = "SIM" if r['valor_estimado'] >= 10000 else "NAO"
    fornecedores_visao.append({
        "fornecedor": r['fornecedor'],
        "n_produtos": int(r['n_produtos']),
        "cobertura_media": float(r['cobertura_media']) if r['cobertura_media'] else 0,
        "valor_estimado": float(r['valor_estimado']),
        "atinge_10k": atinge_10k
    })

# ── VISAO 3: PREVISAO (forecast) ──
# Usar o modelo de regressao existente para projetar 26 semanas
# Como temos apenas o modelo OLS, vamos usar tendencia + sazonalidade
# Simplificacao: usar media movel das ultimas 52 semanas por categoria

previsao = con.execute("""
WITH vendas_semanais AS (
    SELECT 
        p.des_categoria,
        SUM(fv.qtd_pecas) as qtd
    FROM gold.fato_vendas fv
    JOIN gold.dim_tempo dt ON fv.id_data = dt.id_data
    JOIN gold.dim_produto p ON fv.id_produto = p.id_produto
    GROUP BY p.des_categoria
),
media_52s AS (
    SELECT 
        des_categoria,
        ROUND(COALESCE(AVG(qtd), 0), 1) as media_semanal
    FROM vendas_semanais
    WHERE qtd > 0
    GROUP BY des_categoria
)
SELECT * FROM media_52s ORDER BY media_semanal DESC
""").fetchdf()

forecast = []
if len(previsao) > 0:
    for _, r in previsao.iterrows():
        forecast.append({
            "categoria": r['des_categoria'],
            "media_semanal": float(r['media_semanal']),
            "previsao_26s": round(float(r['media_semanal']) * 26, 0)
        })

# Semanas da previsao (proximas 26)
from datetime import datetime, timedelta
ultima_data_query = con.execute("""
    SELECT MAX(dt.dat_dia) as ultima_data 
    FROM gold.fato_vendas fv 
    JOIN gold.dim_tempo dt ON fv.id_data = dt.id_data
""").fetchone()[0]

semanas_forecast = []
if ultima_data_query:
    from datetime import datetime as dt_module
    # ultima_data_query is a datetime.date object
    # Generate 26 weekly points
    for i in range(1, 27):
        d = ultima_data_query + timedelta(weeks=i)
        semanas_forecast.append(f"S{d.isocalendar()[1]}/{d.year}")

# ── Build output ──
output = {
    "kpi": {
        "fornecedores_comprar": kpi_fornecedores,
        "itens_vestuario_falta": kpi_vestuario_falta,
        "valor_total_estimado": float(kpi_valor_estimado)
    },
    "visao1_vestuario": vestuario_itens,
    "visao1_stats": {
        "total_itens": len(vestuario_itens),
        "itens_comprar": sum(1 for i in vestuario_itens if i['acao'] == 'COMPRAR'),
        "itens_ok": sum(1 for i in vestuario_itens if i['acao'] == 'OK')
    },
    "visao2_fornecedores": fornecedores_visao,
    "visao2_stats": {
        "total_fornecedores": len(fornecedores_visao),
        "atingem_10k": sum(1 for f in fornecedores_visao if f['atinge_10k'] == 'SIM')
    },
    "visao3_forecast": forecast,
    "forecast_semanas": semanas_forecast,
    "data_extracao": datetime.now().strftime("%Y-%m-%d %H:%M")
}

with open(OUT, 'w', newline='\n', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f"OK: {len(vestuario_itens)} vestuario items, {len(fornecedores_visao)} fornecedores, {len(forecast)} categorias forecast")
print(f"KPIs: {kpi_fornecedores} fornecedores, {kpi_vestuario_falta} itens falta, R${kpi_valor_estimado:.0f}")
