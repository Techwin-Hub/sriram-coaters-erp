"""
Database utility functions for Overtime (OT) Management.

This module provides functions to interact with the 'overtime' table, including:
- Adding new OT records.
- Fetching OT records for a specific worker within a date range.
- Fetching all OT records within a date range.
"""
import sqlite3

DB_NAME = 'description.db' # Database file name

def add_ot_record(worker_id, date_str, ot_hours, ot_rate, ot_amount):
    """
    Adds a new Overtime (OT) record to the 'overtime' table.

    Args:
        worker_id (int): The ID of the worker.
        date_str (str): The date of the OT, in 'YYYY-MM-DD' format.
        ot_hours (float): The number of OT hours worked.
        ot_rate (float): The rate per OT hour.
        ot_amount (float): The total OT amount (calculated as ot_hours * ot_rate).

    Returns:
        int: The ID of the newly inserted OT record if successful.
        None: If an error occurs during the database operation.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # SQL query to insert a new OT record.
        # Uses placeholders (?) for security against SQL injection.
        cursor.execute("""
            INSERT INTO overtime (worker_id, date, ot_hours, ot_rate, ot_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (worker_id, date_str, ot_hours, ot_rate, ot_amount))
        conn.commit() # Commit the transaction
        return cursor.lastrowid # Return the ID of the new row
    except sqlite3.Error as e:
        print(f"Database error in add_ot_record: {e}")
        conn.rollback() # Rollback on error
        return None
    finally:
        conn.close() # Ensure the connection is always closed

def get_ot_records_for_worker_in_range(worker_id, start_date_str, end_date_str):
    """
    Fetches all OT records for a specific worker within a given date range.
    Records are ordered by date in descending order.

    Args:
        worker_id (int): The ID of the worker whose OT records are to be fetched.
        start_date_str (str): The start date of the range ('YYYY-MM-DD').
        end_date_str (str): The end date of the range ('YYYY-MM-DD').

    Returns:
        list: A list of dictionaries, where each dictionary represents an OT record.
              Returns an empty list if no records are found or an error occurs.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name for easy dict conversion
    cursor = conn.cursor()
    try:
        # SQL query to select OT records for a specific worker and date range.
        cursor.execute("""
            SELECT id, worker_id, date, ot_hours, ot_rate, ot_amount
            FROM overtime
            WHERE worker_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (worker_id, start_date_str, end_date_str))
        records = [dict(row) for row in cursor.fetchall()] # Convert rows to dictionaries
        return records
    except sqlite3.Error as e:
        print(f"Database error in get_ot_records_for_worker_in_range: {e}")
        return [] # Return empty list on error
    finally:
        conn.close()

def get_all_ot_records_in_range(start_date_str, end_date_str):
    """
    Fetches all OT records from all workers within a given date range.
    Records are ordered by date (descending) and then by worker_id.

    Args:
        start_date_str (str): The start date of the range ('YYYY-MM-DD').
        end_date_str (str): The end date of the range ('YYYY-MM-DD').

    Returns:
        list: A list of dictionaries, where each dictionary represents an OT record.
              Returns an empty list if no records are found or an error occurs.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    try:
        # SQL query to select all OT records within the specified date range.
        cursor.execute("""
            SELECT id, worker_id, date, ot_hours, ot_rate, ot_amount
            FROM overtime
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, worker_id
        """, (start_date_str, end_date_str))
        records = [dict(row) for row in cursor.fetchall()]
        return records
    except sqlite3.Error as e:
        print(f"Database error in get_all_ot_records_in_range: {e}")
        return []
    finally:
        conn.close()

if __name__ == '__main__':
    # This block is for testing the functions in this module when run directly.
    # It's recommended to have the database initialized (database_utils.init_db())
    # and some workers present in the 'workers' table for comprehensive testing.

    # Example of how one might set up for testing:
    # from database_utils import init_db
    # init_db() # Ensures tables exist.

    # import worker_db # To get worker IDs for testing
    # workers = worker_db.get_all_workers()
    # test_worker_id = 1 # Default to 1 if no workers found or for simplicity
    # if workers:
    #     test_worker_id = workers[0]['id'] # Use an actual worker ID from the DB
    # else:
    #     print("Warning: No workers found in DB. OT DB tests will use a placeholder worker ID.")
    #     # Optionally, add a test worker if none exist:
    #     # worker_db.add_worker({
    #     #     'first_name': 'OT_DB_Tester', 'last_name': 'Worker',
    #     #     'role': 'Test Role', 'joining_date': '2023-01-01'
    #     #     # ... other required fields ...
    #     # })
    #     # workers = worker_db.get_all_workers() # Re-fetch
    #     # if workers: test_worker_id = workers[0]['id']

    print("Testing ot_db.py...")

    # Using a placeholder worker_id for demonstration.
    # Replace with actual worker ID fetching for robust testing.
    current_test_worker_id = 1

    # 1. Test add_ot_record
    print("\n--- Testing add_ot_record ---")
    # Note: For this test to pass reliably, worker with current_test_worker_id must exist.
    record_id1 = add_ot_record(current_test_worker_id, '2024-07-20', 2.0, 150.0, 300.0)
    if record_id1:
        print(f"SUCCESS: Added OT record with ID: {record_id1}")
        record_id2 = add_ot_record(current_test_worker_id, '2024-07-21', 1.5, 150.0, 225.0)
        if record_id2:
            print(f"SUCCESS: Added another OT record with ID: {record_id2}")
        else:
            print(f"FAILED: Could not add second OT record for worker {current_test_worker_id}.")
    else:
        print(f"FAILED: Could not add first OT record. (Does worker ID {current_test_worker_id} exist?)")

    # 2. Test get_ot_records_for_worker_in_range
    print(f"\n--- Testing get_ot_records_for_worker_in_range (Worker ID: {current_test_worker_id}) ---")
    worker_ot_records = get_ot_records_for_worker_in_range(current_test_worker_id, '2024-07-01', '2024-07-31')
    if worker_ot_records:
        print(f"SUCCESS: Found {len(worker_ot_records)} OT records for worker {current_test_worker_id} in July 2024:")
        for r in worker_ot_records:
            print(f"  Date: {r['date']}, Hours: {r['ot_hours']}, Rate: {r['ot_rate']}, Amount: {r['ot_amount']}")
    else:
        print(f"INFO: No OT records found for worker {current_test_worker_id} in July 2024, or an error occurred.")

    # 3. Test get_all_ot_records_in_range
    print("\n--- Testing get_all_ot_records_in_range ---")
    all_ot_records = get_all_ot_records_in_range('2024-07-01', '2024-07-31')
    if all_ot_records:
        print(f"SUCCESS: Found {len(all_ot_records)} total OT records in July 2024:")
        for r in all_ot_records: # Print a few for verification
            print(f"  Worker ID: {r['worker_id']}, Date: {r['date']}, Hours: {r['ot_hours']}, Amount: {r['ot_amount']}")
    else:
        print("INFO: No OT records found overall in July 2024, or an error occurred.")

    # Example: Add record for a different worker (assuming worker ID 2 exists)
    # For robust testing, ensure worker ID 2 actually exists or create it.
    # add_ot_record(2, '2024-07-20', 3.0, 120.0, 360.0)
    # all_ot_records_updated = get_all_ot_records_in_range('2024-07-01', '2024-07-31')
    # print(f"Total OT records after potentially adding for worker 2: {len(all_ot_records_updated)}")

    print("\n--- ot_db.py testing complete ---")
