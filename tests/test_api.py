"""
Integration tests for FastAPI REST endpoints using TestClient.
"""


def test_serve_dashboard(client):
    """GET / serves the single-page dashboard HTML."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Retail" in res.text
    assert "TRACK_ID: PS03" in res.text


def test_api_health(client):
    """GET /api/health returns healthy status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["track_id"] == "PS03"
    assert "database" in data


def test_api_kpis(client):
    """GET /api/kpis returns executive revenue and profit KPIs."""
    res = client.get("/api/kpis")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] > 100000.0
    assert data["total_profit"] > 50000.0
    assert data["total_orders"] == 1495
    assert data["critical_risk_count"] == 4


def test_api_sales_trends(client):
    """GET /api/sales/trends returns 30-day time-series array."""
    res = client.get("/api/sales/trends")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 30
    assert "daily_revenue" in data[0]
    assert "daily_profit" in data[0]


def test_api_categories(client):
    """GET /api/categories returns breakdown across all 5 categories."""
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert "category" in data[0]
    assert "total_revenue" in data[0]


def test_api_channels(client):
    """GET /api/channels returns In-Store vs Online split."""
    res = client.get("/api/channels")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    channels = {c["channel"] for c in data}
    assert channels == {"In-Store", "Online"}


def test_api_top_products(client):
    """GET /api/top-products returns top 5 ranked products."""
    res = client.get("/api/top-products")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert data[0]["rank"] == 1
    assert data[0]["name"] == "Ultra ANC Wireless Headphones"


def test_api_inventory(client):
    """GET /api/inventory returns catalog of 25 products with DOI runway."""
    res = client.get("/api/inventory")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 25
    assert "days_of_inventory" in data[0]
    assert "risk_status" in data[0]


def test_api_risks(client):
    """GET /api/risks returns 4 critical low-stock items."""
    res = client.get("/api/risks")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    for item in data:
        assert item["risk_status"] == "CRITICAL"


def test_api_suppliers(client):
    """GET /api/suppliers returns supplier performance and exposure."""
    res = client.get("/api/suppliers")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert "supplier_name" in data[0]
    assert "risk_exposure" in data[0]


def test_api_inventory_summary(client):
    """GET /api/inventory/summary returns executive stock health."""
    res = client.get("/api/inventory/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_skus"] == 25
    assert data["critical_skus_count"] == 4


def test_api_export_purchase_orders(client):
    """GET /api/export/purchase-orders returns downloadable CSV."""
    res = client.get("/api/export/purchase-orders")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "PO_Number" in res.text


def test_api_copilot_chat(client):
    """POST /api/copilot/chat returns grounded response."""
    res = client.post("/api/copilot/chat", json={"query": "Which products need attention today?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "evidence_metrics" in data
    assert len(data["evidence_metrics"]) == 4
    assert data["intent"] == "CRITICAL_INVENTORY_ATTENTION"
