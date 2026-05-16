import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def fix_schema():
    print(f"Connecting to {DATABASE_URL}")
    try:
        # Use simple string for connection to avoid unicode issues in some environments
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Add nni column if missing
        print("Checking for 'nni' column...")
        cur.execute("""
            DO $$ 
            BEGIN 
                BEGIN
                    ALTER TABLE users ADD COLUMN nni VARCHAR;
                    ALTER TABLE users ADD CONSTRAINT users_nni_key UNIQUE (nni);
                    CREATE INDEX ix_users_nni ON users (nni);
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column nni already exists in users';
                END;
            END $$;
        """)
        
        # Add phone_number column if missing
        print("Checking for 'phone_number' column...")
        cur.execute("""
            DO $$ 
            BEGIN 
                BEGIN
                    ALTER TABLE users ADD COLUMN phone_number VARCHAR;
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column phone_number already exists in users';
                END;
            END $$;
        """)
        
        print("Schema fix completed.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
