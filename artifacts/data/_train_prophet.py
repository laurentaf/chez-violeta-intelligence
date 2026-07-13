"""
Prophet forecasting for Chez Violeta.
Trains one model per product category using fato_estoque_diario.qtd_venda.
"""
import duckdb
import pandas as pd
import numpy as np
import pickle
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from prophet import Prophet
from prophet.serialize import model_to_json
from pathlib import Path

warnings.filterwarnings('ignore')

OUT_DIR = Path('artifacts/data')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Extrair dados ──────────────────────────────────────────
print("[1/8] Extraindo dados do DuckDB...")
conn = duckdb.connect('artifacts/data/chez_gold.duckdb')

df = conn.execute("""
    SELECT 
        dt.dat_dia as ds,
        l.des_estabelecimento as loja,
        COALESCE(dp.des_categoria, 'OUTROS') as categoria,
        fe.qtd_venda as vendas
    FROM gold.fato_estoque_diario fe
    JOIN gold.dim_tempo dt ON fe.id_data = dt.id_data
    JOIN gold.dim_loja l ON fe.id_loja = l.id_loja
    JOIN gold.dim_produto dp ON fe.id_produto = dp.id_produto
    WHERE fe.qtd_venda > 0
      AND l.id_loja IN (3,4,6,7,8,9,15,16,20,23,27)
    ORDER BY dt.dat_dia, l.des_estabelecimento
""").fetchdf()

conn.close()

df['ds'] = pd.to_datetime(df['ds'])
print(f"  Registros: {len(df):,}")
print(f"  Periodo: {df['ds'].min()} a {df['ds'].max()}")
print(f"  Lojas: {df['loja'].nunique()}")
print(f"  Categorias: {df['categoria'].nunique()}")

# ── 2. Agregar por dia + categoria ────────────────────────────
daily_cat = df.groupby(['ds', 'categoria'])['vendas'].sum().reset_index()
print("\n[2/8] Vendas diarias agregadas por categoria:")

# ── 3. Separar categorias principais ──────────────────────────
top_cats = daily_cat.groupby('categoria')['vendas'].sum().sort_values(ascending=False)
for cat, total in top_cats.items():
    cat_data = daily_cat[daily_cat['categoria'] == cat]
    print(f"  {cat}: total={total:,.0f}, media_diaria={cat_data['vendas'].mean():.1f}")

major_cats = ['UNDERWARE', 'MODA PRAIA', 'VESTUARIO', 'LINHA NOITE']
daily_cat['cat_group'] = daily_cat['categoria'].apply(
    lambda x: x if x in major_cats else 'OUTROS'
)

# ── 4. Treinar 1 modelo por categoria ────────────────────────
models = {}
forecasts = {}
fig, axes = plt.subplots(3, 2, figsize=(18, 14))
axes_flat = axes.flatten()

print("\n[3/8] Treinando modelos Prophet...")

for idx, cat in enumerate(major_cats + ['OUTROS']):
    print(f"\n  --- {cat} ---")

    cat_data = daily_cat[daily_cat['cat_group'] == cat][['ds', 'vendas']].rename(
        columns={'vendas': 'y'}
    ).sort_values('ds').reset_index(drop=True)

    print(f"  Registros: {len(cat_data):,}")
    print(f"  Periodo: {cat_data['ds'].min()} a {cat_data['ds'].max()}")
    print(f"  Media diaria: {cat_data['y'].mean():.1f}")

    if len(cat_data) < 30:
        print(f"  Dados insuficientes ({len(cat_data)} dias), pulando")
        axes_flat[idx].text(0.5, 0.5, f'{cat}\nDADOS INSUFICIENTES',
                          ha='center', va='center', fontsize=14)
        continue

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        interval_width=0.80,
    )
    model.add_country_holidays('BR')
    model.fit(cat_data)

    # Forecast: 26 semanas (182 dias)
    future = model.make_future_dataframe(periods=182)
    forecast = model.predict(future)

    models[cat] = model_to_json(model)
    forecasts[cat] = forecast

    # Plot
    ax = axes_flat[idx]
    model.plot(forecast, ax=ax, xlabel='Data', ylabel='Vendas')
    ax.set_title(f'{cat} - Previsao 26 semanas', fontsize=13, fontweight='bold')

    print(f"  Modelo OK. Previsao ate {forecast['ds'].max().date()}")

# Esconder subplot vazio
axes_flat[-1].set_visible(False)
plt.tight_layout()
plt.savefig(OUT_DIR / 'prophet_components.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n[4/8] Grafico salvo: {OUT_DIR / 'prophet_components.png'}")

# ── 5. Salvar modelos ────────────────────────────────────────
with open(OUT_DIR / 'prophet_models.pkl', 'wb') as f:
    pickle.dump(models, f)
print(f"[5/8] Modelos salvos: {OUT_DIR / 'prophet_models.pkl'}")

# ── 6. Salvar forecast CSV completo ──────────────────────────
forecast_all = pd.DataFrame()
for cat, fc in forecasts.items():
    fc['categoria'] = cat
    forecast_all = pd.concat([forecast_all, fc], ignore_index=True)

forecast_all.to_csv(OUT_DIR / 'prophet_forecast.csv', index=False)
print(f"[6/8] Forecast completo salvo: {OUT_DIR / 'prophet_forecast.csv'} ({len(forecast_all):,} linhas)")

# ── 7. Salvar forecast futuro (182 dias) ─────────────────────
future_only = forecast_all[forecast_all['ds'] > df['ds'].max()].copy()
future_only.to_csv(OUT_DIR / 'prophet_forecast_future.csv', index=False)
print(f"[7/8] Forecast futuro salvo: {OUT_DIR / 'prophet_forecast_future.csv'} ({len(future_only):,} linhas)")

# ── 8. Gerar relatorio ───────────────────────────────────────
print("\n[8/8] Gerando relatorio markdown...")

lines = []
lines.append("# Modelo de Previsao (Prophet)\n")
lines.append("## Resumo\n")
lines.append(f"| Metrica | Valor |")
lines.append(f"|---------|-------|")
lines.append(f"| Fonte | `fato_estoque_diario.qtd_venda` |")
lines.append(f"| Periodo | {df['ds'].min().date()} a {df['ds'].max().date()} |")
lines.append(f"| Registros | {len(df):,} vendas |")
lines.append(f"| Lojas | {df['loja'].nunique()} |")
lines.append(f"| Categorias | {df['categoria'].nunique()} |")
lines.append(f"| Modelos treinados | {len(forecasts)} (1 por categoria) |")
lines.append(f"| Horizonte | 26 semanas (182 dias) |")
lines.append(f"| Feriados | BR (nativo Prophet) |")
lines.append(f"| Sazonalidade | Anual (multiplicativa) |")
lines.append("")

lines.append("## Previsao por Categoria (26 semanas)\n")
lines.append("| Categoria | Previsao Total | Media Diaria | Pico Max | Data do Pico |")
lines.append("|-----------|---------------|--------------|----------|--------------|")

for cat in major_cats + ['OUTROS']:
    if cat not in forecasts:
        continue
    fc = forecasts[cat]
    future_fc = fc[fc['ds'] > df['ds'].max()]
    peak = future_fc.loc[future_fc['yhat'].idxmax()]
    lines.append(f"| {cat} | {future_fc['yhat'].sum():,.0f} | {future_fc['yhat'].mean():.1f} | {peak['yhat']:.0f} | {peak['ds'].date()} |")

lines.append("")
lines.append("## Componentes Sazonais\n")

# Extract seasonality and holiday info per model
for cat in major_cats + ['OUTROS']:
    if cat not in forecasts:
        continue
    fc = forecasts[cat]
    lines.append(f"### {cat}\n")

    # Yearly seasonality peaks
    if 'yearly' in fc.columns:
        yearly = fc[['ds', 'yearly']].copy()
        yearly['mes'] = yearly['ds'].dt.month
        monthly_impact = yearly.groupby('mes')['yearly'].mean()
        top_months = monthly_impact.sort_values(ascending=False).head(3)
        lines.append("**Meses de maior impacto sazonal**")
        for mes, val in top_months.items():
            month_names = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                          7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
            lines.append(f"- {month_names[mes]}: {val:+.1f}")
        lines.append("")

    # Holiday impact
    if 'holidays' in fc.columns:
        holiday_impact = fc[['ds', 'holidays']].dropna()
        holiday_impact = holiday_impact[holiday_impact['holidays'] != 0]
        if len(holiday_impact) > 0:
            top_holidays = holiday_impact.reindex(
                holiday_impact['holidays'].abs().sort_values(ascending=False).index
            ).head(5)
            # Map holiday dates to names using Prophet's built-in holidays
            lines.append("**Feriados de maior impacto**")
            for _, row in top_holidays.iterrows():
                lines.append(f"- {row['ds'].date()}: {row['holidays']:+.1f} unidades")
            lines.append("")

# Recommendation for purchasing
print("\nCalculando recomendacao de compra para 120 dias...")
lines.append("## Recomendacao de Compra (120 dias de cobertura)\n")
lines.append("Considerando a sazonalidade, segue a quantidade estimada de venda para 120 dias por categoria:\n")
lines.append("| Categoria | Previsao 120d (unid) | Estoque Recomendado (unid) |")
lines.append("|-----------|---------------------|--------------------------|")

total_120 = 0
for cat in major_cats + ['OUTROS']:
    if cat not in forecasts:
        continue
    fc = forecasts[cat]
    future_120 = fc[(fc['ds'] > df['ds'].max()) & (fc['ds'] <= df['ds'].max() + pd.Timedelta(days=120))]
    if len(future_120) == 0:
        # If we only have 182d forecast, take first 120 days
        future_fc = fc[fc['ds'] > df['ds'].max()]
        future_120 = future_fc.head(120)
    pred_120 = future_120['yhat'].sum()
    # Recommended stock: previsao + 20% safety margin
    rec_120 = int(pred_120 * 1.2)
    total_120 += rec_120
    lines.append(f"| {cat} | {pred_120:,.0f} | {rec_120:,} |")

lines.append(f"| **TOTAL** | | **{total_120:,}** |")
lines.append("")
lines.append("*Estoque recomendado inclui margem de seguranca de 20% sobre a previsao.*\n")

lines.append("## Graficos\n")
lines.append("![Componentes Sazonais](prophet_components.png)\n")

with open(OUT_DIR / 'prophet_report.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"[8/8] Relatorio salvo: {OUT_DIR / 'prophet_report.md'}")

print("\n" + "="*60)
print("SCRIPT CONCLUIDO!")
print("="*60)
for cat in major_cats + ['OUTROS']:
    if cat not in forecasts:
        continue
    fc = forecasts[cat]
    future_fc = fc[fc['ds'] > df['ds'].max()]
    print(f"  {cat}: {future_fc['yhat'].sum():>8,.0f} unidades (26 sem)")

print(f"\nOutputs:")
print(f"  - {OUT_DIR / 'prophet_models.pkl'}")
print(f"  - {OUT_DIR / 'prophet_forecast.csv'}")
print(f"  - {OUT_DIR / 'prophet_forecast_future.csv'}")
print(f"  - {OUT_DIR / 'prophet_components.png'}")
print(f"  - {OUT_DIR / 'prophet_report.md'}")
