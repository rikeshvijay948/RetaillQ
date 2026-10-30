"""
Unit tests for database schema, connection, and data integrity.
"""
import sqlite3
import database


def test_db_connection():
    """Verify that get_db_connection returns an active connection with Row factory."""
    conn = database.get_db_connection()
    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row
    conn.close()


def test_products_table_count():
    """Verify exactly 25 products exist in the database."""
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 25


def test_sales_table_count():
    """Verify exactly 1,495 sales records exist in the database."""
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sales")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1495


def test_categories_count():
    """Verify 5 distinct categories exist."""
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM products")
    categories = [r[0] for r in cur.fetchall()]
    conn.close()
    assert len(categories) == 5
    assert set(categories) == {
        "Electronics",
        "Apparel",
        "Home & Kitchen",
        "Health & Beauty",
        "Groceries & Snacks",
    }


def test_product_schema_integrity():
    """Verify product records contain positive prices, non-negative stock, and valid SKUs."""
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sku, name, unit_cost, selling_price, current_stock, lead_time_days FROM products")
    rows = cur.fetchall()
    conn.close()

    for r in rows:
        assert r["sku"].startswith("SKU-")
        assert len(r["name"]) > 0
        assert r["unit_cost"] > 0
        assert r["selling_price"] >= r["unit_cost"]
        assert r["current_stock"] >= 0
        assert r["lead_time_days"] > 0


def test_sales_financial_math():
    """Verify revenue = quantity * unit_price and profit = revenue - cost_total for every record."""
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT quantity_sold, unit_price, revenue, cost_total, profit FROM sales LIMIT 100")
    rows = cur.fetchall()
    conn.close()

    for r in rows:
        expected_rev = round(r["quantity_sold"] * r["unit_price"], 2)
        assert abs(r["revenue"] - expected_rev) < 0.05
        expected_prof = round(r["revenue"] - r["cost_total"], 2)
        assert abs(r["profit"] - expected_prof) < 0.05
