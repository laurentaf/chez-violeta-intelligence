# Sales Generator — Synthetic ARIMA Generator for Chez Violeta

## Overview

Gera dados sintéticos de vendas no varejo usando SARIMA (Seasonal ARIMA)
com sazonalidade aprendida de dados reais do Chez Violeta Gold Layer
(`chez_gold.duckdb`). O script extrai padrões mensais, semanais e de
preços do banco real, ajusta um SARIMA por categoria de produto, e
gera N dias de vendas sintéticas.

## Methodology

### 1. Pattern Extraction (from DuckDB Gold Layer)

The script queries three gold-layer tables:

| Table | Purpose |
|-------|---------|
| `gold.fato_vendas` | Raw sales transactions (10.4K rows, 2017-11 to 2020-05) |
| `gold.dim_tempo` | Date dimension with day-of-week, month, year attributes |
| `gold.dim_produto` | Product dimension with category classification |

**Extracted patterns per category** (8 categories + NULL group):

- **Monthly volume**: quantity sold and total revenue per month
- **Price distribution**: mean, median, std dev of unit price
- **Day-of-week weights**: relative frequency of sales by day (e.g., Saturday peaks)
- **Month-of-year seasonality**: average frequency and quantity per month

### 2. SARIMA Model per Category

For each product category with sufficient data, a **Seasonal ARIMA (SARIMA)** model is fit:

```
SARIMA(p,d,q)(P,D,Q)[12] — where 12 = monthly seasonality
```

- **p,d,q**: non-seasonal ARIMA order (auto-detected via AIC grid search)
- **P,D,Q**: seasonal components capturing month-over-month patterns
- **Trend extraction**: the model decomposes sales into trend + seasonal + residual
- **Residual variance**: used to scale synthetic noise

Categories with sparse data (< 12 monthly observations) use a **simplified
seasonal average + noise** approach instead of full SARIMA.

### 3. Synthetic Generation

Generation follows this process for each simulated day:

```
for each day d in [0, N_days):
    for each category c:
        1. Base monthly volume   = SARIMA_predict(c, year_month(d))
        2. Day-of-week multiplier = dw_weight(c, day_of_week(d))
        3. Temperature modifier   = temp_effect(c, temperature(d))
        4. Daily volume          = base * dw_mult * temp_mod + noise
        5. Unit price            = sample from price_distribution(c)
        6. Write row: data, categoria, qtd_vendas, valor_total, temperatura
```

### 4. Temperature Integration

Temperature modulates demand for weather-sensitive categories:

| Category | Sensitivity | Behavior |
|----------|-------------|----------|
| `MODA PRAIA` | High | ↑ sales when temp > 25°C |
| `VESTUARIO` | Medium | ↑ heavy clothing when < 18°C, ↑ light when > 25°C |
| `FITNESS` | Low | Slight boost in mild weather (18-28°C) |
| Others | None | No temperature modulation |

Temperature source priority:
1. External CSV via `--temperature <path>`
2. Internal sinusoidal model (default): summer peak ~30°C, winter ~15°C

## Usage

### Installation

```bash
# Dependencies (auto-checked on run):
uv pip install statsmodels pandas numpy requests
```

### Basic Generation

```bash
python sales-generator.py --days 365 --output vendas_sinteticas.csv
```

### With External Temperature Data

```bash
python sales-generator.py --days 365 \
    --output vendas_sinteticas.csv \
    --temperature temp_data.csv
```

**Temperature CSV format** (required columns):

```csv
data,temperatura
2024-01-01,28.5
2024-01-02,30.1
...
```

### Learning from Live Database

```bash
python sales-generator.py --learn --db-path "F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
```

This saves learned SARIMA parameters to `params.json` (auto-loaded on subsequent runs).

### Full CLI Reference

```
usage: sales-generator.py [-h] [--days DAYS] [--output OUTPUT]
                          [--temperature TEMPERATURE] [--learn]
                          [--db-path DB_PATH] [--params PARAMS]
                          [--seed SEED] [--verbose]

Generate synthetic sales data using SARIMA.

options:
  --days DAYS           Number of days to generate (default: 365)
  --output OUTPUT       Output CSV path (default: vendas_sinteticas.csv)
  --temperature TEMP    External temperature CSV (optional)
  --learn               Force re-learn patterns from DuckDB
  --db-path DB_PATH     DuckDB gold layer path (default: auto-discovered)
  --params PARAMS       SARIMA params JSON file (default: params.json)
  --seed SEED           Random seed for reproducibility (default: 42)
  --verbose             Verbose output with progress
```

## Output Format

```csv
data,categoria,qtd_vendas,valor_total,temperatura
2024-01-01,UNDERWARE,12,287.88,28.5
2024-01-01,LINHA NOITE,3,179.97,28.5
...
```

## Limitations

1. **Sparse real data**: The gold layer has concentrated data (May 2020 = 52% of rows).
   SARIMA params are smoothed with priors for months with no real observations.
2. **No promotion/event modeling**: Discounts, holiday sales, and marketing
   campaigns are not explicitly modeled.
3. **No multi-product correlation**: Each category is generated independently
   — cross-category effects (e.g., beachwear + sandals) are not captured.
4. **Stationary assumption**: SARIMA assumes the underlying process is stationary
   after differencing. The real business may have growth trends not fully captured.
5. **Temperature is a linear modifier**: The actual relationship between
   temperature and demand may be nonlinear or have thresholds.
6. **No stock-out simulation**: The generator does not model inventory constraints.
7. **Synthetic data marker**: All generated data carries the synthetic flag
   and is intended for development/testing, not production decisions.

## Owner

Laurent Ferreira — Data Architect
