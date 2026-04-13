from sqlalchemy import create_engine, text

def check_enum():
    DATABASE_URL = "postgresql://postgres:MO46%22%22@localhost:5432/notaire_db"
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        q = text("""
            SELECT enumlabel 
            FROM pg_enum 
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
            WHERE pg_type.typname = 'acttype'
        """)
        rows = conn.execute(q).fetchall()
        print("ActType Labels in DB:")
        for r in rows:
            print(f"- {r[0]}")
            
        q2 = text("""
            SELECT enumlabel 
            FROM pg_enum 
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
            WHERE pg_type.typname = 'actstatus'
        """)
        rows2 = conn.execute(q2).fetchall()
        print("\nActStatus Labels in DB:")
        for r in rows2:
            print(f"- {r[0]}")

if __name__ == "__main__":
    check_enum()
