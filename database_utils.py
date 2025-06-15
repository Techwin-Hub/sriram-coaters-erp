import sqlite3

def init_db():
    conn = sqlite3.connect('description.db')
    cursor = conn.cursor()
    # Create description_master table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS description_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT UNIQUE NOT NULL,
            customer_part_no TEXT,
            sac_code TEXT,
            rate REAL,
            po_no TEXT
        )
    """)
    conn.commit()

    # Create overtime table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS overtime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            ot_hours REAL NOT NULL,
            ot_rate REAL NOT NULL,
            ot_amount REAL NOT NULL,
            FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    # Create workers table (must be before attendance and overtime)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            photo_path TEXT,
            address TEXT,
            contact_number TEXT,
            previous_experience TEXT,
            salary_amount REAL,
            salary_frequency TEXT,
            role TEXT,
            joining_date TEXT,
            id_proof_path TEXT
        )
    """)
    conn.commit()

    # Create attendance table (depends on workers)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            punch_in_time TEXT,
            punch_out_time TEXT,
            FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
            UNIQUE (worker_id, date)
        )
    """)
    conn.commit()

    # Add sample data to description_master if the table is empty
    cursor.execute("SELECT COUNT(*) FROM description_master")
    if cursor.fetchone()[0] == 0: # Corrected indentation
        cursor.executemany("""
            INSERT INTO description_master (description, customer_part_no, sac_code, rate, po_no)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Paint Coating", "PC-001", "998873", 100, "fc0001-1/12"),
            ("Powder Coating", "PC-002", "998874", 120, "fc0000-1/12"),
        ])
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized and description_master table created (if it didn't exist) with sample data.")
