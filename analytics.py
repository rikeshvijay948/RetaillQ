"""
RetailIQ - Deterministic Analytics Engine (TRACK_ID=PS03)
Performs all mathematical, inventory risk, and sales calculations in pure Python/SQLite.
All facts are strictly verified and deterministic (Zero AI hallucination).
"""

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

