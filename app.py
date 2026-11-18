"""Entry point for the Smart Inventory, Billing & Sales Manager."""

import streamlit as st

from db import initialise_database


st.set_page_config(
    page_title="Smart Business Manager",
    page_icon=":material/storefront:",
    layout="wide",
)

initialise_database()

pages = {
    "Business manager": [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("app_pages/billing.py", title="Create bill", icon=":material/receipt_long:"),
        st.Page("app_pages/inventory.py", title="Inventory", icon=":material/inventory_2:"),
        st.Page("app_pages/reports.py", title="Reports", icon=":material/analytics:"),
    ]
}

with st.sidebar:
    st.title("Smart Business")
    st.caption("Inventory, billing and sales insights")
    st.divider()
    st.caption("Local SQLite database · no internet required")

navigation = st.navigation(pages, position="sidebar")
navigation.run()
