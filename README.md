# Smart Inventory, Billing & Sales Manager

A complete local business-management application built with **Python, Streamlit, SQLite, Pandas and Altair**. It runs without a cloud account, database server, or API key.

## Business features

- Business dashboard with sales, gross-profit, inventory-value and low-stock KPIs
- Product inventory management, product creation and stock-arrival entry
- Customer billing with automatic stock deduction and invoice numbers
- Customer creation and recent-invoice tracking
- Sales reporting by date range and product category
- CSV and Excel export for invoice reports
- Parameterized SQLite queries and transaction-safe invoice creation
- Ready-to-use local demo data: 12 products, 6 customers and 72 invoices

## Run the app

1. Download or clone this project.
2. Double-click `RUN_APP.bat`.
3. Open the local address shown in the terminal, normally `http://localhost:8501`.

Or run in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Data storage

The app creates a local SQLite file at `data/business_manager.db` on its first run. The database is intentionally excluded from Git so each business can start with its own data.

## Resume description

Built a full-stack local business management application using Python, Streamlit and SQLite. Implemented inventory control, transaction-safe billing, automatic stock deduction, customer management, profitability dashboards and CSV/Excel sales reporting.
