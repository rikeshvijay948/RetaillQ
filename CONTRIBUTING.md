# Contributing to RetailIQ

Thank you for your interest in contributing to **RetailIQ — AI Sales & Inventory Copilot (TRACK_ID: PS03)**!

This document outlines the guidelines and workflow for contributing to the repository.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/rikeshvijay948/RetaillQ.git
cd RetaillQ

# Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux/macOS:
source venv/bin/activate

# Install dependencies including testing tools
pip install -r requirements.txt
```

### 3. Initialize the Database
```bash
python -c "import database; database.init_db(force_reseed=False)"
```

### 4. Run the Development Server
```bash
python app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🏛️ Architecture & Contribution Principles

RetailIQ operates on a **strictly grounded, zero-hallucination architecture**:

1. **Deterministic Calculations Only in `analytics.py`**:
   - Never allow LLMs/Gemini to calculate prices, margins, revenues, days of inventory, or reorder quantities.
   - All business logic must be computed deterministically in `analytics.py` from verified SQLite records in `retailiq.db`.
   - Protect all mathematical division operations against zero-division (`safe_division` or default fallbacks).

2. **Copilot Grounding & Fallback in `copilot.py`**:
   - `copilot.py` classifies user intent via `classify_intent()`.
   - Primary path uses Google Gemini (`gemini-3.8-flash` / `gemini-3.6-flash`).
   - If the Gemini API returns an error or quota exhaustion, `build_deterministic_answer()` generates a verified, citation-backed response with exact numerical facts.
   - If a product is not in the catalog (e.g. `iPhone`), explicitly report that it is not found without guessing.

3. **API Endpoints in `app.py`**:
   - All REST routes must return clean JSON payloads or standard CSV file responses.
   - Maintain route compatibility with frontend handlers in `static/js/app.js`.

---

## 🧪 Testing Guidelines

Every change must be validated by the automated test suite before opening a pull request.

Run the full test suite with:
```bash
pytest -v
```

### Test Organization:
- `tests/test_database.py`: Schema validation, table row counts, financial arithmetic constraints.
- `tests/test_analytics.py`: KPI calculations, runway equations, category breakdowns, supplier performance, CSV exports.
- `tests/test_copilot.py`: Intent routing, product name extraction, zero-hallucination guarantees, fallback schema.
- `tests/test_api.py`: FastAPI endpoint responses, HTTP status codes, media types.

---

## 🌿 Git Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit your changes with descriptive, conventional commit messages:
   - `feat:` for new capabilities
   - `fix:` for bug fixes
   - `test:` for test additions or updates
   - `docs:` for documentation updates
   - `chore:` for dependencies, configs, or maintenance
3. Push to your fork/branch and submit a Pull Request against `main`.
4. Ensure all GitHub Actions CI checks pass.
