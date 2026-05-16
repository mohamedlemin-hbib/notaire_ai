from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, full_name, role FROM users"))
    users = result.fetchall()
    print("Users in DB:")
    for u in users:
        print(u)
