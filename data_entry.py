"""
Provides the UI and logic for the Data Entry module, specifically for creating
Delivery Challans and managing work descriptions.

This module includes:
- A `DataEntryPage` class that serves as the main UI for this module, embeddable
  into the main application.
- An `AddDescriptionPopup` class for adding new work descriptions to the database.
- Helper functions to interact with the `description_master` table in the database.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3 # For database interactions
from datetime import date # For default date in forms
from typing import Callable # For type hinting callbacks
from billing import BillingPreviewWindow # For generating billing preview

# Database initialization (init_db) and sample data insertion (insert_sample_data)
# were moved to database_utils.py and are called from main_app.py.

DB_NAME = "description.db" # Define DB_NAME, consistent with other db modules

def get_all_descriptions():
    """
    Fetches all unique descriptions from the 'description_master' table.

    Returns:
        list: A list of description strings.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("SELECT description FROM description_master ORDER BY description")
        results = [row[0] for row in cur.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"Database error in get_all_descriptions: {e}")
        return []
    finally:
        conn.close()


def get_description_details(desc):
    """
    Fetches detailed information for a given description from 'description_master'.

    Args:
        desc (str): The description text to look up.

    Returns:
        dict: A dictionary containing 'customer_part_no', 'sac_code', 'rate', 'po_no'.
              Returns an empty dictionary if the description is not found or an error occurs.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("SELECT customer_part_no, sac_code, rate, po_no FROM description_master WHERE description = ?", (desc,))
        row = cur.fetchone()
        if row:
            return {"customer_part_no": row[0], "sac_code": row[1], "rate": row[2], "po_no": row[3]}
        return {}
    except sqlite3.Error as e:
        print(f"Database error in get_description_details for '{desc}': {e}")
        return {}
    finally:
        conn.close()


def insert_description_to_db(data):
    """
    Inserts a new description record into the 'description_master' table.

    Args:
        data (dict): A dictionary containing the description details. Expected keys are
                     "Description", "Customer Part No.", "SAC Code", "Rate", "PO No".

    Shows an error messagebox if the description already exists (due to UNIQUE constraint).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO description_master (description, customer_part_no, sac_code, rate, po_no)
            VALUES (?, ?, ?, ?, ?)
        """, (data["Description"], data["Customer Part No."], data["SAC Code"], float(data["Rate"]), data["PO No"]))
        conn.commit()
    except sqlite3.IntegrityError: # Specific error for UNIQUE constraint violation
        messagebox.showerror("Error", f"Description '{data['Description']}' already exists.")
    except sqlite3.Error as e:
        print(f"Database error in insert_description_to_db: {e}")
        messagebox.showerror("Database Error", "Could not save the new description.")
    except ValueError: # Handles error if Rate is not a valid float
        messagebox.showerror("Invalid Input", "Rate must be a valid number.")
    finally:
        conn.close()


class AddDescriptionPopup(tk.Toplevel):
    """
    A Toplevel window (popup) for adding a new work description to the database.
    """
    def __init__(self, master, on_submit_callback: Callable):
        """
        Initializes the AddDescriptionPopup window.

        Args:
            master: The parent tkinter widget.
            on_submit_callback (Callable): A function to call after a new description
                                          is successfully submitted and saved.
                                          It typically refreshes the description list in the parent window.
        """
        super().__init__(master)
        self.title("Add New Description")
        self.geometry("400x350") # Adjusted size for better fit
        self.configure(bg="white")
        self.transient(master) # Set to be a transient window of the master
        self.grab_set() # Make it modal

        self.on_submit_callback = on_submit_callback
        self._create_widgets() # Call method to create UI elements

    def _create_widgets(self):
        """Creates and lays out the widgets for the popup form."""
        tk.Label(self, text="Add New Description Entry", font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        fields = ["Description", "Customer Part No.", "SAC Code", "Rate", "PO No"] # Fields for the form
        self.entries = {} # Dictionary to store Entry widgets

        # Create a frame for the form fields for better padding and layout control
        form_fields_frame = ttk.Frame(self)
        form_fields_frame.pack(pady=5, padx=20, fill="x")

        for field in fields:
            row_frame = ttk.Frame(form_fields_frame) # Frame for each label-entry pair
            row_frame.pack(fill="x", pady=2)

            label_widget = ttk.Label(row_frame, text=field + ":", width=15, anchor="w") # Fixed width for alignment
            label_widget.pack(side="left", padx=(0,5))

            entry_widget = ttk.Entry(row_frame, width=30) # Use ttk.Entry for consistent styling
            entry_widget.pack(side="left", expand=True, fill="x")
            self.entries[field] = entry_widget

        # Save Button
        save_button = ttk.Button(self, text="Save Description", command=self._submit_form, style="Accent.TButton")
        save_button.pack(pady=15)

    def _submit_form(self):
        """
        Collects data from form fields, attempts to insert it into the database,
        calls the on_submit_callback, and closes the popup.
        Handles potential errors during insertion.
        """
        # Collect data from entry fields
        data_to_submit = {key: entry.get().strip() for key, entry in self.entries.items()}

        # Basic validation: Description and Rate are important
        if not data_to_submit.get("Description"):
            messagebox.showerror("Validation Error", "Description cannot be empty.", parent=self)
            return
        if not data_to_submit.get("Rate"):
            messagebox.showerror("Validation Error", "Rate cannot be empty.", parent=self)
            return
        try:
            float(data_to_submit["Rate"]) # Check if rate is a valid number
        except ValueError:
            messagebox.showerror("Validation Error", "Rate must be a valid number.", parent=self)
            return

        try:
            insert_description_to_db(data_to_submit) # Call DB function
            self.on_submit_callback(data_to_submit) # Trigger callback to refresh parent UI
            self.destroy() # Close the popup window
        except Exception as e: # Catch-all for unexpected errors during submission
            # Specific errors (like IntegrityError for duplicates) are handled in insert_description_to_db
            messagebox.showerror("Submission Error", f"An unexpected error occurred: {e}", parent=self)


class DataEntryPage(tk.Frame):
    """
    Main UI Frame for the Data Entry module.

    This page allows users to create Delivery Challans by selecting work descriptions
    and entering quantities. It also provides an interface to add new work descriptions.
    It's designed to be embedded within the main application window.
    """
    def __init__(self, master):
        """
        Initializes the DataEntryPage.

        Args:
            master: The parent tkinter widget.
        """
        super().__init__(master)
        self.configure(bg="#f0f0f0") # Set background color for the page
        self._create_widgets() # Call method to create all UI elements

    def _create_widgets(self):
        """Creates and lays out all widgets for the Data Entry page."""
        # --- Page Title ---
        tk.Label(self, text="Delivery Challan Entry Form", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        # --- Main Form Frame (for DC No, Date, PO No, etc.) ---
        form_frame = ttk.LabelFrame(self, text="Challan Details", padding="10") # Changed to LabelFrame
        form_frame.pack(padx=20, pady=10, fill="x")

        # Define labels and corresponding entry fields for the main form
        labels = ["DC No", "Date (YYYY-MM-DD)", "PO No", "DC No & Date", "Challan No"] # TODO: "DC No & Date" seems redundant if Date is separate
        self.challan_detail_entries = {} # Dictionary to store these entry widgets
        for i, label_text in enumerate(labels):
            ttk.Label(form_frame, text=label_text + ":").grid(row=i, column=0, sticky="w", pady=2, padx=5)
            entry = ttk.Entry(form_frame, width=40) # Use ttk.Entry
            entry.grid(row=i, column=1, pady=2, padx=5, sticky="ew")
            if label_text == "Date (YYYY-MM-DD)":
                entry.insert(0, str(date.today())) # Default to today's date
            self.challan_detail_entries[label_text] = entry
        form_frame.columnconfigure(1, weight=1) # Make entries expand

        # --- Item Details Frame (for Description, Qty, Rate, Amount) ---
        item_frame = ttk.LabelFrame(self, text="Item Details", padding="10")
        item_frame.pack(padx=20, pady=10, fill="x")

        # Description Combobox
        ttk.Label(item_frame, text="Description:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.description_cb = ttk.Combobox(item_frame, values=get_all_descriptions(), width=38, state="readonly")
        self.description_cb.grid(row=0, column=1, columnspan=3, sticky="ew", pady=2, padx=5) # Span more columns
        self.description_cb.bind("<<ComboboxSelected>>", self._fill_auto_fields_on_description_select)

        # Auto-filled fields based on description selection
        self.part_entry = self._create_readonly_field(item_frame, "Customer Part No.:", 1, 0)
        self.sac_entry = self._create_readonly_field(item_frame, "SAC Code:", 1, 2)

        # Rate can be auto-filled but also editable, or just auto-filled. Let's make it auto-filled but updatable for calculation.
        self.rate_var = tk.StringVar()
        self.rate_entry = self._create_editable_field(item_frame, "Rate:", 2, 0, textvariable=self.rate_var)
        self.rate_entry.bind("<KeyRelease>", self._calculate_total_amount)

        # PO No (auto-filled from description)
        self.po_no_challan_entry = self._create_readonly_field(item_frame, "PO No (from Desc):", 2, 2)


        # Qty (Editable)
        self.qty_var = tk.StringVar()
        self.qty_entry = self._create_editable_field(item_frame, "Qty:", 3, 0, textvariable=self.qty_var)
        self.qty_entry.bind("<KeyRelease>", self._calculate_total_amount)

        # Amount (Read-only, calculated)
        self.amount_var = tk.StringVar()
        self.amount_entry = self._create_readonly_field(item_frame, "Amount:", 3, 2, textvariable=self.amount_var)

        item_frame.columnconfigure(1, weight=1)
        item_frame.columnconfigure(3, weight=1)


        # --- Action Buttons ---
        btn_frame = ttk.Frame(self) # Use ttk.Frame
        btn_frame.pack(pady=20)

        # Button to add new description (opens popup)
        add_desc_button = ttk.Button(btn_frame, text="➕ Add New Description", command=self._open_add_description_popup)
        add_desc_button.pack(side="left", padx=10)

        # Button to generate the challan/bill preview
        generate_button = ttk.Button(btn_frame, text="🧾 Generate Challan", style="Accent.TButton", command=self._generate_challan_ui)
        generate_button.pack(side="left", padx=10)

    def _create_readonly_field(self, parent, label_text, row, col, textvariable=None):
        """Helper to create a label and a readonly entry field."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, sticky="w", padx=5, pady=2)
        entry_var = textvariable if textvariable else tk.StringVar()
        entry = ttk.Entry(parent, textvariable=entry_var, state="readonly", width=20)
        entry.grid(row=row, column=col+1, sticky="ew", padx=5, pady=2)
        return entry_var # Return the variable to easily set/get its content

    def _create_editable_field(self, parent, label_text, row, col, textvariable=None):
        """Helper to create a label and an editable entry field."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, sticky="w", padx=5, pady=2)
        entry_var = textvariable if textvariable else tk.StringVar()
        entry = ttk.Entry(parent, textvariable=entry_var, width=20)
        entry.grid(row=row, column=col+1, sticky="ew", padx=5, pady=2)
        return entry # Return the widget itself if direct manipulation is needed (like binding)


    def _fill_auto_fields_on_description_select(self, event=None):
        """
        Callback when a description is selected from the combobox.
        Fetches details for the selected description and populates related fields.
        """
        selected_description = self.description_cb.get()
        if not selected_description: return

        details = get_description_details(selected_description)

        # Assuming self.part_entry, self.sac_entry etc. are StringVars from _create_readonly_field
        # Need to adjust how these are accessed if they are widgets.
        # If _create_readonly_field returns the StringVar:
        self.part_entry.set(details.get("customer_part_no", "")) # part_entry is now a StringVar
        self.sac_entry.set(details.get("sac_code", ""))       # sac_entry is now a StringVar
        self.rate_var.set(str(details.get("rate", "")))         # rate_var was already a StringVar
        self.po_no_challan_entry.set(details.get("po_no", "")) # po_no_challan_entry is a StringVar

        # If these were direct widget references, it would be:
        # self.part_entry_widget.config(state="normal"); self.part_entry_widget.delete(0, tk.END); ... .config(state="readonly")

        self._calculate_total_amount() # Recalculate amount if rate changed

    def _calculate_total_amount(self, event=None):
        """Calculates total amount based on quantity and rate."""
        try:
            qty = float(self.qty_var.get())
            rate = float(self.rate_var.get())
            amount = qty * rate
            self.amount_var.set(f"{amount:.2f}")
        except ValueError: # Handle cases where qty or rate are not valid numbers (e.g., empty)
            self.amount_var.set("") # Clear amount or set to "0.00"

    def _open_add_description_popup(self):
        """Opens the popup window for adding a new description."""
        # Define a callback for when the popup submits successfully
        def on_new_description_added(new_data):
            messagebox.showinfo("Saved", f"New description '{new_data['Description']}' added successfully.")
            # Refresh the combobox list with the new description
            self.description_cb["values"] = get_all_descriptions()
            # Optionally, select the newly added description
            # self.description_cb.set(new_data['Description'])
            # self._fill_auto_fields_on_description_select() # And auto-fill fields

        AddDescriptionPopup(self, on_submit_callback=on_new_description_added)

    def _generate_challan_ui(self):
        """
        Collects all data from the form and item fields, then passes it
        to the BillingPreviewWindow for generating a preview or final output.
        """
        # Collect data from the main challan detail entries
        form_data = {key: entry.get() for key, entry in self.challan_detail_entries.items()}

        # Collect data from the item detail section
        item_data = {
            "description": self.description_cb.get(),
            "customer_part_no": self.part_entry.get(), # Assuming part_entry is a StringVar
            "sac_code": self.sac_entry.get(),          # Assuming sac_entry is a StringVar
            "rate": self.rate_var.get(),
            "qty": self.qty_var.get(),
            "amount": self.amount_var.get(),
            "po_no_from_desc": self.po_no_challan_entry.get() # Assuming this is a StringVar
        }

        # Basic validation before generating
        if not form_data.get("DC No") or not item_data.get("description") or not item_data.get("qty"):
            messagebox.showwarning("Missing Data", "DC No, Description, and Quantity are required to generate challan.")
            return
        try:
            float(item_data["qty"])
            float(item_data["rate"])
        except ValueError:
            messagebox.showwarning("Invalid Data", "Quantity and Rate must be valid numbers.")
            return

        # Open the billing preview window with the collected data
        BillingPreviewWindow(self, form_data, item_data)

# Note: The if __name__ == "__main__": block was removed as this module
# is now intended to be part of a larger application and not run standalone.
# Testing of DataEntryPage would typically be done by running main_app.py.
