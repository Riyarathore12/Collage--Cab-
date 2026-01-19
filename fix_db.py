import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'instance', 'database.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Email aur Phone columns add karein
    try:
        cursor.execute('ALTER TABLE student ADD COLUMN email TEXT;')
        print("Email column added.")
    except:
        print("Email column already exists.")

    try:
        cursor.execute('ALTER TABLE student ADD COLUMN phone TEXT;')
        print("Phone column added.")
    except:
        print("Phone column already exists.")
    
    conn.commit()
    print("Mubarak ho! Database columns ready hain.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()