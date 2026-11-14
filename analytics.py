"""
RetailIQ - Deterministic Analytics Engine (TRACK_ID=PS03)
Performs all mathematical, inventory risk, and sales calculations in pure Python/SQLite.
All facts are strictly verified and deterministic (Zero AI hallucination).
"""

import io
import csv
import math
import sqlite3
from typing import Dict, List, Any, Optional
from database import get_db_connection


def get_dataset_days_count() -> int:
    """Returns the distinct number of recorded sales days in the dataset (default: 30)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT date) FROM sales")
    row = cur.fetchone()
    count = row[0] if row and row[0] > 0 else 30
    conn.close()
    return count


# -------------------------------------------------------------------------
# 1. Dashboard Metrics
# -------------------------------------------------------------------------
def get_dashboard_metrics() -> Dict[str, Any]:
    """
    Calculates verified business facts:
    - Total revenue
    - Total units sold
    - Total orders/sales records
    - Number of low-stock products (products at CRITICAL, HIGH, or LOW risk)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(quantity_sold), 0) as total_units_sold,
            COALESCE(SUM(revenue), 0.0) as total_revenue
        FROM sales
    """)
    sales_row = cur.fetchone()
    total_orders = sales_row["total_orders"] if sales_row else 0
    total_units_sold = sales_row["total_units_sold"] if sales_row else 0
    total_revenue = round(sales_row["total_revenue"], 2) if sales_row else 0.0
    conn.close()

    # Calculate low-stock products count from deterministic inventory risks
    inventory_items = get_inventory_risks()
    low_stock_products = [
        item for item in inventory_items
        if item["risk_status"] in ("CRITICAL", "HIGH", "LOW")
    ]

    return {
        "total_revenue": total_revenue,
        "total_units_sold": total_units_sold,
        "total_orders": total_orders,
        "low_stock_products_count": len(low_stock_products),
    }


# -------------------------------------------------------------------------
# 2. Top Products Ranking
# -------------------------------------------------------------------------
def get_top_products(limit: int = 5, sort_by: str = "revenue") -> List[Dict[str, Any]]:
    """
    Ranks products deterministically.
    Returns product name, category, quantity sold, revenue, profit, and margin.
    Supports sort_by: 'revenue', 'units', 'profit'.
    """
    order_clause = "revenue DESC"
    if sort_by in ("units", "quantity_sold", "total_units_sold"):
        order_clause = "quantity_sold DESC"
    elif sort_by in ("profit", "total_profit"):
        order_clause = "profit DESC"

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT 
            p.id as product_id,
            p.sku,
            p.name as product_name,
            p.category,
            p.unit_cost,
            p.selling_price,
            COALESCE(SUM(s.quantity_sold), 0) as quantity_sold,
            ROUND(COALESCE(SUM(s.revenue), 0.0), 2) as revenue,
            ROUND(COALESCE(SUM(s.profit), 0.0), 2) as profit
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id
        ORDER BY {order_clause}
        LIMIT ?
    """, (limit,))

    rows = []
    for rank, r in enumerate(cur.fetchall(), 1):
        d = dict(r)
        rev = d["revenue"]
        prof = d["profit"]
        margin = round((prof / rev * 100), 2) if rev > 0 else 0.0

        # Provide all field aliases to ensure 100% compatibility across frontend, copilot, and test suites
        d["rank"] = rank
        d["name"] = d["product_name"]
        d["total_revenue"] = rev
        d["total_units_sold"] = d["quantity_sold"]
        d["units_sold"] = d["quantity_sold"]
        d["total_profit"] = prof
        d["margin_pct"] = margin
        d["profit_margin_pct"] = margin
        rows.append(d)

    conn.close()
    return rows


# -------------------------------------------------------------------------
# 3. Daily Sales Aggregation
# -------------------------------------------------------------------------
def get_sales_by_day() -> List[Dict[str, Any]]:
    """
    Aggregates revenue and sales records by date for the available 30-day dataset.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            date,
            COUNT(*) as orders_count,
            SUM(quantity_sold) as total_units_sold,
            ROUND(SUM(revenue), 2) as revenue
        FROM sales
        GROUP BY date
        ORDER BY date ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------------------
# 4. Inventory Risks Calculation
# -------------------------------------------------------------------------
def get_inventory_risks() -> List[Dict[str, Any]]:
    """
    For every product calculates:
    - Current stock
    - Reorder level
    - Total units sold
    - Average daily sales (safe against 0 division)
    - Estimated days of stock remaining (safe against 0 division)

    Risk rules:
    - CRITICAL: days remaining <= 2
    - HIGH: days remaining > 2 and <= 5
    - LOW: stock <= reorder level but days remaining > 5
    - HEALTHY: otherwise
    """
    days_count = get_dataset_days_count()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.id as product_id,
            p.sku,
            p.name as product_name,
            p.category,
            p.supplier_name,
            p.unit_cost,
            p.selling_price,
            p.current_stock,
            p.reorder_point as reorder_level,
            p.lead_time_days,
            COALESCE(SUM(s.quantity_sold), 0) as total_units_sold,
            ROUND(COALESCE(SUM(s.revenue), 0.0), 2) as total_revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id
        ORDER BY p.id ASC
    """)

    results = []
    for r in cur.fetchall():
        d = dict(r)
        current_stock = int(d["current_stock"])
        reorder_level = int(d["reorder_level"])
        total_units_sold = int(d["total_units_sold"])

        # Average Daily Sales (ADS) calculation
        if days_count > 0:
            avg_daily_sales = round(total_units_sold / float(days_count), 2)
        else:
            avg_daily_sales = 0.0

        # Estimated days of stock remaining (Runway / DOI)
        if avg_daily_sales > 0:
            days_remaining = round(current_stock / avg_daily_sales, 2)
        else:
            days_remaining = 999.0  # Infinite runway if no demand

        # Deterministic Risk Rules
        if days_remaining <= 2.0:
            risk_status = "CRITICAL"
        elif days_remaining <= 5.0:
            risk_status = "HIGH"
        elif current_stock <= reorder_level:
            risk_status = "LOW"
        else:
            risk_status = "HEALTHY"

        results.append({
            "product_id": d["product_id"],
            "sku": d["sku"],
            "product_name": d["product_name"],
            "category": d["category"],
            "supplier_name": d["supplier_name"],
            "unit_cost": d["unit_cost"],
            "selling_price": d["selling_price"],
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "total_units_sold": total_units_sold,
            "total_revenue": d["total_revenue"],
            "avg_daily_sales": avg_daily_sales,
            "days_remaining": days_remaining,
            "risk_status": risk_status,
            "lead_time_days": d.get("lead_time_days", 5),
        })

    conn.close()
    return results


# -------------------------------------------------------------------------
# 5. Category Performance
# -------------------------------------------------------------------------
def get_category_performance() -> List[Dict[str, Any]]:
    """
    Calculates revenue and units sold by category.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.category,
            COUNT(DISTINCT p.id) as product_count,
            COALESCE(SUM(s.quantity_sold), 0) as units_sold,
            ROUND(COALESCE(SUM(s.revenue), 0.0), 2) as revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------------------
# 6. Product Details Lookup
# -------------------------------------------------------------------------
def get_product_details(product_name: str) -> Dict[str, Any]:
    """
    Returns all relevant information for a product by name or SKU.
    If product does not exist, returns a clear 'not found' result.
    """
    if not product_name or not product_name.strip():
        return {
            "found": False,
            "message": "Product name query cannot be empty."
        }

    search_term = product_name.strip()
    conn = get_db_connection()
    cur = conn.cursor()

    # Exact match first (case-insensitive)
    cur.execute("""
        SELECT 
            id, sku, name, category, unit_cost, selling_price,
            current_stock, safety_stock, reorder_point as reorder_level,
            lead_time_days, supplier_name
        FROM products
        WHERE LOWER(name) = LOWER(?) OR LOWER(sku) = LOWER(?)
    """, (search_term, search_term))
    row = cur.fetchone()

    # Substring match if exact match not found
    if not row:
        cur.execute("""
            SELECT 
                id, sku, name, category, unit_cost, selling_price,
                current_stock, safety_stock, reorder_point as reorder_level,
                lead_time_days, supplier_name
            FROM products
            WHERE LOWER(name) LIKE LOWER(?) OR LOWER(sku) LIKE LOWER(?)
            LIMIT 1
        """, (f"%{search_term}%", f"%{search_term}%"))
        row = cur.fetchone()

    if not row:
        conn.close()
        return {
            "found": False,
            "query": product_name,
            "message": f"Product '{product_name}' was not found in the database."
        }

    p = dict(row)

    # Calculate sales aggregates for this specific product
    cur.execute("""
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(quantity_sold), 0) as total_units_sold,
            COALESCE(SUM(revenue), 0.0) as total_revenue,
            COALESCE(SUM(profit), 0.0) as total_profit
        FROM sales
        WHERE product_id = ?
    """, (p["id"],))
    sales_data = dict(cur.fetchone())

    # Get distinct days count
    cur.execute("SELECT COUNT(DISTINCT date) FROM sales WHERE product_id = ?", (p["id"],))
    days_row = cur.fetchone()
    days_count = days_row[0] if days_row and days_row[0] > 0 else 30

    conn.close()

    total_units = int(sales_data["total_units_sold"])
    total_rev = round(float(sales_data["total_revenue"]), 2)
    total_prof = round(float(sales_data["total_profit"]), 2)
    avg_daily_sales = round(total_units / float(days_count), 2) if days_count > 0 else 0.0

    current_stock = int(p["current_stock"])
    reorder_level = int(p["reorder_level"])
    days_remaining = round(current_stock / avg_daily_sales, 2) if avg_daily_sales > 0 else 999.0

    if days_remaining <= 2.0:
        risk_status = "CRITICAL"
    elif days_remaining <= 5.0:
        risk_status = "HIGH"
    elif current_stock <= reorder_level:
        risk_status = "LOW"
    else:
        risk_status = "HEALTHY"

    return {
        "found": True,
        "product_id": p["id"],
        "sku": p["sku"],
        "name": p["name"],
        "category": p["category"],
        "supplier_name": p["supplier_name"],
        "unit_cost": p["unit_cost"],
        "selling_price": p["selling_price"],
        "current_stock": current_stock,
        "safety_stock": p["safety_stock"],
        "reorder_level": reorder_level,
        "lead_time_days": p["lead_time_days"],
        "total_orders": sales_data["total_orders"],
        "total_units_sold": total_units,
        "total_revenue": total_rev,
        "total_profit": total_prof,
        "profit_margin_pct": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0.0,
        "avg_daily_sales": avg_daily_sales,
        "days_remaining": days_remaining,
        "risk_status": risk_status,
    }


# -------------------------------------------------------------------------
# Legacy Compatibility Aliases (for existing API endpoints)
# -------------------------------------------------------------------------
def get_executive_kpis(days: int = 30) -> Dict[str, Any]:
    metrics = get_dashboard_metrics()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(cost_total), 0), COALESCE(SUM(profit), 0) FROM sales")
    cost_total, profit_total = cur.fetchone()
    cur.execute("SELECT COUNT(*), SUM(current_stock), SUM(current_stock * unit_cost), SUM(current_stock * selling_price) FROM products")
    skus, stock_units, val_cost, val_retail = cur.fetchone()
    conn.close()

    risks = get_inventory_risks()
    crit = [r for r in risks if r["risk_status"] == "CRITICAL"]
    high = [r for r in risks if r["risk_status"] == "HIGH"]

    rev = metrics["total_revenue"]
    profit = round(profit_total, 2)
    orders = metrics["total_orders"]

    return {
        "period_days": days,
        "total_revenue": rev,
        "total_cost": round(cost_total, 2),
        "total_profit": profit,
        "gross_margin_pct": round((profit / rev * 100), 2) if rev > 0 else 0.0,
        "total_orders": orders,
        "total_units_sold": metrics["total_units_sold"],
        "avg_order_value": round((rev / orders), 2) if orders > 0 else 0.0,
        "total_skus": skus,
        "total_stock_units": stock_units,
        "inventory_valuation_cost": round(val_cost, 2),
        "inventory_valuation_retail": round(val_retail, 2),
        "critical_risk_count": len(crit),
        "high_risk_count": len(high),
        "low_stock_count": metrics["low_stock_products_count"],
    }


def get_sales_trends() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            date,
            COUNT(*) as orders_count,
            SUM(quantity_sold) as units_sold,
            ROUND(SUM(revenue), 2) as daily_revenue,
            ROUND(SUM(profit), 2) as daily_profit
        FROM sales
        GROUP BY date
        ORDER BY date ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_category_breakdown() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.category,
            COUNT(DISTINCT p.id) as product_count,
            COALESCE(SUM(s.quantity_sold), 0) as units_sold,
            ROUND(COALESCE(SUM(s.revenue), 0), 2) as total_revenue,
            ROUND(COALESCE(SUM(s.profit), 0), 2) as total_profit,
            COALESCE(SUM(p.current_stock), 0) as total_stock_units,
            ROUND(COALESCE(SUM(p.current_stock * p.unit_cost), 0), 2) as inventory_valuation
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.category
        ORDER BY total_revenue DESC
    """)
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        rev = d["total_revenue"]
        prof = d["total_profit"]
        d["margin_pct"] = round((prof / rev * 100), 2) if rev > 0 else 0.0
        rows.append(d)
    conn.close()
    return rows


def get_channel_breakdown() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            channel,
            COUNT(*) as orders_count,
            SUM(quantity_sold) as units_sold,
            ROUND(SUM(revenue), 2) as total_revenue,
            ROUND(SUM(profit), 2) as total_profit
        FROM sales
        GROUP BY channel
        ORDER BY total_revenue DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_inventory_health() -> List[Dict[str, Any]]:
    """Returns inventory health formatted for UI display with risk badges."""
    risks = get_inventory_risks()
    badge_map = {
        "CRITICAL": ("bg-red-500 text-white", "Critical Stockout Imminent"),
        "HIGH": ("bg-amber-500 text-white", "Reorder Needed Immediately"),
        "LOW": ("bg-yellow-500 text-gray-900", "Low Stock Watchlist"),
        "HEALTHY": ("bg-emerald-500 text-white", "Healthy Supply"),
    }
    for item in risks:
        badge, status_text = badge_map.get(item["risk_status"], ("bg-slate-500 text-white", "Normal"))
        item["risk_level"] = item["risk_status"].capitalize()
        item["risk_badge"] = badge
        item["status_text"] = status_text
        item["days_of_inventory"] = item["days_remaining"]
        item["name"] = item["product_name"]
        item["calculated_reorder_point"] = item["reorder_level"]
        # Suggested reorder target
        target = int(round((30 * item["avg_daily_sales"]) + 15))
        item["suggested_reorder_qty"] = max(0, target - item["current_stock"])
        item["reorder_estimated_cost"] = round(item["suggested_reorder_qty"] * item["unit_cost"], 2)
    return risks


def get_stockout_risks() -> List[Dict[str, Any]]:
    health = get_inventory_health()
    filtered = [p for p in health if p["risk_status"] in ("CRITICAL", "HIGH", "LOW")]
    filtered.sort(key=lambda x: (x["days_remaining"], x["current_stock"]))
    return filtered


def get_grounded_context_for_query(query: str = "") -> Dict[str, Any]:
    return {
        "dashboard_metrics": get_dashboard_metrics(),
        "inventory_risks": get_inventory_risks(),
        "top_products": get_top_products(limit=5),
        "categories": get_category_performance(),
        "sales_by_day": get_sales_by_day()[:7],  # Recent trend sample
    }


# -------------------------------------------------------------------------
# 7. Supplier Analytics & Purchase Order Automation
# -------------------------------------------------------------------------
def get_supplier_performance() -> List[Dict[str, Any]]:
    """
    Calculates operational and risk exposure metrics per supplier.
    Aggregates product catalog counts, stock valuation, lead times,
    revenue generated, and stockout threats per supplier.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.supplier_name,
            COUNT(DISTINCT p.id) as product_count,
            COALESCE(SUM(p.current_stock), 0) as total_stock_units,
            ROUND(COALESCE(SUM(p.current_stock * p.unit_cost), 0.0), 2) as inventory_valuation,
            ROUND(AVG(p.lead_time_days), 1) as avg_lead_time_days,
            COALESCE(SUM(s.quantity_sold), 0) as total_units_sold,
            ROUND(COALESCE(SUM(s.revenue), 0.0), 2) as total_revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.supplier_name
        ORDER BY total_revenue DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # Cross-reference inventory risks to identify supplier risk exposure
    inventory_items = get_inventory_health()
    for row in rows:
        sup_name = row["supplier_name"]
        sup_items = [item for item in inventory_items if item["supplier_name"] == sup_name]
        crit_items = [item for item in sup_items if item["risk_status"] == "CRITICAL"]
        high_items = [item for item in sup_items if item["risk_status"] == "HIGH"]
        reorder_units = sum(item["suggested_reorder_qty"] for item in sup_items)
        reorder_cost = round(sum(item["reorder_estimated_cost"] for item in sup_items), 2)

        row["critical_risk_skus"] = len(crit_items)
        row["high_risk_skus"] = len(high_items)
        row["suggested_reorder_units"] = reorder_units
        row["suggested_reorder_cost"] = reorder_cost
        row["risk_exposure"] = "CRITICAL" if len(crit_items) > 0 else ("HIGH" if len(high_items) > 0 else "STABLE")

    return rows


def generate_purchase_orders_csv() -> str:
    """
    Generates an RFC 4180-compliant CSV string containing purchase orders
    for all products requiring replenishment, prioritized by runway urgency.
    """
    items = get_inventory_health()
    reorder_items = [p for p in items if p["suggested_reorder_qty"] > 0]
    # Sort by urgency: lowest days remaining first
    reorder_items.sort(key=lambda x: (x["days_remaining"], -x["suggested_reorder_qty"]))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "PO_Number",
        "SKU",
        "Product_Name",
        "Category",
        "Supplier_Name",
        "Current_Stock",
        "Reorder_Level",
        "Days_Runway",
        "Suggested_Reorder_Qty",
        "Unit_Cost",
        "Estimated_Total_Cost",
        "Lead_Time_Days",
        "Priority_Level"
    ])

    for idx, item in enumerate(reorder_items, 1):
        po_num = f"PO-2026-{idx:04d}"
        writer.writerow([
            po_num,
            item["sku"],
            item["name"],
            item["category"],
            item["supplier_name"],
            item["current_stock"],
            item["reorder_level"],
            item["days_remaining"],
            item["suggested_reorder_qty"],
            f"{item['unit_cost']:.2f}",
            f"{item['reorder_estimated_cost']:.2f}",
            item["lead_time_days"],
            item["risk_status"]
        ])

    return output.getvalue()


def get_inventory_health_summary() -> Dict[str, Any]:
    """
    Returns high-level executive inventory health statistics.
    """
    health = get_inventory_health()
    total_skus = len(health)
    crit = [p for p in health if p["risk_status"] == "CRITICAL"]
    high = [p for p in health if p["risk_status"] == "HIGH"]
    low = [p for p in health if p["risk_status"] == "LOW"]
    healthy = [p for p in health if p["risk_status"] == "HEALTHY"]

    total_reorder_qty = sum(p["suggested_reorder_qty"] for p in health)
    total_reorder_cost = round(sum(p["reorder_estimated_cost"] for p in health), 2)

    return {
        "total_skus": total_skus,
        "critical_skus_count": len(crit),
        "high_risk_skus_count": len(high),
        "low_risk_skus_count": len(low),
        "healthy_skus_count": len(healthy),
        "critical_products": [p["name"] for p in crit],
        "total_suggested_reorder_units": total_reorder_qty,
        "total_suggested_reorder_cost": total_reorder_cost,
        "inventory_health_score_pct": round((len(healthy) / total_skus * 100), 1) if total_skus > 0 else 0.0
    }


# -------------------------------------------------------------------------
# 8. Advanced Inventory Optimization (ABC Pareto, EOQ, & Turnover)
# -------------------------------------------------------------------------
def get_abc_classification() -> Dict[str, Any]:
    """
    Performs Pareto (80/20) ABC Inventory Classification.
    Ranks products by total revenue contribution:
    - Class A: Top ~70% cumulative revenue (tightest control & highest strategic value)
    - Class B: Next ~20% cumulative revenue (moderate control)
    - Class C: Remaining ~10% cumulative revenue (routine periodic review)
    """
    products = get_top_products(limit=100, sort_by="revenue")
    total_rev = sum(p["total_revenue"] for p in products)

    cumulative_rev = 0.0
    a_items, b_items, c_items = [], [], []

    for p in products:
        cumulative_rev += p["total_revenue"]
        cum_pct = (cumulative_rev / total_rev * 100) if total_rev > 0 else 0.0
        item_data = {
            "product_id": p["product_id"],
            "sku": p["sku"],
            "name": p["name"],
            "category": p["category"],
            "revenue": p["total_revenue"],
            "revenue_share_pct": round((p["total_revenue"] / total_rev * 100), 2) if total_rev > 0 else 0.0,
            "cumulative_revenue_pct": round(cum_pct, 2),
            "units_sold": p["total_units_sold"]
        }

        if cum_pct <= 70.0 or len(a_items) == 0:
            item_data["abc_class"] = "A"
            a_items.append(item_data)
        elif cum_pct <= 90.0 or len(b_items) == 0:
            item_data["abc_class"] = "B"
            b_items.append(item_data)
        else:
            item_data["abc_class"] = "C"
            c_items.append(item_data)

    return {
        "total_revenue": round(total_rev, 2),
        "total_skus": len(products),
        "summary": {
            "class_a": {
                "sku_count": len(a_items),
                "sku_share_pct": round(len(a_items) / len(products) * 100, 1),
                "revenue": round(sum(i["revenue"] for i in a_items), 2),
                "revenue_share_pct": round(sum(i["revenue"] for i in a_items) / total_rev * 100, 1) if total_rev > 0 else 0.0,
                "strategy": "Daily cycle counts, automated replenishment, strict safety stock."
            },
            "class_b": {
                "sku_count": len(b_items),
                "sku_share_pct": round(len(b_items) / len(products) * 100, 1),
                "revenue": round(sum(i["revenue"] for i in b_items), 2),
                "revenue_share_pct": round(sum(i["revenue"] for i in b_items) / total_rev * 100, 1) if total_rev > 0 else 0.0,
                "strategy": "Weekly review, standard reorder point policies."
            },
            "class_c": {
                "sku_count": len(c_items),
                "sku_share_pct": round(len(c_items) / len(products) * 100, 1),
                "revenue": round(sum(i["revenue"] for i in c_items), 2),
                "revenue_share_pct": round(sum(i["revenue"] for i in c_items) / total_rev * 100, 1) if total_rev > 0 else 0.0,
                "strategy": "Monthly bulk purchase orders, minimal buffer tracking."
            }
        },
        "class_a_products": a_items,
        "class_b_products": b_items,
        "class_c_products": c_items
    }


def get_eoq_analysis(order_cost: float = 35.0, holding_rate: float = 0.20) -> List[Dict[str, Any]]:
    """
    Computes Economic Order Quantity (EOQ) and optimal ordering frequencies.
    Formula: EOQ = sqrt((2 * Demand * Order_Cost) / (Holding_Cost_Per_Unit))
    - order_cost: fixed administrative ordering cost per purchase order ($35 default)
    - holding_rate: annual inventory carrying rate (20% default of unit cost)
    """
    health = get_inventory_health()
    results = []

    for item in health:
        annual_demand = round(item["avg_daily_sales"] * 365, 0)
        unit_cost = item["unit_cost"]
        annual_holding_cost = max(0.50, round(unit_cost * holding_rate, 2))

        if annual_demand > 0 and annual_holding_cost > 0:
            eoq = round(math.sqrt((2 * annual_demand * order_cost) / annual_holding_cost), 0)
            optimal_orders_per_year = round(annual_demand / eoq, 1) if eoq > 0 else 0.0
            order_interval_days = round(365 / optimal_orders_per_year, 0) if optimal_orders_per_year > 0 else 0.0
        else:
            eoq = 0.0
            optimal_orders_per_year = 0.0
            order_interval_days = 0.0

        results.append({
            "product_id": item["product_id"],
            "sku": item["sku"],
            "name": item["name"],
            "category": item["category"],
            "unit_cost": unit_cost,
            "avg_daily_sales": item["avg_daily_sales"],
            "annualized_demand": annual_demand,
            "eoq_units": int(eoq),
            "optimal_orders_per_year": optimal_orders_per_year,
            "order_interval_days": int(order_interval_days),
            "current_stock": item["current_stock"],
            "reorder_level": item["reorder_level"],
            "risk_status": item["risk_status"]
        })

    return results


def get_inventory_turnover() -> Dict[str, Any]:
    """
    Calculates inventory turnover ratios, Days Sales of Inventory (DSI),
    and detects slow-moving / dead stock threats.
    """
    kpis = get_executive_kpis()
    health = get_inventory_health()

    total_cost_goods_sold = kpis.get("total_cost", 0.0)
    inventory_val_cost = kpis.get("inventory_valuation_cost", 1.0)

    turnover_30d = (total_cost_goods_sold / inventory_val_cost) if inventory_val_cost > 0 else 0.0
    turnover_annual = round(turnover_30d * 12.0, 2)
    dsi_days = round(365.0 / turnover_annual, 1) if turnover_annual > 0 else 0.0

    slow_moving = [
        {
            "product_id": p["product_id"],
            "sku": p["sku"],
            "name": p["name"],
            "category": p["category"],
            "current_stock": p["current_stock"],
            "unit_cost": p["unit_cost"],
            "stock_value": round(p["current_stock"] * p["unit_cost"], 2),
            "days_of_inventory": p["days_of_inventory"],
            "avg_daily_sales": p["avg_daily_sales"]
        }
        for p in health
        if p["days_of_inventory"] > 45.0 or (p["avg_daily_sales"] < 1.0 and p["current_stock"] > 30)
    ]

    return {
        "period_cogs": total_cost_goods_sold,
        "current_inventory_valuation": inventory_val_cost,
        "annualized_inventory_turnover_ratio": turnover_annual,
        "days_sales_of_inventory_dsi": dsi_days,
        "turnover_benchmark": "Healthy (Target: 4-8x)" if turnover_annual >= 4.0 else "Needs Optimization",
        "slow_moving_skus_count": len(slow_moving),
        "slow_moving_capital_tied_up": round(sum(s["stock_value"] for s in slow_moving), 2),
        "slow_moving_products": slow_moving
    }


# -------------------------------------------------------------------------
# 9. GMROI & Inventory Productivity Matrix
# -------------------------------------------------------------------------
def get_gmroi_analysis() -> Dict[str, Any]:
    """
    Computes Gross Margin Return on Investment (GMROI) and product quadrant categorization.
    GMROI = Gross Margin ($) / Average Inventory Cost ($)
    Measures how many gross profit dollars each dollar invested in inventory yields.

    Quadrant Classification (2x2 Matrix using Median Revenue and Median GMROI):
    - Stars (High Revenue, High GMROI): Premier cash engines; maintain 100% in-stock.
    - Traffic Builders (High Revenue, Low GMROI): High customer velocity; optimize pricing/margins.
    - Profit Generators (Low Revenue, High GMROI): Highly efficient margins; boost marketing & prominence.
    - Underperformers (Low Revenue, Low GMROI): Weak velocity and low return; bundle, discount, or phase out.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.id, p.sku, p.name, p.category, p.unit_cost, p.selling_price, p.current_stock,
            COALESCE(SUM(s.revenue), 0.0) as revenue,
            COALESCE(SUM(s.profit), 0.0) as profit,
            COALESCE(SUM(s.quantity_sold), 0) as units_sold
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id
        ORDER BY revenue DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not rows:
        return {"total_skus": 0, "store_gmroi": 0.0, "quadrants": {}, "products": []}

    # Calculate baseline metrics for each product
    analyzed_items = []
    total_store_profit = sum(r["profit"] for r in rows)
    total_store_inv_cost = sum(r["current_stock"] * r["unit_cost"] for r in rows)
    store_gmroi = round(total_store_profit / total_store_inv_cost, 2) if total_store_inv_cost > 0 else 0.0

    for r in rows:
        inv_cost = max(10.0, round(r["current_stock"] * r["unit_cost"], 2))
        profit = round(r["profit"], 2)
        revenue = round(r["revenue"], 2)
        gmroi = round(profit / inv_cost, 2)
        annualized_gmroi = round(gmroi * (365.0 / 30.0), 2)
        margin_pct = round((profit / revenue * 100), 1) if revenue > 0 else 0.0

        analyzed_items.append({
            "product_id": r["id"],
            "sku": r["sku"],
            "name": r["name"],
            "category": r["category"],
            "unit_cost": r["unit_cost"],
            "selling_price": r["selling_price"],
            "current_stock": r["current_stock"],
            "inventory_valuation_cost": inv_cost,
            "units_sold": r["units_sold"],
            "revenue": revenue,
            "profit": profit,
            "margin_pct": margin_pct,
            "gmroi": gmroi,
            "annualized_gmroi": annualized_gmroi,
        })

    # Medians for 2x2 matrix thresholding
    sorted_rev = sorted([item["revenue"] for item in analyzed_items])
    sorted_gmroi = sorted([item["gmroi"] for item in analyzed_items])
    median_revenue = sorted_rev[len(sorted_rev) // 2]
    median_gmroi = sorted_gmroi[len(sorted_gmroi) // 2]

    stars = []
    traffic_builders = []
    profit_generators = []
    underperformers = []

    for item in analyzed_items:
        is_high_rev = item["revenue"] >= median_revenue
        is_high_gmroi = item["gmroi"] >= median_gmroi

        if is_high_rev and is_high_gmroi:
            item["quadrant"] = "Star"
            item["action"] = "Core profit driver; protect safety stock and prioritize prime shelf placement."
            stars.append(item)
        elif is_high_rev and not is_high_gmroi:
            item["quadrant"] = "Traffic Builder"
            item["action"] = "High sales pace with lower capital return; explore modest price increase or supplier discounts."
            traffic_builders.append(item)
        elif not is_high_rev and is_high_gmroi:
            item["quadrant"] = "Profit Generator"
            item["action"] = "High capital efficiency; boost promotional visibility and cross-selling bundles."
            profit_generators.append(item)
        else:
            item["quadrant"] = "Underperformer"
            item["action"] = "Sub-median sales and return; evaluate discount promotion, bundle liquidation, or phase-out."
            underperformers.append(item)

    # Category GMROI summary
    categories_dict: Dict[str, Dict[str, Any]] = {}
    for item in analyzed_items:
        cat = item["category"]
        if cat not in categories_dict:
            categories_dict[cat] = {"category": cat, "profit": 0.0, "inv_cost": 0.0, "product_count": 0}
        categories_dict[cat]["profit"] += item["profit"]
        categories_dict[cat]["inv_cost"] += item["inventory_valuation_cost"]
        categories_dict[cat]["product_count"] += 1

    category_gmroi = []
    for cat_data in categories_dict.values():
        c_profit = cat_data["profit"]
        c_inv = cat_data["inv_cost"]
        c_gmroi = round(c_profit / c_inv, 2) if c_inv > 0 else 0.0
        category_gmroi.append({
            "category": cat_data["category"],
            "gmroi": c_gmroi,
            "product_count": cat_data["product_count"],
            "total_profit": round(c_profit, 2),
            "total_inv_cost": round(c_inv, 2)
        })
    category_gmroi.sort(key=lambda x: x["gmroi"], reverse=True)

    return {
        "total_skus": len(analyzed_items),
        "store_average_gmroi": store_gmroi,
        "median_revenue_threshold": round(median_revenue, 2),
        "median_gmroi_threshold": round(median_gmroi, 2),
        "quadrant_counts": {
            "stars": len(stars),
            "traffic_builders": len(traffic_builders),
            "profit_generators": len(profit_generators),
            "underperformers": len(underperformers)
        },
        "quadrants": {
            "stars": stars,
            "traffic_builders": traffic_builders,
            "profit_generators": profit_generators,
            "underperformers": underperformers
        },
        "category_gmroi": category_gmroi,
        "all_products": analyzed_items
    }


# -------------------------------------------------------------------------
# 10. Predictive Demand Forecasting & Statistical Safety Stock Engine
# -------------------------------------------------------------------------
def _normal_cdf(z: float) -> float:
    """Calculates cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def get_demand_forecast(horizon_days: int = 7) -> Dict[str, Any]:
    """
    Computes forward-looking demand forecasts, dynamic statistical safety stocks,
    and lead-time stockout probabilities for all catalog products.

    - Uses exponentially weighted blend of recent 7-day velocity (60%) and 30-day baseline (40%).
    - Computes empirical daily demand standard deviation (sigma_d).
    - Statistical Safety Stock: Z(95%) * sigma_d * sqrt(Lead_Time) where Z = 1.65.
    - Stockout Risk Probability: Gaussian CDF evaluation of lead time stock coverage.
    """
    if horizon_days <= 0:
        horizon_days = 7

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, sku, name, category, unit_cost, selling_price, current_stock, lead_time_days, supplier_name
        FROM products
        ORDER BY id ASC
    """)
    products = [dict(r) for r in cur.fetchall()]

    forecasted_products = []
    total_proj_units = 0
    total_proj_revenue = 0.0

    for p in products:
        p_id = p["id"]
        cur.execute("""
            SELECT date, COALESCE(SUM(quantity_sold), 0) as units
            FROM sales
            WHERE product_id = ?
            GROUP BY date
            ORDER BY date ASC
        """, (p_id,))
        daily_records = [r["units"] for r in cur.fetchall()]

        n_days = len(daily_records)
        mean_30d = (sum(daily_records) / n_days) if n_days > 0 else 0.0

        # Sample standard deviation of daily sales (sigma_d)
        if n_days > 1:
            variance = sum((x - mean_30d) ** 2 for x in daily_records) / (n_days - 1)
            sigma_d = round(math.sqrt(variance), 2)
        else:
            sigma_d = 0.5

        # Recent 7-day velocity
        recent_7 = daily_records[-7:] if n_days >= 7 else daily_records
        mean_7d = (sum(recent_7) / len(recent_7)) if recent_7 else mean_30d

        # Exponentially smoothed pace: 60% recent velocity + 40% monthly baseline
        smoothed_daily_pace = round((0.60 * mean_7d) + (0.40 * mean_30d), 2)
        momentum = round((mean_7d / mean_30d), 2) if mean_30d > 0 else 1.0

        # Horizon projections
        projected_units = max(0, int(round(smoothed_daily_pace * horizon_days)))
        projected_revenue = round(projected_units * p["selling_price"], 2)

        total_proj_units += projected_units
        total_proj_revenue += projected_revenue

        # Statistical Safety Stock (95% Service Level SLA: Z = 1.65)
        lead_time = max(1, p["lead_time_days"])
        stat_safety_stock = max(1, int(round(1.65 * sigma_d * math.sqrt(lead_time))))

        # Lead time demand & stockout probability
        lead_time_demand = round(mean_30d * lead_time, 1)
        sigma_lead_time = max(0.5, sigma_d * math.sqrt(lead_time))
        current_stock = p["current_stock"]

        # Z-score for current stock coverage during replenishment window
        z_score = (current_stock - lead_time_demand) / sigma_lead_time
        stockout_prob_pct = round(max(0.0, min(100.0, (1.0 - _normal_cdf(z_score)) * 100.0)), 1)

        is_under_buffered = current_stock < stat_safety_stock
        target_reorder_qty = max(0, int(round(lead_time_demand + stat_safety_stock - current_stock)))

        forecasted_products.append({
            "product_id": p_id,
            "sku": p["sku"],
            "name": p["name"],
            "category": p["category"],
            "supplier_name": p["supplier_name"],
            "unit_cost": p["unit_cost"],
            "selling_price": p["selling_price"],
            "current_stock": current_stock,
            "lead_time_days": lead_time,
            "baseline_daily_pace": round(mean_30d, 2),
            "recent_7d_pace": round(mean_7d, 2),
            "smoothed_daily_pace": smoothed_daily_pace,
            "demand_momentum": momentum,
            "daily_sales_std_dev": sigma_d,
            "forecast_horizon_days": horizon_days,
            "forecast_units": projected_units,
            "forecast_revenue": projected_revenue,
            "lead_time_demand": lead_time_demand,
            "statistical_safety_stock": stat_safety_stock,
            "stockout_probability_pct": stockout_prob_pct,
            "is_under_buffered": is_under_buffered,
            "suggested_reorder_qty": target_reorder_qty
        })

    conn.close()

    # Sort products by stockout probability descending, then revenue impact
    forecasted_products.sort(key=lambda x: (-x["stockout_probability_pct"], -x["forecast_revenue"]))

    high_risk_count = sum(1 for p in forecasted_products if p["stockout_probability_pct"] >= 50.0)
    under_buffered_count = sum(1 for p in forecasted_products if p["is_under_buffered"])

    return {
        "forecast_horizon_days": horizon_days,
        "total_catalog_skus": len(forecasted_products),
        "total_projected_units": total_proj_units,
        "total_projected_revenue": round(total_proj_revenue, 2),
        "high_stockout_risk_skus_count": high_risk_count,
        "under_buffered_skus_count": under_buffered_count,
        "top_forecast_revenue_drivers": sorted(forecasted_products, key=lambda x: x["forecast_revenue"], reverse=True)[:5],
        "products": forecasted_products
    }



