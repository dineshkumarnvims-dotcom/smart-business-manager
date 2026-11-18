"""SQLite data layer for the Smart Business Manager application."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "business_manager.db"


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """Return a shared local database connection for the current app process."""
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def refresh_data() -> None:
    """Clear cached UI data after a business transaction."""
    st.cache_data.clear()


def initialise_database() -> None:
    """Create tables and a useful, local demo dataset on the first run."""
    connection = get_connection()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            cost_price REAL NOT NULL CHECK (cost_price >= 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
            reorder_level INTEGER NOT NULL DEFAULT 5 CHECK (reorder_level >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT,
            city TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            invoice_date TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            discount REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE IF NOT EXISTS invoice_items (
            invoice_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """
    )
    connection.commit()
    if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        _seed_demo_data(connection)


def _seed_demo_data(connection: sqlite3.Connection) -> None:
    """Add sample records so a user can see the complete app immediately."""
    products = [
        ("ELEC-001", "Wireless Headphones", "Electronics", 1350, 2200, 44, 10),
        ("ELEC-002", "Bluetooth Speaker", "Electronics", 1700, 2900, 19, 8),
        ("ELEC-003", "Power Bank 10000mAh", "Electronics", 650, 1200, 11, 10),
        ("HOME-001", "Steel Water Bottle", "Home & Kitchen", 260, 520, 64, 15),
        ("HOME-002", "Storage Box Set", "Home & Kitchen", 430, 850, 23, 8),
        ("HOME-003", "LED Desk Lamp", "Home & Kitchen", 590, 1150, 7, 8),
        ("CARE-001", "Herbal Face Wash", "Personal Care", 110, 249, 85, 20),
        ("CARE-002", "Shampoo 650ml", "Personal Care", 190, 399, 49, 12),
        ("OFF-001", "Premium Notebook", "Office Supplies", 55, 120, 112, 30),
        ("OFF-002", "Gel Pen Pack", "Office Supplies", 90, 190, 95, 25),
        ("FIT-001", "Yoga Mat", "Fitness", 420, 850, 17, 8),
        ("FIT-002", "Resistance Band Set", "Fitness", 280, 600, 31, 10),
    ]
    customers = [
        ("Arun Stores", "9876543210", "Chennai"),
        ("Meena Enterprises", "9876543211", "Coimbatore"),
        ("Karthik Traders", "9876543212", "Madurai"),
        ("Sree Balaji Mart", "9876543213", "Salem"),
        ("Priya Retail", "9876543214", "Tiruchirappalli"),
        ("Walk-in Customer", "", "Chennai"),
    ]
    connection.executemany(
        """INSERT INTO products
        (sku, product_name, category, cost_price, unit_price, stock_quantity, reorder_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        products,
    )
    connection.executemany(
        "INSERT INTO customers (customer_name, phone, city) VALUES (?, ?, ?)", customers
    )
    connection.commit()

    product_rows = connection.execute(
        "SELECT product_id, unit_price, cost_price FROM products ORDER BY product_id"
    ).fetchall()
    customer_rows = connection.execute("SELECT customer_id FROM customers").fetchall()
    rng = random.Random(2026)
    today = date.today()
    for index in range(72):
        invoice_date = today - timedelta(days=rng.randint(0, 120))
        chosen_products = rng.sample(product_rows, rng.randint(1, 3))
        item_rows: list[tuple[int, int, float, float, float]] = []
        subtotal = 0.0
        for product in chosen_products:
            quantity = rng.randint(1, 4)
            line_total = round(product["unit_price"] * quantity, 2)
            subtotal += line_total
            item_rows.append(
                (product["product_id"], quantity, product["unit_price"], product["cost_price"], line_total)
            )
        discount = round(subtotal * rng.choice([0, 0, 0.03, 0.05]), 2)
        total = round(subtotal - discount, 2)
        cursor = connection.execute(
            """INSERT INTO invoices
            (invoice_number, invoice_date, customer_id, subtotal, discount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                f"INV-DEMO-{index + 1:03d}",
                invoice_date.isoformat(),
                rng.choice(customer_rows)["customer_id"],
                subtotal,
                discount,
                total,
            ),
        )
        connection.executemany(
            """INSERT INTO invoice_items
            (invoice_id, product_id, quantity, unit_price, unit_cost, line_total)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [(cursor.lastrowid, *item) for item in item_rows],
        )
    connection.commit()


@st.cache_data(ttl=60, max_entries=20, show_spinner=False)
def query_dataframe(query: str, params: tuple[object, ...] = ()) -> pd.DataFrame:
    """Read a query into a DataFrame; all user values stay parameterized."""
    return pd.read_sql_query(query, get_connection(), params=params)


def add_product(
    sku: str,
    name: str,
    category: str,
    cost_price: float,
    unit_price: float,
    stock_quantity: int,
    reorder_level: int,
) -> None:
    get_connection().execute(
        """INSERT INTO products
        (sku, product_name, category, cost_price, unit_price, stock_quantity, reorder_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (sku.strip().upper(), name.strip(), category.strip(), cost_price, unit_price, stock_quantity, reorder_level),
    )
    get_connection().commit()
    refresh_data()


def adjust_stock(product_id: int, quantity_to_add: int) -> None:
    if quantity_to_add <= 0:
        raise ValueError("Stock quantity must be greater than zero.")
    get_connection().execute(
        "UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?",
        (quantity_to_add, product_id),
    )
    get_connection().commit()
    refresh_data()


def add_customer(name: str, phone: str, city: str) -> None:
    get_connection().execute(
        "INSERT INTO customers (customer_name, phone, city) VALUES (?, ?, ?)",
        (name.strip(), phone.strip(), city.strip()),
    )
    get_connection().commit()
    refresh_data()


def create_invoice(
    customer_id: int,
    invoice_date: date,
    discount: float,
    requested_items: Iterable[tuple[int, int]],
) -> str:
    """Create an invoice and atomically deduct the sold quantity from stock."""
    connection = get_connection()
    items = [(int(product_id), int(quantity)) for product_id, quantity in requested_items if int(quantity) > 0]
    if not items:
        raise ValueError("Add at least one product quantity before saving the invoice.")
    if discount < 0:
        raise ValueError("Discount cannot be negative.")

    try:
        connection.execute("BEGIN")
        item_rows: list[tuple[int, int, float, float, float]] = []
        subtotal = 0.0
        for product_id, quantity in items:
            product = connection.execute(
                """SELECT product_id, product_name, unit_price, cost_price, stock_quantity
                FROM products WHERE product_id = ?""",
                (product_id,),
            ).fetchone()
            if product is None:
                raise ValueError("One selected product no longer exists.")
            if quantity > product["stock_quantity"]:
                raise ValueError(
                    f"Only {product['stock_quantity']} unit(s) available for {product['product_name']}."
                )
            line_total = round(product["unit_price"] * quantity, 2)
            subtotal += line_total
            item_rows.append((product_id, quantity, product["unit_price"], product["cost_price"], line_total))

        discount = min(round(discount, 2), subtotal)
        total = round(subtotal - discount, 2)
        year = invoice_date.year
        sequence = connection.execute(
            "SELECT COUNT(*) + 1 FROM invoices WHERE invoice_number LIKE ?", (f"INV-{year}-%",)
        ).fetchone()[0]
        invoice_number = f"INV-{year}-{sequence:04d}"
        cursor = connection.execute(
            """INSERT INTO invoices
            (invoice_number, invoice_date, customer_id, subtotal, discount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (invoice_number, invoice_date.isoformat(), customer_id, subtotal, discount, total),
        )
        connection.executemany(
            """INSERT INTO invoice_items
            (invoice_id, product_id, quantity, unit_price, unit_cost, line_total)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [(cursor.lastrowid, *item) for item in item_rows],
        )
        for product_id, quantity, *_ in item_rows:
            connection.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                (quantity, product_id),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    refresh_data()
    return invoice_number
