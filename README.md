# RetailIQ — AI Sales and Inventory Copilot

[![RetailIQ CI](https://github.com/rikeshvijay948/RetaillQ/actions/workflows/ci.yml/badge.svg)](https://github.com/rikeshvijay948/RetaillQ/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)
![Database](https://img.shields.io/badge/SQLite-Local%20Verified-003B57.svg?logo=sqlite&logoColor=white)
![AI Engine](https://img.shields.io/badge/Google%20Gemini-Grounded%20Synthesis-4285F4.svg?logo=google&logoColor=white)

**TRACK_ID:** `PS03` (Retail – Sales and Inventory Copilot)

RetailIQ is an executive sales and inventory intelligence web platform powered by deterministic analytics and evidence-grounded Gemini AI.

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Set Gemini API Key
To enable generative synthesis with Google Gemini:
```bash
# Windows PowerShell:
$env:GEMINI_API_KEY="your_api_key_here"

# Windows CMD:
set GEMINI_API_KEY=your_api_key_here

# Linux/macOS:
export GEMINI_API_KEY="your_api_key_here"
```
*(Note: If `GEMINI_API_KEY` is omitted or quota is exhausted, RetailIQ automatically routes to the built-in Grounded Deterministic Intelligence Engine without interruption).*

### 3. Launch Application
```bash
python app.py
```

### 4. Open in Browser
Visit **[http://localhost:8000](http://localhost:8000)**.

---

## 🧪 Automated Test Suite

RetailIQ includes an extensive 34-test automated verification suite covering database integrity, mathematical constraints, risk thresholds, API responses, and zero-hallucination guarantees:

```bash
pytest -v
```

All 34 tests run across Linux and Windows in continuous integration on every commit and pull request.

---

## 🏛️ Architecture & Zero-Hallucination Grounding

```text
┌────────────────────────────────────────┐
│   FastAPI Web Server (Port 8000)       │
│  - Serves Dashboard UI & REST Endpoints│
└──────────────────┬─────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   Deterministic Engine  │  │   Local SQLite Database │
│   (analytics.py)        │◄─┤   (retailiq.db)         │
│ - 30-Day Sales & Margin │  │ - 25 Products           │
│ - Runway & Days of Inv  │  │ - 5 Categories          │
│ - Reorder Points (ROP)  │  │ - 1,495 Transactions    │
│ - Supplier Analytics    │  │ - 5 Verified Suppliers  │
│ - Stockout Risk Alerts  │  └─────────────────────────┘
│ - Automated PO Export   │
└───────────┬─────────────┘
            │ Real-time Calculated Facts
            ▼
┌────────────────────────────────────────┐
│   Gemini AI Copilot (copilot.py)       │
│ - Strict Grounding Prompt Injection    │
│ - Intent Classification & Route Engine │
│ - Evidence & Calculation Proof Citations│
│ - Actionable PO Recommendations        │
│ - Out-of-Catalog Zero-Hallucination    │
└────────────────────────────────────────┘
```

---

## 🌟 Core Features

1. **Executive Sales Dashboard**
   - 30-day Revenue ($123,572.73), Gross Profit ($71,710.03), and Profit Margin (58.03%).
   - Interactive Chart.js time-series trend lines (Daily Revenue vs. Profit).
   - Category donut breakdown and channel distribution (In-Store vs. Online).
   - Ranked bestsellers by volume, revenue, and gross profit contribution.

2. **Inventory Intelligence & Runway Meter**
   - Real-time Days of Inventory remaining ($\text{DOI} = \frac{\text{Current Stock}}{\text{Average Daily Sales}}$).
   - Dynamic Reorder Point calculation ($\text{ROP} = (\text{ADS} \times \text{Lead Time}) + \text{Safety Stock}$).
   - Multi-parameter filtering by search query, product category, and urgency level.

3. **Stockout Risk Center**
   - Real-time alerts on **4 intentionally low-stock products** facing stockout threats in $< 1$ day.
   - 1-click purchase order quantity suggestions and supplier contact details.

4. **Supplier Operational Analytics & Automated PO Export**
   - Aggregated supplier lead times, product exposure, and risk levels across 5 verified suppliers.
   - Ready-to-dispatch Purchase Orders exportable directly to RFC 4180-compliant CSV (`/api/export/purchase-orders`).

5. **Natural Language AI Copilot**
   - Interactive chat assistant with real-time intent routing.
   - **Calculation Evidence Inspector** displaying exact mathematical figures backing each AI response.
   - Honest fallback for out-of-catalog items (e.g. searching for iPhones explicitly states non-existence).

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves unified executive dashboard UI |
| `GET` | `/api/health` | Service health check and AI engine configuration status |
| `GET` | `/api/kpis` | Executive revenue, profit, units sold, and valuation metrics |
| `GET` | `/api/sales/trends` | 30-day time-series daily revenue and profit array |
| `GET` | `/api/categories` | Revenue, profit, and stock valuation grouped by category |
| `GET` | `/api/channels` | Sales distribution breakdown by channel (In-Store vs Online) |
| `GET` | `/api/top-products` | Top revenue-driving products (`limit` and `sort_by` params) |
| `GET` | `/api/inventory` | Catalog of 25 products with computed DOI runway and ROP |
| `GET` | `/api/inventory/summary` | High-level stock health score and total reorder valuation |
| `GET` | `/api/inventory/abc` | Pareto ABC classification (Class A 70%, Class B 20%, Class C 10%) |
| `GET` | `/api/inventory/eoq` | Economic Order Quantity (EOQ) optimization and order interval days |
| `GET` | `/api/inventory/turnover` | Annualized inventory turnover ratio, DSI, and slow-moving stock analysis |
| `GET` | `/api/risks` | Imminent stockout risk SKUs sorted by runway urgency |
| `GET` | `/api/suppliers` | Supplier lead times, supplied SKUs, and risk exposure |
| `GET` | `/api/export/purchase-orders` | Downloadable CSV purchase orders for products needing reorder |
| `POST` | `/api/copilot/chat` | Evidence-grounded natural-language query resolution |

---

## 💬 Sample Copilot Questions

- *"Which products need attention today?"* → Identifies 4 critical low-stock items with $< 1$ day runway.
- *"What are our top 5 products by revenue?"* → Returns exact #1 to #5 rankings with revenue and margins.
- *"Which product has the highest revenue?"* → Details Ultra ANC Wireless Headphones ($22,798.48) with inventory alert.
- *"If I can only reorder two products today, which should I prioritize?"* → Prioritizes items by runway depletion urgency.
- *"What is our ABC inventory classification?"* → 70/20/10 Pareto breakdown with inventory control strategies.
- *"What are our recommended EOQ batch sizes?"* → Wilson formula batch sizing balancing holding vs order costs.
- *"What is our inventory turnover ratio and slow moving stock?"* → Turnover ratio ($35.65\times$), Days Sales of Inventory, and tied-up capital.
- *"Who are our suppliers?"* → Summarizes supplier lead times, product volume, and risk exposure.
- *"Do we sell iPhones?"* → Explicitly confirms item is not in the dataset (zero hallucination).

---

## 🤝 Contributing

Contributions are welcome! Please review [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, architecture standards, and test suite instructions.
