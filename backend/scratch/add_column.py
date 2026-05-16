"""Add missing phone_number column to users table."""
import sys
sys.path.insert(0, ".")

from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR NULL"))
        conn.commit()
        print("Column 'phone_number' added successfully!")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("Column 'phone_number' already exists, skipping.")
        else:
            print(f"Error: {e}")
