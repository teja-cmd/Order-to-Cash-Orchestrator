import sqlite3
import os
from contextlib import contextmanager
from typing import Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'orchestrator.db')

@contextmanager
def get_db_connection():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_product(product_id: int) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def get_customer(customer_id: int) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def get_customer_payment_history(customer_id: int) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payment_history WHERE customer_id = ?", (customer_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
