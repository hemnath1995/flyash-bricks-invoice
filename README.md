
# Fly-ash Bricks Invoice Register App

A Streamlit web application to manage daily invoices for a Fly-ash Bricks company and automatically prepare:
- **Daily Invoices** log
- **Monthly Summary**
- **GST Report** (helpful for GSTR-1)

## Setup

```bash
git clone <repo-url>
cd flyash_bricks_invoice_app
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run flyash_bricks_invoice_app.py
```

The first time you save an invoice, the workbook `Flyash_Bricks_Daily_Invoice_Register.xlsx`
will be created alongside the app file, containing three sheets:
1. **Daily Invoices**
2. **Monthly Summary**
3. **GST Report**

## Export

Use the sidebar **Download Excel Workbook** button anytime to back up your data.
