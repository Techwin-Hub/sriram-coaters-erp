"""
Database initialization utility for the Sriram Coaters ERP application.

This module contains the `init_db` function which is responsible for:
1. Establishing a connection to the SQLite database file (`description.db`).
2. Creating all necessary tables if they do not already exist. This includes
   `description_master`, `workers`, `attendance`, and `overtime`.
3. Ensuring that tables with foreign key dependencies are created in the correct order.
4. Populating the `description_master` table with sample data if it's empty.
"""
import sqlite3

DB_NAME = 'description.db' # Centralized database name

def init_db():
    """
    Initializes the database by creating tables and inserting sample data.

    Connects to the SQLite database (`description.db`).
    Creates the following tables if they don't exist, in logical order
    to satisfy foreign key constraints:
    1. `description_master`: Stores descriptions of services/products.
    2. `workers`: Stores worker information.
    3. `overtime`: Stores overtime records for workers (depends on `workers`).
    4. `attendance`: Stores attendance records for workers (depends on `workers`).

    Also, populates `description_master` with some initial sample data
    if the table is found to be empty.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create description_master table
    # Stores details about different types of work descriptions or services.
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

    # 5. Create invoice_headers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_headers (
            invoice_no TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            total_amount REAL, -- This will be sum of line items
            gst_percentage REAL,
            payment_method TEXT,
            grn_date_from TEXT,
            grn_date_to TEXT,
            po_number TEXT -- New column
        )
    """)
    conn.commit()

    # 6. Create invoice_line_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL,
            line_no INTEGER NOT NULL, -- e.g., 1, 2, 3 for each item in an invoice
            item_description TEXT,
            part_no TEXT,
            hsn_code TEXT,
            quantity REAL NOT NULL,
            rate REAL NOT NULL,
            amount REAL NOT NULL, -- quantity * rate
            FOREIGN KEY (invoice_no) REFERENCES invoice_headers(invoice_no) ON DELETE CASCADE,
            UNIQUE (invoice_no, line_no) -- Ensures line numbers are unique within an invoice
        )
    """)
    conn.commit()

    # 2. Create workers table
    # This table must be created before 'attendance' and 'overtime' tables
    # due to foreign key constraints in those tables referencing 'workers.id'.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            photo_path TEXT,         -- File path to worker's photo
            address TEXT,
            contact_number TEXT,
            previous_experience TEXT,
            salary_amount REAL,
            salary_frequency TEXT,   -- e.g., "Monthly", "Weekly"
            role TEXT,
            joining_date TEXT,       -- Expected format: YYYY-MM-DD
            id_proof_path TEXT       -- File path to worker's ID proof (optional)
        )
    """)
    conn.commit()

    # 3. Create overtime table (depends on workers table)
    # Stores overtime records for workers.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS overtime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,     -- Foreign key to workers table
            date TEXT NOT NULL,             -- Date of overtime (YYYY-MM-DD)
            ot_hours REAL NOT NULL,         -- Number of OT hours
            ot_rate REAL NOT NULL,          -- Rate per OT hour
            ot_amount REAL NOT NULL,        -- Calculated: ot_hours * ot_rate
            FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    # 4. Create attendance table (depends on workers table)
    # Stores daily attendance records for workers.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,     -- Foreign key to workers table
            date TEXT NOT NULL,             -- Date of attendance (YYYY-MM-DD)
            status TEXT NOT NULL,           -- e.g., "Present", "Absent"
            punch_in_time TEXT,             -- Time of punch-in (HH:MM, optional)
            punch_out_time TEXT,            -- Time of punch-out (HH:MM, optional)
            FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
            UNIQUE (worker_id, date)        -- Ensures one attendance record per worker per day
        )
    """)
    conn.commit()

    # Add sample data to description_master if the table is empty.
    # This helps with initial setup and testing of the data_entry module.
    cursor.execute("SELECT COUNT(*) FROM description_master")
    if cursor.fetchone()[0] == 0: # Check if the table is empty
        sample_descriptions = [
            ("Paint Coating", "PC-001", "998873", 100.0, "PO001/A"),
            ("Powder Coating", "PC-002", "998874", 120.0, "PO002/B"),
            ("Surface Treatment", "ST-001", "998875", 80.0, "PO003/C")
        ]
        cursor.executemany("""
            INSERT INTO description_master (description, customer_part_no, sac_code, rate, po_no)
            VALUES (?, ?, ?, ?, ?)
        """, sample_descriptions)
        conn.commit()
        print("Inserted sample data into description_master.")

    conn.close() # Ensure the database connection is closed.

if __name__ == '__main__':
    # This block executes when the script is run directly.
    # Useful for initializing the database from the command line.
    print("Initializing database...")
    init_db()
    print("Database initialization process complete.")
    # To verify, you can open 'description.db' with a SQLite browser.
