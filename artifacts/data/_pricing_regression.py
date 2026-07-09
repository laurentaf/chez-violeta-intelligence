#!/usr/bin/env python3
"""
Chez Violeta - Log-Log Price Elasticity Regression
Run from LAOS venv: uv run python <path>
"""
import duckdb, sys

DB = "F:/Projetos/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
conn = duckdb.connect(DB)

# Create aggregate log-log view
conn.execute("""
CREATE OR REPLACE TEMP VIEW v_agg_log AS
SELECT 
    COALESCE(dp.des_categoria, 'OUTROS') as categoria,
    DATE_TRUNC('month', dt.dat_dia)::DATE as mes,
    SUM(fv.qtd_pecas)::DOUBLE as qtd,
    AVG(fv.val_venda_liquida)::DOUBLE as preco,
    LN(SUM(fv.qtd_pecas)::DOUBLE) as ln_qtd,
    LN(AVG(fv.val_venda_liquida)::DOUBLE) as ln_preco,
    COUNT(*)::INTEGER as transacoes
FROM gold.fato_vendas fv
JOIN gold.dim_tempo dt ON fv.id_data=dt.id_data
JOIN gold.dim_produto dp ON fv.id_produto=dp.id_produto
WHERE fv.qtd_pecas>0 AND fv.val_venda_liquida>0 AND dp.des_categoria IS NOT NULL
GROUP BY dp.des_categoria, DATE_TRUNC('month', dt.dat_dia)
""")

print("=== LOG-LOG ELASTICITY BY CATEGORY ===")
print("Model: ln(qty) = alpha + beta * ln(price)")
print()

cats = conn.execute("SELECT DISTINCT categoria FROM v_agg_log ORDER BY 1").fetchall()
cat_results = []
for c in cats:
    cat = c[0]
    q = f"""
        SELECT 
            COUNT(*)::INTEGER as n,
            regr_slope(ln_qtd, ln_preco) as beta,
            regr_intercept(ln_qtd, ln_preco) as alpha,
            regr_r2(ln_qtd, ln_preco) as r2,
            CORR(ln_qtd, ln_preco) as r,
            AVG(preco)::DOUBLE as preco_medio,
            SUM(qtd)::INTEGER as qtd_total,
            COUNT(DISTINCT mes)::INTEGER as meses
        FROM v_agg_log
        WHERE categoria = ?
    """
    r = conn.execute(q, [cat]).fetchone()
    
    n = r[0]
    beta = r[1]
    if n >= 3 and beta is not None and str(beta) != 'nan':
        print(f"  {cat:<15} n={n:>2}  elasticidade={beta:>+8.4f}  alpha={r[2]:>+8.4f}  R2={r[3]:>.4f}  r={r[4]:>.4f}  precomed=R${r[5]:>.2f}  qtdtotal={r[6]:>5}")
        cat_results.append({
            "categoria": cat,
            "n": n,
            "elasticidade": float(beta),
            "alpha": float(r[2]),
            "r2": float(r[3]) if r[3] is not None and str(r[3]) != 'nan' else 0.0,
            "r": float(r[4]) if r[4] is not None and str(r[4]) != 'nan' else 0.0,
            "preco_medio": float(r[5]),
            "qtd_total": r[6],
            "meses": r[7]
        })
    elif n > 0:
        print(f"  {cat:<15} n={n:>2}  (insufficient variation for regression)")

# Pooled regression
print()
print("=== POOLED LOG-LOG (all categories) ===")
pooled = conn.execute("""
    SELECT 
        COUNT(*)::INTEGER,
        regr_slope(ln_qtd, ln_preco) as beta,
        regr_intercept(ln_qtd, ln_preco) as alpha,
        regr_r2(ln_qtd, ln_preco) as r2,
        CORR(ln_qtd, ln_preco) as r
    FROM v_agg_log
""").fetchone()
print(f"  n={pooled[0]}  elasticidade={pooled[1]:.6f}  alpha={pooled[2]:.6f}  R2={pooled[3]:.6f}  r={pooled[4]:.6f}")

# Interpretation
print()
print("=== INTERPRETATION ===")
print()
for cr in cat_results:
    e = cr["elasticidade"]
    if e > 0.5:
        interp = "Elastic (positive - mix/composition effect)"
    elif e > 0.1:
        interp = "Slightly elastic (positive)"
    elif e > -0.1:
        interp = "Near-unit elastic"
    elif e > -0.5:
        interp = "Slightly inelastic"
    elif e > -1.0:
        interp = "Inelastic"
    elif e > -2.0:
        interp = "Elastic"
    else:
        interp = "Highly elastic"
    print(f"  {cr['categoria']:<15} beta={e:>+8.4f}  R2={cr['r2']:.4f}  -> {interp}")

print()
print("NOTE: Positive elasticities indicate composition effects,")
print("not true Veblen demand. When high-price products sell more")
print("in certain months, aggregate regression picks up the mix shift.")
print()

# Raw data for documentation
print("=== OBSERVATIONS ===")
rows = conn.execute("""
    SELECT categoria, mes, qtd::INTEGER, ROUND(preco,2), 
           ROUND(ln_qtd,4), ROUND(ln_preco,4), transacoes 
    FROM v_agg_log ORDER BY categoria, mes
""").fetchall()
print(f"{'Categoria':<16} {'Mes':<12} {'Qtd':>6} {'Preco':>8} {'Ln(Qtd)':>10} {'Ln(Preco)':>10} {'Tx':>4}")
print("-"*66)
for r in rows:
    mes = str(r[1])[:10] if r[1] else 'N/A'
    qtd = r[2] if r[2] else 0
    preco = r[3] if r[3] else 0
    lnq = r[4] if r[4] else 0
    lnp = r[5] if r[5] else 0
    tx = r[6] if r[6] else 0
    print(f"{r[0]:<16} {mes:<12} {qtd:>6} R${preco:>6} {lnq:>10.4f} {lnp:>10.4f} {tx:>4}")

conn.close()
print()
print("Done.")
