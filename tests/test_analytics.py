"""
Unit tests for deterministic business calculations in analytics.py.
"""
import analytics


def test_dashboard_metrics():
    """Verify high-level sales and operational metrics."""
    metrics = analytics.get_dashboard_metrics()
    assert "total_revenue" in metrics
    assert "total_units_sold" in metrics
    assert "total_orders" in metrics
    assert "low_stock_products_count" in metrics

    assert metrics["total_revenue"] > 100000.0
    assert metrics["total_orders"] == 1495
    assert metrics["total_units_sold"] > 3000
    assert metrics["low_stock_products_count"] == 4


def test_top_products_limit_and_sorting():
    """Verify ranking products by revenue, units sold, and profit."""
    top_5 = analytics.get_top_products(limit=5, sort_by="revenue")
    assert len(top_5) == 5
    for i in range(len(top_5) - 1):
        assert top_5[i]["total_revenue"] >= top_5[i + 1]["total_revenue"]
        assert top_5[i]["rank"] == i + 1

    # Units sorting
    top_units = analytics.get_top_products(limit=3, sort_by="units")
    assert len(top_units) == 3
    assert top_units[0]["total_units_sold"] >= top_units[1]["total_units_sold"]

    # Profit sorting
    top_profit = analytics.get_top_products(limit=3, sort_by="profit")
    assert len(top_profit) == 3
    assert top_profit[0]["total_profit"] >= top_profit[1]["total_profit"]


def test_sales_by_day_aggregation():
    """Verify 30-day time-series aggregation continuity."""
    daily_sales = analytics.get_sales_by_day()
    assert len(daily_sales) == 30
    for day in daily_sales:
        assert "date" in day
        assert day["orders_count"] > 0
        assert day["revenue"] > 0.0


def test_inventory_risks_and_runway_rules():
    """Verify inventory risk calculation rules and safe division."""
    risks = analytics.get_inventory_risks()
    assert len(risks) == 25

    critical_items = [p for p in risks if p["risk_status"] == "CRITICAL"]
    high_items = [p for p in risks if p["risk_status"] == "HIGH"]
    healthy_items = [p for p in risks if p["risk_status"] == "HEALTHY"]

    # Exactly 4 intentionally low-stock products in benchmark dataset
    assert len(critical_items) == 4
    for p in critical_items:
        assert p["days_remaining"] <= 2.0

    for p in healthy_items:
        assert p["days_remaining"] > 5.0 or p["current_stock"] > p["reorder_level"]


def test_category_performance_breakdown():
    """Verify category aggregations across all 5 product categories."""
    cats = analytics.get_category_performance()
    assert len(cats) == 5
    total_rev = sum(c["revenue"] for c in cats)
    dash_rev = analytics.get_dashboard_metrics()["total_revenue"]
    assert abs(total_rev - dash_rev) < 1.0


def test_product_details_lookup():
    """Verify exact lookup, partial search, and not-found handling."""
    # Exact lookup
    item = analytics.get_product_details("Ultra ANC Wireless Headphones")
    assert item["found"] is True
    assert item["sku"] == "SKU-ELC-001"
    assert item["risk_status"] == "CRITICAL"

    # Substring search
    partial = analytics.get_product_details("Espresso")
    assert partial["found"] is True
    assert "Espresso" in partial["name"]

    # Not found search
    missing = analytics.get_product_details("iPhone 16 Pro Max")
    assert missing["found"] is False
    assert "not found" in missing["message"].lower()

    # Empty search
    empty = analytics.get_product_details("")
    assert empty["found"] is False


def test_supplier_performance():
    """Verify supplier operational aggregation and risk tagging."""
    suppliers = analytics.get_supplier_performance()
    assert len(suppliers) == 5
    for s in suppliers:
        assert s["product_count"] > 0
        assert s["avg_lead_time_days"] > 0
        assert s["total_revenue"] > 0
        assert s["risk_exposure"] in ("CRITICAL", "HIGH", "STABLE")


def test_inventory_health_summary():
    """Verify executive inventory health score and critical counts."""
    summary = analytics.get_inventory_health_summary()
    assert summary["total_skus"] == 25
    assert summary["critical_skus_count"] == 4
    assert len(summary["critical_products"]) == 4
    assert summary["total_suggested_reorder_units"] > 0
    assert summary["inventory_health_score_pct"] > 50.0


def test_generate_purchase_orders_csv():
    """Verify CSV header, columns, and data completeness."""
    csv_text = analytics.generate_purchase_orders_csv()
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    assert len(lines) >= 20  # multiple items need reordering
    header = lines[0].split(",")
    assert "PO_Number" in header
    assert "SKU" in header
    assert "Supplier_Name" in header
    assert "Suggested_Reorder_Qty" in header
    assert "Priority_Level" in header
