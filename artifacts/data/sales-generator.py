#!/usr/bin/env python3
"""
Chez Violeta — Gerador de Vendas Sintéticas ARIMA
==================================================
Gera dados sintéticos de vendas usando SARIMA com sazonalidade
aprendida de dados reais do Chez Violeta Gold Layer.

Uso:
    python sales-generator.py --days 365 --output vendas_sinteticas.csv
    python sales-generator.py --learn  # re-learn from DuckDB
    python sales-generator.py --temperature temp.csv --days 90

Dependências: pandas, numpy, statsmodels, requests
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning, module="statsmodels")

# ─── Version ────────────────────────────────────────────────────────────────
VERSION = "1.0.0"

# ─── Default Learned Parameters (from real DuckDB gold layer) ──────────────
# These are the encoded patterns extracted from the real Chez Violeta data.
# The script can also re-learn from the live DB via --learn.

DEFAULT_PARAMS: dict[str, Any] = {
    "meta": {
        "source": "chez_gold.duckdb (gold.fato_vendas + dim_tempo + dim_produto)",
        "extracted_at": "2026-07-08",
        "version": VERSION,
        "date_range": ["2017-11-21", "2020-05-28"],
        "total_rows": 10435,
    },
    "categories": {
        "UNDERWARE": {
            "monthly_base_avg": 580.0,
            "monthly_base_std": 250.0,
            "avg_unit_price": 22.97,
            "std_unit_price": 16.49,
            "med_unit_price": 15.99,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.15, 4: 0.17, 5: 0.16, 6: 0.27, 7: 0.01
            },
            "month_seasonality": {
                1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.3,
                6: 1.2, 7: 1.1, 8: 1.0, 9: 0.9, 10: 1.1,
                11: 1.3, 12: 1.1
            },
            "sarima_order": [1, 1, 1],
            "sarima_seasonal_order": [1, 1, 1, 12],
            "residual_std": 48.0,
            "temperature_sensitivity": "none",
        },
        "LINHA NOITE": {
            "monthly_base_avg": 320.0,
            "monthly_base_std": 130.0,
            "avg_unit_price": 53.81,
            "std_unit_price": 24.34,
            "med_unit_price": 59.99,
            "day_of_week_weights": {
                1: 0.11, 2: 0.14, 3: 0.16, 4: 0.17, 5: 0.16, 6: 0.25, 7: 0.01
            },
            "month_seasonality": {
                1: 0.7, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.1,
                6: 1.8, 7: 1.5, 8: 1.2, 9: 0.9, 10: 0.8,
                11: 1.2, 12: 1.4
            },
            "sarima_order": [1, 1, 1],
            "sarima_seasonal_order": [1, 1, 1, 12],
            "residual_std": 35.0,
            "temperature_sensitivity": "none",
        },
        "MODA PRAIA": {
            "monthly_base_avg": 180.0,
            "monthly_base_std": 120.0,
            "avg_unit_price": 54.74,
            "std_unit_price": 29.97,
            "med_unit_price": 49.90,
            "day_of_week_weights": {
                1: 0.09, 2: 0.13, 3: 0.15, 4: 0.18, 5: 0.17, 6: 0.27, 7: 0.01
            },
            "month_seasonality": {
                1: 1.8, 2: 2.0, 3: 1.5, 4: 1.0, 5: 0.6,
                6: 0.3, 7: 0.3, 8: 0.4, 9: 0.5, 10: 1.2,
                11: 1.5, 12: 1.9
            },
            "sarima_order": [1, 1, 1],
            "sarima_seasonal_order": [1, 1, 1, 12],
            "residual_std": 42.0,
            "temperature_sensitivity": "hot",
        },
        "VESTUARIO": {
            "monthly_base_avg": 160.0,
            "monthly_base_std": 80.0,
            "avg_unit_price": 61.65,
            "std_unit_price": 36.87,
            "med_unit_price": 59.99,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.16, 4: 0.17, 5: 0.16, 6: 0.26, 7: 0.01
            },
            "month_seasonality": {
                1: 0.8, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.1,
                6: 1.2, 7: 1.1, 8: 1.0, 9: 0.9, 10: 1.0,
                11: 1.1, 12: 1.0
            },
            "sarima_order": [1, 1, 1],
            "sarima_seasonal_order": [1, 1, 1, 12],
            "residual_std": 28.0,
            "temperature_sensitivity": "dual",
        },
        "FITNESS": {
            "monthly_base_avg": 12.0,
            "monthly_base_std": 8.0,
            "avg_unit_price": 39.22,
            "std_unit_price": 11.72,
            "med_unit_price": 39.90,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.15, 4: 0.18, 5: 0.17, 6: 0.25, 7: 0.01
            },
            "month_seasonality": {
                1: 0.8, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2,
                6: 1.3, 7: 1.2, 8: 1.1, 9: 1.0, 10: 0.9,
                11: 0.8, 12: 0.7
            },
            "sarima_order": [1, 0, 0],
            "sarima_seasonal_order": [0, 0, 0, 12],
            "residual_std": 4.0,
            "temperature_sensitivity": "mild",
        },
        "EROTICA": {
            "monthly_base_avg": 10.0,
            "monthly_base_std": 7.0,
            "avg_unit_price": 28.76,
            "std_unit_price": 25.60,
            "med_unit_price": 15.90,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.15, 4: 0.18, 5: 0.17, 6: 0.25, 7: 0.01
            },
            "month_seasonality": {
                1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.1,
                6: 1.0, 7: 1.0, 8: 1.0, 9: 0.9, 10: 1.0,
                11: 1.1, 12: 1.1
            },
            "sarima_order": [1, 0, 0],
            "sarima_seasonal_order": [0, 0, 0, 12],
            "residual_std": 3.5,
            "temperature_sensitivity": "none",
        },
        "BIJU / JOIAS": {
            "monthly_base_avg": 6.0,
            "monthly_base_std": 5.0,
            "avg_unit_price": 8.45,
            "std_unit_price": 2.19,
            "med_unit_price": 7.99,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.15, 4: 0.18, 5: 0.17, 6: 0.25, 7: 0.01
            },
            "month_seasonality": {
                1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.2,
                6: 1.0, 7: 1.0, 8: 1.0, 9: 0.9, 10: 1.0,
                11: 0.9, 12: 1.1
            },
            "sarima_order": [1, 0, 0],
            "sarima_seasonal_order": [0, 0, 0, 12],
            "residual_std": 2.5,
            "temperature_sensitivity": "none",
        },
        "ACESSORIOS": {
            "monthly_base_avg": 2.0,
            "monthly_base_std": 1.5,
            "avg_unit_price": 5.90,
            "std_unit_price": 0.00,
            "med_unit_price": 5.90,
            "day_of_week_weights": {
                1: 0.10, 2: 0.14, 3: 0.15, 4: 0.18, 5: 0.17, 6: 0.25, 7: 0.01
            },
            "month_seasonality": {
                1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.1,
                6: 1.1, 7: 1.0, 8: 1.0, 9: 0.9, 10: 1.1,
                11: 1.0, 12: 1.0
            },
            "sarima_order": [0, 0, 0],
            "sarima_seasonal_order": [0, 0, 0, 12],
            "residual_std": 1.0,
            "temperature_sensitivity": "none",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Core Generation Engine
# ═══════════════════════════════════════════════════════════════════════════

def _temperature_sinusoidal(d: date, base_lat: float = -23.5) -> float:
    """Generate synthetic temperature for a given date using a sinusoidal model.
    
    Uses a simplified Brazilian Southeast climate model:
    - Summer (Dec-Feb): peak ~30°C
    - Winter (Jun-Aug): trough ~15°C
    - Spring/Autumn: transitional
    
    Args:
        d: Target date
        base_lat: Reference latitude (default: São Paulo ~ -23.5)
    
    Returns:
        Temperature in °C
    """
    day_of_year = d.timetuple().tm_yday
    # Peak on Jan 15 (day 15), trough on Jul 15 (day 196)
    amplitude = 7.5  # ±7.5°C around mean
    mean_temp = 22.5  # base mean temperature
    rad = 2 * np.pi * (day_of_year - 15) / 365.0
    temp = mean_temp + amplitude * np.cos(rad + np.pi)  # flip: cos peaks at 0
    # Add small random perturbation (±1°C)
    noise = np.random.normal(0, 0.5)
    return round(float(temp + noise), 1)


def _load_temperature(temperature_path: str | None, days: int,
                      start_date: date) -> dict[date, float]:
    """Load or generate temperature data.
    
    Args:
        temperature_path: Optional path to external CSV
        days: Number of days
        start_date: Start date for generation
    
    Returns:
        Dict mapping date → temperature
    """
    result: dict[date, float] = {}
    
    if temperature_path:
        path = Path(temperature_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Temperature file not found: {temperature_path}"
            )
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    d = datetime.strptime(row["data"].strip(), "%Y-%m-%d").date()
                    temp = float(row["temperatura"].strip())
                    result[d] = temp
                except (ValueError, KeyError) as e:
                    print(f"  [warn] Skipping bad row in temperature CSV: {e}")
    
    # Fill missing dates with sinusoidal model
    for i in range(days):
        d = start_date + timedelta(days=i)
        if d not in result:
            result[d] = _temperature_sinusoidal(d)
    
    return result


def _temperature_modifier(cat_params: dict[str, Any],
                          temperature: float) -> float:
    """Compute temperature-based demand modifier for a category.
    
    Args:
        cat_params: Category parameters dict
        temperature: Current temperature in °C
    
    Returns:
        Multiplier (1.0 = no effect)
    """
    sensitivity = cat_params.get("temperature_sensitivity", "none")
    
    if sensitivity == "none":
        return 1.0
    elif sensitivity == "hot":
        # MODA PRAIA: sells more when hot
        if temperature >= 28:
            return np.random.uniform(1.3, 1.8)
        elif temperature >= 25:
            return np.random.uniform(1.1, 1.4)
        elif temperature <= 20:
            return np.random.uniform(0.3, 0.7)
        else:
            return 1.0
    elif sensitivity == "dual":
        # VESTUARIO: cold = heavy clothing, hot = light clothing, both sell
        if temperature <= 16:
            return np.random.uniform(1.1, 1.4)
        elif temperature >= 30:
            return np.random.uniform(1.0, 1.3)
        elif 18 <= temperature <= 25:
            return np.random.uniform(0.6, 0.9)
        else:
            return 1.0
    elif sensitivity == "mild":
        # FITNESS: slight boost in pleasant weather
        if 18 <= temperature <= 28:
            return np.random.uniform(1.05, 1.2)
        else:
            return 0.85
    else:
        return 1.0


def _sample_price(cat_params: dict[str, Any], rng: np.random.Generator) -> float:
    """Sample a unit price from a category's price distribution.
    
    Uses a truncated normal mixture to match observed real distribution.
    
    Args:
        cat_params: Category parameters dict
        rng: NumPy random generator
    
    Returns:
        Unit price
    """
    avg = cat_params["avg_unit_price"]
    std = cat_params["std_unit_price"]
    med = cat_params.get("med_unit_price", avg)
    
    if std < 0.01:
        return round(avg, 2)
    
    # Use log-normal for right-skewed price distributions
    mu = np.log(med)
    sigma = np.sqrt(np.log(1 + (std / med) ** 2)) if med > 0 else 0.3
    
    price = float(rng.lognormal(mu, max(sigma, 0.1)))
    # Clip to reasonable range
    return round(max(1.0, min(price, avg + 3 * std)), 2)


def _seasonal_multiplier(cat_params: dict[str, Any], month: int) -> float:
    """Get the seasonal multiplier for a given month.
    
    Args:
        cat_params: Category parameters dict
        month: Month number (1-12)
    
    Returns:
        Multiplier centered around 1.0
    """
    seas = cat_params.get("month_seasonality", {})
    return seas.get(month, 1.0)


def _day_of_week_weight(cat_params: dict[str, Any], dow: int) -> float:
    """Get the day-of-week weight for a given day.
    
    Args:
        cat_params: Category parameters dict
        dow: Day of week (1=Monday, 7=Sunday)
    
    Returns:
        Relative weight
    """
    weights = cat_params.get("day_of_week_weights", {})
    return weights.get(dow, 0.14)


def generate_sales(
    params: dict[str, Any],
    days: int = 365,
    start_date: date | None = None,
    temperature_data: dict[date, float] | None = None,
    seed: int = 42,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Generate synthetic sales data.
    
    Args:
        params: Full parameters dict (DEFAULT_PARAMS or learned)
        days: Number of days to generate
        start_date: Start date (default: today)
        temperature_data: Dict of date → temperature
        seed: Random seed
        verbose: Print progress
    
    Returns:
        List of dicts with keys: data, categoria, qtd_vendas, valor_total, temperatura
    """
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    
    if start_date is None:
        start_date = date.today()
    
    if temperature_data is None:
        temperature_data = _load_temperature(None, days, start_date)
    
    categories = params.get("categories", {})
    # Filter out any category with no params
    active_categories: dict[str, dict] = {}
    for cat_name, cat_params in categories.items():
        if cat_params.get("monthly_base_avg", 0) > 0:
            active_categories[cat_name] = cat_params
    
    if not active_categories:
        raise ValueError("No active categories found in params")
    
    rows: list[dict[str, Any]] = []
    
    if verbose:
        print(f"  Generating {days} days x {len(active_categories)} categories...")
        print(f"  Date range: {start_date} -> {start_date + timedelta(days=days - 1)}")
    
    for day_offset in range(days):
        d = start_date + timedelta(days=day_offset)
        month = d.month
        dow = d.isoweekday()  # 1=Monday, 7=Sunday
        temp = temperature_data.get(d, _temperature_sinusoidal(d))
        
        for cat_name, cat_params in active_categories.items():
            # 1. Base monthly volume (with ARIMA-like auto-regressive component)
            base_avg = cat_params["monthly_base_avg"]
            base_std = cat_params["monthly_base_std"]
            resid_std = cat_params.get("residual_std", base_std * 0.15)
            
            # Monthly base: seasonal average + autoregressive noise
            seas_mult = _seasonal_multiplier(cat_params, month)
            monthly_volume = base_avg * seas_mult
            
            # Add auto-regressive noise (SARIMA-like residual)
            # Use a simple AR(1) approximation
            if day_offset == 0:
                ar_component = 0.0
            else:
                phi = cat_params.get("sarima_order", [1, 0, 0])[0] * 0.3
                prev_noise = cat_params.get("_last_noise", 0.0)
                ar_component = phi * prev_noise
            
            noise = float(rng.normal(0, resid_std))
            cat_params["_last_noise"] = noise
            
            daily_base = monthly_volume / 30.0  # spread over 30 days
            daily_volume = daily_base + ar_component + (noise * 0.3)
            
            # 2. Day-of-week multiplier
            dw_mult = _day_of_week_weight(cat_params, dow)
            
            # Normalize DOW weights to not inflate overall volume
            # (average weight ≈ 0.14 per day, so 7 * 0.14 ≈ 1.0)
            dw_mult_normalized = dw_mult / 0.14
            
            # 3. Temperature modifier
            temp_mod = _temperature_modifier(cat_params, temp)
            
            # 4. Final quantity
            raw_qty = daily_volume * dw_mult_normalized * temp_mod
            qtd = max(0, int(round(raw_qty)))
            
            if qtd <= 0:
                # Skip zero-quantity rows (rare, but possible in slow categories)
                if rng.random() > 0.3:
                    continue
                qtd = 1
            
            # 5. Price
            unit_price = _sample_price(cat_params, rng)
            valor_total = round(qtd * unit_price, 2)
            
            rows.append({
                "data": d.isoformat(),
                "categoria": cat_name,
                "qtd_vendas": qtd,
                "valor_total": valor_total,
                "temperatura": round(temp, 1),
            })
        
        if verbose and day_offset > 0 and day_offset % 90 == 0:
            print(f"    ... day {day_offset}/{days} ({rows[-1]['data']})")
    
    if verbose:
        print(f"  Generated {len(rows)} rows total.")
    
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Learning from Live DuckDB
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_statsmodels() -> None:
    """Check that statsmodels is available (needed for learning mode)."""
    try:
        import statsmodels  # noqa: F401
    except ImportError:
        print("  [INFO] statsmodels nao encontrado. Instalando...")
        import subprocess
        result = subprocess.run(
            ["uv", "pip", "install", "statsmodels", "--system"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(
                "  [ERROR] Nao foi possivel instalar statsmodels.\n"
                "         Tente manualmente:  uv pip install statsmodels --system\n"
                "         Ou use os parametros padrao (sem --learn)."
            )
            sys.exit(1)
        print("  [OK] statsmodels instalado.")
        import statsmodels  # noqa: F401


def _check_duckdb() -> tuple[Any, Any]:
    """Check DuckDB connectivity and return connection + execute function."""
    try:
        import duckdb  # noqa: F401
    except ImportError:
        print("  [INFO] duckdb nao encontrado. Instalando...")
        import subprocess
        result = subprocess.run(
            ["uv", "pip", "install", "duckdb", "--system"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(
                "  [ERROR] Nao foi possivel instalar duckdb.\n"
                "         Tente manualmente:  uv pip install duckdb --system"
            )
            sys.exit(1)
        print("  [OK] duckdb instalado.")
        import duckdb  # noqa: F401
    
    # Try to load from latade library first, or use raw duckdb
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "latade"))
        from src.tools.database import execute_query  # type: ignore
        return duckdb, execute_query
    except ImportError:
        pass
    
    return duckdb, None


def learn_from_duckdb(db_path: str, verbose: bool = False) -> dict[str, Any]:
    """Learn patterns from the Chez Violeta Gold layer DuckDB.
    
    Connects to the database, extracts monthly volumes, price distributions,
    day-of-week patterns, month seasonality, and fits SARIMA models per category.
    
    Args:
        db_path: Path to chez_gold.duckdb
        verbose: Print progress
    
    Returns:
        Parameters dict suitable for generate_sales()
    """
    _ensure_statsmodels()
    import statsmodels.api as sm  # noqa: F811
    
    duckdb_mod, exec_fn = _check_duckdb()
    
    if verbose:
        print(f"  Connecting to: {db_path}")
    
    con = duckdb_mod.connect(db_path, read_only=True)
    
    try:
        # ── Extract monthly data per category ─────────────────
        if verbose:
            print("  Extracting monthly sales per category...")
        
        monthly_raw = con.execute("""
            SELECT
                t.num_ano,
                t.num_mes_ano,
                p.des_categoria,
                CAST(SUM(f.qtd_pecas) AS FLOAT) as total_qtd,
                CAST(SUM(f.val_venda_liquida) AS FLOAT) as total_valor,
                COUNT(*) as num_vendas
            FROM gold.fato_vendas f
            JOIN gold.dim_tempo t ON f.id_data = t.id_data
            JOIN gold.dim_produto p ON f.id_produto = p.id_produto
            WHERE p.des_categoria IS NOT NULL
            GROUP BY t.num_ano, t.num_mes_ano, p.des_categoria
            ORDER BY p.des_categoria, t.num_ano, t.num_mes_ano
        """).fetchall()
        
        # ── Categories list ──────────────────────────────────
        categories_raw = con.execute("""
            SELECT DISTINCT des_categoria
            FROM gold.dim_produto
            WHERE des_categoria IS NOT NULL
            ORDER BY des_categoria
        """).fetchall()
        category_names = [r[0] for r in categories_raw]
        
        if verbose:
            print(f"  Found {len(category_names)} categories: {category_names}")
        
        # ── Day-of-week patterns ────────────────────────────
        if verbose:
            print("  Extracting day-of-week patterns...")
        
        dow_raw = con.execute("""
            SELECT
                t.num_dia_semana,
                COUNT(*) as num_vendas
            FROM gold.fato_vendas f
            JOIN gold.dim_tempo t ON f.id_data = t.id_data
            GROUP BY t.num_dia_semana
            ORDER BY t.num_dia_semana
        """).fetchall()
        
        total_vendas = sum(r[1] for r in dow_raw)
        dow_weights: dict[int, float] = {}
        for r in dow_raw:
            dow_weights[int(r[0])] = float(r[1]) / total_vendas if total_vendas > 0 else 0.14
        
        # ── Price stats per category ────────────────────────
        if verbose:
            print("  Extracting price distributions...")
        
        price_raw = con.execute("""
            SELECT
                p.des_categoria,
                COUNT(*) as num_vendas,
                AVG(CAST(f.val_venda_liquida / NULLIF(f.qtd_pecas, 0) AS FLOAT)) as avg_price,
                STDDEV(CAST(f.val_venda_liquida / NULLIF(f.qtd_pecas, 0) AS FLOAT)) as std_price,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.val_venda_liquida / NULLIF(f.qtd_pecas, 0)) as med_price
            FROM gold.fato_vendas f
            JOIN gold.dim_produto p ON f.id_produto = p.id_produto
            WHERE f.qtd_pecas > 0 AND p.des_categoria IS NOT NULL
            GROUP BY p.des_categoria
        """).fetchall()
        
        price_by_cat: dict[str, dict] = {}
        for r in price_raw:
            price_by_cat[str(r[0])] = {
                "avg_unit_price": float(r[2]) if r[2] else 20.0,
                "std_unit_price": float(r[3]) if r[3] else 10.0,
                "med_unit_price": float(r[4]) if r[4] else 15.0,
            }
        
        # ── Build per-category parameters ─────────────────────
        if verbose:
            print("  Building SARIMA models per category...")
        
        # Organize monthly data by category
        monthly_by_cat: dict[str, list[tuple[int, int, float, float, int]]] = {
            c: [] for c in category_names
        }
        for r in monthly_raw:
            cat = str(r[2])
            if cat in monthly_by_cat:
                monthly_by_cat[cat].append((
                    int(r[0]), int(r[1]), float(r[3]), float(r[4]), int(r[5])
                ))
        
        categories: dict[str, dict] = {}
        
        for cat_name in category_names:
            cat_data = monthly_by_cat.get(cat_name, [])
            prices = price_by_cat.get(cat_name, {})
            
            if not cat_data:
                if verbose:
                    print(f"    {cat_name}: no data, skipping")
                continue
            
            # Monthly vols
            monthly_vols = [r[2] for r in cat_data]
            avg_vol = float(np.mean(monthly_vols)) if monthly_vols else 10.0
            std_vol = float(np.std(monthly_vols)) if len(monthly_vols) > 1 else avg_vol * 0.3
            
            # Month seasonality: compute per-month average
            month_vals: dict[int, list[float]] = {m: [] for m in range(1, 13)}
            for r in cat_data:
                month_vals[r[1]].append(r[2])
            
            overall_avg = avg_vol
            month_seas: dict[int, float] = {}
            for m in range(1, 13):
                vals = month_vals[m]
                if vals:
                    month_seas[m] = float(np.mean(vals)) / max(overall_avg, 1.0)
                else:
                    month_seas[m] = 1.0
            
            # ── SARIMA fitting ──
            sarima_order = [1, 1, 1]
            sarima_seasonal = [1, 1, 1, 12]
            resid_std = max(std_vol * 0.15, 1.0)
            
            if len(monthly_vols) >= 12:
                try:
                    # Build time series
                    # Sort by (year, month) and create continuous index
                    cat_data_sorted = sorted(cat_data, key=lambda x: (x[0], x[1]))
                    
                    # Create a full monthly grid
                    if cat_data_sorted:
                        min_ym = cat_data_sorted[0][0] * 100 + cat_data_sorted[0][1]
                        max_ym = cat_data_sorted[-1][0] * 100 + cat_data_sorted[-1][1]
                        
                        ts_data = []
                        for ym in range(min_ym, max_ym + 1):
                            year = ym // 100
                            month_num = ym % 100
                            if month_num == 0:
                                year -= 1
                                month_num = 12
                            elif month_num > 12:
                                year += 1
                                month_num = 1
                            
                            matched = [v[2] for v in cat_data_sorted
                                       if v[0] == year and v[1] == month_num]
                            ts_data.append(matched[0] if matched else 0.0)
                        
                        if len(ts_data) >= 12 and max(ts_data) > 0:
                            # Try fitting SARIMA
                            try:
                                model = sm.tsa.statespace.SARIMAX(
                                    ts_data,
                                    order=(1, 1, 1),
                                    seasonal_order=(1, 1, 1, 12),
                                    enforce_stationarity=False,
                                    enforce_invertibility=False,
                                )
                                results = model.fit(disp=False, maxiter=200)
                                resid = results.resid
                                resid_std = max(float(np.std(resid)), resid_std * 0.5)
                                sarima_order = [1, 1, 1]
                                sarima_seasonal = [1, 1, 1, 12]
                                
                                if verbose:
                                    aic = results.aic if hasattr(results, 'aic') else 'N/A'
                                    print(f"    {cat_name}: SARIMA fitted, resid_std={resid_std:.2f}, AIC={aic}")
                            except Exception as e:
                                if verbose:
                                    print(f"    {cat_name}: SARIMA failed ({e}), using seasonal averages")
                except Exception:
                    if verbose:
                        print(f"    {cat_name}: could not build time series, using defaults")
            
            # Determine temperature sensitivity
            temp_sensitivity = "none"
            cat_upper = cat_name.upper()
            if "PRAIA" in cat_upper:
                temp_sensitivity = "hot"
            elif "VESTUARIO" in cat_upper:
                temp_sensitivity = "dual"
            elif "FITNESS" in cat_upper:
                temp_sensitivity = "mild"
            
            categories[cat_name] = {
                "monthly_base_avg": round(avg_vol, 1),
                "monthly_base_std": round(std_vol, 1),
                **prices,
                "day_of_week_weights": dow_weights,
                "month_seasonality": {k: round(v, 2) for k, v in month_seas.items()},
                "sarima_order": sarima_order,
                "sarima_seasonal_order": sarima_seasonal,
                "residual_std": round(resid_std, 2),
                "temperature_sensitivity": temp_sensitivity,
            }
        
        # Get date range
        date_range = con.execute("""
            SELECT MIN(t.dat_dia), MAX(t.dat_dia)
            FROM gold.fato_vendas f
            JOIN gold.dim_tempo t ON f.id_data = t.id_data
        """).fetchone()
        
        total_rows = con.execute("SELECT COUNT(*) FROM gold.fato_vendas").fetchone()[0]
        
        return {
            "meta": {
                "source": db_path,
                "extracted_at": datetime.now().isoformat(),
                "version": VERSION,
                "date_range": [
                    str(date_range[0]) if date_range[0] else "",
                    str(date_range[1]) if date_range[1] else "",
                ],
                "total_rows": int(total_rows) if total_rows else 0,
            },
            "categories": categories,
        }
    
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Gerador de Vendas Sinteticas ARIMA - Chez Violeta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python sales-generator.py --days 365 --output vendas_sinteticas.csv
  python sales-generator.py --learn --db-path chez_gold.duckdb
  python sales-generator.py --temperature temp.csv --days 90
        """.replace("Exemplos:", "Exemplos:"),
    )
    parser.add_argument(
        "--days", type=int, default=365,
        help="Numero de dias para gerar (default: 365)",
    )
    parser.add_argument(
        "--output", type=str, default="vendas_sinteticas.csv",
        help="Caminho do CSV de saida (default: vendas_sinteticas.csv)",
    )
    parser.add_argument(
        "--temperature", type=str, default=None,
        help="CSV opcional com dados de temperatura (colunas: data, temperatura)",
    )
    parser.add_argument(
        "--learn", action="store_true",
        help="Re-aprender padroes do DuckDB gold layer",
    )
    parser.add_argument(
        "--db-path", type=str,
        default="F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb",
        help="Caminho do DuckDB gold layer (default: auto-detect)",
    )
    parser.add_argument(
        "--params", type=str, default=None,
        help="Arquivo JSON de parametros SARIMA (default: params.json)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Seed aleatorio para reprodutibilidade (default: 42)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Output verboso com progresso",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = parse_args(argv)
    
    print(f"[Chez Violeta] Gerador de Vendas Sinteticas v{VERSION}")
    print(f"  Dias: {args.days}  |  Output: {args.output}")
    print()
    
    # ── Determine parameters ──────────────────────────────────
    params: dict[str, Any] | None = None
    params_path = args.params or "params.json"
    
    if args.learn:
        # Re-learn from DuckDB
        print("[LEARN] Extraindo padroes do DuckDB...")
        params = learn_from_duckdb(args.db_path, verbose=args.verbose)
        
        # Save params
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2, ensure_ascii=False, default=str)
        print(f"  [OK] Parametros salvos em: {params_path}")
        
        # Also save as default params backup
        backup_path = params_path.replace(".json", "_learned.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2, ensure_ascii=False, default=str)
        print(f"  [OK] Backup salvo em: {backup_path}")
    else:
        # Try to load from file, fall back to built-in defaults
        p_path = Path(params_path)
        if p_path.exists():
            if args.verbose:
                print(f"  [PARAMS] Carregando parametros de: {params_path}")
            with open(p_path, "r", encoding="utf-8") as f:
                params = json.load(f)
        else:
            if args.verbose:
                print("  [DEFAULT] Usando parametros padrao embutidos")
            params = DEFAULT_PARAMS
    
    if params is None:
        print("  [ERROR] Nenhum parametro disponivel. Use --learn ou forneca um arquivo .json.")
        sys.exit(1)
    
    # ── Load temperature ──────────────────────────────────────
    if args.verbose:
        print("  [TEMP] Carregando dados de temperatura...")
    
    try:
        start_date = date.today()
        temperature_data = _load_temperature(
            args.temperature, args.days, start_date
        )
    except FileNotFoundError as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)
    
    if args.verbose:
        temp_range = (min(temperature_data.values()), max(temperature_data.values()))
        print(f"  Temperatura: {temp_range[0]:.1f}C ~ {temp_range[1]:.1f}C")
    
    # ── Generate ──────────────────────────────────────────────
    print("  [GEN] Gerando dados sinteticos...")
    
    try:
        rows = generate_sales(
            params=params,
            days=args.days,
            start_date=start_date,
            temperature_data=temperature_data,
            seed=args.seed,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"  [ERROR] Erro na geracao: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # ── Write output ──────────────────────────────────────────
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "categoria", "qtd_vendas", "valor_total", "temperatura"])
        writer.writeheader()
        writer.writerows(rows)
    
    # Quick stats
    total_valor = sum(r["valor_total"] for r in rows)
    total_qtd = sum(r["qtd_vendas"] for r in rows)
    num_categorias = len(set(r["categoria"] for r in rows))
    
    print(f"  [OK] {len(rows)} linhas geradas em: {args.output}")
    print(f"       Categorias: {num_categorias}")
    print(f"       Total qtd: {total_qtd:,}")
    print(f"       Total valor: R$ {total_valor:,.2f}")
    print(f"       Media diaria: R$ {total_valor / max(args.days, 1):,.2f}")
    print()
    
    if args.learn:
        print("  [TIP] Na proxima execucao sem --learn, o script usara")
        print(f"        o arquivo '{params_path}' salvo automaticamente.")
    print("  [OK] Concluido!")


if __name__ == "__main__":
    main()
