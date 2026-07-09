#!/usr/bin/env python3
"""Generate the Chez Violeta Buyer Dashboard HTML from CSV data."""

import csv
import json
import os
from collections import defaultdict

INPUT_DIR = r"F:\projects\chez-violeta-intelligence\artifacts\simulation\output-360d-v2"
OUTPUT_FILE = r"F:\projects\chez-violeta-intelligence\artifacts\design\dashboard-comprador\index.html"

def read_csv(filename):
    path = os.path.join(INPUT_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    daily_log = read_csv("daily_log.csv")
    suppliers = read_csv("supplier_performance.csv")
    slow = read_csv("slow_movers.csv")
    alerts = read_csv("purchase_alerts.csv")

    # Convert and clean daily_log
    dl_js = []
    for r in daily_log:
        dl_js.append({
            "date": r["date"],
            "stock": int(float(r["total_stock"])),
            "salesQty": int(float(r["total_sales_qty"])),
            "salesValue": float(r["total_sales_value"]),
            "stockouts": int(float(r["stockouts"])),
            "receipts": int(float(r["receipts"]) if r["receipts"] else 0),
            "alerts": int(float(r["alerts"])),
            "slowMovers": int(float(r["slow_movers"]))
        })

    # Suppliers
    sup_js = []
    for r in suppliers:
        compliance = float(r["compliance_rate"]) if r["compliance_rate"] else 0
        sup_js.append({
            "name": r["supplier"],
            "orders": int(float(r["total_orders"])),
            "onTime": int(float(r["on_time"])),
            "late": int(float(r["late"])),
            "avgDelay": float(r["avg_delay_days"]),
            "compliance": compliance,
            "leadTime": int(float(r["estimated_lead_time_mean"])),
        })

    # Slow movers - top 100 by days_without_sale
    slow_sorted = sorted(slow, key=lambda x: -int(x["days_without_sale"]))
    slow_js = []
    seen = set()
    for r in slow_sorted:
        pid = r["product_id"]
        if pid in seen:
            continue
        seen.add(pid)
        slow_js.append({
            "id": int(pid),
            "cat": r["category"],
            "stock": int(float(r["stock_qty"])),
            "dws": int(float(r["days_without_sale"])),
            "disc": r["suggested_discount"],
            "lastSale": r.get("last_sale_date", "N/A")
        })
        if len(slow_js) >= 100:
            break

    # Alerts
    urgency_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    category_counts = defaultdict(int)
    supplier_totals = defaultdict(float)
    total_alert_cost = 0.0
    
    all_suppliers = set()
    all_categories = set()
    all_dates = set()
    
    for r in alerts:
        urg = r["urgency"].strip().upper()
        cat = r["category"].strip()
        sup = r["supplier"].strip()
        d = r["alert_date"].strip()
        tc = float(r["total_cost"]) if r["total_cost"] else 0.0
        
        if urg in urgency_counts:
            urgency_counts[urg] += 1
        category_counts[cat] += 1
        supplier_totals[sup] += tc
        total_alert_cost += tc
        all_suppliers.add(sup)
        all_categories.add(cat)
        all_dates.add(d)
    
    sorted_dates = sorted(all_dates)

    # Alert entries (last 30 days)
    last_30_dates = set(sorted_dates[-30:] if len(sorted_dates) > 30 else sorted_dates)
    recent_alerts = [r for r in alerts if r["alert_date"].strip() in last_30_dates]
    
    alert_entries_js = []
    for r in recent_alerts:
        alert_entries_js.append({
            "date": r["alert_date"].strip(),
            "id": int(float(r["product_id"])),
            "cat": r["category"].strip(),
            "regime": r["regime"].strip(),
            "supplier": r["supplier"].strip(),
            "qty": int(float(r["quantity"])),
            "coverage": float(r["coverage_days"]),
            "urgency": r["urgency"].strip().upper(),
            "unitCost": float(r["unit_cost"]) if r["unit_cost"] else 0.0,
            "totalCost": float(r["total_cost"]) if r["total_cost"] else 0.0,
        })

    # Recent critical count (last 7 days)
    recent_7 = set(sorted_dates[-7:] if len(sorted_dates) > 7 else sorted_dates)
    recent_critical = sum(1 for r in alerts if r["urgency"].strip().upper() == "CRITICAL" and r["alert_date"].strip() in recent_7)

    # Top 10 suppliers by alert value
    top10 = sorted(supplier_totals.items(), key=lambda x: -x[1])[:10]

    # Worst 5 suppliers by compliance (with >=5 orders)
    suppliers_with_orders = [s for s in sup_js if s["orders"] >= 5]
    worst_suppliers = sorted(suppliers_with_orders, key=lambda x: x["compliance"])[:5]

    category_pie = sorted(category_counts.items(), key=lambda x: -x[1])

    # Build data JSON
    data = {
        "DAILY_LOG": dl_js,
        "SUPPLIERS": sup_js,
        "SLOW_MOVERS": slow_js,
        "ALERT_ENTRIES": alert_entries_js,
        "URGENCY_COUNTS": urgency_counts,
        "CATEGORY_LABELS": [c[0] for c in category_pie],
        "CATEGORY_VALUES": [c[1] for c in category_pie],
        "TOP10_LABELS": [s[0] for s in top10],
        "TOP10_VALUES": [s[1] for s in top10],
        "TOTAL_ALERT_COST": round(total_alert_cost, 2),
        "RECENT_CRITICAL": recent_critical,
        "WORST_SUPPLIERS": [{"name": s["name"], "compliance": s["compliance"]} for s in worst_suppliers],
    }

    # Read HTML template
    template_path = os.path.join(os.path.dirname(__file__), "template.html")
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Replace placeholder
    html = template.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {OUTPUT_FILE}")
    print(f"  Daily log entries: {len(dl_js)}")
    print(f"  Suppliers: {len(sup_js)}")
    print(f"  Slow movers: {len(slow_js)}")
    print(f"  Alert entries: {len(alert_entries_js)}")
    print(f"  Total alert cost: R$ {total_alert_cost:.2f}")

if __name__ == "__main__":
    main()
