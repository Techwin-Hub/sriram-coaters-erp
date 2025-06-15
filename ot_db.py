import sqlite3

DB_NAME = 'description.db'

def add_ot_record(worker_id, date_str, ot_hours, ot_rate, ot_amount):
    """Adds a new OT record to the overtime table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO overtime (worker_id, date, ot_hours, ot_rate, ot_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (worker_id, date_str, ot_hours, ot_rate, ot_amount))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in add_ot_record: {e}")
        return None
    finally:
        conn.close()

def get_ot_records_for_worker_in_range(worker_id, start_date_str, end_date_str):
    """Fetches OT records for a specific worker within a given date range."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, worker_id, date, ot_hours, ot_rate, ot_amount
            FROM overtime
            WHERE worker_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (worker_id, start_date_str, end_date_str))
        records = [dict(row) for row in cursor.fetchall()]
        return records
    except sqlite3.Error as e:
        print(f"Database error in get_ot_records_for_worker_in_range: {e}")
        return []
    finally:
        conn.close()

def get_all_ot_records_in_range(start_date_str, end_date_str):
    """Fetches all OT records within a given date range."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
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
    # For testing - ensure database_utils.init_db() has been run once
    # from database_utils import init_db
    # init_db()

    # Also ensure worker_db has some workers, e.g., by running worker_management.py or:
    # import worker_db
    # try:
    #     if not worker_db.get_all_workers(): # Assuming get_all_workers exists
    #         worker_db.add_worker({'first_name': 'OT Test', 'last_name': 'Worker', 'role': 'Tester', 'joining_date': '2023-01-01'})
    # except Exception as e:
    #     print(f"Could not ensure test worker: {e}")

    # worker_list = worker_db.get_all_workers() # Need a worker_id for testing
    # test_worker_id = 1
    # if worker_list:
    #     test_worker_id = worker_list[0]['id']
    # else:
    #     print("Cannot run full OT DB tests without workers in the DB.")
    #     test_worker_id = 1 # Fallback, might fail if worker 1 doesn't exist

    print("Testing ot_db.py...")
    test_worker_id = 1 # Assume worker with ID 1 exists for basic tests.
                       # A more robust test would fetch a worker ID first.

    # 1. Test add_ot_record
    print("\n--- Testing add_ot_record ---")
    record_id = add_ot_record(test_worker_id, '2024-07-15', 2.5, 100.0, 250.0)
    if record_id:
        print(f"Added OT record with ID: {record_id}")
        record_id_2 = add_ot_record(test_worker_id, '2024-07-16', 1.0, 120.0, 120.0)
        print(f"Added another OT record with ID: {record_id_2 if record_id_2 else 'Failed'}")
    else:
        print("Failed to add OT record. (Does worker ID 1 exist?)")

    # 2. Test get_ot_records_for_worker_in_range
    print("\n--- Testing get_ot_records_for_worker_in_range ---")
    worker_records = get_ot_records_for_worker_in_range(test_worker_id, '2024-07-01', '2024-07-31')
    if worker_records:
        print(f"Found {len(worker_records)} OT records for worker {test_worker_id} in July 2024:")
        for rec in worker_records:
            print(f"  Date: {rec['date']}, Hours: {rec['ot_hours']}, Rate: {rec['ot_rate']}, Amount: {rec['ot_amount']}")
    else:
        print(f"No OT records found for worker {test_worker_id} in July 2024, or error.")

    # 3. Test get_all_ot_records_in_range
    print("\n--- Testing get_all_ot_records_in_range ---")
    all_records = get_all_ot_records_in_range('2024-07-01', '2024-07-31')
    if all_records:
        print(f"Found {len(all_records)} total OT records in July 2024:")
        for rec in all_records:
            print(f"  Worker ID: {rec['worker_id']}, Date: {rec['date']}, Hours: {rec['ot_hours']}, Amount: {rec['ot_amount']}")
    else:
        print("No OT records found at all in July 2024, or error.")

    # Test with a different worker (assuming worker ID 2 might exist)
    add_ot_record(2, '2024-07-15', 3.0, 110.0, 330.0)
    all_records_after_new = get_all_ot_records_in_range('2024-07-01', '2024-07-31')
    print(f"Total OT records after adding for worker 2: {len(all_records_after_new)}")


    print("\not_db.py testing complete.")
