
# flyash_bricks_invoice_app.py
"""Streamlit app for managing daily invoices of a Fly-ash Bricks company
and automatically preparing Monthly Summary & GST Report sheets suitable for GST filing.

How to run:
    pip install -r requirements.txt
    streamlit run flyash_bricks_invoice_app.py

The app stores data in an Excel workbook named
    Flyash_Bricks_Daily_Invoice_Register.xlsx
in the same folder. If the file doesn't exist, it will be created on first save.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd
import streamlit as st

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
FILE_PATH = Path("Flyash_Bricks_Daily_Invoice_Register.xlsx")

INVOICE_COLUMNS = [
    "Date",
    "Invoice No.",
    "Buyer Name",
    "Buyer GSTIN",
    "Place of Supply",
    "Invoice Value",
    "Taxable Value",
    "CGST %", "CGST Amt",
    "SGST %", "SGST Amt",
    "IGST %", "IGST Amt",
    "Total GST", "Total Invoice Value",
    "Payment Mode", "Vehicle No.", "Remarks",
]

# -------------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------------
def _load_invoices() -> pd.DataFrame:
    """Load the Daily Invoices sheet if it exists; otherwise return empty DataFrame."""
    if FILE_PATH.exists():
        try:
            return pd.read_excel(FILE_PATH, sheet_name="Daily Invoices", dtype=str)
        except Exception:
            pass
    return pd.DataFrame(columns=INVOICE_COLUMNS)

def _calculate_tax_values(
    taxable_value: float,
    cgst_percent: float,
    sgst_percent: float,
    igst_percent: float,
) -> tuple[float, float, float, float, float]:
    """Return CGST amount, SGST amount, IGST amount, total GST, total invoice value"""
    cgst_amt = round(taxable_value * cgst_percent / 100, 2)
    sgst_amt = round(taxable_value * sgst_percent / 100, 2)
    igst_amt = round(taxable_value * igst_percent / 100, 2)
    total_gst = round(cgst_amt + sgst_amt + igst_amt, 2)
    total_invoice_value = round(taxable_value + total_gst, 2)
    return cgst_amt, sgst_amt, igst_amt, total_gst, total_invoice_value

def _save_workbook(df: pd.DataFrame) -> None:
    """Write Daily Invoices, Monthly Summary, and GST Report sheets to the workbook."""
    df_temp = df.copy()
    df_temp["Date"] = pd.to_datetime(df_temp["Date"], dayfirst=True)
    df_temp["Month"] = df_temp["Date"].dt.to_period("M").astype(str)

   # Convert numeric columns properly
num_cols = [
    "Taxable Value", "CGST Amt", "SGST Amt", "IGST Amt",
    "Total GST", "Total Invoice Value"
]
for col in num_cols:
    df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce").fillna(0)

summary = (
    df_temp.groupby("Month", as_index=False)
    .agg({
        "Invoice No.": "count",
        "Taxable Value": "sum",
        "CGST Amt": "sum",
        "SGST Amt": "sum",
        "IGST Amt": "sum",
        "Total GST": "sum",
        "Total Invoice Value": "sum",
    })
    .rename(columns={"Invoice No.": "Total Invoices"})
)

    gst_report = df[
        [
            "Invoice No.", "Date", "Buyer GSTIN", "Place of Supply",
            "Taxable Value", "CGST Amt", "SGST Amt", "IGST Amt",
            "Total GST", "Total Invoice Value",
        ]
    ]

    with pd.ExcelWriter(FILE_PATH, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Daily Invoices")
        summary.to_excel(writer, index=False, sheet_name="Monthly Summary")
        gst_report.to_excel(writer, index=False, sheet_name="GST Report")

# -------------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------------
st.set_page_config(page_title="Fly-ash Bricks Invoice Register", layout="wide")

st.title("🧱 Fly-ash Bricks - Daily Invoice Register & GST Tool")

invoice_df = _load_invoices()

# Data Entry
with st.expander("➕ Add a New Invoice", expanded=not FILE_PATH.exists()):
    with st.form("add_invoice_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("Date", value=_dt.date.today())
            buyer_name = st.text_input("Buyer Name")
            place_supply = st.text_input("Place of Supply")
            payment_mode = st.selectbox("Payment Mode", ["Cash", "Bank", "UPI", "Credit"])
        with col2:
            invoice_no = st.text_input("Invoice No.")
            buyer_gstin = st.text_input("Buyer GSTIN", placeholder="29ABCDE1234F2Z5")
            taxable_value = st.number_input("Taxable Value (₹)", min_value=0.0, step=0.01, format="%0.2f")
            vehicle_no = st.text_input("Vehicle No.")
        with col3:
            cgst_percent = st.number_input("CGST %", min_value=0.0, max_value=100.0, value=9.0, step=0.1)
            sgst_percent = st.number_input("SGST %", min_value=0.0, max_value=100.0, value=9.0, step=0.1)
            igst_percent = st.number_input("IGST %", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            remarks = st.text_input("Remarks")

        submitted = st.form_submit_button("Add Invoice")
        if submitted:
            if not invoice_no or taxable_value <= 0:
                st.error("Invoice No. and Taxable Value are required.")
            else:
                c_amt, s_amt, i_amt, tot_gst, tot_invoice = _calculate_tax_values(
                    taxable_value, cgst_percent, sgst_percent, igst_percent)
                new_row = pd.DataFrame({
                    "Date": [date.strftime("%d-%m-%Y")],
                    "Invoice No.": [invoice_no],
                    "Buyer Name": [buyer_name],
                    "Buyer GSTIN": [buyer_gstin],
                    "Place of Supply": [place_supply],
                    "Invoice Value": [tot_invoice],
                    "Taxable Value": [taxable_value],
                    "CGST %": [cgst_percent], "CGST Amt": [c_amt],
                    "SGST %": [sgst_percent], "SGST Amt": [s_amt],
                    "IGST %": [igst_percent], "IGST Amt": [i_amt],
                    "Total GST": [tot_gst], "Total Invoice Value": [tot_invoice],
                    "Payment Mode": [payment_mode],
                    "Vehicle No.": [vehicle_no],
                    "Remarks": [remarks],
                })
                invoice_df = pd.concat([invoice_df, new_row], ignore_index=True)
                _save_workbook(invoice_df)
                st.success(f"Invoice {invoice_no} added and saved.")

# Tabs
tab1, tab2, tab3 = st.tabs(["📄 Daily Invoices", "📊 Monthly Summary", "🗂️ GST Report"])
with tab1:
    st.subheader("Daily Invoices")
    st.dataframe(invoice_df, use_container_width=True, hide_index=True)
with tab2:
    st.subheader("Monthly Summary")
    if not invoice_df.empty:
        tmp = invoice_df.copy()
        tmp["Date"] = pd.to_datetime(tmp["Date"], dayfirst=True)
        tmp = tmp.assign(Month=tmp["Date"].dt.to_period("M").astype(str))
        summary_view = tmp.groupby("Month", as_index=False).agg(
            Total_Invoices=("Invoice No.", "count"),
            Total_Taxable_Value=("Taxable Value", "sum"),
            Total_CGST=("CGST Amt", "sum"),
            Total_SGST=("SGST Amt", "sum"),
            Total_IGST=("IGST Amt", "sum"),
            Total_GST=("Total GST", "sum"),
            Total_Invoice_Value=("Total Invoice Value", "sum"),
        )
        st.dataframe(summary_view, use_container_width=True, hide_index=True)
    else:
        st.info("No invoices yet.")
with tab3:
    st.subheader("GST Report")
    gst_cols = [
        "Invoice No.", "Date", "Buyer GSTIN", "Place of Supply",
        "Taxable Value", "CGST Amt", "SGST Amt", "IGST Amt",
        "Total GST", "Total Invoice Value",
    ]
    st.dataframe(invoice_df[gst_cols], use_container_width=True, hide_index=True)

# Sidebar download
with st.sidebar:
    st.header("⬇️ Export / Backup")
    if FILE_PATH.exists():
        with open(FILE_PATH, "rb") as f:
            st.download_button(
                label="Download Excel Workbook",
                data=f,
                file_name=FILE_PATH.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.warning("No data saved yet.")
