import sqlite3
import os
from app.db import DB_PATH

def seed_db():
    print(f"Seeding database at {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            stock INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            credit_limit REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            invoice_amount REAL,
            days_to_pay INTEGER,
            status TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)
    
    # Insert mock data
    
    # Products (some with low stock for exception paths)
    products = [
        (1, "Widget A", 100, 10.0),
        (2, "Widget B", 50, 20.0),
        (3, "Widget C", 0, 15.0), # Deliberately out of stock
        (4, "Widget D", 3, 50.0), # Deliberately low stock
        (5, "Gadget X", 200, 5.0),
    ]
    cursor.executemany("INSERT INTO products (id, name, stock, price) VALUES (?, ?, ?, ?)", products)
    
    # Customers
    customers = [
        (1, "Clean Payer Inc", 10000.0),
        (2, "Risky Business Ltd", 2000.0),
        (3, "New Client LLC", 1000.0),
    ]
    cursor.executemany("INSERT INTO customers (id, name, credit_limit) VALUES (?, ?, ?)", customers)
    
    # Payment History
    # Customer 1: Clean payer
    history = [
        (1, 500.0, 15, "PAID_ON_TIME"),
        (1, 1200.0, 28, "PAID_ON_TIME"),
        (1, 300.0, 10, "PAID_ON_TIME"),
        # Customer 2: Risky
        (2, 2000.0, 45, "LATE"),
        (2, 500.0, 60, "LATE"),
        (2, 1000.0, 35, "LATE"),
        # Customer 3: No history (New Client) - leave empty
    ]
    cursor.executemany("INSERT INTO payment_history (customer_id, invoice_amount, days_to_pay, status) VALUES (?, ?, ?, ?)", history)
    
    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
