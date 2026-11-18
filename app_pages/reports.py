from io import BytesIO

import pandas as pd
import streamlit as st

from db import query_dataframe


def to_excel(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Sales report")
    return output.getvalue()


st.title("Sales and profit reports")
st.caption("Review sales performance and download business reports")

limits = query_dataframe("SELECT MIN(invoice_date) AS first_date, MAX(invoice_date) AS last_date FROM invoices")
first_date = pd.to_datetime(limits.at[0, "first_date"]).date()
last_date = pd.to_datetime(limits.at[0, "last_date"]).date()
selected_dates = st.sidebar.date_input("Report period", value=(first_date, last_date), min_value=first_date, max_value=last_date)
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

invoices = query_dataframe(
    """SELECT i.invoice_number AS Invoice, i.invoice_date AS Date,
    c.customer_name AS Customer, i.total_amount AS Sales
    FROM invoices i JOIN customers c ON c.customer_id = i.customer_id
    WHERE i.invoice_date BETWEEN ? AND ? ORDER BY i.invoice_date DESC, i.invoice_id DESC""",
    (start_date.isoformat(), end_date.isoformat()),
)
category_sales = query_dataframe(
    """SELECT p.category AS Category, COALESCE(SUM(ii.line_total), 0) AS Sales,
    COALESCE(SUM((ii.line_total - ii.unit_cost * ii.quantity)), 0) AS Profit
    FROM invoice_items ii JOIN invoices i ON i.invoice_id = ii.invoice_id
    JOIN products p ON p.product_id = ii.product_id
    WHERE i.invoice_date BETWEEN ? AND ?
    GROUP BY p.category ORDER BY Sales DESC""",
    (start_date.isoformat(), end_date.isoformat()),
)
profit = float(category_sales["Profit"].sum()) if not category_sales.empty else 0.0
sales = float(invoices["Sales"].sum()) if not invoices.empty else 0.0
with st.container(horizontal=True):
    st.metric("Sales", f"₹{sales:,.0f}", border=True)
    st.metric("Gross profit", f"₹{profit:,.0f}", border=True)
    st.metric("Invoices", f"{len(invoices):,}", border=True)
    st.metric("Average bill", f"₹{(sales / len(invoices)) if len(invoices) else 0:,.0f}", border=True)

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Sales by category")
        if category_sales.empty:
            st.info("No sales in the selected period.")
        else:
            st.bar_chart(category_sales, x="Category", y="Sales")
with right:
    with st.container(border=True):
        st.subheader("Category profit")
        if category_sales.empty:
            st.info("No profit data in the selected period.")
        else:
            st.bar_chart(category_sales, x="Category", y="Profit")

with st.container(border=True):
    st.subheader("Invoice register")
    st.dataframe(invoices, hide_index=True, column_config={"Sales": st.column_config.NumberColumn(format="₹%.0f")})
    st.download_button("Download CSV", invoices.to_csv(index=False).encode("utf-8"), "sales_report.csv", "text/csv", icon=":material/download:")
    st.download_button("Download Excel", to_excel(invoices), "sales_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/download:")
