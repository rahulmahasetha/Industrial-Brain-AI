import sqlite3

def add_column():
    conn = sqlite3.connect("industrial_brain.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE compliance_records ADD COLUMN evidence_data TEXT DEFAULT '{}'")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error (maybe column exists): {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column()
