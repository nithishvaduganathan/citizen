import sqlite3
import os

DB_FILE = "citizen.db"

def fix_schema():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    columns_to_add_users = [
        ("role", "TEXT DEFAULT 'citizen'"),
        ("department", "TEXT"),
        ("state", "TEXT"),
        ("district", "TEXT"),
        ("sub_district", "TEXT")
    ]
    
    columns_to_add_reports = [
        ("image_path", "TEXT")
    ]

    print("Checking and fixing 'users' table schema...")
    cursor.execute("PRAGMA table_info(users)")
    existing_columns_users = [info[1] for info in cursor.fetchall()]
    
    for col_name, col_type in columns_to_add_users:
        if col_name not in existing_columns_users:
            try:
                print(f"Adding column '{col_name}' to users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding '{col_name}': {e}")

    print("Checking and fixing 'reports' table schema...")
    cursor.execute("PRAGMA table_info(reports)")
    existing_columns_reports = [info[1] for info in cursor.fetchall()]

    for col_name, col_type in columns_to_add_reports:
        if col_name not in existing_columns_reports:
            try:
                print(f"Adding column '{col_name}' to reports...")
                cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}")
                print(f"Successfully added '{col_name}'.")
            except sqlite3.OperationalError as e:
                print(f"Error adding '{col_name}': {e}")

    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    fix_schema()
