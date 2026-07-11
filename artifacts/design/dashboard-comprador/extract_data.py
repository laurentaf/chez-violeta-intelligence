#!/usr/bin/env python3
"""Extract CSV data to JSON for embedding in the dashboard HTML."""
import csv, json, collections, os

BASE = "F:/projects/chez-violeta-intelligence"

# ── Purchase Alerts ──
alerts = []
with open(os.path.join(BASE, "artifacts/simulation/output-360d-v2/purchase_alerts_enriched.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        coverage = float(row.get("coverage_days", 0) or 0)
        arrival = int(row.get("days_until_expected_arrival", 0) or 0)
        pending = row.get("has_pending_order", "False") == "True"
        total_cost = float(row.get("total_cost", 0) or 0)
        
        # Compute "Chega Antes da Ruptura?"
        arrives_before = "SIM" if (pending and arrival < coverage) else "NÃO"
        if not pending:
            arrives_before = "—"
        
        # Classify risk based on coverage
        risk = row.get("risk_score", "MEDIUM")
        
        alerts.append({
            "date": row["alert_date"],
            "id": row["product_id"],
            "name": row.get("product_name", ""),
            "code": row.get("product_code", ""),
            "cat": row["category"],
            "regime": row["regime"],
            "supplier": row["supplier"],
            "coverage": round(coverage, 1),
            "qty": int(row.get("quantity", 0)),
            "urgency": row.get("urgency", "MEDIUM"),
            "risk": risk,
            "hasPending": pending,
            "pendingDate": row.get("pending_expected_date", ""),
            "daysUntilArrival": arrival,
            "arrivesBefore": arrives_before,
            "unitCost": float(row.get("unit_cost", 0) or 0),
            "totalCost": round(total_cost, 2)
        })

print(f"ALERTS: {len(alerts)}")

# ── Supplier Performance ──
suppliers = []
with open(os.path.join(BASE, "artifacts/simulation/output-360d-v2/supplier_performance.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        compliance = float(row["compliance_rate"])
        pct = round(compliance * 100, 1)
        if pct >= 95:
            grade = "A"
        elif pct >= 90:
            grade = "B"
        elif pct >= 85:
            grade = "C"
        else:
            grade = "D"
        suppliers.append({
            "name": row["supplier"],
            "orders": int(row["total_orders"]),
            "onTime": int(row["on_time"]),
            "late": int(row["late"]),
            "compliance": round(compliance, 4),
            "compliancePct": pct,
            "grade": grade,
            "avgDelay": float(row["avg_delay_days"]),
            "leadTime": int(row["estimated_lead_time_mean"]),
            "explanation": row.get("explanation", "")
        })

print(f"SUPPLIERS: {len(suppliers)}")

# ── Stock by Store ──
stocks = []
with open(os.path.join(BASE, "artifacts/data/stock_by_store.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        stocks.append({
            "date": row["id_data"],
            "storeId": row["id_loja"],
            "store": row["des_estabelecimento"],
            "productId": row["id_produto"].split(".")[0],
            "qty": int(float(row["qtd_estoque"]))
        })

print(f"STOCKS: {len(stocks)}")

# ── Summary stats ──
total_alerts = len(alerts)
high_crit = len([a for a in alerts if a["risk"] in ("HIGH", "CRITICAL")])
high_crit_pct = round(high_crit / total_alerts * 100, 1) if total_alerts else 0
will_rupture = len([a for a in alerts if a["arrivesBefore"] == "NÃO"])

alert_supplier_names = set(a["supplier"] for a in alerts)
active_suppliers = [s for s in suppliers if s["name"] in alert_supplier_names]
worst_supplier = min(active_suppliers, key=lambda s: s["compliance"]) if active_suppliers else None

print(f"Total alerts: {total_alerts}")
print(f"HIGH/CRIT: {high_crit} ({high_crit_pct}%)")
print(f"Will rupture: {will_rupture}")
print(f"Worst supplier: {worst_supplier['name'] if worst_supplier else 'N/A'} ({worst_supplier['compliancePct'] if worst_supplier else 0}%)")

# Build stock index by product
stock_by_prod = collections.defaultdict(list)
for s in stocks:
    stock_by_prod[s["productId"]].append({"store": s["store"], "qty": s["qty"]})

# Build counts for charts
urgency_counts = collections.Counter(a["risk"] for a in alerts)
cat_counts = collections.Counter(a["cat"] for a in alerts)

print(f"Urgency counts: {dict(urgency_counts)}")
print(f"Category counts: {dict(cat_counts)}")

# Output JSON summary
summary = {
    "totalAlerts": total_alerts,
    "highCritCount": high_crit,
    "highCritPct": high_crit_pct,
    "willRupture": will_rupture,
    "worstSupplier": worst_supplier["name"] if worst_supplier else "N/A",
    "worstCompliance": worst_supplier["compliancePct"] if worst_supplier else 0,
    "urgencyCounts": dict(urgency_counts),
    "catCounts": dict(cat_counts),
    "latestDate": max(a["date"] for a in alerts),
    "alertSupplierCount": len(alert_supplier_names)
}

print(f"\nSUMMARY: {json.dumps(summary, indent=2, ensure_ascii=False)}")

# Save sample data for dashboard (limit to 200 latest alerts for performance)
alerts_sorted = sorted(alerts, key=lambda a: a["date"] + a["name"], reverse=True)
alerts_sample = alerts_sorted[:200]

output = {
    "summary": summary,
    "alerts": alerts_sample,
    "suppliers": [s for s in suppliers if s["compliancePct"] > 0],
    "stockByProduct": dict(stock_by_prod)
}

with open(os.path.join(BASE, "artifacts/design/dashboard-comprador/data.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f"\nData saved to data.json")
print(f"Alerts in sample: {len(alerts_sample)}")
print(f"Active suppliers: {len(alert_supplier_names)}")
