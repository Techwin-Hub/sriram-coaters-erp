import sqlite3

DB_NAME = 'description.db'

def add_worker(worker_data):
    """Adds a new worker to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO workers (
                first_name, last_name, photo_path, address, contact_number,
                previous_experience, salary_amount, salary_frequency, role,
                joining_date, id_proof_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            worker_data.get('first_name'), worker_data.get('last_name'),
            worker_data.get('photo_path'), worker_data.get('address'),
            worker_data.get('contact_number'), worker_data.get('previous_experience'),
            worker_data.get('salary_amount'), worker_data.get('salary_frequency'),
            worker_data.get('role'), worker_data.get('joining_date'),
            worker_data.get('id_proof_path')
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in add_worker: {e}")
        return None
    finally:
        conn.close()

def get_all_workers():
    """Fetches all workers from the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workers ORDER BY first_name, last_name")
        workers = [dict(row) for row in cursor.fetchall()]
        return workers
    except sqlite3.Error as e:
        print(f"Database error in get_all_workers: {e}")
        return []
    finally:
        conn.close()

def get_worker_by_id(worker_id):
    """Fetches a single worker by their ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workers WHERE id = ?", (worker_id,))
        worker = cursor.fetchone()
        return dict(worker) if worker else None
    except sqlite3.Error as e:
        print(f"Database error in get_worker_by_id: {e}")
        return None
    finally:
        conn.close()

def update_worker(worker_id, worker_data):
    """Updates an existing worker's details."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE workers SET
                first_name = ?, last_name = ?, photo_path = ?, address = ?,
                contact_number = ?, previous_experience = ?, salary_amount = ?,
                salary_frequency = ?, role = ?, joining_date = ?, id_proof_path = ?
            WHERE id = ?
        """, (
            worker_data.get('first_name'), worker_data.get('last_name'),
            worker_data.get('photo_path'), worker_data.get('address'),
            worker_data.get('contact_number'), worker_data.get('previous_experience'),
            worker_data.get('salary_amount'), worker_data.get('salary_frequency'),
            worker_data.get('role'), worker_data.get('joining_date'),
            worker_data.get('id_proof_path'), worker_id
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in update_worker: {e}")
        return False
    finally:
        conn.close()

def delete_worker(worker_id):
    """Deletes a worker from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Optionally, delete associated files first
        # worker = get_worker_by_id(worker_id) # Be careful with re-opening connection or pass cursor
        # if worker and worker.get('photo_path') and os.path.exists(worker.get('photo_path')):
        #     os.remove(worker.get('photo_path'))
        # if worker and worker.get('id_proof_path') and os.path.exists(worker.get('id_proof_path')):
        #     os.remove(worker.get('id_proof_path'))

        cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_worker: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # Basic testing
    # Ensure database and table exist by running database_utils.init_db() first
    # from database_utils import init_db
    # init_db()
    print("Testing worker_db.py...")

    sample_worker = {
        'first_name': 'John', 'last_name': 'Doe', 'photo_path': None,
        'address': '123 Main St', 'contact_number': '555-1234',
        'previous_experience': '5 years', 'salary_amount': 50000.0,
        'salary_frequency': 'Monthly', 'role': 'Painter',
        'joining_date': '2024-01-15', 'id_proof_path': None
    }

    worker_id = add_worker(sample_worker)
    if worker_id:
        print(f"Added worker with ID: {worker_id}")

        all_workers = get_all_workers()
        print(f"All workers ({len(all_workers)}): {all_workers}")

        fetched_worker = get_worker_by_id(worker_id)
        print(f"Fetched worker by ID ({worker_id}): {fetched_worker}")

        update_data = {'role': 'Senior Painter', 'salary_amount': 55000.0}
        sample_worker.update(update_data) # Keep local dict updated for update_worker
        if update_worker(worker_id, sample_worker):
            print(f"Updated worker ID {worker_id}.")
            updated_worker = get_worker_by_id(worker_id)
            print(f"Updated worker details: {updated_worker}")
        else:
            print(f"Failed to update worker ID {worker_id}.")

        # if delete_worker(worker_id):
        #     print(f"Deleted worker ID {worker_id}.")
        #     remaining_workers = get_all_workers()
        #     print(f"Remaining workers ({len(remaining_workers)}): {remaining_workers}")
        # else:
        #     print(f"Failed to delete worker ID {worker_id}.")
    else:
        print("Failed to add worker.")

    print("Testing complete.")
