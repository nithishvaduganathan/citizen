import sqlite3
import os

DB_FILE = "citizen.db"

def backfill_users():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Backfilling existing users with default data...")

    # Update users where role is NULL or empty
    # Setting default to: Role=citizen, State=Maharashtra, District=Pune, Sub-District=Haveli
    try:
        cursor.execute("""
            UPDATE users 
            SET role = 'citizen',
                state = 'Maharashtra',
                district = 'Pune',
                sub_district = 'Haveli',
                department = NULL
            WHERE state IS NULL OR state = ''
        """)
        
        updated_rows = cursor.rowcount
        print(f"Updated {updated_rows} user(s).")
        
        conn.commit()
    except Exception as e:
        print(f"Error during backfill: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    backfill_users()
