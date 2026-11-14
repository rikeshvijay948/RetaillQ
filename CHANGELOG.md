# Changelog

All notable changes to the RetailIQ project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-11-14

### Added
- **Gross Margin Return on Investment (GMROI) Matrix**:
  - Implemented `analytics.get_gmroi_analysis()` computing product-level and store-level capital efficiency ($\frac{\text{Gross Margin \$}}{\text{Inventory Cost \$}}$).
  - Categorizes all 25 catalog SKUs into 4 strategic quadrants: **Stars**, **Traffic Builders**, **Profit Generators**, and **Underperformers** using median thresholds ($3.22\text{x}$ GMROI, $\$3,999.20$ revenue).
  - Computes category-level GMROI rankings (led by Groceries & Snacks at $6.35\text{x}$).
  - Exposed via `GET /api/inventory/gmroi`.
- **Predictive Demand Forecasting & Statistical Safety Stock**:
  - Implemented `analytics.get_demand_forecast(horizon_days)` blending recent 7-day velocity (60%) with 30-day baseline pace (40%).
  - Computes empirical daily demand standard deviation ($\sigma_d$) and statistical safety stock ($1.65 \times \sigma_d \times \sqrt{L}$ for 95% service level).
  - Computes Gaussian CDF lead-time stockout probabilities, detecting products facing $>50\%$ stockout threat.
  - Exposed via `GET /api/inventory/forecast`.
- **Copilot Grounded Intent Routing**:
  - Added dedicated intent classification and mathematical responses for `GMROI_ANALYSIS` and `DEMAND_FORECAST`.
  - Added dynamic follow-up suggestions for forecasting and merchandising optimization.
- **Dashboard UI Enhancements**:
  - Added Store GMROI ($4.11\text{x}$) and 7-Day Revenue Forecast ($\$29,088$) badges to the Inventory Intelligence header.
  - Added 1-click Copilot quick prompt buttons for GMROI and demand forecasting.
- **Expanded Automated Test Suite**:
  - Added unit and integration tests across `tests/test_analytics.py`, `tests/test_api.py`, and `tests/test_copilot.py`.
  - Suite expanded from 43 to **49 automated tests (100% pass rate)**.

---

## [1.1.0] - 2026-11-07

### Added
- **ABC Pareto Classification Engine**:
  - Implemented `analytics.get_abc_classification()` using an empirical 70/20/10 revenue cumulative curve.
  - Automatic SKU grouping into Class A (high strategic value, daily counts), Class B (moderate), and Class C (routine bulk ordering).
  - Exposed via `GET /api/inventory/abc`.
- **Wilson Economic Order Quantity (EOQ) Optimization**:
  - Implemented `analytics.get_eoq_analysis()` calculating optimal batch order quantities balancing administrative order fees ($35) and holding costs (20%).
  - Added optimal orders per year and cycle order interval days for all 25 catalog SKUs.
  - Exposed via `GET /api/inventory/eoq`.
- **Inventory Turnover & Dead Stock Detection**:
  - Implemented `analytics.get_inventory_turnover()` computing annualized turnover ratio ($35.65\times$) and Days Sales of Inventory ($10.2\text{d}$).
  - Detection of slow-moving items ($>45$ days DOI or $<1$ sale/day with $>30$ units) and tied-up working capital quantification.
  - Exposed via `GET /api/inventory/turnover`.
- **Copilot Intent Engine Expansion**:
  - Added dedicated intent classification and deterministic answer synthesis for `ABC_ANALYSIS`, `ECONOMIC_ORDER_QUANTITY`, and `INVENTORY_TURNOVER`.
  - Zero hallucination guarantees backed by mathematical facts from SQLite.
  - Contextual follow-up suggestions dynamically rendered per intent.
- **1-Click Purchase Order CSV Export UI**:
  - Added direct download button to the Inventory tab and the Stockout Risks section in `templates/index.html`.
  - Added `downloadPurchaseOrdersCsv()` helper in `static/js/app.js`.
- **Test Suite Expansion**:
  - Expanded automated test suite from 34 to 43 comprehensive unit and integration tests across `tests/test_analytics.py`, `tests/test_api.py`, and `tests/test_copilot.py`.
  - 100% test pass rate with CI verification.

---

## [1.0.0] - 2026-11-06

### Added
- **Core Retail Analytics Platform**:
  - SQLite transactional database with 25 products and 1,495 sales records across 30 days.
  - Deterministic calculations for DOI, ADS velocity, Reorder Points, and financial KPIs.
- **Evidence-Grounded AI Copilot**:
  - Dual-engine architecture with primary Google Gemini GenAI synthesis and robust Grounded Rule Engine fallback.
  - Real-time intent classification with exact numerical provenance.
- **Interactive Single-Page Dashboard**:
  - Chart.js 30-day sales trajectory and category distribution visualizations.
  - Filterable inventory management table with live search and risk badges.
- **Continuous Integration**:
  - GitHub Actions CI workflow testing across Ubuntu, Windows, and macOS on Python 3.10 and 3.11.
