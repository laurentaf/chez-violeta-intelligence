"""Explore the DuckDB gold schema to understand tables and columns."""
import duckdb
import pandas as pd

conn = duckdb.connect('artifacts/data/chez_gold.duckdb')

# List gold tables
tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='gold'").fetchdf()
print("=== GOLD TABLES ===")
print(tables.to_string())
print()

# For each table, show schema + row count
for t in tables['table_name']:
    print(f"\n=== gold.{t} ===")
    schema = conn.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='gold' AND table_name='{t}'").fetchdf()
    print(schema.to_string())
    cnt = conn.execute(f"SELECT COUNT(*) as n FROM gold.{t}").fetchdf()
    print(f"Rows: {cnt['n'][0]}")
    print(f"Sample:")
    sample = conn.execute(f"SELECT * FROM gold.{t} LIMIT 3").fetchdf()
    print(sample.to_string())
