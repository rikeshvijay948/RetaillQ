"""
RetailIQ - Main Application Entry Point (TRACK_ID=PS03)
FastAPI server serving API and Frontend on Port 8000.
Single-command startup: python app.py
"""

import os
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import uvicorn

# Load environment variables securely from .env if present
load_dotenv(find_dotenv(), override=True)

import database
import analytics
import copilot

# Initialize SQLite database and seed deterministic data on startup
database.init_db(force_reseed=False)

app = FastAPI(
    title="RetailIQ - Sales & Inventory Copilot",
    description="Deterministic retail operations engine with evidence-grounded Gemini AI copilot.",
    version="1.0.0"
)

# Enable CORS for local convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets and Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


class ChatQueryRequest(BaseModel):
    query: str


# ----------------- Frontend Route -----------------
@app.get("/")
async def serve_dashboard(request: Request):
    """Serves the unified single-page executive dashboard."""
    index_file = os.path.join(templates_dir, "index.html")
    return FileResponse(index_file)


# ----------------- REST API Endpoints -----------------
@app.get("/api/health")
async def health_check():
    """Returns backend status and whether GEMINI_API_KEY is configured."""
    has_gemini = bool(copilot.get_gemini_api_key())
    return {
        "status": "healthy",
        "gemini_active": has_gemini,
        "database": "SQLite (retailiq.db)",
        "track_id": "PS03"
    }



@app.get("/api/kpis")
async def get_kpis():
    """Returns top-level sales, profitability, and inventory valuation KPIs."""
    return analytics.get_executive_kpis()


@app.get("/api/sales/trends")
async def get_sales_trends():
    """Returns 30-day time-series revenue and profit trends."""
    return analytics.get_sales_trends()


@app.get("/api/categories")
async def get_category_breakdown():
    """Returns sales and inventory performance grouped by product category."""
    return analytics.get_category_breakdown()


@app.get("/api/channels")
async def get_channel_breakdown():
    """Returns sales breakdown by channel (In-Store vs Online)."""
    return analytics.get_channel_breakdown()


@app.get("/api/top-products")
async def get_top_products(limit: int = 5, sort_by: str = "revenue"):
    """Returns top best-selling products."""
    return analytics.get_top_products(limit=limit, sort_by=sort_by)


@app.get("/api/inventory")
async def get_inventory():
    """Returns full product catalog with computed DOI runway, ADS velocity, and ROP."""
    return analytics.get_inventory_health()


@app.get("/api/risks")
async def get_risks():
    """Returns products with imminent stockout risk sorted by runway urgency."""
    return analytics.get_stockout_risks()


@app.get("/api/suppliers")
async def get_suppliers():
    """Returns supplier performance, lead times, and risk exposure metrics."""
    return analytics.get_supplier_performance()


@app.get("/api/inventory/summary")
async def get_inventory_summary():
    """Returns high-level executive inventory health summary and reorder valuation."""
    return analytics.get_inventory_health_summary()


@app.get("/api/inventory/abc")
async def get_abc_analysis():
    """Returns Pareto ABC inventory classification (Class A 70%, Class B 20%, Class C 10%)."""
    return analytics.get_abc_classification()


@app.get("/api/inventory/eoq")
async def get_eoq_analysis():
    """Returns Wilson Economic Order Quantity (EOQ) and optimal batch frequencies for all SKUs."""
    return analytics.get_eoq_analysis()


@app.get("/api/inventory/turnover")
async def get_inventory_turnover():
    """Returns inventory turnover ratio, Days Sales of Inventory (DSI), and slow-moving SKU analysis."""
    return analytics.get_inventory_turnover()


@app.get("/api/export/purchase-orders")
async def export_purchase_orders():
    """Generates and downloads an RFC 4180-compliant CSV containing purchase orders for items needing replenishment."""
    csv_data = analytics.generate_purchase_orders_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=retailiq_purchase_orders.csv"}
    )


@app.post("/api/copilot/chat")
async def copilot_chat(payload: ChatQueryRequest):
    """
    Grounded Natural-Language Copilot:
    Uses deterministic database queries + Gemini synthesis to provide citation-backed answers.
    """
    response = copilot.generate_copilot_response(payload.query)
    return response


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(">> RetailIQ - AI Sales and Inventory Copilot (TRACK_ID=PS03)")
    print(">> Local Web Dashboard: http://localhost:8000")
    print(">> Grounded Engine: SQLite retail database active")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(">> Gemini GenAI: Enabled (GEMINI_API_KEY detected)")
    else:
        print(">> Gemini GenAI: Deterministic Fallback Mode (GEMINI_API_KEY not set)")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)

