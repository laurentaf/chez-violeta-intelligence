#!/usr/bin/env python3
"""Get Prophet 120-day totals per category"""
import duckdb

con = duckdb.connect('artifacts/data/chez_gold.duckdb')

# Get 120d prophet totals (2019-12-01 to 2020-03-29 = 120 days)
pf = con.execute("""
SELECT categoria, 
       COUNT(*) as days,
       ROUND(SUM(yhat), 2) as total_120d_yhat
FROM read_csv_auto('artifacts/data/prophet_forecast_future.csv') 
WHERE ds < '2020-03-30'  -- 120 days from 2019-12-01
GROUP BY categoria
ORDER BY categoria
""").fetchdf()
print("Prophet 120-day totals:")
print(pf.to_string())

print("\nGrand total:", pf['total_120d_yhat'].sum())

con.close()
