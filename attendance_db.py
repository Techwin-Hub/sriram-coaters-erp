import sqlite3
from datetime import date

DB_NAME = 'description.db'

def get_all_active_workers_for_attendance():
    """
    Fetches id, first_name, and last_name from the workers table.
    Returns a list of dictionaries.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()
    try:
        # Assuming all workers in the table are 'active' for now
        cursor.execute("SELECT id, first_name, last_name FROM workers ORDER BY first_name, last_name")
        workers = [dict(row) for row in cursor.fetchall()]
        return workers
    except sqlite3.Error as e:
        print(f"Database error in get_all_active_workers_for_attendance: {e}")
        return []
    finally:
        conn.close()

def get_attendance_records(date_str):
    """
    Fetches attendance records for a given date (YYYY-MM-DD).
    Returns a dictionary mapping worker_id to their attendance data.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    records = {}
    try:
        cursor.execute("""
            SELECT worker_id, status, punch_in_time, punch_out_time
            FROM attendance
            WHERE date = ?
        """, (date_str,))
        for row in cursor.fetchall():
            records[row['worker_id']] = {
                'status': row['status'],
                'punch_in_time': row['punch_in_time'],
                'punch_out_time': row['punch_out_time']
            }
        return records
    except sqlite3.Error as e:
        print(f"Database error in get_attendance_records for date {date_str}: {e}")
        return {}
    finally:
        conn.close()

def save_attendance_records(records_to_save):
    """
    Saves multiple attendance records.
    Uses INSERT OR REPLACE based on the UNIQUE constraint (worker_id, date).
    Args:
        records_to_save (list): A list of dictionaries, where each dict has:
                                worker_id, date, status, punch_in_time, punch_out_time.
    Returns:
        bool: True if successful, False otherwise.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.executemany("""
            INSERT INTO attendance (worker_id, date, status, punch_in_time, punch_out_time)
            VALUES (:worker_id, :date, :status, :punch_in_time, :punch_out_time)
            ON CONFLICT(worker_id, date) DO UPDATE SET
                status = excluded.status,
                punch_in_time = excluded.punch_in_time,
                punch_out_time = excluded.punch_out_time
        """, records_to_save)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in save_attendance_records: {e}")
        conn.rollback() # Rollback on error
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # For testing - ensure database_utils.init_db() has been run once before
    # from database_utils import init_db
    # init_db() # To create tables if they don't exist

    print("Testing attendance_db.py...")

    # 1. Test get_all_active_workers_for_attendance
    print("\n--- Testing get_all_active_workers_for_attendance ---")
    workers = get_all_active_workers_for_attendance()
    if workers:
        print(f"Found {len(workers)} workers. First few: {workers[:3]}")
    else:
        print("No workers found or error occurred. (Ensure workers table has data for a full test)")
        # You might want to add a test worker using worker_db.py if DB is empty
        # import worker_db
        # worker_db.add_worker({'first_name': 'Test', 'last_name': 'WorkerAttend', 'role': 'Tester', 'joining_date': '2024-01-01'})
        # workers = get_all_active_workers_for_attendance()
        # print(f"After potential add: Found {len(workers)} workers.")


    today_date_str = date.today().isoformat()

    # Create dummy records for testing save and get
    if workers: # Proceed if we have at least one worker
        test_records_initial = [
            {
                'worker_id': workers[0]['id'], 'date': today_date_str, 'status': 'Present',
                'punch_in_time': '09:00', 'punch_out_time': '17:00'
            }
        ]
        if len(workers) > 1:
             test_records_initial.append({
                'worker_id': workers[1]['id'], 'date': today_date_str, 'status': 'Absent',
                'punch_in_time': '', 'punch_out_time': ''
            })

        # 2. Test save_attendance_records (Initial Insert)
        print("\n--- Testing save_attendance_records (Initial Insert) ---")
        if save_attendance_records(test_records_initial):
            print(f"Successfully saved initial records for {today_date_str}.")
        else:
            print(f"Failed to save initial records for {today_date_str}.")

        # 3. Test get_attendance_records
        print("\n--- Testing get_attendance_records ---")
        retrieved_records = get_attendance_records(today_date_str)
        if retrieved_records:
            print(f"Retrieved {len(retrieved_records)} records for {today_date_str}:")
            for worker_id, data in retrieved_records.items():
                print(f"  Worker ID {worker_id}: Status={data['status']}, In={data['punch_in_time']}, Out={data['punch_out_time']}")
        else:
            print(f"No records found for {today_date_str} after save, or error occurred.")

        # 4. Test save_attendance_records (Update Existing - ON CONFLICT DO UPDATE)
        print("\n--- Testing save_attendance_records (Update Existing) ---")
        test_records_update = [
            {
                'worker_id': workers[0]['id'], 'date': today_date_str, 'status': 'Present',
                'punch_in_time': '09:05', 'punch_out_time': '17:30' # Updated times
            }
        ]
        if len(workers) > 1: # If second worker exists
            test_records_update.append({ # New record for another worker if they exist
                'worker_id': workers[1]['id'], 'date': today_date_str, 'status': 'Present', # Changed status
                'punch_in_time': '10:00', 'punch_out_time': '18:00'
            })

        if save_attendance_records(test_records_update):
            print(f"Successfully updated/saved records for {today_date_str}.")
            updated_retrieved_records = get_attendance_records(today_date_str)
            if updated_retrieved_records:
                print(f"Retrieved {len(updated_retrieved_records)} records for {today_date_str} after update:")
                for worker_id, data in updated_retrieved_records.items():
                    print(f"  Worker ID {worker_id}: Status={data['status']}, In={data['punch_in_time']}, Out={data['punch_out_time']}")
            else:
                print(f"No records found for {today_date_str} after update, or error occurred.")
        else:
            print(f"Failed to update/save records for {today_date_str}.")
    else:
        print("\nSkipping save/get records tests as no workers were fetched.")

    print("\nTesting with a date that likely has no records:")
    older_date = "2023-01-01"
    older_records = get_attendance_records(older_date)
    if not older_records:
        print(f"Correctly found no records for {older_date}.")
    else:
        print(f"Found unexpected records for {older_date}: {older_records}")

    print("\nattendance_db.py testing complete.")
