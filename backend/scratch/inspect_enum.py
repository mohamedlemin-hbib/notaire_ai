"""Investigate enum values for userrole."""
import sys
sys.path.insert(0, ".")
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'userrole'")).fetchall()
    print('Enum values:', [r[0] for r in res])
