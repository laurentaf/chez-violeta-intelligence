---
task_id: simulation-data-profile
status: blocked_on_mcp
error_class: database_library_unavailable
timestamp: 2026-07-08T00:00:00Z
---

# Simulation Data Profile — EXTRACTION BLOCKED

## Status

**BLOCKED** — latade MCP database library unavailable.

## Failure Details

- **Error:** `database library unavailable` (returned by all 7 queries)
- **Health check:** `database: False, wired: {database: false, bronze: false, silver: false, gold: false}`
- **DB path:** `F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb`
- **Root cause:** latade MCP server cannot load DuckDB library. Likely missing dependency or corrupted venv.

## Queries Attempted (all SELECT-only, all failed)

| # | Query | Purpose |
|---|-------|---------|
| 1 | Product profile by category | SKU count, volume, avg price/cost per category/line/collection |
| 2 | Supplier profile (lead time) | Order count, avg qty, avg value, date range per supplier |
| 3 | Current stock (last day) | Stock levels by category/line/collection |
| 4 | Sales velocity (90 days) | SKUs sold, total volume, avg per SKU, days with sales |
| 5 | Monthly seasonality | Sales by category × month |
| 6 | Substitute products (exchanges) | Exchange patterns: returned → substituted product |
| 7 | Purchase frequency regime | How often each SKU is repurchased (single/low/moderate/high) |

## Resolution Required

```
latade health falhou: rode `uv sync` em ../latade/ e reinicie o MCP
```

After latade is restored, re-run this task. All 7 queries are validated SELECT-only and ready to execute.

## Impact on Simulation Design

Without these profiles, the simulation engine cannot be parameterized with real data. The following design decisions depend on this data:

- **Reorder points** — need sales velocity (Q4) + current stock (Q3)
- **Safety stock** — need seasonality (Q5) + demand variability
- **Lead time estimation** — need supplier profile (Q2)
- **Substitute mapping** — need exchange patterns (Q6)
- **Category-level aggregation** — need product profile (Q1) + purchase frequency (Q7)
