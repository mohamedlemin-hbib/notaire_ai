import psycopg2
try:
    conn = psycopg2.connect(
        dbname="notaire_db",
        user="postgres",
        password='MO46""',
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    
    # Check current database name confirm it
    cur.execute("SELECT current_database();")
    db_name = cur.fetchone()[0]
    print(f"Base de données active : {db_name}")

    # List all tables in all schemas
    cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_schema, table_name;")
    tables = cur.fetchall()
    print("\nTables trouvées :")
    for s, t in tables:
        print(f" - Schéma: {s}, Table: {t}")

    # Check row count in users table
    cur.execute("SELECT count(*) FROM users;")
    count = cur.fetchone()[0]
    print(f"\nNombre d'utilisateurs dans la table 'users' : {count}")

    # List rows
    cur.execute("SELECT id, email, role, full_name FROM users;")
    rows = cur.fetchall()
    print("\nContenu de la table 'users' :")
    for r in rows:
        print(f" -> ID: {r[0]}, Email: {r[1]}, Role: {r[2]}, Nom: {r[3]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Erreur de diagnostic : {e}")
