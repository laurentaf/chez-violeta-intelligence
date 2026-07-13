"""Inspect forecast output columns and holiday impact."""
import pandas as pd

fc = pd.read_csv('artifacts/data/prophet_forecast.csv')
print("Colunas:", list(fc.columns))
print()
print(fc.head(2).to_string())

# Check holiday cols
holiday_cols = [c for c in fc.columns if 'holiday' in c.lower()]
print("\nHoliday cols:", holiday_cols)

# Check yearly
print("\n--- UNDERWARE yearly stats ---")
cat = fc[fc['categoria'] == 'UNDERWARE']
if 'yearly' in fc.columns:
    print(cat['yearly'].describe())

# Check holidays
if 'holidays' in fc.columns:
    h = cat[cat['holidays'] != 0].dropna(subset=['holidays'])
    print(f"\nNon-zero holidays: {len(h)}")
    if len(h) > 0:
        print(h[['ds','holidays']].head(10).to_string())
    else:
        # Show any non-zero holiday values
        print("All zero - checking max abs: ", cat['holidays'].abs().max())

# Check all extra regressor columns
extra = [c for c in fc.columns if c not in ['ds','yhat','yhat_lower','yhat_upper','categoria']]
print("\nExtra columns beyond standard:", extra[:10])
