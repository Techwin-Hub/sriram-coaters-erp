"""
Database utility functions for the Attendance System.

This module provides functions to:
- Fetch active workers for populating attendance marking UI.
- Retrieve existing attendance records for a specific date.
- Save (insert or update) attendance records.
"""
import sqlite3
from datetime import date # For testing with today's date

DB_NAME = 'description.db' # Database file name

def get_all_active_workers_for_attendance():
    """
    Fetches basic details (id, first_name, last_name) of all workers.

    These details are used to populate the UI where attendance is marked.
    Currently, "active" status is not explicitly checked; all workers are fetched.
    Results are ordered by first name, then last name.

    Returns:
        list: A list of dictionaries, where each dictionary contains 'id',
              'first_name', and 'last_name' of a worker.
              Returns an empty list if no workers are found or an error occurs.
    """
    conn = None  # Initialize conn to None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Access columns by name for easy dict conversion
        cursor = conn.cursor()
        # SQL query to select necessary worker details.
        cursor.execute("SELECT id, first_name, last_name FROM workers ORDER BY first_name, last_name")
        workers = [dict(row) for row in cursor.fetchall()] # Convert each row to a dictionary
        return workers
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in get_all_active_workers_for_attendance: {e_op}")
        return []
    except sqlite3.Error as e:
        print(f"Database error in get_all_active_workers_for_attendance: {e}")
        return [] # Return an empty list in case of error
    finally:
        if conn:
            conn.close() # Ensure the database connection is always closed

def get_attendance_records(date_str):
    """
    Fetches attendance records for a specific date.

    Args:
        date_str (str): The date for which to fetch records, in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary mapping each worker_id to their attendance data
              (status, punch_in_time, punch_out_time) for the given date.
              Returns an empty dictionary if no records are found or an error occurs.
    """
    conn = None  # Initialize conn to None
    records = {} # Initialize an empty dictionary to store results
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row # To access columns by name
        cursor = conn.cursor()
        # SQL query to get attendance details for the specified date.
        cursor.execute("""
            SELECT worker_id, status, punch_in_time, punch_out_time
            FROM attendance
            WHERE date = ?
        """, (date_str,))
        for row in cursor.fetchall():
            # Store each record in the dictionary, keyed by worker_id.
            records[row['worker_id']] = {
                'status': row['status'],
                'punch_in_time': row['punch_in_time'],
                'punch_out_time': row['punch_out_time']
            }
        return records
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in get_attendance_records for date {date_str}: {e_op}")
        return {}
    except sqlite3.Error as e:
        print(f"Database error in get_attendance_records for date {date_str}: {e}")
        return {} # Return empty dict on error
    finally:
        if conn:
            conn.close()

def save_attendance_records(records_to_save):
    """
    Saves (inserts or updates) multiple attendance records in the database.

    It uses an 'INSERT ... ON CONFLICT DO UPDATE' (upsert) mechanism based on the
    UNIQUE constraint on (worker_id, date) in the 'attendance' table.

    Args:
        records_to_save (list): A list of dictionaries. Each dictionary must contain:
                                'worker_id', 'date', 'status',
                                'punch_in_time', and 'punch_out_time'.

    Returns:
        bool: True if all records were saved successfully, False otherwise.
    """
    conn = None  # Initialize conn to None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # SQL query for batch insert or update (upsert).
        # :named_placeholders are used, matching keys in the dictionaries.
        cursor.executemany("""
            INSERT INTO attendance (worker_id, date, status, punch_in_time, punch_out_time)
            VALUES (:worker_id, :date, :status, :punch_in_time, :punch_out_time)
            ON CONFLICT(worker_id, date) DO UPDATE SET
                status = excluded.status,
                punch_in_time = excluded.punch_in_time,
                punch_out_time = excluded.punch_out_time
        """, records_to_save)
        conn.commit() # Commit the transaction
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in save_attendance_records: {e_op}")
        if conn: # Attempt rollback only if connection was established
            conn.rollback()
        return False
    except sqlite3.Error as e:
        print(f"Database error in save_attendance_records: {e}")
        if conn: # Attempt rollback only if connection was established
            conn.rollback() # Rollback changes if any error occurs during the transaction
        return False
    finally:
        if conn:
            conn.close()

def delete_attendance_record(worker_id: int, date_str: str) -> bool:
    """
    Deletes a specific attendance record for a given worker and date.

    Args:
        worker_id (int): The ID of the worker.
        date_str (str): The date of the attendance record in 'YYYY-MM-DD' format.

    Returns:
        bool: True if the record was deleted successfully (or didn't exist), False on error.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE worker_id = ? AND date = ?", (worker_id, date_str))
        conn.commit()
        # cursor.rowcount might be 0 if no record matched, which is a successful "deletion" in this context.
        # It's > 0 if a record was actually deleted. It's -1 if not supported without PRAGMA.
        # For simplicity, assume success if no exception.
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in delete_attendance_record for worker {worker_id}, date {date_str}: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Database error in delete_attendance_record for worker {worker_id}, date {date_str}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This block is for testing the functions in this module when run directly.
    # It's advisable to ensure that 'database_utils.init_db()' has been run at least once
    # to create the necessary tables, and that there's some data in the 'workers' table.

    # from database_utils import init_db
    # init_db() # Example: Ensure tables exist.

    # To test effectively, you might need to add some workers if your DB is empty:
    # import worker_db
    # if not get_all_active_workers_for_attendance(): # Check if any workers exist
    #     worker_db.add_worker({
    #         'first_name': 'AttDB', 'last_name': 'TestWorker', 'role': 'Tester',
    #         'joining_date': '2023-01-01'
    #         # Add other required fields for worker_db.add_worker as per its definition
    #     })

    print("Testing attendance_db.py...")

    # 1. Test get_all_active_workers_for_attendance
    print("\n--- Testing get_all_active_workers_for_attendance ---")
    workers = get_all_active_workers_for_attendance()
    if workers:
        print(f"Found {len(workers)} workers. First few (max 3): {workers[:3]}")
    else:
        print("No workers found. For a full test, ensure the 'workers' table has data.")

    today_date_str = date.today().isoformat() # Get today's date in YYYY-MM-DD format

    # Proceed with tests that require worker data only if workers were found
    if workers:
        # Prepare sample records for testing save and get operations
        sample_records_initial = [
            {
                'worker_id': workers[0]['id'], 'date': today_date_str, 'status': 'Present',
                'punch_in_time': '09:00', 'punch_out_time': '17:00'
            }
        ]
        if len(workers) > 1: # If there's a second worker, add a record for them too
             sample_records_initial.append({
                'worker_id': workers[1]['id'], 'date': today_date_str, 'status': 'Absent',
                'punch_in_time': '', 'punch_out_time': ''
            })

        # 2. Test save_attendance_records (Initial Insert)
        print(f"\n--- Testing save_attendance_records (Initial Insert for {today_date_str}) ---")
        if save_attendance_records(sample_records_initial):
            print("SUCCESS: Initial records saved.")
        else:
            print("FAILED: Could not save initial records.")

        # 3. Test get_attendance_records
        print(f"\n--- Testing get_attendance_records (for {today_date_str}) ---")
        retrieved_records = get_attendance_records(today_date_str)
        if retrieved_records:
            print(f"SUCCESS: Retrieved {len(retrieved_records)} records:")
            for worker_id, data in retrieved_records.items():
                print(f"  Worker ID {worker_id}: Status={data['status']}, In='{data['punch_in_time']}', Out='{data['punch_out_time']}'")
        else:
            print(f"INFO: No records found for {today_date_str}, or an error occurred during retrieval.")

        # 4. Test save_attendance_records (Update Existing records - Upsert functionality)
        print(f"\n--- Testing save_attendance_records (Update Existing for {today_date_str}) ---")
        sample_records_update = [
            { # Update first worker's times
                'worker_id': workers[0]['id'], 'date': today_date_str, 'status': 'Present',
                'punch_in_time': '09:05', 'punch_out_time': '17:35'
            }
        ]
        if len(workers) > 1: # If second worker exists, update their status
            sample_records_update.append({
                'worker_id': workers[1]['id'], 'date': today_date_str, 'status': 'Present',
                'punch_in_time': '10:00', 'punch_out_time': '18:00' # Also changed status to Present
            })

        if save_attendance_records(sample_records_update):
            print("SUCCESS: Records updated/saved.")
            # Verify by fetching again
            updated_retrieved_records = get_attendance_records(today_date_str)
            if updated_retrieved_records:
                print("  Verification: Retrieved records after update:")
                for worker_id, data in updated_retrieved_records.items():
                    print(f"    Worker ID {worker_id}: Status={data['status']}, In='{data['punch_in_time']}', Out='{data['punch_out_time']}'")
            else:
                print(f"  Verification INFO: No records found for {today_date_str} after update attempt.")
        else:
            print("FAILED: Could not update/save records.")
    else:
        print("\nSkipping save/get records tests as no workers were available to create sample records.")

    # Test fetching for a date that is unlikely to have records
    print("\n--- Testing get_attendance_records for a date with no expected records ---")
    far_past_date = "2000-01-01"
    far_past_records = get_attendance_records(far_past_date)
    if not far_past_records: # Empty dictionary evaluates to False
        print(f"SUCCESS: Correctly found no records for {far_past_date}.")
    else:
        print(f"INFO: Unexpectedly found {len(far_past_records)} records for {far_past_date}: {far_past_records}")

    # Test delete_attendance_record
    if workers: # Only test delete if we had workers and potentially saved records
        test_worker_id_for_delete = workers[0]['id']
        test_date_for_delete = today_date_str
        # First, ensure a record exists or try to save one for deletion test
        print(f"\n--- Testing delete_attendance_record for Worker ID {test_worker_id_for_delete} on {test_date_for_delete} ---")
        # Ensure record exists (it might from previous save test)
        # save_attendance_records([{'worker_id': test_worker_id_for_delete, 'date': test_date_for_delete,
        #                           'status': 'Present', 'punch_in_time': '08:00', 'punch_out_time': '16:00'}])

        if delete_attendance_record(test_worker_id_for_delete, test_date_for_delete):
            print("SUCCESS: delete_attendance_record reported success.")
            # Verify by trying to fetch it
            deleted_record_check = get_attendance_records(test_date_for_delete)
            if not deleted_record_check.get(test_worker_id_for_delete):
                print(f"VERIFIED: Record for Worker ID {test_worker_id_for_delete} on {test_date_for_delete} is no longer found.")
            else:
                print(f"VERIFICATION FAILED: Record for Worker ID {test_worker_id_for_delete} on {test_date_for_delete} still exists.")
        else:
            print("FAILED: delete_attendance_record reported an error.")
    else:
        print("\nSkipping delete_attendance_record test as no workers were available.")


    print("\n--- attendance_db.py testing complete ---")
