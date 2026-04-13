from sqlalchemy import create_engine, text
import sys

def fix_enum():
    DATABASE_URL = "postgresql://postgres:MO46%22%22@localhost:5432/notaire_db"
    # We add both cases to be 100% safe
    new_values = [
        'vente_immobilier', 'vente_vehicule', 'vente_societe', 'mariage',
        'VENTE_IMMOBILIER', 'VENTE_VEHICULE', 'VENTE_SOCIETE', 'MARIAGE'
    ]
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # Check existing values
            result = conn.execute(text("SELECT enum_range(NULL::acttype)"))
            existing_values = result.fetchone()[0]
            print(f"Existing values in DB enum 'acttype': {existing_values}")
            
            for val in new_values:
                if val not in existing_values:
                    print(f"Adding value: {val}")
                    conn.execute(text(f"ALTER TYPE acttype ADD VALUE '{val}'"))
                else:
                    print(f"Value '{val}' already exists.")
            
            print("Database Enum 'acttype' updated successfully with all cases!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_enum()
