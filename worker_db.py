"""
Database utility functions for worker management.

This module provides functions to interact with the 'workers' table in the database,
including adding, retrieving, updating, and deleting worker records.
"""
import sqlite3

DB_NAME = 'description.db' # Database file name

def add_worker(worker_data):
    """
    Adds a new worker to the 'workers' table.

    Args:
        worker_data (dict): A dictionary containing the worker's details.
                            Expected keys match the column names in the 'workers' table
                            (e.g., 'first_name', 'last_name', 'photo_path', etc.).

    Returns:
        int: The ID of the newly inserted worker row if successful.
        None: If an error occurs during the database operation.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # SQL statement to insert a new worker.
    # Using placeholders (?) to prevent SQL injection vulnerabilities.
    try:
        # The keys in worker_data should correspond to these column names.
        cursor.execute("""
            INSERT INTO workers (
                first_name, last_name, photo_path, address, contact_number,
                previous_experience, salary_amount, salary_frequency, role,
                joining_date, id_proof_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            worker_data.get('first_name'),
            worker_data.get('last_name'),
            worker_data.get('photo_path'),
            worker_data.get('address'),
            worker_data.get('contact_number'),
            worker_data.get('previous_experience'),
            worker_data.get('salary_amount'),
            worker_data.get('salary_frequency'),
            worker_data.get('role'),
            worker_data.get('joining_date'),
            worker_data.get('id_proof_path')
        ))
        conn.commit() # Commit the transaction
        return cursor.lastrowid # Return the ID of the newly inserted row
    except sqlite3.Error as e:
        print(f"Database error in add_worker: {e}")
        conn.rollback() # Rollback changes if an error occurs
        return None
    finally:
        conn.close() # Ensure connection is always closed

def get_all_workers():
    """
    Fetches all workers from the 'workers' table, ordered by name.

    Returns:
        list: A list of dictionaries, where each dictionary represents a worker.
              Returns an empty list if no workers are found or an error occurs.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workers ORDER BY first_name, last_name")
        workers = [dict(row) for row in cursor.fetchall()] # Convert rows to dicts
        return workers
    except sqlite3.Error as e:
        print(f"Database error in get_all_workers: {e}")
        return [] # Return empty list on error
    finally:
        conn.close()

def get_worker_by_id(worker_id):
    """
    Fetches a single worker from the 'workers' table by their ID.

    Args:
        worker_id (int): The ID of the worker to retrieve.

    Returns:
        dict: A dictionary containing the worker's details if found.
        None: If no worker with the given ID is found or an error occurs.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workers WHERE id = ?", (worker_id,))
        worker = cursor.fetchone() # Fetch a single row
        return dict(worker) if worker else None # Convert to dict if a row was found
    except sqlite3.Error as e:
        print(f"Database error in get_worker_by_id: {e}")
        return None
    finally:
        conn.close()

def update_worker(worker_id, worker_data):
    """
    Updates an existing worker's details in the 'workers' table.

    Args:
        worker_id (int): The ID of the worker to update.
        worker_data (dict): A dictionary containing the worker's new details.
                            Expected keys match column names.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # SQL statement to update worker details.
        cursor.execute("""
            UPDATE workers SET
                first_name = ?, last_name = ?, photo_path = ?, address = ?,
                contact_number = ?, previous_experience = ?, salary_amount = ?,
                salary_frequency = ?, role = ?, joining_date = ?, id_proof_path = ?
            WHERE id = ?
        """, (
            worker_data.get('first_name'),
            worker_data.get('last_name'),
            worker_data.get('photo_path'),
            worker_data.get('address'),
            worker_data.get('contact_number'),
            worker_data.get('previous_experience'),
            worker_data.get('salary_amount'),
            worker_data.get('salary_frequency'),
            worker_data.get('role'),
            worker_data.get('joining_date'),
            worker_data.get('id_proof_path'),
            worker_id
        ))
        conn.commit()
        return True # Return True on successful update
    except sqlite3.Error as e:
        print(f"Database error in update_worker: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_worker(worker_id):
    """
    Deletes a worker from the 'workers' table by their ID.
    Associated attendance and overtime records are deleted automatically
    due to 'ON DELETE CASCADE' in the table definitions.

    Args:
        worker_id (int): The ID of the worker to delete.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Note: Physical file deletion (photos, ID proofs) is not handled here.
        # That would require fetching file paths before deletion and using os.remove.
        # The ON DELETE CASCADE in 'attendance' and 'overtime' tables handles related DB records.
        cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_worker: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # This block is for testing purposes when the script is run directly.
    # It's good practice to include some basic tests for your DB functions.
    # Example:
    # from database_utils import init_db # Ensure tables are created
    # init_db()

    print("Testing worker_db.py...")

    # Sample data for testing
    sample_worker_data = {
        'first_name': 'Test', 'last_name': 'User', 'photo_path': None,
        'address': '1 Test St', 'contact_number': '111-2222',
        'previous_experience': '2 years', 'salary_amount': 60000.0,
        'salary_frequency': 'Monthly', 'role': 'Tester',
        'joining_date': '2024-01-01', 'id_proof_path': None
    }

    # Test add_worker
    new_id = add_worker(sample_worker_data)
    if new_id:
        print(f"add_worker: SUCCESS, new ID: {new_id}")

        # Test get_worker_by_id
        worker = get_worker_by_id(new_id)
        if worker and worker['first_name'] == 'Test':
            print(f"get_worker_by_id: SUCCESS, fetched: {worker['first_name']}")
        else:
            print(f"get_worker_by_id: FAILED for ID {new_id}")

        # Test update_worker
        update_info = {'role': 'Senior Tester', 'salary_amount': 65000.0}
        # Need to provide all fields for the current update_worker structure
        full_updated_data = worker.copy() # Start with existing data
        full_updated_data.update(update_info)

        if update_worker(new_id, full_updated_data):
            print(f"update_worker: SUCCESS for ID {new_id}")
            updated_worker = get_worker_by_id(new_id)
            if updated_worker and updated_worker['role'] == 'Senior Tester':
                print(f"  Verification: Role is now {updated_worker['role']}")
            else:
                print(f"  Verification: Update FAILED or data mismatch for ID {new_id}")
        else:
            print(f"update_worker: FAILED for ID {new_id}")

        # Test get_all_workers
        all_workers = get_all_workers()
        if any(w['id'] == new_id for w in all_workers):
            print(f"get_all_workers: SUCCESS, found {len(all_workers)} workers, including new ID {new_id}.")
        else:
            print(f"get_all_workers: FAILED or new ID {new_id} not found.")

        # Test delete_worker
        # if delete_worker(new_id):
        #     print(f"delete_worker: SUCCESS for ID {new_id}")
        #     if not get_worker_by_id(new_id):
        #         print(f"  Verification: Worker ID {new_id} correctly deleted.")
        #     else:
        #         print(f"  Verification: Worker ID {new_id} still exists after delete call.")
        # else:
        #     print(f"delete_worker: FAILED for ID {new_id}")
    else:
        print("add_worker: FAILED. Subsequent tests might be affected.")

    print("\nWorker DB testing finished.")
