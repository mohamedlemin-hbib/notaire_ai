"""Promote a user to admin role."""
import sys
sys.path.insert(0, ".")

from app.db.session import engine
from sqlalchemy import text
from app.db.models import UserRole

email = "mohamedleminaidelha@gmail.com"

with engine.connect() as conn:
    try:
        # Check if user exists first
        result = conn.execute(text("SELECT id, email, role FROM users WHERE email = :email"), {"email": email}).fetchone()
        if result:
            conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = :email"), {"email": email})
            conn.commit()
            print(f"User {email} promoted to ADMIN successfully!")
        else:
            print(f"Error: User with email {email} not found.")
    except Exception as e:
        print(f"Error: {e}")
