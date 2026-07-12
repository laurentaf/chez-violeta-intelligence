#!/usr/bin/env python3
# ruff: noqa
# synthetic: true
# granted_by: orchestrator (user-directed simulation task)
# granted_at: 2026-07-08
# reason: Motor de simulacao gera vendas sinteticas como parte do modelo preditivo. Dados reais de estoque/catalogo extraidos do DuckDB gold layer.
"""
Chez Violeta -- Motor de Simulação de Estoque
=============================================
Simulação dia-a-dia partindo do estoque real do DuckDB gold layer.
Gera vendas sintéticas (Poisson com sazonalidade ARIMA-like),
simula recebimentos com lead time, e gera alertas de compra.

Uso:
    python simulation_engine.py --days 30 --output artifacts/simulation/output/
    python simulation_engine.py --days 90 --seed 123 --verbose

Dependências: pandas, numpy, duckdb, (opcional: matplotlib para dashboard)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
import warnings
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION = "1.0.0"

# --- Path defaults ----------------------------------------------------------
DEFAULT_DB_PATH = "F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "simulation_config.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"


# ???????????????????????????????????????????????????????????????????????????
# Data Classes
# ???????????????????????????????????????????????????????????????????????????

@dataclass
class Produto:
    """Produto ativo no estoque."""
    id_produto: int
    cod_artigo: str
    des_categoria: Optional[str]
    des_linha: Optional[str]
    des_colecao: Optional[str]
    des_status: Optional[str]
    cod_fornecedor: Optional[str]
    val_custo_inicial: float = 0.0
    preco_medio: float = 0.0
    qtd_estoque: int = 0
    regime: str = "fashion"
    last_sale_date: Optional[date] = None
    last_sale_qty: int = 0


@dataclass
class Sale:
    """Uma venda gerada na simulação."""
    id_produto: int
    qty: int
    day: date
    unit_price: float = 0.0
    total_value: float = 0.0
    categoria: str = ""


@dataclass
class PendingReceipt:
    """Pedido pendente de recebimento."""
    id_produto: int
    supplier: str
    quantity: int
    order_date: date
    expected_date: date
    actual_arrival: Optional[date] = None
    status: str = "pending"  # pending, tagging, received, delayed
    delay_days: int = 0
    on_time: bool = True
    tagging_until: Optional[date] = None
    regime: str = "fashion"
    category: str = ""


@dataclass
class GoodsReceipt:
    """Entrada de mercadoria processada."""
    id_produto: int
    supplier: str
    quantity: int
    receipt_date: date
    order_date: date
    expected_date: date
    on_time: bool
    delay_days: int
    tagging_days: int = 1


@dataclass
class PurchaseAlert:
    """Alerta de compra gerado."""
    id_produto: int
    categoria: str
    regime: str
    supplier: str
    coverage_days: float
    target_coverage: int
    quantity: int
    urgency: str
    unit_cost: float
    total_cost: float
    alert_date: date
    substitutes: list[dict] = field(default_factory=list)


@dataclass
class SlowMover:
    """Produto lento (sem venda por 60+ dias)."""
    id_produto: int
    categoria: str
    regime: str
    stock_qty: int
    days_without_sale: int
    suggested_discount: float
    last_sale_date: Optional[date] = None


@dataclass
class DaySnapshot:
    """Snapshot do estado em um dia."""
    date: date
    total_stock: int = 0
    total_sales_qty: int = 0
    total_sales_value: float = 0.0
    stockouts: int = 0
    receipts: int = 0
    alerts: int = 0
    slow_movers: int = 0
    category_stock: dict = field(default_factory=dict)
    category_sales: dict = field(default_factory=dict)


@dataclass
class SimulationState:
    """Estado completo da simulação."""
    products: dict[int, Produto]  # id_produto -> Produto
    stock: dict[int, int]  # id_produto -> qtd_estoque atual
    pending_receipts: list[PendingReceipt]
    sales_history: dict[int, list[tuple[date, int]]]  # id_produto -> [(date, qty)]
    category_products: dict[str, list[int]]  # categoria -> [id_produto]
    last_sale_dates: dict[int, date]  # id_produto -> last_sale_date
    temperature: dict[date, float]  # Temperatura para cada dia simulado
    seed: int


# ???????????????????????????????????????????????????????????????????????????
# Regime Classification
# ???????????????????????????????????????????????????????????????????????????

def classify_regime(produto: Produto) -> str:
    """
    Classifica produto em commodity, fashion ou seasonal.
    Baseado na Seção 5 do spec.
    """
    # Produtos com status diferente de ATIVO não devem ser repostos
    status = (produto.des_status or "").strip().upper()
    if status not in ("ATIVO", "ATIVO", "ATIVA", ""):
        return "inactive"

    cat = (produto.des_categoria or "").strip().upper()
    linha = (produto.des_linha or "").strip().upper()
    colecao = (produto.des_colecao or "").strip().upper()

    # Regra 1: Coleção CONTÍNUO ou SEMI-CONTINUO -> commodity
    if colecao in ("CONTINUO", "SEMI-CONTINUO", "CONTÍNUO", "SEMI-CONTÍNUO"):
        return "commodity"

    # Regra 2: VESTUARIO com coleção sazonal (VERÃO*/INVERNO*) -> fashion
    if cat == "VESTUARIO":
        if any(c in colecao for c in ("VERAO", "VERÃO", "INVERNO")):
            return "fashion"
        # VESTUARIO CONTINUO já tratado na regra 1
        return "fashion"

    # Regra 3: MODA PRAIA -> seasonal (com exceção BASICO -> commodity)
    if cat == "MODA PRAIA":
        return "commodity" if linha == "BASICO" else "seasonal"

    # Regra 4: LINHA NOITE -> seasonal (BASICO -> commodity)
    if cat == "LINHA NOITE":
        return "commodity" if linha == "BASICO" else "seasonal"

    # Regra 5: FITNESS -> commodity
    if cat == "FITNESS":
        return "commodity"

    # Regra 6: UNDERWARE -> commodity (categorias principais de commodity)
    if cat == "UNDERWARE":
        return "commodity"

    # Regra 7: BIJU / JOIAS -> fashion
    if cat in ("BIJU / JOIAS", "BIJU/JOIAS"):
        return "fashion"

    # Default
    return "fashion"


# ???????????????????????????????????????????????????????????????????????????
# Substitute Detection
# ???????????????????????????????????????????????????????????????????????????

def find_substitutes(
    produto: Produto,
    all_products: list[Produto],
    stock: dict[int, int],
    max_results: int = 5,
) -> list[dict]:
    """
    Encontra produtos substitutos: mesma categoria + mesma linha + preço ±20%.
    Retorna produtos que ainda têm estoque > 0.
    """
    if produto.preco_medio <= 0:
        return []

    substitutes = []
    for p in all_products:
        if p.id_produto == produto.id_produto:
            continue
        if stock.get(p.id_produto, 0) <= 0:
            continue
        if (p.des_categoria == produto.des_categoria
                and p.des_linha == produto.des_linha
                and p.preco_medio > 0):
            price_diff = abs(p.preco_medio - produto.preco_medio) / produto.preco_medio
            if price_diff < 0.20:
                substitutes.append({
                    "id_produto": p.id_produto,
                    "cod_artigo": p.cod_artigo,
                    "categoria": p.des_categoria,
                    "linha": p.des_linha,
                    "preco": round(p.preco_medio, 2),
                    "estoque": stock.get(p.id_produto, 0),
                    "price_diff_pct": round(price_diff * 100, 1),
                })

    substitutes.sort(key=lambda x: x["price_diff_pct"])
    return substitutes[:max_results]


# ???????????????????????????????????????????????????????????????????????????
# Purchase Alert Generation
# ???????????????????????????????????????????????????????????????????????????

def generate_purchase_alert(
    produto: Produto,
    coverage_days: float,
    daily_demand: float,
    regime: str,
    regime_params: dict,
    alert_date: date,
    all_products: list[Produto],
    stock: dict[int, int],
) -> PurchaseAlert:
    """Gera alerta de compra com quantidade calculada."""
    params = regime_params[regime]
    target_coverage = params["coverage_days"]
    lead_time = params["lead_time_days"]
    order_multiple = params["order_multiple"]

    # Calcular quantidade
    days_to_cover = target_coverage - coverage_days + lead_time
    qty_needed = max(0, int(days_to_cover * daily_demand))
    qty_ordered = math.ceil(qty_needed / order_multiple) * order_multiple
    qty_ordered = max(qty_ordered, params["min_order_qty"])

    # Urgência
    if coverage_days <= 7:
        urgency = "CRITICAL"
    elif coverage_days <= 14:
        urgency = "HIGH"
    elif coverage_days <= 30:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    unit_cost = float(produto.val_custo_inicial or 0)
    total_cost = qty_ordered * unit_cost

    substitutes = find_substitutes(produto, all_products, stock)

    return PurchaseAlert(
        id_produto=produto.id_produto,
        categoria=produto.des_categoria or "",
        regime=regime,
        supplier=produto.cod_fornecedor or "N/A",
        coverage_days=round(coverage_days, 1),
        target_coverage=target_coverage,
        quantity=qty_ordered,
        urgency=urgency,
        unit_cost=round(unit_cost, 2),
        total_cost=round(total_cost, 2),
        alert_date=alert_date,
        substitutes=substitutes,
    )


def calculate_discount(days_without_sale: int, discount_tiers: list[dict]) -> float:
    """Calcula desconto sugerido baseado em dias sem venda."""
    discount = 0.0
    for tier in discount_tiers:
        if tier["min_days"] <= days_without_sale and (
            tier["max_days"] is None or days_without_sale < tier["max_days"]
        ):
            discount = max(discount, tier["discount"])
    return discount


# ???????????????????????????????????????????????????????????????????????????
# Data Extraction from DuckDB
# ???????????????????????????????????????????????????????????????????????????

def extract_data(db_path: str, verbose: bool = False) -> SimulationState:
    """
    Extrai dados do DuckDB gold layer e monta o estado inicial.
    Returns: SimulationState com produtos, estoque, fornecedores.
    """
    if verbose:
        print("? Conectando ao DuckDB...")

    import duckdb

    con = duckdb.connect(db_path)

    # 1. Última data com estoque
    max_stock_id = con.execute(
        "SELECT MAX(id_data) FROM gold.fato_estoque_diario"
    ).fetchone()[0]

    max_stock_date = con.execute(
        f"SELECT dat_dia FROM gold.dim_tempo WHERE id_data = {max_stock_id}"
    ).fetchone()[0]
    if isinstance(max_stock_date, str):
        max_stock_date = date.fromisoformat(max_stock_date)

    if verbose:
        print(f"? Último estoque disponível: {max_stock_date}")

    # 2. Produtos ativos
    if verbose:
        print("? Carregando produtos ativos...")
    products_df = con.execute("""
        SELECT p.id_produto, p.cod_artigo, p.des_categoria, p.des_linha,
               p.des_colecao, p.des_status, p.cod_fornecedor, p.val_custo_inicial
        FROM gold.dim_produto p
        WHERE p.dat_fim_vigencia IS NULL
          AND p.id_produto > 0
    """).fetchdf()

    # 3. Estoque atual (último dia)
    if verbose:
        print("? Carregando estoque atual...")
    stock_df = con.execute(f"""
        SELECT id_produto, qtd_estoque
        FROM gold.fato_estoque_diario
        WHERE id_data = {max_stock_id}
          AND qtd_estoque > 0
          AND id_produto > 0
    """).fetchdf()

    # 4. Preços médios por produto (das vendas)
    if verbose:
        print("? Carregando preços médios...")
    prices_df = con.execute("""
        SELECT id_produto, AVG(val_venda_liquida / NULLIF(qtd_pecas, 0)) as preco_medio
        FROM gold.fato_vendas
        WHERE id_produto > 0 AND qtd_pecas > 0
        GROUP BY id_produto
    """).fetchdf()

    # 5. Última venda por produto (para slow movers)
    if verbose:
        print("? Carregando histórico de vendas...")
    last_sale_df = con.execute("""
        SELECT fv.id_produto, MAX(t.dat_dia) as ultima_venda
        FROM gold.fato_vendas fv
        JOIN gold.dim_tempo t ON fv.id_data = t.id_data
        WHERE fv.id_produto > 0
        GROUP BY fv.id_produto
    """).fetchdf()

    # 6. Fornecedores - lead time histórico (aproximado por diferença entre pedidos)
    if verbose:
        print("? Carregando dados de fornecedores...")
    supplier_lt_df = con.execute("""
        SELECT f.id_fornecedor, d.cod_fornecedor,
               COUNT(DISTINCT f.num_pedido) as total_pedidos,
               AVG(f.qtd_pecas) as qtd_media
        FROM gold.fato_compras f
        JOIN gold.dim_fornecedor d ON f.id_fornecedor = d.id_fornecedor
        WHERE f.id_fornecedor > 0
        GROUP BY f.id_fornecedor, d.cod_fornecedor
    """).fetchdf()

    con.close()

    # --- Montar estado ------------------------------------------------

    # Merge products with stock
    product_stock = stock_df.set_index("id_produto")["qtd_estoque"].to_dict()
    product_prices = prices_df.set_index("id_produto")["preco_medio"].to_dict()
    last_sale_dates_raw = last_sale_df.set_index("id_produto")["ultima_venda"].to_dict()

    # Convert last sale dates
    last_sale_dates: dict[int, date] = {}
    for pid, d in last_sale_dates_raw.items():
        if isinstance(d, str):
            last_sale_dates[int(pid)] = date.fromisoformat(d)
        elif isinstance(d, datetime):
            last_sale_dates[int(pid)] = d.date()
        elif isinstance(d, date):
            last_sale_dates[int(pid)] = d

    products: dict[int, Produto] = {}
    stock: dict[int, int] = {}
    category_products: dict[str, list[int]] = {}

    for _, row in products_df.iterrows():
        pid = int(row["id_produto"])
        qtd = product_stock.get(pid, 0)
        if qtd <= 0:
            continue

        preco_raw = product_prices.get(pid, 0.0)
        preco = 0.0 if (preco_raw is None or (isinstance(preco_raw, float) and math.isnan(preco_raw))) else float(preco_raw)

        custo_raw = row.get("val_custo_inicial")
        custo = 0.0 if (custo_raw is None or (isinstance(custo_raw, float) and math.isnan(float(custo_raw)))) else float(custo_raw)

        prod = Produto(
            id_produto=pid,
            cod_artigo=str(row.get("cod_artigo", "") or ""),
            des_categoria=str(row.get("des_categoria") or "") if row.get("des_categoria") else None,
            des_linha=str(row.get("des_linha") or "") if row.get("des_linha") else None,
            des_colecao=str(row.get("des_colecao") or "") if row.get("des_colecao") else None,
            des_status=str(row.get("des_status") or "") if row.get("des_status") else None,
            cod_fornecedor=str(row.get("cod_fornecedor") or "") if row.get("cod_fornecedor") else None,
            val_custo_inicial=custo,
            preco_medio=preco,
            qtd_estoque=int(qtd),
            last_sale_date=last_sale_dates.get(pid),
        )
        prod.regime = classify_regime(prod)

        products[pid] = prod
        stock[pid] = int(qtd)

        cat = prod.des_categoria or "N/A"
        if cat not in category_products:
            category_products[cat] = []
        category_products[cat].append(pid)

    # Supplier lead time estimates
    supplier_lead_time: dict[str, dict[str, float]] = {}
    for _, row in supplier_lt_df.iterrows():
        code = str(row["cod_fornecedor"])
        num_orders = int(row["total_pedidos"])
        # Estimate lead time based on number of orders (proxy for reliability)
        if num_orders > 100:
            lt_mean, lt_std, compliance = 20, 5, 0.85
        elif num_orders > 50:
            lt_mean, lt_std, compliance = 25, 7, 0.78
        elif num_orders > 20:
            lt_mean, lt_std, compliance = 30, 10, 0.72
        else:
            lt_mean, lt_std, compliance = 35, 15, 0.65
        supplier_lead_time[code] = {
            "mean": lt_mean,
            "std": lt_std,
            "compliance": compliance,
            "total_orders": num_orders,
        }

    if verbose:
        total_prods = len(products)
        total_stock_units = sum(stock.values())
        print(f"   {total_prods} produtos carregados com {total_stock_units} unidades em estoque")
        regime_counts = {}
        for p in products.values():
            regime_counts[p.regime] = regime_counts.get(p.regime, 0) + 1
        for r, c in sorted(regime_counts.items()):
            print(f"   - {r}: {c} produtos")
        print(f"   {len(supplier_lead_time)} fornecedores com lead time estimado")

    state = SimulationState(
        products=products,
        stock=stock,
        pending_receipts=[],
        sales_history={pid: [] for pid in products},
        category_products=category_products,
        last_sale_dates=last_sale_dates,
        temperature={},
        seed=0,
    )
    state.supplier_lead_time = supplier_lead_time  # type: ignore
    state.max_stock_date = max_stock_date  # type: ignore

    return state


# ???????????????????????????????????????????????????????????????????????????
# Temperature Simulation
# ???????????????????????????????????????????????????????????????????????????

def generate_temperature(
    start_date: date,
    num_days: int,
    temp_by_month: dict,
    seed: int,
) -> dict[date, float]:
    """Gera temperatura diária simulada baseada no mês."""
    rng = np.random.default_rng(seed + 999)
    temperatures: dict[date, float] = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        month = d.month
        month_key = str(month)
        if month_key in temp_by_month:
            t_min = temp_by_month[month_key]["min"]
            t_max = temp_by_month[month_key]["max"]
        else:
            t_min, t_max = 20, 30
        temp = rng.uniform(t_min, t_max)
        temperatures[d] = round(temp, 1)
    return temperatures


# ???????????????????????????????????????????????????????????????????????????
# Core Simulation Logic
# ???????????????????????????????????????????????????????????????????????????

def calculate_velocity(
    produto: Produto,
    state: SimulationState,
    recent_days: int = 30,
) -> float:
    """Calcula a demanda diária média do produto (peças/dia)."""
    history = state.sales_history.get(produto.id_produto, [])
    if not history:
        return 0.0

    # Consider only recent sales
    cutoff = len(history)
    recent = history[-min(cutoff, recent_days):]
    if not recent:
        return 0.0

    total_qty = sum(q for _, q in recent)
    return total_qty / max(len(recent), 1)


def simulate_day(
    day: date,
    state: SimulationState,
    config: dict,
    all_product_list: list[Produto],
    discount_tiers: list[dict],
) -> DaySnapshot:
    """
    Simula um dia completo de operação.
    Retorna snapshot com vendas, recebimentos, alertas.
    """
    rng = np.random.default_rng(state.seed + day.toordinal())
    regime_params = config["regime_params"]
    sales_model = config["sales_model"]
    snapshot = DaySnapshot(date=day)

    # Temperature for this day
    temperature = state.temperature.get(day, 25.0)

    day_sales: list[Sale] = []
    day_stockouts: list[int] = []
    day_alerts: list[PurchaseAlert] = []
    day_receipts: list[GoodsReceipt] = []
    day_slow_movers: list[SlowMover] = []

    category_stock: dict[str, int] = {}
    category_sales_qty: dict[str, int] = {}
    category_sales_val: dict[str, float] = {}

    # -- 1. Generate Sales -----------------------------------------
    for pid, produto in list(state.products.items()):
        current_stock = state.stock.get(pid, 0)
        cat = produto.des_categoria or "N/A"
        regime = produto.regime

        # Track category stock
        category_stock[cat] = category_stock.get(cat, 0) + current_stock

        if current_stock <= 0:
            continue

        # Get sales parameters for this category
        sales_params = sales_model.get(cat)
        if sales_params is None:
            # Fallback to generic parameters
            base_rate = 0.3  # per 1000 units stock
            seasonal_factor = 1.0
            dow_factor = 1.0
            temp_sensitivity = 0.01
        else:
            base_rate = sales_params["base_daily_per_1000_stock"]
            seasonality = sales_params["seasonality"]
            seasonal_factor = seasonality[day.month - 1]
            dow = day.weekday()  # 0=Monday
            dow_factor = sales_params["day_of_week"][dow]
            temp_sensitivity = sales_params["temperature_sensitivity"]

        # Temperature effect
        temp_factor = 1.0 + (temperature - 25.0) * temp_sensitivity
        temp_factor = max(0.3, min(3.0, temp_factor))

        # Expected demand from this product (Poisson rate)
        # Scale by stock quantity / 1000
        stock_scale = max(1, current_stock) / 1000.0
        expected_rate = base_rate * stock_scale * seasonal_factor * dow_factor * temp_factor

        # Adding some random noise (ARIMA-like via residual)
        residual_noise = max(0, rng.poisson(expected_rate * 0.3))

        expected_demand = expected_rate + residual_noise * 0.1

        # Actual sales (Poisson + capped by stock)
        if expected_demand > 0:
            actual_sales = min(int(rng.poisson(max(0.01, expected_demand))), current_stock)
        else:
            actual_sales = 0

        if actual_sales > 0:
            state.stock[pid] = current_stock - actual_sales
            if produto.preco_medio and produto.preco_medio > 0:
                unit_price = produto.preco_medio
            elif produto.val_custo_inicial and produto.val_custo_inicial > 0:
                unit_price = produto.val_custo_inicial * 2.5
            else:
                unit_price = 29.99  # fallback default price
            sale = Sale(
                id_produto=pid,
                qty=actual_sales,
                day=day,
                unit_price=round(unit_price, 2),
                total_value=round(actual_sales * unit_price, 2),
                categoria=cat,
            )
            day_sales.append(sale)
            category_sales_qty[cat] = category_sales_qty.get(cat, 0) + actual_sales
            category_sales_val[cat] = category_sales_val.get(cat, 0) + sale.total_value

            # Track sale in history
            if pid not in state.sales_history:
                state.sales_history[pid] = []
            state.sales_history[pid].append((day, actual_sales))
            state.last_sale_dates[pid] = day
        else:
            # No sale today - check if this is a slow mover candidate
            last_sale = state.last_sale_dates.get(pid)
            if last_sale and current_stock > 0:
                days_without = (day - last_sale).days
                if days_without >= 60:
                    discount = calculate_discount(days_without, discount_tiers)
                    if discount > 0:
                        day_slow_movers.append(SlowMover(
                            id_produto=pid,
                            categoria=cat,
                            regime=regime,
                            stock_qty=current_stock,
                            days_without_sale=days_without,
                            suggested_discount=discount,
                            last_sale_date=last_sale,
                        ))

        # Detect stockout
        if state.stock.get(pid, 0) <= 0 < current_stock:
            day_stockouts.append(pid)

    # -- 2. Process Pending Receipts --------------------------------
    supplier_lt = getattr(state, "supplier_lead_time", {})

    # Phase A: pending -> tagging (goods physically arrive, start 10-day processing / etiquetagem)
    for receipt in state.pending_receipts:
        if receipt.status != "pending":
            continue

        # Check if expected arrival has been reached
        if day >= receipt.expected_date:
            # Simulate actual arrival (could be delayed)
            supplier_info = supplier_lt.get(receipt.supplier, {"std": 5, "mean": 20})
            lt_std = supplier_info.get("std", 5)

            # Generate delay using normal distribution
            delay = int(round(rng.normal(0, lt_std)))
            delay = max(0, delay)

            actual_arrival = receipt.expected_date + timedelta(days=delay)

            if actual_arrival <= day:
                # Goods arrived! Start 10-day processing (tagging/etiquetagem)
                receipt.status = "tagging"
                receipt.actual_arrival = actual_arrival
                receipt.delay_days = delay
                days_from_order = (actual_arrival - receipt.order_date).days
                receipt.on_time = days_from_order <= 45
                receipt.tagging_until = day + timedelta(days=10)  # 10 days processing for ALL merchandise

    # Phase B: tagging -> received (10-day processing complete, enters stock)
    for receipt in state.pending_receipts:
        if receipt.status != "tagging":
            continue

        if receipt.tagging_until is not None and day >= receipt.tagging_until:
            qty_to_add = receipt.quantity
            current = state.stock.get(receipt.id_produto, 0)
            state.stock[receipt.id_produto] = current + qty_to_add

            goods = GoodsReceipt(
                id_produto=receipt.id_produto,
                supplier=receipt.supplier,
                quantity=qty_to_add,
                receipt_date=day,
                order_date=receipt.order_date,
                expected_date=receipt.expected_date,
                on_time=receipt.on_time,
                delay_days=receipt.delay_days,
                tagging_days=10,
            )
            day_receipts.append(goods)
            receipt.status = "received"
            receipt.actual_arrival = receipt.actual_arrival or day

    # Clean up received orders
    receipts_to_remove = [r for r in state.pending_receipts if r.status == "received"]
    for r in receipts_to_remove:
        state.pending_receipts.remove(r)

    # -- 3. Check Reorder Points ------------------------------------
    for pid, produto in list(state.products.items()):
        regime = produto.regime
        params = regime_params.get(regime)
        if not params:
            continue

        if params.get("no_reorder"):
            continue  # Fashion does not reorder

        # Check if already has an active order
        has_active = any(
            r.id_produto == pid and r.status == "pending"
            for r in state.pending_receipts
        )
        if has_active:
            continue

        current_stock = state.stock.get(pid, 0)
        if current_stock <= 0:
            continue

        # Calculate daily demand velocity
        daily_demand = calculate_velocity(produto, state)
        if daily_demand <= 0:
            continue

        coverage_days = current_stock / daily_demand

        if coverage_days <= params["reorder_point_days"]:
            # Generate purchase alert
            alert = generate_purchase_alert(
                produto=produto,
                coverage_days=coverage_days,
                daily_demand=daily_demand,
                regime=regime,
                regime_params=regime_params,
                alert_date=day,
                all_products=all_product_list,
                stock=state.stock,
            )
            day_alerts.append(alert)

            # Create pending order
            lead_time_mean = supplier_lt.get(
                produto.cod_fornecedor or "",
                {"mean": params["lead_time_days"]}
            )["mean"]

            expected_date = day + timedelta(days=int(lead_time_mean))
            order = PendingReceipt(
                id_produto=pid,
                supplier=produto.cod_fornecedor or "N/A",
                quantity=alert.quantity,
                order_date=day,
                expected_date=expected_date,
                regime=regime,
                category=produto.des_categoria or "",
            )
            state.pending_receipts.append(order)

    # -- 4. Build Snapshot ------------------------------------------
    snapshot.total_stock = sum(state.stock.values())
    snapshot.total_sales_qty = sum(s.qty for s in day_sales)
    snapshot.total_sales_value = sum(s.total_value for s in day_sales if not (isinstance(s.total_value, float) and math.isnan(s.total_value)))
    snapshot.stockouts = len(day_stockouts)
    snapshot.receipts = len(day_receipts)
    snapshot.alerts = len(day_alerts)
    snapshot.slow_movers = len(day_slow_movers)
    snapshot.category_stock = category_stock
    snapshot.category_sales = category_sales_qty

    # Store day results in state for later reference
    state._day_sales = day_sales
    if not hasattr(state, '_all_alerts'):
        state._all_alerts = []
    state._all_alerts.extend(day_alerts)
    if not hasattr(state, '_all_stockouts'):
        state._all_stockouts = []
    state._all_stockouts.extend(day_stockouts)
    if not hasattr(state, '_all_receipts'):
        state._all_receipts = []
    state._all_receipts.extend(day_receipts)
    if not hasattr(state, '_all_slow_movers'):
        state._all_slow_movers = []
    state._all_slow_movers.extend(day_slow_movers)

    return snapshot


# ???????????????????????????????????????????????????????????????????????????
# Simulation Execution
# ???????????????????????????????????????????????????????????????????????????

def run_simulation(
    state: SimulationState,
    config: dict,
    num_days: int = 30,
    verbose: bool = False,
) -> tuple[list[DaySnapshot], SimulationState]:
    """
    Executa a simulação completa por N dias.
    Returns: (snapshots, state_final)
    """
    if verbose:
        print(f"\n? Iniciando simulação de {num_days} dias...")

    regime_params = config["regime_params"]
    temp_by_month = config["temperature_by_month"]
    discount_tiers = config["simulation"]["discount_tiers"]

    start_date = getattr(state, "max_stock_date", date(2019, 11, 30))
    start_date_sim = start_date + timedelta(days=1)

    # Generate temperatures
    state.temperature = generate_temperature(
        start_date_sim, num_days, temp_by_month, state.seed
    )

    # Pre-compute product list for substitute detection
    all_product_list = list(state.products.values())

    snapshots: list[DaySnapshot] = []
    daily_pending_snapshots: list[dict] = []

    for day_offset in range(num_days):
        sim_day = start_date_sim + timedelta(days=day_offset)

        if verbose:
            pct = (day_offset + 1) / num_days * 100
            print(f"   Dia {day_offset + 1}/{num_days} ({sim_day}) [{pct:.0f}%]...", end=" ")

        snapshot = simulate_day(
            day=sim_day,
            state=state,
            config=config,
            all_product_list=all_product_list,
            discount_tiers=discount_tiers,
        )
        snapshots.append(snapshot)

        # Snapshot pending receipt states for buyer reports
        total_received_so_far = sum(1 for r in state.pending_receipts if r.status == "received") + len(getattr(state, '_all_receipts', []))
        received_today = 0
        if daily_pending_snapshots:
            prev_total = daily_pending_snapshots[-1].get("_cumulative_received", 0)
            received_today = max(0, total_received_so_far - prev_total)

        pending_snap = {
            "day": sim_day.isoformat(),
            "pending": [],
            "tagging": [],
            "received_today": received_today,
            "_cumulative_received": total_received_so_far,
        }
        for r in state.pending_receipts:
            pending_snap[r.status].append({
                "product_id": r.id_produto,
                "supplier": r.supplier,
                "quantity": r.quantity,
                "order_date": r.order_date.isoformat(),
                "expected_date": r.expected_date.isoformat(),
                "regime": r.regime,
                "tagging_until": r.tagging_until.isoformat() if r.tagging_until else "",
                "delay_days": r.delay_days,
            })
        daily_pending_snapshots.append(pending_snap)

        if verbose:
            total = snapshot.total_stock
            sales = snapshot.total_sales_qty
            alerts = snapshot.alerts
            recv = snapshot.receipts
            print(f"Estoque: {total} | Vendas: {sales} un | Alertas: {alerts} | Receb: {recv}")

    # Store daily pending snapshots for output
    state._daily_pending_snapshots = daily_pending_snapshots

    if verbose:
        print(f"\nOK Simulação concluída: {num_days} dias simulados.")

    return snapshots, state


# ???????????????????????????????????????????????????????????????????????????
# Output Generation
# ???????????????????????????????????????????????????????????????????????????

def generate_outputs(
    snapshots: list[DaySnapshot],
    state: SimulationState,
    output_dir: Path,
    verbose: bool = False,
) -> dict:
    """
    Gera todos os arquivos de saída da simulação.
    Returns: summary dict
    """
    if verbose:
        print("\n? Gerando arquivos de saída...")

    output_dir.mkdir(parents=True, exist_ok=True)
    regime_params = _get_config()["regime_params"]

    # -- daily_log.csv --------------------------------------------
    daily_rows = []
    all_alerts: list[PurchaseAlert] = []
    all_stockouts: list[dict] = []
    all_receipts: list[GoodsReceipt] = []
    all_slow_movers: list[SlowMover] = []

    for snap in snapshots:
        daily_rows.append({
            "date": snap.date.isoformat(),
            "total_stock": snap.total_stock,
            "total_sales_qty": snap.total_sales_qty,
            "total_sales_value": round(snap.total_sales_value, 2),
            "stockouts": snap.stockouts,
            "receipts": snap.receipts,
            "alerts": snap.alerts,
            "slow_movers": snap.slow_movers,
        })

        # Accumulate daily data from snapshots
        # (alerts, stockouts, receipts, slow_movers accumulated in state._all_* lists)

    # Populate from accumulated state lists
    all_alerts = getattr(state, '_all_alerts', [])
    all_stockouts_raw = getattr(state, '_all_stockouts', [])
    all_receipts = getattr(state, '_all_receipts', [])
    all_slow_movers_raw = getattr(state, '_all_slow_movers', [])

    # Build stockout dicts from accumulated data
    # Track first stockout date per product
    first_stockout: dict[int, str] = {}
    # Reconstruct from _all_stockouts per day (we lost per-day mapping in the refactor)
    # Instead, use snapshot-level stockout info
    # Simpler: generate from state._all_stockouts which has PIDs
    seen_stockout_products = set()
    for pid in all_stockouts_raw:
        if pid not in seen_stockout_products:
            seen_stockout_products.add(pid)
            produto = state.products.get(pid)
            all_stockouts.append({
                "product_id": pid,
                "product_name": produto.cod_artigo if produto else "",
                "category": produto.des_categoria if produto else "",
                "stockout_date": snapshots[-1].date.isoformat() if snapshots else "N/A",
                "days_until_restocked": 0,
            })

    df_daily = pd.DataFrame(daily_rows)
    df_daily.to_csv(output_dir / "daily_log.csv", index=False)
    if verbose:
        print(f"   ? daily_log.csv -- {len(df_daily)} linhas")

    # -- stockouts.csv ---------------------------------------------
    # Update days_until_restocked for stockouts
    for stockout in all_stockouts:
        restock_date = None
        for r in all_receipts:
            if r.id_produto == stockout["product_id"]:
                restock_date = r.receipt_date
                break
        if restock_date:
            stockout_date_str = stockout.get("stockout_date", "")
            if stockout_date_str:
                stockout_date = date.fromisoformat(stockout_date_str)
                stockout["days_until_restocked"] = (restock_date - stockout_date).days

    df_stockouts = pd.DataFrame(all_stockouts)
    if not df_stockouts.empty:
        # Remove duplicates (same product, first stockout date wins)
        df_stockouts = df_stockouts.drop_duplicates(subset=["product_id", "stockout_date"])
    df_stockouts.to_csv(output_dir / "stockouts.csv", index=False)
    if verbose:
        print(f"   ? stockouts.csv -- {len(df_stockouts)} linhas")

    # -- purchase_alerts.csv ----------------------------------------
    alert_rows = []
    for alert in all_alerts:
        alert_rows.append({
            "alert_date": alert.alert_date.isoformat(),
            "product_id": alert.id_produto,
            "category": alert.categoria,
            "regime": alert.regime,
            "supplier": alert.supplier,
            "coverage_days": alert.coverage_days,
            "quantity": alert.quantity,
            "urgency": alert.urgency,
            "unit_cost": alert.unit_cost,
            "total_cost": alert.total_cost,
            "substitutes_count": len(alert.substitutes),
        })

    df_alerts = pd.DataFrame(alert_rows)
    if not df_alerts.empty:
        df_alerts = df_alerts.sort_values("urgency", ascending=False)
    df_alerts.to_csv(output_dir / "purchase_alerts.csv", index=False)
    if verbose:
        print(f"   ? purchase_alerts.csv -- {len(df_alerts)} linhas")

    # -- supplier_performance.csv ----------------------------------
    supplier_lt = getattr(state, "supplier_lead_time", {})
    supplier_stats: dict[str, dict] = {}

    for receipt in all_receipts:
        sup = receipt.supplier
        if sup not in supplier_stats:
            supplier_stats[sup] = {
                "total_orders": 0,
                "on_time": 0,
                "late": 0,
                "total_delay_days": 0,
            }
        supplier_stats[sup]["total_orders"] += 1
        if receipt.on_time:
            supplier_stats[sup]["on_time"] += 1
        else:
            supplier_stats[sup]["late"] += 1
            supplier_stats[sup]["total_delay_days"] += receipt.delay_days

    supplier_rows = []
    for sup, stats in supplier_stats.items():
        total = stats["total_orders"]
        compliance = stats["on_time"] / total if total > 0 else 0
        avg_delay = stats["total_delay_days"] / max(1, stats["late"])
        lt_info = supplier_lt.get(sup, {})
        supplier_rows.append({
            "supplier": sup,
            "supplier_category": lt_info.get("supplier_category", ""),
            "total_orders": total,
            "on_time": stats["on_time"],
            "late": stats["late"],
            "avg_delay_days": round(avg_delay, 1),
            "compliance_rate": round(compliance, 4),
            "estimated_lead_time_mean": lt_info.get("mean", 0),
        })

    # Include all suppliers from the state (even those without receipts)
    for sup, lt_info in supplier_lt.items():
        if sup not in supplier_stats:
            supplier_rows.append({
                "supplier": sup,
                "supplier_category": lt_info.get("supplier_category", ""),
                "total_orders": lt_info.get("total_orders", 0),
                "on_time": 0,
                "late": 0,
                "avg_delay_days": 0.0,
                "compliance_rate": 1.0,
                "estimated_lead_time_mean": lt_info.get("mean", 0),
            })

    df_suppliers = pd.DataFrame(supplier_rows)
    df_suppliers.to_csv(output_dir / "supplier_performance.csv", index=False)
    if verbose:
        print(f"   ? supplier_performance.csv -- {len(df_suppliers)} linhas")

    # -- slow_movers.csv -------------------------------------------
    # Deduplicate slow movers (keep latest recommendation per product)
    sm_dedup: dict[int, SlowMover] = {}
    for sm in all_slow_movers_raw:
        pid = sm.id_produto
        if pid not in sm_dedup or sm.days_without_sale > sm_dedup[pid].days_without_sale:
            sm_dedup[pid] = sm

    sm_rows = []
    for sm in sm_dedup.values():
        sm_rows.append({
            "product_id": sm.id_produto,
            "category": sm.categoria,
            "regime": sm.regime,
            "stock_qty": sm.stock_qty,
            "days_without_sale": sm.days_without_sale,
            "suggested_discount": f"{sm.suggested_discount * 100:.0f}%",
            "last_sale_date": sm.last_sale_date.isoformat() if sm.last_sale_date else "",
        })

    df_sm = pd.DataFrame(sm_rows)
    df_sm.to_csv(output_dir / "slow_movers.csv", index=False)
    if verbose:
        print(f"   ? slow_movers.csv -- {len(df_sm)} linhas")

    # -- daily_pending_log.csv ------------------------------------
    daily_pending = getattr(state, '_daily_pending_snapshots', [])
    if daily_pending:
        pending_rows = []
        for ps in daily_pending:
            row = {
                "day": ps["day"],
                "pending_count": len(ps["pending"]),
                "tagging_count": len(ps["tagging"]),
            }
            pending_rows.append(row)
        df_pending = pd.DataFrame(pending_rows)
        df_pending.to_csv(output_dir / "daily_pending_log.csv", index=False)
        if verbose:
            print(f"   ? daily_pending_log.csv -- {len(df_pending)} linhas")

        # Also save full state as JSON for buyer reports
        import json as _json
        with open(output_dir / "daily_pending_detail.json", "w") as f:
            _json.dump(daily_pending, f, indent=2, default=str)
        if verbose:
            print(f"   ? daily_pending_detail.json -- detalhe completo dos pedidos pendentes")

    # -- summary.json ----------------------------------------------
    total_sales_qty = sum(s.total_sales_qty for s in snapshots)
    total_revenue = sum(s.total_sales_value for s in snapshots)
    total_stockouts = sum(s.stockouts for s in snapshots)
    total_alerts = sum(s.alerts for s in snapshots)
    total_receipts = sum(s.receipts for s in snapshots)
    total_slow = sum(s.slow_movers for s in snapshots)

    regime_dist = {}
    for p in state.products.values():
        regime_dist[p.regime] = regime_dist.get(p.regime, 0) + 1

    summary = {
        "simulation_metadata": {
            "version": VERSION,
            "total_days": len(snapshots),
            "start_date": snapshots[0].date.isoformat() if snapshots else "N/A",
            "end_date": snapshots[-1].date.isoformat() if snapshots else "N/A",
            "seed": state.seed,
        },
        "totals": {
            "total_sales_units": int(total_sales_qty),
            "total_revenue_brl": round(total_revenue, 2),
            "total_stockouts": int(total_stockouts),
            "stockout_products_unique": len(df_stockouts),
            "total_purchase_alerts": int(total_alerts),
            "total_receipts": int(total_receipts),
            "total_slow_movers": int(total_slow),
            "slow_mover_products_unique": len(df_sm),
        },
        "final_stock": {
            "total_units": int(state.stock.get(-1, sum(state.stock.values()))),
            "unique_products": len([s for s in state.stock.values() if s > 0]),
            "zero_stock_products": len([s for s in state.stock.values() if s <= 0]),
        },
        "regime_distribution": regime_dist,
        "suppliers_tracked": len(supplier_lt),
        "suppliers_with_receipts": len(supplier_stats),
    }

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    if verbose:
        print(f"   ? summary.json -- resumo completo")

    if verbose:
        print(f"\n? Resumo da Simulação:")
        print(f"   Dias: {summary['simulation_metadata']['total_days']}")
        print(f"   Período: {summary['simulation_metadata']['start_date']} -> {summary['simulation_metadata']['end_date']}")
        print(f"   Vendas: {summary['totals']['total_sales_units']} un | R$ {summary['totals']['total_revenue_brl']:,.2f}")
        print(f"   Rupturas: {summary['totals']['stockout_products_unique']} produtos")
        print(f"   Alertas: {summary['totals']['total_purchase_alerts']}")
        print(f"   Recebimentos: {summary['totals']['total_receipts']}")
        print(f"   Lentos: {summary['totals']['slow_mover_products_unique']} produtos")

    return summary


def _get_config(config_path: Optional[Path] = None) -> dict:
    """Load config from JSON file."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    with open(config_path) as f:
        return json.load(f)


# ???????????????????????????????????????????????????????????????????????????
# Main Entry Point
# ???????????????????????????????????????????????????????????????????????????

def main():
    parser = argparse.ArgumentParser(
        description="Motor de Simulação de Estoque - Chez Violeta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python simulation_engine.py --days 30 --verbose
  python simulation_engine.py --days 90 --seed 123
  python simulation_engine.py --db-path ../data/chez_gold.duckdb
        """,
    )
    parser.add_argument("--days", type=int, default=30, help="Número de dias para simular (default: 30)")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="Caminho do DuckDB gold layer")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH), help="Caminho do config JSON")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Diretório de saída")
    parser.add_argument("--seed", type=int, default=42, help="Seed aleatório (default: 42)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verboso com progresso")
    parser.add_argument("--version", action="version", version=f"v{VERSION}")

    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output)

    if not config_path.exists():
        print(f"X Config não encontrado: {config_path}")
        sys.exit(1)

    if not os.path.exists(args.db_path):
        print(f"X DuckDB não encontrado: {args.db_path}")
        sys.exit(1)

    if args.verbose:
        print(f"=== Motor de Simulacao de Estoque v{VERSION} ===")
        print(f"   Config: {config_path}")
        print(f"   DuckDB: {args.db_path}")
        print(f"   Output: {output_dir}")
        print(f"   Dias: {args.days}")
        print(f"   Seed: {args.seed}")

    # Load config
    config = _get_config(config_path)

    # Set seed
    config["simulation"]["seed"] = args.seed
    np.random.seed(args.seed)
    random.seed(args.seed)

    # Extract data from DuckDB
    state = extract_data(args.db_path, verbose=args.verbose)
    state.seed = args.seed

    # Run simulation
    snapshots, final_state = run_simulation(
        state=state,
        config=config,
        num_days=args.days,
        verbose=args.verbose,
    )

    # Generate outputs
    summary = generate_outputs(
        snapshots=snapshots,
        state=final_state,
        output_dir=output_dir,
        verbose=args.verbose,
    )

    if args.verbose:
        print(f"\nOK Simulação completa! Arquivos em: {output_dir}")

    # Return path for orchestrator
    return str(output_dir)


if __name__ == "__main__":
    main()
