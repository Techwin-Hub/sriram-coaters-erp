"""
Manages the Overtime (OT) Management UI for the ERP application.

This module provides a Tkinter Frame (`OTManagementPage`) that allows users to:
- Enter new OT records for workers (date, hours, rate).
- View a summary of OT records, filterable by worker and date range.
- See live calculation of OT amount when entering hours and rate.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta, datetime # datetime for date validation

import ot_db     # For database operations related to OT records
import worker_db # For fetching worker names to populate selection comboboxes

class OTManagementPage(tk.Frame):
    """
    A Tkinter Frame class for managing worker Overtime (OT) records.

    It includes sections for entering new OT data and for viewing a summary of
    existing OT records with filtering capabilities.
    """
    def __init__(self, master):
        """
        Initializes the OTManagementPage.

        Args:
            master: The parent tkinter widget.
        """
        super().__init__(master)
        self.configure(bg="white")

        # Dictionaries to map worker display names to IDs and vice-versa.
        # Used for comboboxes and displaying names in the summary.
        self.worker_id_map = {}
        self.worker_name_map = {}

        self._fetch_worker_data() # Populate the worker maps

        # --- Main Layout: Two primary sections ---
        # Top section for entering new OT data.
        entry_frame_container = ttk.LabelFrame(self, text="Enter OT Data", padding="10")
        entry_frame_container.pack(fill="x", padx=10, pady=10)
        self._create_ot_entry_section(entry_frame_container)

        # Bottom section for viewing a summary of OT records.
        summary_frame_container = ttk.LabelFrame(self, text="View OT Summary", padding="10")
        summary_frame_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._create_ot_summary_section(summary_frame_container)

        self._set_default_dates() # Set default dates for entry and filter fields.

    def _fetch_worker_data(self):
        """
        Fetches worker data (ID, first name, last name) from the database
        and populates `self.worker_id_map` and `self.worker_name_map`.
        These maps are used for populating worker selection comboboxes and
        displaying names in the OT summary view.
        """
        workers = worker_db.get_all_workers() # Assumes this returns a list of worker dicts
        # Create a display name format: "FirstName LastName (ID: X)" for comboboxes
        self.worker_id_map = {
            f"{w['first_name']} {w.get('last_name', '')} (ID: {w['id']})": w['id']
            for w in workers
        }
        # Simple map from ID to "FirstName LastName" for display in Treeview
        self.worker_name_map = {
            w['id']: f"{w['first_name']} {w.get('last_name', '')}".strip()
            for w in workers
        }

    def _create_ot_entry_section(self, parent_frame):
        """
        Creates and lays out the UI elements for the OT data entry section.

        Args:
            parent_frame: The parent tkinter widget (a LabelFrame) for this section.
        """
        frame = ttk.Frame(parent_frame) # Inner frame for grid layout
        frame.pack(fill="x")

        # Worker Selection Combobox
        ttk.Label(frame, text="Select Worker:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.worker_combo_var = tk.StringVar()
        self.worker_combo = ttk.Combobox(frame, textvariable=self.worker_combo_var,
                                         values=list(self.worker_id_map.keys()),
                                         state="readonly", width=30)
        self.worker_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Date Entry
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.date_var = tk.StringVar(value=date.today().isoformat()) # Default to today
        self.date_entry = ttk.Entry(frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # OT Hours Entry
        ttk.Label(frame, text="OT Hours:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ot_hours_var = tk.StringVar()
        self.ot_hours_entry = ttk.Entry(frame, textvariable=self.ot_hours_var, width=15)
        self.ot_hours_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        # Bind KeyRelease to live calculate OT amount
        self.ot_hours_entry.bind("<KeyRelease>", self._calculate_ot_amount_live)

        # OT Rate Entry
        ttk.Label(frame, text="OT Rate:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ot_rate_var = tk.StringVar()
        self.ot_rate_entry = ttk.Entry(frame, textvariable=self.ot_rate_var, width=15)
        self.ot_rate_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        # Bind KeyRelease to live calculate OT amount
        self.ot_rate_entry.bind("<KeyRelease>", self._calculate_ot_amount_live)

        # Calculated OT Amount Display (Read-only)
        ttk.Label(frame, text="OT Amount:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.calculated_ot_amount_var = tk.StringVar(value="0.00") # Displays calculated amount
        ttk.Label(frame, textvariable=self.calculated_ot_amount_var,
                  font=('Arial', 10, 'bold')).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Save Button
        save_button = ttk.Button(frame, text="Save OT Record", command=self._save_ot_record, style="Accent.TButton")
        save_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Define Accent.TButton style (could be centralized in main_app.py)
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="dodgerblue")

    def _calculate_ot_amount_live(self, event=None):
        """
        Calculates OT amount live based on input in OT hours and rate fields.
        Updates the `calculated_ot_amount_label`. Handles non-numeric input gracefully.
        Triggered by <KeyRelease> events.
        """
        try:
            hours = float(self.ot_hours_var.get())
            rate = float(self.ot_rate_var.get())
            amount = hours * rate
            self.calculated_ot_amount_var.set(f"{amount:.2f}") # Format to 2 decimal places
        except ValueError: # If hours or rate are not valid floats (e.g., empty or text)
            self.calculated_ot_amount_var.set("0.00") # Default or indicate error

    def _save_ot_record(self):
        """
        Handles saving a new OT record.
        Validates inputs, calculates final OT amount, calls database function to add record,
        and provides user feedback via messageboxes. Clears input fields on success.
        """
        worker_display_name = self.worker_combo_var.get()
        if not worker_display_name: # Validate worker selection
            messagebox.showerror("Validation Error", "Please select a worker.")
            return
        worker_id = self.worker_id_map.get(worker_display_name) # Get actual worker_id

        date_str = self.date_var.get()
        try: # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        try: # Validate numeric inputs for hours and rate
            ot_hours = float(self.ot_hours_var.get())
            ot_rate = float(self.ot_rate_var.get())
            # Basic business rule validation
            if ot_hours <= 0:
                messagebox.showerror("Validation Error", "OT hours must be greater than zero.")
                return
            if ot_rate < 0: # Rate could be zero if it's non-compensatory OT being tracked
                messagebox.showerror("Validation Error", "OT rate cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "OT hours and rate must be numeric values.")
            return

        ot_amount = ot_hours * ot_rate # Final calculation before saving

        # Call database function to add the record
        record_id = ot_db.add_ot_record(worker_id, date_str, ot_hours, ot_rate, ot_amount)
        if record_id:
            messagebox.showinfo("Success", f"OT Record added successfully with ID: {record_id}")
            # Clear input fields for next entry (except worker, user might add multiple for them)
            self.ot_hours_var.set('')
            self.ot_rate_var.set('')
            self.calculated_ot_amount_var.set('0.00')
            # Optionally, refresh summary view if the new record falls within its current filters
            self._show_ot_summary(auto_refresh=True)
        else:
            messagebox.showerror("Database Error", "Failed to save OT record to the database.")

    def _create_ot_summary_section(self, parent_frame):
        """
        Creates and lays out the UI elements for the OT summary view section.
        This includes filters for worker and date range, a Treeview to display
        records, and labels for total OT hours and amount.

        Args:
            parent_frame: The parent tkinter widget (a LabelFrame) for this section.
        """
        # Frame for filter controls
        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(fill="x", pady=(0,5))

        # Worker Filter Combobox
        ttk.Label(controls_frame, text="Worker:").pack(side="left", padx=(0,2))
        self.filter_worker_var = tk.StringVar(value="All Workers") # Default to show all
        filter_worker_options = ["All Workers"] + list(self.worker_id_map.keys())
        self.filter_worker_combo = ttk.Combobox(controls_frame, textvariable=self.filter_worker_var,
                                                values=filter_worker_options, state="readonly", width=25)
        self.filter_worker_combo.pack(side="left", padx=2)

        # Start Date Filter Entry
        ttk.Label(controls_frame, text="From:").pack(side="left", padx=(5,2))
        self.start_date_filter_var = tk.StringVar()
        self.start_date_filter_entry = ttk.Entry(controls_frame, textvariable=self.start_date_filter_var, width=10)
        self.start_date_filter_entry.pack(side="left", padx=2)

        # End Date Filter Entry
        ttk.Label(controls_frame, text="To:").pack(side="left", padx=(5,2))
        self.end_date_filter_var = tk.StringVar()
        self.end_date_filter_entry = ttk.Entry(controls_frame, textvariable=self.end_date_filter_var, width=10)
        self.end_date_filter_entry.pack(side="left", padx=2)

        # Button to trigger summary display/refresh
        show_button = ttk.Button(controls_frame, text="Show Summary", command=self._show_ot_summary)
        show_button.pack(side="left", padx=5)

        # Frame for the Treeview and its scrollbar
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill="both", expand=True)

        # Treeview to display OT records
        self.ot_summary_treeview = ttk.Treeview(
            tree_frame,
            columns=("worker_name", "date", "ot_hours", "ot_rate", "ot_amount"), # Define columns
            show="headings" # Hide the default empty first column
        )
        # Define column headings
        self.ot_summary_treeview.heading("worker_name", text="Worker Name")
        self.ot_summary_treeview.heading("date", text="Date")
        self.ot_summary_treeview.heading("ot_hours", text="OT Hours")
        self.ot_summary_treeview.heading("ot_rate", text="OT Rate")
        self.ot_summary_treeview.heading("ot_amount", text="OT Amount")

        # Configure column properties (width, text alignment)
        self.ot_summary_treeview.column("worker_name", width=150)
        self.ot_summary_treeview.column("date", width=100, anchor="center")
        self.ot_summary_treeview.column("ot_hours", width=80, anchor="e") # 'e' for East (right-aligned)
        self.ot_summary_treeview.column("ot_rate", width=80, anchor="e")
        self.ot_summary_treeview.column("ot_amount", width=100, anchor="e")

        # Vertical scrollbar for the Treeview
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ot_summary_treeview.yview)
        self.ot_summary_treeview.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.ot_summary_treeview.pack(fill="both", expand=True)

        # Frame for displaying total OT hours and amount
        totals_frame = ttk.Frame(parent_frame, padding=(0,5,0,0))
        totals_frame.pack(fill="x")
        self.total_ot_hours_var = tk.StringVar(value="Total Hours: 0.00")
        self.total_ot_amount_var = tk.StringVar(value="Total Amount: 0.00")
        ttk.Label(totals_frame, textvariable=self.total_ot_hours_var,
                  font=('Arial', 10, 'bold')).pack(side="left", padx=10)
        ttk.Label(totals_frame, textvariable=self.total_ot_amount_var,
                  font=('Arial', 10, 'bold')).pack(side="left", padx=10)

    def _set_default_dates(self):
        """Sets default date values for OT entry and summary filter fields."""
        today = date.today()
        self.date_var.set(today.isoformat()) # Default OT entry date to today

        # Default filter dates to the current month (from 1st to today)
        first_day_of_month = today.replace(day=1)
        self.start_date_filter_var.set(first_day_of_month.isoformat())
        self.end_date_filter_var.set(today.isoformat())

    def _show_ot_summary(self, auto_refresh=False):
        """
        Fetches and displays OT records in the Treeview based on selected filters.
        Calculates and displays total OT hours and amount for the filtered data.

        Args:
            auto_refresh (bool): If True, suppresses error popups for invalid filter dates.
                                 Used when refreshing summary after saving a new record.
        """
        start_date_str = self.start_date_filter_var.get()
        end_date_str = self.end_date_filter_var.get()
        worker_filter_display_name = self.filter_worker_var.get()

        try: # Validate date formats for filters
            datetime.strptime(start_date_str, "%Y-%m-%d")
            datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            if not auto_refresh: # Only show error if not an auto-refresh
                 messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format for filter dates.")
            return

        # Clear existing items from Treeview before loading new data
        for item in self.ot_summary_treeview.get_children():
            self.ot_summary_treeview.delete(item)

        records = [] # To store fetched OT records
        # Fetch records based on whether "All Workers" or a specific worker is selected
        if worker_filter_display_name == "All Workers":
            records = ot_db.get_all_ot_records_in_range(start_date_str, end_date_str)
        else:
            worker_id = self.worker_id_map.get(worker_filter_display_name) # Get ID from display name
            if worker_id:
                records = ot_db.get_ot_records_for_worker_in_range(worker_id, start_date_str, end_date_str)
            elif not auto_refresh: # Avoid error if it's an auto-refresh due to save action
                messagebox.showwarning("Worker Not Found", f"Could not find ID for worker: {worker_filter_display_name}")

        total_hours = 0.0
        total_amount = 0.0
        # Populate the Treeview with fetched records
        for record in records:
            # Get worker name using worker_id from the record and the pre-fetched map
            worker_name = self.worker_name_map.get(record['worker_id'], f"ID: {record['worker_id']}")
            self.ot_summary_treeview.insert("", tk.END, values=(
                worker_name,
                record['date'],
                f"{record['ot_hours']:.2f}",  # Format to 2 decimal places
                f"{record['ot_rate']:.2f}",
                f"{record['ot_amount']:.2f}"
            ))
            # Accumulate totals
            total_hours += record['ot_hours']
            total_amount += record['ot_amount']

        # Update total labels
        self.total_ot_hours_var.set(f"Total Hours: {total_hours:.2f}")
        self.total_ot_amount_var.set(f"Total Amount: {total_amount:.2f}")


if __name__ == '__main__':
    # This block allows testing this OT Management page standalone.
    # For proper testing, ensure:
    # 1. `database_utils.init_db()` has been run to create tables.
    # 2. The `workers` table has some data (e.g., by running `worker_management.py` or `main_app.py`).

    # from database_utils import init_db
    # init_db() # Ensure tables exist

    # Example: Add a test worker if none exist for standalone testing
    # if not worker_db.get_all_workers():
    #     worker_db.add_worker({
    #         'first_name': 'OT_Page_Tester', 'last_name': 'User',
    #         'role':'Developer', 'joining_date':'2024-01-01'
    #         # Add other required fields as per worker_db.add_worker
    #     })

    root = tk.Tk()
    root.title("OT Management Test Standalone")
    root.geometry("800x600")

    # Define Accent.TButton style if testing standalone (normally in main_app.py)
    s = ttk.Style(root)
    s.configure("Accent.TButton", foreground="white", background="dodgerblue")

    ot_page = OTManagementPage(root)
    ot_page.pack(fill="both", expand=True)
    ot_page._show_ot_summary() # Load initial summary based on default filter dates
    root.mainloop()
