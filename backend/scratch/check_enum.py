import psycopg2
import os

def check_enum():
    conn = psycopg2.connect("postgresql://postgres:MO46\"\"@127.0.0.1:5432/notaire_db")
    cur = conn.cursor()
    
    # Check values of the 'acttype' enum
    cur.execute("SELECT n.nspname as schema, t.typname as type, e.enumlabel as value "
                "FROM pg_type t "
                "JOIN pg_enum e ON t.oid = e.enumtypid "
                "JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace "
                "WHERE t.typname = 'acttype';")
    
    rows = cur.fetchall()
    print("Enum 'acttype' values:")
    for row in rows:
        print(f" - {row[2]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_enum()
