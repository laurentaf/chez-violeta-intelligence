#!/usr/bin/env python3
# synthetic: true
# granted_by: orchestrator (user-directed simulation task)
# granted_at: 2026-07-08
# reason: Relatorios sinteticos gerados a partir da simulacao de estoque. Dados de produto extraidos do DuckDB gold layer.
"""
Gerador de Relatórios Diários do Comprador
===========================================
Gera 360 relatórios markdown (um por dia simulado) no formato que o comprador
receberia: resumo do dia, alertas de compra, pedidos em processamento, produtos lentos.

Uso:
    python generate_buyer_reports.py --input-dir artifacts/simulation/output-360d-v2/ --output-dir artifacts/simulation/output-360d-v2/buyer_reports/
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# --- Path defaults ----------------------------------------------------------
DEFAULT_DB_PATH = "F:/projects/chez-violeta-intelligence/artifacts/data/chez_gold.duckdb"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "simulation_config.json"


def load_products(db_path: str) -> dict[int, dict]:
    """Load product catalog from DuckDB (id_produto -> cod_artigo mapping)."""
    try:
        import duckdb
        con = duckdb.connect(db_path)
        df = con.execute("""
            SELECT id_produto, cod_artigo, des_categoria, des_linha, des_colecao,
                   cod_fornecedor, val_custo_inicial
            FROM gold.dim_produto
            WHERE dat_fim_vigencia IS NULL AND id_produto > 0
        """).fetchdf()
        con.close()
        products = {}
        for _, row in df.iterrows():
            pid = int(row["id_produto"])
            products[pid] = {
                "cod_artigo": str(row.get("cod_artigo", "") or ""),
                "des_categoria": str(row.get("des_categoria", "") or ""),
                "des_linha": str(row.get("des_linha", "") or ""),
                "cod_fornecedor": str(row.get("cod_fornecedor", "") or ""),
            }
        return products
    except Exception as e:
        print(f"! Aviso: não foi possível carregar produtos do DuckDB: {e}")
        return {}


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return json.load(f)


def format_brl(value: float) -> str:
    """Format as Brazilian currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_date(d: str) -> str:
    """Convert ISO date to Brazilian format DD/MM/YYYY."""
    try:
        dt = date.fromisoformat(d)
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return d


def get_coverage_label(coverage_days: float) -> str:
    """Human-readable coverage label."""
    if coverage_days <= 3:
        return "Crítico"
    elif coverage_days <= 7:
        return "Muito Baixo"
    elif coverage_days <= 14:
        return "Baixo"
    elif coverage_days <= 30:
        return "Médio"
    elif coverage_days <= 60:
        return "Bom"
    else:
        return "Confortável"


def parse_date(date_val) -> Optional[date]:
    """Try to parse a value as date."""
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        try:
            return date.fromisoformat(date_val.split("T")[0])
        except (ValueError, TypeError):
            return None
    return None


def generate_reports(
    input_dir: Path,
    output_dir: Path,
    config_path: Path,
    db_path: str,
    verbose: bool = False,
):
    """Generate buyer daily reports from simulation outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_config(config_path)
    regime_params = config["regime_params"]

    # Load product catalog
    products = load_products(db_path)
    if verbose:
        print(f"? {len(products)} produtos carregados do DuckDB")

    # Load daily log
    daily_log_path = input_dir / "daily_log.csv"
    if not daily_log_path.exists():
        print(f"X daily_log.csv não encontrado em {input_dir}")
        return

    df_daily = pd.read_csv(daily_log_path)
    df_daily["date_obj"] = pd.to_datetime(df_daily["date"])

    if verbose:
        print(f"? daily_log.csv: {len(df_daily)} dias carregados")

    # Load purchase alerts
    alerts_path = input_dir / "purchase_alerts.csv"
    df_alerts = None
    if alerts_path.exists():
        df_alerts = pd.read_csv(alerts_path)
        df_alerts["alert_date_obj"] = pd.to_datetime(df_alerts["alert_date"])
        if verbose:
            print(f"? purchase_alerts.csv: {len(df_alerts)} alertas carregados")

    # Load daily pending detail
    pending_path = input_dir / "daily_pending_detail.json"
    daily_pending = None
    if pending_path.exists():
        with open(pending_path) as f:
            daily_pending = json.load(f)
        if verbose:
            print(f"? daily_pending_detail.json: {len(daily_pending)} dias de pendentes carregados")

    # Load slow movers
    sm_path = input_dir / "slow_movers.csv"
    df_sm = None
    if sm_path.exists():
        df_sm = pd.read_csv(sm_path)
        if verbose:
            print(f"? slow_movers.csv: {len(df_sm)} produtos lentos carregados")

    # Build pending lookup: day -> list of pending/tagging orders
    pending_by_day: dict[str, dict] = {}
    if daily_pending:
        for ps in daily_pending:
            pending_by_day[ps["day"]] = ps

    # Build alert lookup: day -> list of alerts
    alerts_by_day: dict[str, list[dict]] = {}
    if df_alerts is not None and not df_alerts.empty:
        for _, row in df_alerts.iterrows():
            d = row["alert_date"]
            if d not in alerts_by_day:
                alerts_by_day[d] = []
            alerts_by_day[d].append(row.to_dict())

    # Generate reports
    report_paths = []
    total_days = len(df_daily)

    for idx, row_tuple in enumerate(df_daily.iterrows()):
        _, day_row = row_tuple
        day_str = day_row["date"]
        day_date = day_row["date_obj"]

        # --- Summary ---
        sales_qty = int(day_row["total_sales_qty"])
        sales_value = float(day_row["total_sales_value"])
        total_stock = int(day_row["total_stock"])
        stockouts = int(day_row["stockouts"])
        receipts = int(day_row["receipts"])

        # --- Alerts for this day ---
        day_alerts = alerts_by_day.get(day_str, [])

        # --- Pending orders ---
        pending_info = pending_by_day.get(day_str, {"pending": [], "tagging": []})
        pending_orders = pending_info.get("pending", [])
        tagging_orders = pending_info.get("tagging", [])

        # --- Slow movers (sample top 5) ---
        slow_movers_sample = []
        if df_sm is not None and not df_sm.empty:
            # Sort by days_without_sale descending
            sm_sorted = df_sm.sort_values("days_without_sale", ascending=False)
            slow_movers_sample = sm_sorted.head(5).to_dict("records")

        # Build report
        report_lines = []
        report_lines.append(f"# Relatório do Comprador — {format_date(day_str)}")
        report_lines.append("")

        # Resumo
        report_lines.append("## Resumo")
        report_lines.append("")
        report_lines.append(f"- **Vendas do dia:** {sales_qty} unidades ({format_brl(sales_value)})")
        report_lines.append(f"- **Estoque total:** {total_stock:,} unidades".replace(",", "."))
        report_lines.append(f"- **Rupturas:** {stockouts} produtos")
        report_lines.append(f"- **Recebimentos:** {receipts} pedidos")
        report_lines.append(f"- **Dia:** {idx + 1} de {total_days}")
        report_lines.append("")

        # Alertas de Compra
        report_lines.append("## Alertas de Compra")
        report_lines.append("")
        if day_alerts:
            report_lines.append("| Produto | Fornecedor | Estoque | Cobertura | Urgência | Qtd Sugerida |")
            report_lines.append("|---------|-----------|---------|-----------|----------|--------------|")
            for alert in day_alerts:
                pid = int(alert["product_id"])
                prod = products.get(pid, {})
                cod = prod.get("cod_artigo", str(pid))
                supplier = alert.get("supplier", "N/A")
                coverage = alert.get("coverage_days", 0)
                urgency = alert.get("urgency", "N/A")
                qty = int(alert.get("quantity", 0))

                # Get current stock (approximate from avg coverage)
                est_stock = "N/A"

                report_lines.append(
                    f"| {cod} | {supplier} | {est_stock} | {coverage:.0f}d ({get_coverage_label(coverage)}) | **{urgency}** | {qty} |"
                )
        else:
            report_lines.append("*Nenhum alerta de compra hoje.*")
        report_lines.append("")

        # Pedidos Pendentes
        report_lines.append("## Pedidos em Andamento")
        report_lines.append("")

        all_active = pending_orders + tagging_orders

        if all_active:
            report_lines.append("| Produto | Fornecedor | Qtd | Previsão Chegada | Status | Dias Restantes |")
            report_lines.append("|---------|-----------|-----|-----------------|--------|---------------|")
            for order in all_active:
                pid = order.get("product_id", 0)
                prod = products.get(pid, {})
                cod = prod.get("cod_artigo", str(pid))
                supplier = order.get("supplier", "N/A")
                qty = order.get("quantity", 0)
                expected = order.get("expected_date", "")
                regime = order.get("regime", "")
                tagging_until = order.get("tagging_until", "")

                status = order.get("status", "pending")
                if status == "pending":
                    status_label = "Em trânsito"
                    # Days until expected arrival
                    expected_dt = parse_date(expected)
                    if expected_dt:
                        remaining = (expected_dt - date.fromisoformat(day_str.split("T")[0])).days
                    else:
                        remaining = "?"
                elif status == "tagging":
                    status_label = "Em etiquetagem"
                    tagging_dt = parse_date(tagging_until)
                    if tagging_dt:
                        remaining = (tagging_dt - date.fromisoformat(day_str.split("T")[0])).days
                    else:
                        remaining = "?"
                else:
                    status_label = status
                    remaining = "?"

                remaining_str = f"{remaining}d" if isinstance(remaining, int) and remaining > 0 else "Hoje!" if isinstance(remaining, int) else str(remaining)
                expected_fmt = format_date(expected)

                report_lines.append(
                    f"| {cod} | {supplier} | {qty} | {expected_fmt} | {status_label} | {remaining_str} |"
                )
        else:
            report_lines.append("*Nenhum pedido pendente.*")
        report_lines.append("")

        # Produtos Lentos
        report_lines.append("## Produtos Lentos (sugestão de desconto)")
        report_lines.append("")
        if slow_movers_sample:
            report_lines.append("| Produto | Estoque | Dias sem vender | Desconto Sugerido |")
            report_lines.append("|---------|--------|----------------|-------------------|")
            for sm in slow_movers_sample:
                pid = sm.get("product_id", 0)
                prod = products.get(pid, {})
                cod = prod.get("cod_artigo", str(pid))
                stock_qty = int(sm.get("stock_qty", 0))
                days_wo = int(sm.get("days_without_sale", 0))
                discount = sm.get("suggested_discount", "0%")
                report_lines.append(
                    f"| {cod} | {stock_qty} | {days_wo} dias | {discount} |"
                )
        else:
            report_lines.append("*Nenhum produto lento identificado.*")
        report_lines.append("")

        # --- Write report ---
        report_filename = f"relatorio-{day_str}.md"
        report_path = output_dir / report_filename
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
        report_paths.append((day_str, report_path))

        if verbose and (idx + 1) % 30 == 0:
            print(f"   Gerados {idx + 1}/{total_days} relatórios...")

    # --- Generate index.md ---
    index_lines = []
    index_lines.append("# Índice de Relatórios do Comprador")
    index_lines.append("")
    index_lines.append(f"**Simulação:** {total_days} dias")
    index_lines.append(f"**Período:** {format_date(str(df_daily.iloc[0]['date']))} a {format_date(str(df_daily.iloc[-1]['date']))}")
    index_lines.append("")
    index_lines.append("## Navegação por Mês")
    index_lines.append("")

    # Group by month
    from collections import OrderedDict
    months = OrderedDict()
    for day_str, _ in report_paths:
        dt = date.fromisoformat(day_str)
        month_key = dt.strftime("%Y-%m")
        month_label = dt.strftime("%B de %Y").capitalize()
        if month_key not in months:
            months[month_key] = {"label": month_label, "days": []}
        months[month_key]["days"].append((day_str, dt.day))

    for month_key, month_data in months.items():
        index_lines.append(f"### {month_data['label']}")
        index_lines.append("")
        # Make a compact table
        days_in_month = month_data["days"]
        # Row per week
        week_rows = []
        current_week = []
        for day_str, day_num in days_in_month:
            link = f"[Dia {day_num:02d}](relatorio-{day_str}.md)"
            current_week.append(link)
            if len(current_week) == 7:
                week_rows.append(" | ".join(current_week))
                current_week = []
        if current_week:
            week_rows.append(" | ".join(current_week))

        for row in week_rows:
            index_lines.append(f"- {row}")
        index_lines.append("")
        index_lines.append("---")
        index_lines.append("")

    index_lines.append("## Estatísticas Gerais")
    index_lines.append("")

    total_sales_qty = int(df_daily["total_sales_qty"].sum())
    total_sales_value = float(df_daily["total_sales_value"].sum())
    avg_daily_sales = total_sales_qty / total_days if total_days > 0 else 0
    avg_daily_value = total_sales_value / total_days if total_days > 0 else 0

    index_lines.append(f"- **Total de vendas:** {total_sales_qty} unidades ({format_brl(total_sales_value)})")
    index_lines.append(f"- **Média diária:** {avg_daily_sales:.1f} unidades ({format_brl(avg_daily_value)})")
    index_lines.append(f"- **Total de alertas:** {len(df_alerts) if df_alerts is not None else 0}")
    index_lines.append(f"- **Total de recebimentos:** {int(df_daily['receipts'].sum())}")
    index_lines.append("")

    # Last day summary
    last_day = df_daily.iloc[-1]
    index_lines.append(f"### Último dia ({format_date(str(last_day['date']))})")
    index_lines.append(f"- Estoque final: {int(last_day['total_stock']):,} unidades")
    index_lines.append(f"- Vendas: {int(last_day['total_sales_qty'])} un | {format_brl(float(last_day['total_sales_value']))}")

    index_path = output_dir / "index.md"
    with open(index_path, "w") as f:
        f.write("\n".join(index_lines))

    if verbose:
        print(f"\n? {total_days} relatórios gerados em: {output_dir}")
        print(f"? Índice: {index_path}")

    return len(report_paths)


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de Relatórios Diários do Comprador - Chez Violeta"
    )
    parser.add_argument("--input-dir", type=str,
                        default=str(Path(__file__).parent / "output-360d-v2"),
                        help="Diretório com outputs da simulação (default: output-360d-v2/)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Diretório para os relatórios (default: <input-dir>/buyer_reports/)")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH),
                        help="Caminho do config JSON")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH,
                        help="Caminho do DuckDB gold layer")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / "buyer_reports"

    if not input_dir.exists():
        print(f"X Diretório de input não encontrado: {input_dir}")
        sys.exit(1)

    if args.verbose:
        print("=== Gerador de Relatórios do Comprador ===")
        print(f"   Input: {input_dir}")
        print(f"   Output: {output_dir}")

    n = generate_reports(
        input_dir=input_dir,
        output_dir=output_dir,
        config_path=Path(args.config),
        db_path=args.db_path,
        verbose=args.verbose,
    )

    print(f"\nOK {n} relatórios gerados em: {output_dir}")


if __name__ == "__main__":
    main()
