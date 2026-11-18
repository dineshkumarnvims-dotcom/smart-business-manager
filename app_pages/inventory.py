import sqlite3

import streamlit as st

from db import add_product, adjust_stock, query_dataframe


st.title("Inventory management")
st.caption("Add products, track stock and record stock arrivals")

products = query_dataframe(
    """SELECT product_id, sku AS SKU, product_name AS Product, category AS Category,
    cost_price AS Cost, unit_price AS Selling_price, stock_quantity AS Stock,
    reorder_level AS Reorder_level FROM products ORDER BY product_name"""
)
view = st.segmented_control("Inventory view", ["All products", "Low stock"], default="All products")
search = st.text_input("Search inventory", placeholder="Search product or SKU")
shown = products.copy()
if view == "Low stock":
    shown = shown[shown["Stock"] <= shown["Reorder_level"]]
if search:
    shown = shown[shown["Product"].str.contains(search, case=False, na=False) | shown["SKU"].str.contains(search, case=False, na=False)]

with st.container(border=True):
    st.subheader(f"Products ({len(shown)})")
    st.dataframe(
        shown.drop(columns=["product_id"]),
        hide_index=True,
        column_config={
            "Cost": st.column_config.NumberColumn(format="₹%.0f"),
            "Selling_price": st.column_config.NumberColumn("Selling price", format="₹%.0f"),
        },
    )

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Add product")
        with st.form("product_form", clear_on_submit=True):
            sku = st.text_input("SKU")
            name = st.text_input("Product name")
            category = st.text_input("Category", value="Other")
            cost = st.number_input("Cost price", min_value=0.0, value=100.0)
            price = st.number_input("Selling price", min_value=0.0, value=150.0)
            stock = st.number_input("Opening stock", min_value=0, value=10)
            reorder = st.number_input("Reorder level", min_value=0, value=5)
            save = st.form_submit_button("Add product", type="primary", icon=":material/add_box:")
        if save:
            try:
                if not sku.strip() or not name.strip():
                    raise ValueError("SKU and product name are required.")
                if price < cost:
                    raise ValueError("Selling price cannot be below cost price.")
                add_product(sku, name, category, cost, price, int(stock), int(reorder))
                st.success("Product added.")
                st.rerun()
            except (ValueError, sqlite3.IntegrityError) as error:
                st.error(str(error))
with right:
    with st.container(border=True):
        st.subheader("Record stock arrival")
        options = {f"{row.Product} · {row.SKU}": int(row.product_id) for row in products.itertuples()}
        with st.form("stock_form", clear_on_submit=True):
            product = st.selectbox("Product", list(options))
            quantity = st.number_input("Quantity received", min_value=1, value=1)
            update = st.form_submit_button("Add stock", type="primary", icon=":material/inventory:")
        if update:
            adjust_stock(options[product], int(quantity))
            st.success("Stock updated.")
            st.rerun()
