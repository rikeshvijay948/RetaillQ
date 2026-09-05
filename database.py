"""
RetailIQ - Database Management & Local Seed Dataset
Handles SQLite initialization, schema creation, and deterministic sample data seeding.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retailiq.db")


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reseed: bool = False):
    """Initializes the database tables and seeds 25 products with 30 days of realistic sales data."""
    if force_reseed and os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Create Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_cost REAL NOT NULL,
        selling_price REAL NOT NULL,
        current_stock INTEGER NOT NULL,
        safety_stock INTEGER NOT NULL,
        reorder_point INTEGER NOT NULL,
        lead_time_days INTEGER NOT NULL,
        supplier_name TEXT NOT NULL
    );
    """)

    # 2. Create Sales History Table (30 days)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity_sold INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        revenue REAL NOT NULL,
        cost_total REAL NOT NULL,
        profit REAL NOT NULL,
        channel TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    # Check if data is already seeded
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.commit()
    conn.close()


def seed_data(conn: sqlite3.Connection):
    """Seeds 25 realistic products across 5 categories with 4 intentionally low-stock items and 30-day sales."""
    cursor = conn.cursor()

    # 25 Products (5 Categories x 5 Products)
    # Intentionally low-stock products:
    # 1. SKU-ELC-001: Ultra ANC Wireless Headphones (stock: 3, daily sales ~4.5) -> Critical Risk
    # 2. SKU-GRO-001: Organic Fair-Trade Espresso Beans (stock: 5, daily sales ~8.4) -> Critical Risk
    # 3. SKU-HOM-001: Ergonomic Memory Foam Pillow (stock: 4, daily sales ~5.1) -> Critical Risk
    # 4. SKU-BEA-001: Hydrating Hyaluronic Acid Serum (stock: 6, daily sales ~7.0) -> Critical Risk

    products = [
        # --- Category 1: Electronics (Supplier: Apex Tech Logistics) ---
        {
            "sku": "SKU-ELC-001",
            "name": "Ultra ANC Wireless Headphones",
            "category": "Electronics",
            "unit_cost": 85.00,
            "selling_price": 149.99,
            "current_stock": 3,          # <--- INTENTIONALLY LOW STOCK (Critical Risk)
            "safety_stock": 15,
            "reorder_point": 35,
            "lead_time_days": 7,
            "supplier_name": "Apex Tech Logistics",
            "avg_daily_target": 4.5
        },
        {
            "sku": "SKU-ELC-002",
            "name": "Smart Fitness Watch V3",
            "category": "Electronics",
            "unit_cost": 45.00,
            "selling_price": 89.99,
            "current_stock": 52,
            "safety_stock": 12,
            "reorder_point": 25,
            "lead_time_days": 5,
            "supplier_name": "Apex Tech Logistics",
            "avg_daily_target": 3.2
        },
        {
            "sku": "SKU-ELC-003",
            "name": "65W USB-C Fast Charger",
            "category": "Electronics",
            "unit_cost": 11.50,
            "selling_price": 29.99,
            "current_stock": 120,
            "safety_stock": 25,
            "reorder_point": 50,
            "lead_time_days": 4,
            "supplier_name": "Apex Tech Logistics",
            "avg_daily_target": 6.8
        },
        {
            "sku": "SKU-ELC-004",
            "name": "Mechanical RGB Gaming Keyboard",
            "category": "Electronics",
            "unit_cost": 42.00,
            "selling_price": 79.99,
            "current_stock": 38,
            "safety_stock": 10,
            "reorder_point": 20,
            "lead_time_days": 6,
            "supplier_name": "Apex Tech Logistics",
            "avg_daily_target": 2.1
        },
        {
            "sku": "SKU-ELC-005",
            "name": "Portable Bluetooth Speaker Mini",
            "category": "Electronics",
            "unit_cost": 18.00,
            "selling_price": 39.99,
            "current_stock": 64,
            "safety_stock": 15,
            "reorder_point": 30,
            "lead_time_days": 5,
            "supplier_name": "Apex Tech Logistics",
            "avg_daily_target": 3.5
        },

        # --- Category 2: Apparel (Supplier: ThreadCraft Distributing) ---
        {
            "sku": "SKU-APP-001",
            "name": "Classic Crewneck Organic Cotton Tee",
            "category": "Apparel",
            "unit_cost": 8.00,
            "selling_price": 24.50,
            "current_stock": 145,
            "safety_stock": 30,
            "reorder_point": 65,
            "lead_time_days": 5,
            "supplier_name": "ThreadCraft Distributing",
            "avg_daily_target": 7.5
        },
        {
            "sku": "SKU-APP-002",
            "name": "Slim-Fit Stretch Denim Jeans",
            "category": "Apparel",
            "unit_cost": 22.00,
            "selling_price": 58.00,
            "current_stock": 48,
            "safety_stock": 15,
            "reorder_point": 32,
            "lead_time_days": 6,
            "supplier_name": "ThreadCraft Distributing",
            "avg_daily_target": 3.0
        },
        {
            "sku": "SKU-APP-003",
            "name": "Water-Resistant Hooded Windbreaker",
            "category": "Apparel",
            "unit_cost": 28.00,
            "selling_price": 69.99,
            "current_stock": 34,
            "safety_stock": 10,
            "reorder_point": 22,
            "lead_time_days": 7,
            "supplier_name": "ThreadCraft Distributing",
            "avg_daily_target": 1.8
        },
        {
            "sku": "SKU-APP-004",
            "name": "Athletic Moisture-Wicking Socks (3-Pack)",
            "category": "Apparel",
            "unit_cost": 4.20,
            "selling_price": 14.99,
            "current_stock": 190,
            "safety_stock": 35,
            "reorder_point": 70,
            "lead_time_days": 4,
            "supplier_name": "ThreadCraft Distributing",
            "avg_daily_target": 8.2
        },
        {
            "sku": "SKU-APP-005",
            "name": "Merino Wool Blend Winter Beanie",
            "category": "Apparel",
            "unit_cost": 7.50,
            "selling_price": 22.00,
            "current_stock": 75,
            "safety_stock": 15,
            "reorder_point": 30,
            "lead_time_days": 5,
            "supplier_name": "ThreadCraft Distributing",
            "avg_daily_target": 2.4
        },

        # --- Category 3: Home & Kitchen (Supplier: Nordic Living Supplies) ---
        {
            "sku": "SKU-HOM-001",
            "name": "Ergonomic Memory Foam Pillow",
            "category": "Home & Kitchen",
            "unit_cost": 16.00,
            "selling_price": 42.50,
            "current_stock": 4,           # <--- INTENTIONALLY LOW STOCK (Critical Risk)
            "safety_stock": 12,
            "reorder_point": 30,
            "lead_time_days": 6,
            "supplier_name": "Nordic Living Supplies",
            "avg_daily_target": 5.1
        },
        {
            "sku": "SKU-HOM-002",
            "name": "Stainless Steel Pour-Over Kettle (1L)",
            "category": "Home & Kitchen",
            "unit_cost": 15.50,
            "selling_price": 38.00,
            "current_stock": 32,
            "safety_stock": 10,
            "reorder_point": 20,
            "lead_time_days": 5,
            "supplier_name": "Nordic Living Supplies",
            "avg_daily_target": 2.2
        },
        {
            "sku": "SKU-HOM-003",
            "name": "Double-Wall Insulated Travel Tumbler",
            "category": "Home & Kitchen",
            "unit_cost": 8.00,
            "selling_price": 24.99,
            "current_stock": 88,
            "safety_stock": 20,
            "reorder_point": 45,
            "lead_time_days": 4,
            "supplier_name": "Nordic Living Supplies",
            "avg_daily_target": 5.4
        },
        {
            "sku": "SKU-HOM-004",
            "name": "Non-Stick Ceramic Frying Pan (10-inch)",
            "category": "Home & Kitchen",
            "unit_cost": 19.00,
            "selling_price": 49.99,
            "current_stock": 41,
            "safety_stock": 12,
            "reorder_point": 25,
            "lead_time_days": 6,
            "supplier_name": "Nordic Living Supplies",
            "avg_daily_target": 2.5
        },
        {
            "sku": "SKU-HOM-005",
            "name": "Aromatherapy Ultrasonic Essential Oil Diffuser",
            "category": "Home & Kitchen",
            "unit_cost": 12.00,
            "selling_price": 32.00,
            "current_stock": 55,
            "safety_stock": 15,
            "reorder_point": 28,
            "lead_time_days": 5,
            "supplier_name": "Nordic Living Supplies",
            "avg_daily_target": 3.1
        },

        # --- Category 4: Health & Beauty (Supplier: PureBotanica Labs) ---
        {
            "sku": "SKU-BEA-001",
            "name": "Hydrating Hyaluronic Acid Serum (50ml)",
            "category": "Health & Beauty",
            "unit_cost": 9.50,
            "selling_price": 28.00,
            "current_stock": 6,           # <--- INTENTIONALLY LOW STOCK (Critical Risk)
            "safety_stock": 18,
            "reorder_point": 42,
            "lead_time_days": 6,
            "supplier_name": "PureBotanica Labs",
            "avg_daily_target": 7.0
        },
        {
            "sku": "SKU-BEA-002",
            "name": "Vitamin C Radiance Daily Face Moisturizer",
            "category": "Health & Beauty",
            "unit_cost": 10.00,
            "selling_price": 26.50,
            "current_stock": 62,
            "safety_stock": 15,
            "reorder_point": 35,
            "lead_time_days": 5,
            "supplier_name": "PureBotanica Labs",
            "avg_daily_target": 4.3
        },
        {
            "sku": "SKU-BEA-003",
            "name": "Mineral SPF 50 Broad Spectrum Sunscreen",
            "category": "Health & Beauty",
            "unit_cost": 8.00,
            "selling_price": 21.99,
            "current_stock": 94,
            "safety_stock": 20,
            "reorder_point": 40,
            "lead_time_days": 4,
            "supplier_name": "PureBotanica Labs",
            "avg_daily_target": 5.2
        },
        {
            "sku": "SKU-BEA-004",
            "name": "Organic Argan Oil Hair Treatment Mask",
            "category": "Health & Beauty",
            "unit_cost": 7.00,
            "selling_price": 19.50,
            "current_stock": 46,
            "safety_stock": 12,
            "reorder_point": 26,
            "lead_time_days": 5,
            "supplier_name": "PureBotanica Labs",
            "avg_daily_target": 2.9
        },
        {
            "sku": "SKU-BEA-005",
            "name": "Natural Charcoal Whitening Toothpaste (100g)",
            "category": "Health & Beauty",
            "unit_cost": 2.80,
            "selling_price": 8.99,
            "current_stock": 150,
            "safety_stock": 25,
            "reorder_point": 50,
            "lead_time_days": 4,
            "supplier_name": "PureBotanica Labs",
            "avg_daily_target": 6.1
        },

        # --- Category 5: Groceries & Snacks (Supplier: Harvest Valley Wholesale) ---
        {
            "sku": "SKU-GRO-001",
            "name": "Organic Fair-Trade Espresso Beans (1kg)",
            "category": "Groceries & Snacks",
            "unit_cost": 8.50,
            "selling_price": 22.99,
            "current_stock": 5,           # <--- INTENTIONALLY LOW STOCK (Critical Risk)
            "safety_stock": 20,
            "reorder_point": 45,
            "lead_time_days": 5,
            "supplier_name": "Harvest Valley Wholesale",
            "avg_daily_target": 8.4
        },
        {
            "sku": "SKU-GRO-002",
            "name": "Artisanal Dark Chocolate 72% Sea Salt (100g)",
            "category": "Groceries & Snacks",
            "unit_cost": 1.80,
            "selling_price": 5.49,
            "current_stock": 180,
            "safety_stock": 35,
            "reorder_point": 70,
            "lead_time_days": 3,
            "supplier_name": "Harvest Valley Wholesale",
            "avg_daily_target": 11.2
        },
        {
            "sku": "SKU-GRO-003",
            "name": "Cold-Pressed Extra Virgin Olive Oil (500ml)",
            "category": "Groceries & Snacks",
            "unit_cost": 6.20,
            "selling_price": 16.99,
            "current_stock": 70,
            "safety_stock": 15,
            "reorder_point": 30,
            "lead_time_days": 4,
            "supplier_name": "Harvest Valley Wholesale",
            "avg_daily_target": 3.7
        },
        {
            "sku": "SKU-GRO-004",
            "name": "Gluten-Free Honey Almond Granola (400g)",
            "category": "Groceries & Snacks",
            "unit_cost": 3.20,
            "selling_price": 9.25,
            "current_stock": 82,
            "safety_stock": 18,
            "reorder_point": 38,
            "lead_time_days": 4,
            "supplier_name": "Harvest Valley Wholesale",
            "avg_daily_target": 4.8
        },
        {
            "sku": "SKU-GRO-005",
            "name": "Raw Organic Wildflower Honey (500g)",
            "category": "Groceries & Snacks",
            "unit_cost": 4.50,
            "selling_price": 12.50,
            "current_stock": 60,
            "safety_stock": 15,
            "reorder_point": 28,
            "lead_time_days": 5,
            "supplier_name": "Harvest Valley Wholesale",
            "avg_daily_target": 3.0
        }
    ]

    # Insert products and record their assigned IDs
    inserted_products = []
    for p in products:
        cursor.execute("""
        INSERT INTO products (
            sku, name, category, unit_cost, selling_price,
            current_stock, safety_stock, reorder_point,
            lead_time_days, supplier_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["sku"], p["name"], p["category"], p["unit_cost"],
            p["selling_price"], p["current_stock"], p["safety_stock"],
            p["reorder_point"], p["lead_time_days"], p["supplier_name"]
        ))
        p_id = cursor.lastrowid
        inserted_products.append({**p, "id": p_id})

    # Seed 30 Days of Realistic Sales Data
    rng = random.Random(42)
    end_date = datetime(2026, 9, 4)
    start_date = end_date - timedelta(days=29)

    sales_records = []
    channels = ["In-Store", "Online"]
    channel_weights = [0.65, 0.35]

    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        is_weekend = current_date.weekday() >= 5  # Saturday or Sunday
        weekend_multiplier = 1.35 if is_weekend else 1.0

        for prod in inserted_products:
            # Base daily demand with slight variance and weekend lift
            base_demand = prod["avg_daily_target"] * weekend_multiplier
            variance = rng.uniform(0.75, 1.25)
            daily_units = max(1, int(round(base_demand * variance)))

            # Split daily sales into 1-3 transactions (In-Store vs Online)
            num_txns = rng.choice([1, 2, 2, 3])
            remaining_units = daily_units

            for i in range(num_txns):
                if remaining_units <= 0:
                    break
                if i == num_txns - 1:
                    qty = remaining_units
                else:
                    qty = max(1, remaining_units // (num_txns - i))
                remaining_units -= qty

                channel = rng.choices(channels, weights=channel_weights, k=1)[0]
                unit_price = prod["selling_price"]
                revenue = round(qty * unit_price, 2)
                cost_total = round(qty * prod["unit_cost"], 2)
                profit = round(revenue - cost_total, 2)

                sales_records.append((
                    date_str, prod["id"], qty, unit_price,
                    revenue, cost_total, profit, channel
                ))

    cursor.executemany("""
    INSERT INTO sales (
        date, product_id, quantity_sold, unit_price,
        revenue, cost_total, profit, channel
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sales_records)

    conn.commit()


if __name__ == "__main__":
    print(f"Initializing database at: {DB_FILE}")
    init_db(force_reseed=True)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    prod_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*), SUM(revenue), SUM(quantity_sold) FROM sales")
    sales_count, total_rev, total_units = c.fetchone()
    print(f"Products seeded: {prod_count}")
    print(f"Sales records seeded: {sales_count}")
    print(f"Total 30-day Revenue: ${total_rev:,.2f}")
    print(f"Total 30-day Units Sold: {total_units:,}")
    conn.close()
