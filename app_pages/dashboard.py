from datetime import date

import streamlit as st

from db import query_dataframe


st.title("Business dashboard")
st.caption("Sales, inventory and profit overview")

month_start = date.today().replace(day=1).isoformat()
summary = query_dataframe(
    """SELECT COALESCE(SUM(total_amount), 0) AS sales, COUNT(*) AS invoices
    FROM invoices WHERE invoice_date >= ?""",
    (month_start,),
)
profit = query_dataframe(
    """SELECT COALESCE(SUM(ii.line_total - ii.unit_cost * ii.quantity), 0) AS profit
    FROM invoice_items ii JOIN invoices i ON i.invoice_id = ii.invoice_id
    WHERE i.invoice_date >= ?""",
    (month_start,),
)
inventory = query_dataframe(
    """SELECT COALESCE(SUM(stock_quantity * cost_price), 0) AS inventory_value,
    SUM(CASE WHEN stock_quantity <= reorder_level THEN 1 ELSE 0 END) AS low_stock
    FROM products"""
)

sales = float(summary.at[0, "sales"])
with st.container(horizontal=True):
    st.metric("This month sales", f"₹{sales:,.0f}", border=True)
    st.metric("Gross profit", f"₹{float(profit.at[0, 'profit']):,.0f}", border=True)
    st.metric("Invoices", f"{int(summary.at[0, 'invoices']):,}", border=True)
    st.metric("Inventory value", f"₹{float(inventory.at[0, 'inventory_value']):,.0f}", f"{int(inventory.at[0, 'low_stock'])} low stock", border=True)

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Sales by category")
        category_sales = query_dataframe(
            """SELECT p.category AS Category, SUM(ii.line_total) AS Sales
            FROM invoice_items ii JOIN products p ON p.product_id = ii.product_id
            GROUP BY p.category ORDER BY Sales DESC"""
        )
        st.bar_chart(category_sales, x="Category", y="Sales")
with right:
    with st.container(border=True):
        st.subheader("Top products")
        top_products = query_dataframe(
            """SELECT p.product_name AS Product, SUM(ii.line_total) AS Sales
            FROM invoice_items ii JOIN products p ON p.product_id = ii.product_id
            GROUP BY p.product_id, p.product_name ORDER BY Sales DESC LIMIT 6"""
        )
        st.bar_chart(top_products, x="Product", y="Sales")

with st.container(border=True):
    st.subheader("Low-stock alerts")
    low_stock = query_dataframe(
        """SELECT sku AS SKU, product_name AS Product, stock_quantity AS Stock,
        reorder_level AS Reorder_level FROM products
        WHERE stock_quantity <= reorder_level ORDER BY stock_quantity"""
    )
    if low_stock.empty:
        st.success("All products are above their reorder level.")
    else:
        st.warning(f"{len(low_stock)} product(s) need restocking.")
        st.dataframe(low_stock, hide_index=True)
