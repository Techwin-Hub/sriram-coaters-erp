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
                                           'total_amount', 'gst_percentage', 'payment_method',
                                           'grn_date_from', 'grn_date_to', 'po_number'.
    Returns:
        bool | str: True if successful, "DUPLICATE" if integrity error (invoice_no exists), False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        columns = ['invoice_no', 'date', 'customer_name', 'total_amount',
                   'gst_percentage', 'payment_method', 'grn_date_from', 'grn_date_to', 'po_number']

        data_for_insert = {col: header_data.get(col) for col in columns}

        cursor.execute(f"""
            INSERT INTO invoice_headers ({', '.join(columns)})
            VALUES (:{', :'.join(columns)})
        """, data_for_insert)
        conn.commit()
        return True
    except sqlite3.IntegrityError as ie:
        print(f"Database IntegrityError in add_invoice_header for invoice '{header_data.get('invoice_no')}': {ie}")
        if conn:
            conn.rollback()
        return "DUPLICATE"
    except sqlite3.OperationalError as e_op:
        print(f"Database OperationalError in add_invoice_header: {e_op}")
        return False
    except sqlite3.Error as e:
        print(f"Generic Database Error in add_invoice_header: {e}")
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
            SELECT invoice_no, date, customer_name, total_amount, gst_percentage, payment_method, grn_date_from, grn_date_to, po_number
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

def get_last_invoice_no() -> str | None:
    """
    Fetches the last (highest) invoice number from the invoice_headers table.
    Tries to cast invoice_no to INTEGER for numeric comparison first.
    If that fails (e.g., non-numeric prefixes), it falls back to lexicographical MAX.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Primary attempt: Cast to integer to get true numerical max
        cursor.execute("SELECT MAX(CAST(invoice_no AS INTEGER)) FROM invoice_headers")
        result = cursor.fetchone()
        if result and result[0] is not None:
            return str(result[0])
        # If table is empty or all invoice_no are non-castable, result[0] might be None
        # Fall through to lexicographical sort in this case as well.
        raise sqlite3.OperationalError # Trigger fallback explicitly if no numeric max found
    except sqlite3.OperationalError:
        # Fallback: Try lexicographical max if cast fails or returned None
        # This works best for zero-padded numbers or consistent prefix alphanumeric strings
        print(f"Warning: Could not determine last invoice number by numeric cast. Trying lexicographical MAX.")
        try:
            if conn: # conn might be None if connect itself failed initially
                cursor = conn.cursor() # Reuse cursor if conn is still valid
            else:
                conn = sqlite3.connect(DB_NAME) # Need a new connection if previous failed
                cursor = conn.cursor()

            cursor.execute("SELECT MAX(invoice_no) FROM invoice_headers WHERE LENGTH(invoice_no) > 0") # Ensure not empty string
            result = cursor.fetchone()
            if result and result[0] is not None:
                return str(result[0])
            return None # No invoices found at all
        except sqlite3.Error as e_fallback:
            print(f"Fallback DB error in get_last_invoice_no: {e_fallback}")
            return None
    except sqlite3.Error as e: # Catch other potential sqlite3 errors from primary attempt
        print(f"DB error in get_last_invoice_no (primary attempt): {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Basic Test for database functions
    # Ensure database_utils.init_db() has been run to create tables.
    # from database_utils import init_db # You would uncomment and use this if DB_NAME was from database_utils
    # init_db()
    print("Running basic tests for billing_db.py...")

    # Setup test data
    INV_EDIT_TEST = 'INV_EDIT_TEST_001'
    add_invoice_header({
        'invoice_no': INV_EDIT_TEST, 'date': '2024-07-01', 'customer_name': 'Edit Test Initial',
        'total_amount': 100.0, 'gst_percentage': 10.0, 'payment_method': 'Cash',
        'grn_date_from': '2024-06-01', 'grn_date_to': '2024-06-15', 'po_number': 'PO123'
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
    update_data = {
        'customer_name': 'Edit Test Updated',
        'total_amount': 120.0,
        'grn_date_from': '2024-06-20',
        'grn_date_to': None,
        'po_number': 'PO456Updated'
    }
    if update_invoice_header(INV_EDIT_TEST, update_data):
        print(f"SUCCESS: Updated header {INV_EDIT_TEST}.")
        updated_header = get_invoice_header_by_no(INV_EDIT_TEST)
        if updated_header and \
           updated_header['customer_name'] == 'Edit Test Updated' and \
           updated_header['total_amount'] == 120.0 and \
           updated_header['grn_date_from'] == '2024-06-20' and \
           updated_header['grn_date_to'] is None and \
           updated_header['po_number'] == 'PO456Updated':
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
        'total_amount': 10.0, 'gst_percentage': 1.0, 'payment_method': 'N/A',
        'grn_date_from': '2023-12-01', 'grn_date_to': '2023-12-05', 'po_number': 'PO789'
    })
    INV_KEEP_TEST_002 = 'INV_KEEP_TEST_002'
    add_invoice_header({
        'invoice_no': INV_KEEP_TEST_002, 'date': '2024-01-02', 'customer_name': 'To Be Kept',
        'total_amount': 20.0, 'gst_percentage': 2.0, 'payment_method': 'Cash',
        'grn_date_from': '2023-12-10', 'grn_date_to': '2023-12-15', 'po_number': 'POABC'
    })

    print("\n--- Testing get_all_invoice_headers (no filter, should include GRN and PO numbers) ---")
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

    print("\n--- Testing get_last_invoice_no ---")
    # Ensure table is empty for first test of get_last_invoice_no
    # Note: This is a bit destructive for other tests if run in isolation without full setup/teardown.
    # For a real test suite, manage data carefully.
    print("Deleting all headers for get_last_invoice_no empty test...")
    all_inv = get_all_invoice_headers()
    for h in all_inv:
        delete_line_items_for_invoice(h['invoice_no']) # Clear line items first due to FK if any
        delete_invoice_header(h['invoice_no'])

    last_inv = get_last_invoice_no()
    print(f"Last invoice_no (empty table): {last_inv}, Expected: None")
    if last_inv is None:
        print("SUCCESS: get_last_invoice_no on empty table.")
    else:
        print("FAILED: get_last_invoice_no on empty table.")

    add_invoice_header({'invoice_no': '1', 'date': '2023-01-01', 'customer_name': 'Test 1'})
    last_inv = get_last_invoice_no()
    print(f"Last invoice_no (after '1'): {last_inv}, Expected: 1")
    if last_inv == '1': print("SUCCESS") 
    else: print("FAILED")

    add_invoice_header({'invoice_no': '002', 'date': '2023-01-02', 'customer_name': 'Test 2'})
    last_inv = get_last_invoice_no()
    print(f"Last invoice_no (after '002'): {last_inv}, Expected: 2 (due to CAST)") # CAST makes it 2, not "002"
    if last_inv == '2': print("SUCCESS") 
    else: print("FAILED")

    add_invoice_header({'invoice_no': '10', 'date': '2023-01-03', 'customer_name': 'Test 3'})
    last_inv = get_last_invoice_no()
    print(f"Last invoice_no (after '10'): {last_inv}, Expected: 10")
    if last_inv == '10': print("SUCCESS") 
    else: print("FAILED")

    add_invoice_header({'invoice_no': 'INV005', 'date': '2023-01-04', 'customer_name': 'Test INV'})
    last_inv = get_last_invoice_no() # This will use lexicographical due to "INV"
    print(f"Last invoice_no (after 'INV005'): {last_inv}, Expected: INV005 (lexicographical due to fallback)")
    if last_inv == 'INV005': print("SUCCESS") 
    else: print("FAILED")

    add_invoice_header({'invoice_no': '100', 'date': '2023-01-05', 'customer_name': 'Test 100'})
    last_inv = get_last_invoice_no() # Numeric cast should work here and be > INV005 lexicographically
    print(f"Last invoice_no (after '100'): {last_inv}, Expected: 100 (numeric cast should override INV005)")
    if last_inv == '100': print("SUCCESS") 
    else: print("FAILED")


    # Clean up after tests
    delete_invoice_header('1')
    delete_invoice_header('002') # Will try to delete '2' due to cast, might fail if '2' doesn't exist
    delete_invoice_header('2')   # Explicitly delete '2'
    delete_invoice_header('10')
    delete_invoice_header('INV005')
    delete_invoice_header('100')

    print("\nBilling_db.py testing finished.")
