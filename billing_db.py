import sqlite3

# It's better to import DB_NAME if it's defined in a central place like database_utils.
# For now, defining it locally. If you have a central DB_NAME, change this.
# from database_utils import DB_NAME
DB_NAME = 'description.db'

def add_invoice_header(header_data: dict) -> bool:
    """
    Adds a new invoice header record to the invoice_headers table.

    Args:
        header_data (dict): A dictionary containing invoice header details.
                            Expected keys: 'invoice_no', 'date', 'customer_name',
                                           'total_amount', 'gst_percentage', 'payment_method'.
    Returns:
        bool: True if the record was added successfully, False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoice_headers (invoice_no, date, customer_name, total_amount, gst_percentage, payment_method)
            VALUES (:invoice_no, :date, :customer_name, :total_amount, :gst_percentage, :payment_method)
        """, header_data)
        conn.commit()
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in add_invoice_header: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Database error in add_invoice_header: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_invoice_line_item(line_item_data: dict) -> bool:
    """
    Adds a single invoice line item to the invoice_line_items table.

    Args:
        line_item_data (dict): A dictionary containing line item details.
                               Expected keys: 'invoice_no', 'line_no', 'item_description',
                                              'part_no', 'hsn_code', 'quantity', 'rate', 'amount'.
    Returns:
        bool: True if the record was added successfully, False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoice_line_items
                (invoice_no, line_no, item_description, part_no, hsn_code, quantity, rate, amount)
            VALUES
                (:invoice_no, :line_no, :item_description, :part_no, :hsn_code, :quantity, :rate, :amount)
        """, line_item_data)
        conn.commit()
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in add_invoice_line_item: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Database error in add_invoice_line_item: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_invoice_line_items_batch(line_items_list: list) -> bool:
    """
    Adds multiple invoice line items to the invoice_line_items table using executemany.

    Args:
        line_items_list (list): A list of dictionaries, where each dictionary contains
                                line item details (same keys as add_invoice_line_item).
    Returns:
        bool: True if all records were added successfully, False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO invoice_line_items
                (invoice_no, line_no, item_description, part_no, hsn_code, quantity, rate, amount)
            VALUES
                (:invoice_no, :line_no, :item_description, :part_no, :hsn_code, :quantity, :rate, :amount)
        """, line_items_list)
        conn.commit()
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in add_invoice_line_items_batch: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Database error in add_invoice_line_items_batch: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_all_invoice_headers(invoice_no_filter: str = None) -> list:
    """
    Fetches invoice headers from the invoice_headers table.
    If invoice_no_filter is provided, it filters by invoice_no using LIKE.
    Results are ordered by date and invoice_no in descending order.

    Args:
        invoice_no_filter (str, optional): The invoice number to filter by (allows partial matches).
                                           Defaults to None (fetch all).

    Returns:
        list: A list of dictionaries, where each dictionary represents an invoice header.
              Returns an empty list if no headers are found or an error occurs.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        params = []
        sql_query = """
            SELECT invoice_no, date, customer_name, total_amount, gst_percentage, payment_method
            FROM invoice_headers
        """

        if invoice_no_filter and invoice_no_filter.strip():
            sql_query += " WHERE invoice_no LIKE ? "
            params.append(f"%{invoice_no_filter.strip()}%")

        sql_query += " ORDER BY date DESC, invoice_no DESC "

        cursor.execute(sql_query, params)
        headers = [dict(row) for row in cursor.fetchall()]
        return headers
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in get_all_invoice_headers (filter: {invoice_no_filter}): {e_op}")
        return []
    except sqlite3.Error as e:
        print(f"Database error in get_all_invoice_headers (filter: {invoice_no_filter}): {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_invoice_header(invoice_no: str) -> bool:
    """
    Deletes an invoice header and its associated line items (due to ON DELETE CASCADE).

    Args:
        invoice_no (str): The invoice number to delete.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Enabling foreign key support is crucial for ON DELETE CASCADE to work
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("DELETE FROM invoice_headers WHERE invoice_no = ?", (invoice_no,))
        conn.commit()
        # Check if deletion was successful (at least one row affected)
        # For DELETE, rowcount is often -1 with SQLite unless PRAGMA count_changes is ON.
        # A more reliable way is to try to fetch it again, or just assume success if no error.
        # For simplicity, we'll assume success if no error.
        # If you need to confirm, you'd check affected_rows if your sqlite version supports it well,
        # or attempt to fetch the deleted record.
        return True
    except sqlite3.OperationalError as e_op:
        print(f"Database connection error in delete_invoice_header for {invoice_no}: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Database error in delete_invoice_header for {invoice_no}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_invoice_header_by_no(invoice_no: str) -> dict | None:
    """Fetches a single invoice header by its invoice_no."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoice_headers WHERE invoice_no = ?", (invoice_no,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.OperationalError as e_op:
        print(f"DB connection error in get_invoice_header_by_no for {invoice_no}: {e_op}")
        return None
    except sqlite3.Error as e:
        print(f"DB error in get_invoice_header_by_no for {invoice_no}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_line_items_for_invoice(invoice_no: str) -> list:
    """Fetches all line items for a given invoice_no, ordered by line_no."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoice_line_items WHERE invoice_no = ? ORDER BY line_no", (invoice_no,))
        items = [dict(row) for row in cursor.fetchall()]
        return items
    except sqlite3.OperationalError as e_op:
        print(f"DB connection error in get_line_items_for_invoice for {invoice_no}: {e_op}")
        return []
    except sqlite3.Error as e:
        print(f"DB error in get_line_items_for_invoice for {invoice_no}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_invoice_header(invoice_no: str, header_data: dict) -> bool:
    """Updates an existing invoice header."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Construct SET clause dynamically for flexibility, though ensure keys are controlled
        set_clause = ", ".join([f"{key} = :{key}" for key in header_data.keys()])
        params = header_data.copy()
        params['invoice_no_to_update'] = invoice_no # Use a different key for WHERE to avoid conflict if 'invoice_no' is in header_data

        # Ensure 'invoice_no' itself is not in the SET clause if it's part of header_data for update
        # (though typically primary key isn't updated, but if it was part of header_data by mistake)
        if 'invoice_no' in params and 'invoice_no' in header_data:
            del params['invoice_no'] # remove it from SET parameters if it exists
            set_clause = ", ".join([f"{key} = :{key}" for key in params.keys() if key != 'invoice_no_to_update'])


        sql = f"UPDATE invoice_headers SET {set_clause} WHERE invoice_no = :invoice_no_to_update"

        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount > 0 # Check if any row was actually updated
    except sqlite3.OperationalError as e_op:
        print(f"DB connection error in update_invoice_header for {invoice_no}: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"DB error in update_invoice_header for {invoice_no}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def delete_line_items_for_invoice(invoice_no: str) -> bool:
    """Deletes all line items for a given invoice_no."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;") # Good practice, though not strictly needed if not relying on it here
        cursor.execute("DELETE FROM invoice_line_items WHERE invoice_no = ?", (invoice_no,))
        conn.commit()
        return True
    except sqlite3.OperationalError as e_op:
        print(f"DB connection error in delete_line_items_for_invoice for {invoice_no}: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"DB error in delete_line_items_for_invoice for {invoice_no}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Basic Test for database functions
    # Ensure database_utils.init_db() has been run to create tables.
    # from database_utils import init_db # You would uncomment and use this if DB_NAME was from database_utils
    # init_db() # Make sure tables are created by running database_utils.py or uncommenting this
    print("Running basic tests for billing_db.py...")

    # Setup test data
    INV_EDIT_TEST = 'INV_EDIT_TEST_001'
    add_invoice_header({
        'invoice_no': INV_EDIT_TEST, 'date': '2024-07-01', 'customer_name': 'Edit Test Initial',
        'total_amount': 100.0, 'gst_percentage': 10.0, 'payment_method': 'Cash'
    })
    add_invoice_line_items_batch([
        {'invoice_no': INV_EDIT_TEST, 'line_no': 1, 'item_description': 'Item A', 'part_no': 'P1', 'hsn_code': 'H1', 'quantity': 1, 'rate': 50, 'amount': 50},
        {'invoice_no': INV_EDIT_TEST, 'line_no': 2, 'item_description': 'Item B', 'part_no': 'P2', 'hsn_code': 'H2', 'quantity': 1, 'rate': 50, 'amount': 50}
    ])

    print(f"\n--- Testing get_invoice_header_by_no ({INV_EDIT_TEST}) ---")
    header = get_invoice_header_by_no(INV_EDIT_TEST)
    if header:
        print(f"SUCCESS: Found header: {header}")
    else:
        print(f"FAILED: Could not find header {INV_EDIT_TEST}")

    print(f"\n--- Testing get_line_items_for_invoice ({INV_EDIT_TEST}) ---")
    items = get_line_items_for_invoice(INV_EDIT_TEST)
    if items and len(items) == 2:
        print(f"SUCCESS: Found {len(items)} line items. First: {items[0]}")
    else:
        print(f"FAILED: Could not find line items or incorrect count for {INV_EDIT_TEST}. Found: {items}")

    print(f"\n--- Testing update_invoice_header ({INV_EDIT_TEST}) ---")
    update_data = {'customer_name': 'Edit Test Updated', 'total_amount': 120.0}
    if update_invoice_header(INV_EDIT_TEST, update_data):
        print(f"SUCCESS: Updated header {INV_EDIT_TEST}.")
        updated_header = get_invoice_header_by_no(INV_EDIT_TEST)
        if updated_header and updated_header['customer_name'] == 'Edit Test Updated' and updated_header['total_amount'] == 120.0:
            print(f"VERIFIED: Update successful. New data: {updated_header}")
        else:
            print(f"VERIFICATION FAILED for update. Current data: {updated_header}")
    else:
        print(f"FAILED: Could not update header {INV_EDIT_TEST}")

    print(f"\n--- Testing delete_line_items_for_invoice ({INV_EDIT_TEST}) ---")
    if delete_line_items_for_invoice(INV_EDIT_TEST):
        print(f"SUCCESS: Deleted line items for {INV_EDIT_TEST}.")
        items_after_delete = get_line_items_for_invoice(INV_EDIT_TEST)
        if not items_after_delete:
            print(f"VERIFIED: Line items for {INV_EDIT_TEST} are deleted.")
        else:
            print(f"VERIFICATION FAILED: Line items still exist for {INV_EDIT_TEST}. Found: {items_after_delete}")
    else:
        print(f"FAILED: Could not delete line items for {INV_EDIT_TEST}")

    # Clean up the main test header used for edit tests
    delete_invoice_header(INV_EDIT_TEST)

    # Previous tests (slightly refactored for clarity)
    add_invoice_header({
        'invoice_no': 'INV_DEL_TEST_001', 'date': '2024-01-01', 'customer_name': 'To Be Deleted',
        'total_amount': 10.0, 'gst_percentage': 1.0, 'payment_method': 'N/A'
    })
    INV_KEEP_TEST_002 = 'INV_KEEP_TEST_002'
    add_invoice_header({
        'invoice_no': INV_KEEP_TEST_002, 'date': '2024-01-02', 'customer_name': 'To Be Kept',
        'total_amount': 20.0, 'gst_percentage': 2.0, 'payment_method': 'Cash'
    })

    print("\n--- Testing get_all_invoice_headers (no filter) ---")
    all_headers_no_filter = get_all_invoice_headers()
    print(f"Retrieved {len(all_headers_no_filter)} invoice headers initially.")

    print("\n--- Testing delete_invoice_header ('INV_DEL_TEST_001') ---")
    if delete_invoice_header('INV_DEL_TEST_001'):
        print("SUCCESS: delete_invoice_header 'INV_DEL_TEST_001'.")
    else:
        print("FAILED: delete_invoice_header 'INV_DEL_TEST_001'.")

    print("\n--- Testing get_all_invoice_headers (with filter 'KEEP_TEST_002') ---")
    filtered_headers = get_all_invoice_headers(invoice_no_filter=INV_KEEP_TEST_002)
    if filtered_headers and filtered_headers[0]['invoice_no'] == INV_KEEP_TEST_002:
        print(f"SUCCESS: Retrieved filtered: {filtered_headers[0]}")
    else:
        print(f"FAILED: Could not retrieve or verify {INV_KEEP_TEST_002}.")

    # Clean up remaining test data
    delete_invoice_header(INV_KEEP_TEST_002)
    print("\nBilling_db.py testing finished.")
