"""
Regenerate Prophet report with better holiday and seasonality info.
Uses forecast CSV columns directly for robustness.
"""
import pandas as pd

OUT = 'artifacts/data'
fc = pd.read_csv(f'{OUT}/prophet_forecast.csv', parse_dates=['ds'])
fc_future = pd.read_csv(f'{OUT}/prophet_forecast_future.csv', parse_dates=['ds'])

# Known holiday columns from Prophet BR holidays
holiday_cols_in_data = [
    "All Souls' Day", "Christmas Day", "Good Friday", 
    "Independence Day", "Our Lady of Aparecida",
    "Republic Proclamation Day", "Tiradentes' Day",
    "Universal Fraternization Day", "Worker's Day"
]

# Only those that actually exist
existing_holidays = [h for h in holiday_cols_in_data if h in fc.columns]

future_start = fc_future['ds'].min()
historical_end = fc[fc['ds'] < future_start]['ds'].max()

major_cats = ['UNDERWARE', 'MODA PRAIA', 'VESTUARIO', 'LINHA NOITE']

lines = []
lines.append("# Modelo de Previsao (Prophet)")
lines.append("")
lines.append("## Resumo")
lines.append("")
lines.append("| Metrica | Valor |")
lines.append("|---------|-------|")
lines.append("| Fonte | `fato_estoque_diario.qtd_venda` |")
lines.append(f"| Periodo historico | 2017-12-01 a {historical_end.strftime('%Y-%m-%d')} |")
lines.append("| Registros | 619,289 vendas (qtd_venda > 0) |")
lines.append("| Lojas | 11 |")
lines.append("| Categorias | 9 (agrupadas em 5 modelos) |")
lines.append("| Modelos treinados | 5 (1 por categoria) |")
lines.append("| Horizonte | 26 semanas (182 dias) |")
lines.append("| Feriados | BR (11 feriados nacionais) |")
lines.append("| Sazonalidade | Anual (multiplicativa) |")
lines.append("")

# Previsao por categoria
lines.append("## Previsao por Categoria (26 semanas)")
lines.append("")
lines.append("| Categoria | Previsao Total | Media Diaria | Pico Max | Data do Pico |")
lines.append("|-----------|---------------|--------------|----------|--------------|")
for cat in major_cats + ['OUTROS']:
    c = fc_future[fc_future['categoria'] == cat]
    if len(c) == 0:
        continue
    pk = c.loc[c['yhat'].idxmax()]
    lines.append(f"| {cat} | {c['yhat'].sum():>9,.0f} | {c['yhat'].mean():>8.1f} | {pk['yhat']:>5.0f} | {pk['ds'].strftime('%Y-%m-%d')} |")
lines.append("")

# Componentes sazonais
lines.append("## Componentes Sazonais")
lines.append("")

month_names = {1:'Janeiro', 2:'Fevereiro', 3:'Marco', 4:'Abril', 5:'Maio', 6:'Junho',
              7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

# Holiday name mapping for Portuguese display
holiday_names_pt = {
    "All Souls' Day": "Finados (02/11)",
    "Christmas Day": "Natal (25/12)",
    "Good Friday": "Sexta-Feira Santa",
    "Independence Day": "Independencia (07/09)",
    "Our Lady of Aparecida": "Nossa Sra Aparecida (12/10)",
    "Republic Proclamation Day": "Proclamacao Republica (15/11)",
    "Tiradentes' Day": "Tiradentes (21/04)",
    "Universal Fraternization Day": "Confraternizacao Universal (01/01)",
    "Worker's Day": "Dia do Trabalho (01/05)"
}

for cat in major_cats + ['OUTROS']:
    c = fc[fc['categoria'] == cat].copy()
    if len(c) == 0:
        continue
    
    lines.append(f"### {cat}")
    lines.append("")
    
    # Yearly seasonality - multiplicative factor
    if 'yearly' in c.columns:
        c['mes'] = pd.to_datetime(c['ds']).dt.month
        monthly = c.groupby('mes')['yearly'].mean()
        
        # Yearly is multiplicative: 1 + yearly = multiplier
        # So yearly = -0.1 means 0.9x baseline (10% below)
        # yearly = +0.3 means 1.3x baseline (30% above)
        
        lines.append("**Meses por impacto sazonal (vs media anual)**")
        for mes, val in monthly.sort_values(ascending=False).items():
            pct = val * 100  # convert to %
            sinal = "+" if val >= 0 else ""
            lines.append(f"- {month_names[mes]}: {sinal}{pct:.0f}%")
        lines.append("")
    
    # Holiday impact - total additive contribution
    if existing_holidays:
        holiday_totals = []
        for hname in existing_holidays:
            if hname in c.columns:
                total_impact = c[hname].sum()
                holiday_totals.append((hname, total_impact))
        
        holiday_totals.sort(key=lambda x: abs(x[1]), reverse=True)
        meaningful = [(h, t) for h, t in holiday_totals if abs(t) > 1]
        
        if meaningful:
            lines.append("**Feriados de maior impacto (unidades totais adicionadas no periodo)**")
            for hname, impact in meaningful:
                pt_name = holiday_names_pt.get(hname, hname)
                lines.append(f"- {pt_name}: {impact:+.0f}")
            lines.append("")

# Recomendacao de compra
lines.append("## Recomendacao de Compra (120 dias de cobertura)")
lines.append("")
lines.append("Considerando a sazonalidade, segue a quantidade estimada de venda para 120 dias por categoria:")
lines.append("")
lines.append("| Categoria | Previsao 120d (unid) | Estoque Recomendado (unid) |")
lines.append("|-----------|---------------------|--------------------------|")

total_rec = 0
for cat in major_cats + ['OUTROS']:
    cf = fc_future[fc_future['categoria'] == cat].head(120)
    if len(cf) == 0:
        continue
    pred_120 = cf['yhat'].sum()
    rec = int(pred_120 * 1.2)
    total_rec += rec
    lines.append(f"| {cat} | {pred_120:>10,.0f} | {rec:>10,} |")

lines.append(f"| **TOTAL** | | **{total_rec:,}** |")
lines.append("")
lines.append("*Estoque recomendado inclui margem de seguranca de 20% sobre a previsao.*")
lines.append("")

lines.append("## Graficos")
lines.append("")
lines.append("![Componentes Sazonais - Previsao vs Historico](prophet_components.png)")
lines.append("")

with open(f'{OUT}/prophet_report.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Report regenerated successfully!")
