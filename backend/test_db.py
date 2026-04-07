import psycopg2
import sys
import os

try:
    conn = psycopg2.connect(
        dbname="notaire_db",
        user="postgres",
        password='MO46""',
        host="localhost",
        port="5432",
        client_encoding='utf8'
    )
    print("Connection successful!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"Connection failed: {repr(e)}")
    sys.exit(1)
