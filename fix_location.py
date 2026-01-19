import sqlite3
import os

def update_db():
    # Path check: Agar instance folder ke andar hai toh 'instance/database.db' use karein
    db_path = 'instance/database.db' if os.path.exists('instance/database.db') else 'database.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Connecting to database at: {db_path}")
        
        # Latitude column add karein
        try:
            cursor.execute("ALTER TABLE student ADD COLUMN latitude FLOAT")
            print("Added: latitude")
        except sqlite3.OperationalError:
            print("Skip: latitude already exists")

        # Longitude column add karein
        try:
            cursor.execute("ALTER TABLE student ADD COLUMN longitude FLOAT")
            print("Added: longitude")
        except sqlite3.OperationalError:
            print("Skip: longitude already exists")

        conn.commit()
        conn.close()
        print("Done! Database updated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_db()
    