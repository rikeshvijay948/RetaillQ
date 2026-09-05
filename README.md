# RetailIQ — AI Sales and Inventory Copilot

**TRACK_ID:** `PS03` (Retail – Sales and Inventory Copilot)

RetailIQ is an executive sales and inventory intelligence web platform powered by deterministic analytics and evidence-grounded Gemini AI.

---

## ⚡ Quick Start (Hackathon Judge Instructions)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Set Gemini API Key
To enable full generative synthesis with Gemini:
```bash
# Windows PowerShell:
$env:GEMINI_API_KEY="your_api_key_here"

# Windows CMD:
set GEMINI_API_KEY=your_api_key_here

# Linux/macOS:
export GEMINI_API_KEY="your_api_key_here"
```
*(Note: If `GEMINI_API_KEY` is omitted, RetailIQ automatically runs in deterministic grounded mode without crashing).*

### 3. Launch Application
```bash
python app.py
```

### 4. Open in Browser
Visit **[http://localhost:8000](http://localhost:8000)**.

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
│ - Stockout Risk Alerts  │  └─────────────────────────┘
└───────────┬─────────────┘
            │ Real-time Calculated Facts
            ▼
┌────────────────────────────────────────┐
│   Gemini AI Copilot (copilot.py)       │
│ - Strict Grounding Prompt Injection    │
│ - Evidence & Calculation Proof Citations│
│ - Actionable PO Recommendations        │
│ - Out-of-Scope / Insufficient Data Guard│
└────────────────────────────────────────┘
```

---

## 🌟 Core Features

1. **Executive Sales Dashboard**
   - 30-day Revenue ($123,572.73), Gross Profit ($71,710.03), and Profit Margin (58.03%).
   - Interactive Chart.js time-series trend lines (Daily Revenue vs. Profit).
   - Category donut breakdown and channel split (In-Store vs. Online).
   - Ranked bestsellers by volume and revenue contribution.

2. **Inventory Intelligence & Runway Meter**
   - Real-time Days of Inventory remaining ($\text{DOI} = \frac{\text{Stock}}{\text{Average Daily Sales}}$).
   - Dynamic Reorder Point calculation ($\text{ROP} = (\text{ADS} \times \text{Lead Time}) + \text{Safety Stock}$).
   - Multi-parameter filtering by search query, product category, and urgency level.

3. **Stockout Risk Center**
   - Real-time alerts on **4 intentionally low-stock products** facing stockout threats in $< 1$ day.
   - 1-click purchase order quantity suggestions and supplier contact details.

4. **Natural Language AI Copilot**
   - Interactive chat drawer and dedicated assistant view.
   - Quick-prompt suggestions for rapid evaluation.
   - **Calculation Evidence Inspector** displaying exact mathematical figures backing each AI response.
   - Honest fallback for ambiguous/out-of-scope queries (e.g. asking about unknown warehouses).
