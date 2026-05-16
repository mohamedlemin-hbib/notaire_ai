import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_columns():
    print(f"Connecting to {DATABASE_URL}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
        columns = [row[0] for row in cur.fetchall()]
        print("Columns in 'users' table:")
        for col in columns:
            print(f"- {col}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
