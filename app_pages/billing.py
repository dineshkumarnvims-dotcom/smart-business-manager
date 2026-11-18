from datetime import date

import streamlit as st

from db import add_customer, create_invoice, query_dataframe


st.title("Create customer bill")
st.caption("Save invoices and deduct stock automatically")

customers = query_dataframe("SELECT customer_id, customer_name, city FROM customers ORDER BY customer_name")
catalog = query_dataframe("SELECT product_id, sku, product_name, unit_price, stock_quantity FROM products WHERE stock_quantity > 0 ORDER BY product_name")

if catalog.empty:
    st.error("No stock is available. Add stock from the Inventory page.")
    st.stop()

customer_options = {f"{row.customer_name} · {row.city or 'No city'}": int(row.customer_id) for row in customers.itertuples()}
cart = catalog.rename(columns={"product_id": "Product ID", "sku": "SKU", "product_name": "Product", "unit_price": "Unit price", "stock_quantity": "Available"})
cart["Quantity"] = 0

with st.container(border=True):
    st.subheader("New invoice")
    with st.form("invoice_form"):
        customer = st.selectbox("Customer", list(customer_options))
        bill_date = st.date_input("Invoice date", value=date.today())
        discount = st.number_input("Flat discount", min_value=0.0, value=0.0, step=10.0)
        edited = st.data_editor(
            cart,
            hide_index=True,
            disabled=["Product ID", "SKU", "Product", "Unit price", "Available"],
            column_config={
                "Product ID": None,
                "Unit price": st.column_config.NumberColumn(format="₹%.0f"),
                "Available": st.column_config.NumberColumn(format="%d"),
                "Quantity": st.column_config.NumberColumn(min_value=0, step=1),
            },
            key="invoice_cart",
        )
        save_bill = st.form_submit_button("Save invoice and update stock", type="primary", icon=":material/receipt_long:")
    if save_bill:
        items = [(int(row["Product ID"]), int(row["Quantity"])) for _, row in edited.iterrows() if int(row["Quantity"]) > 0]
        try:
            invoice_number = create_invoice(customer_options[customer], bill_date, discount, items)
            st.success(f"Invoice {invoice_number} saved successfully.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Add customer")
        with st.form("customer_form", clear_on_submit=True):
            name = st.text_input("Customer name")
            phone = st.text_input("Phone")
            city = st.text_input("City")
            add = st.form_submit_button("Add customer", icon=":material/person_add:")
        if add:
            if name.strip():
                add_customer(name, phone, city)
                st.success("Customer added.")
                st.rerun()
            else:
                st.error("Customer name is required.")
with right:
    with st.container(border=True):
        st.subheader("Recent invoices")
        recent = query_dataframe(
            """SELECT i.invoice_number AS Invoice, i.invoice_date AS Date,
            c.customer_name AS Customer, i.total_amount AS Amount
            FROM invoices i JOIN customers c ON c.customer_id = i.customer_id
            ORDER BY i.invoice_id DESC LIMIT 8"""
        )
        st.dataframe(recent, hide_index=True, column_config={"Amount": st.column_config.NumberColumn(format="₹%.0f")})
