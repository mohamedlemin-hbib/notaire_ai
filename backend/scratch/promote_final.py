"""Ensure responsable accounts are promoted to ADMIN."""
import sys
sys.path.insert(0, ".")
from app.db.session import engine
from sqlalchemy import text

emails_to_promote = [
    "mohamedleminaidelha@gmail.com",
    "notaire.responsable@gmail.com"
]

with engine.connect() as conn:
    for email in emails_to_promote:
        try:
            # Using exact string 'ADMIN' which corresponds to the DB enum
            conn.execute(
                text("UPDATE users SET role = 'ADMIN' WHERE email = :email"),
                {"email": email}
            )
            print(f"Promotion attempt for {email} successful.")
        except Exception as e:
            print(f"Error promoting {email}: {e}")
    conn.commit()
    print("Database transaction committed.")
