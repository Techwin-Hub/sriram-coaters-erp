import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

import ot_db # Assumes this file is in the same directory or python path
import worker_db # For fetching worker names

class OTManagementPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg="white")
        self.worker_id_map = {} # For mapping display name to worker_id and vice-versa
        self.worker_name_map = {} # For mapping worker_id to display name for summary

        self._fetch_worker_data() # Populate worker_id_map and worker_name_map

        # --- Main Layout ---
        # Top frame for entering OT data
        entry_frame_container = ttk.LabelFrame(self, text="Enter OT Data", padding="10")
        entry_frame_container.pack(fill="x", padx=10, pady=10)
        self._create_ot_entry_section(entry_frame_container)

        # Bottom frame for viewing OT summary
        summary_frame_container = ttk.LabelFrame(self, text="View OT Summary", padding="10")
        summary_frame_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._create_ot_summary_section(summary_frame_container)

        self._set_default_dates()

    def _fetch_worker_data(self):
        workers = worker_db.get_all_workers() # Expects list of dicts
        self.worker_id_map = {f"{w['first_name']} {w.get('last_name', '')} (ID: {w['id']})": w['id'] for w in workers}
        self.worker_name_map = {w['id']: f"{w['first_name']} {w.get('last_name', '')}" for w in workers}


    def _create_ot_entry_section(self, parent_frame):
        frame = ttk.Frame(parent_frame)
        frame.pack(fill="x")

        # Worker Selection
        ttk.Label(frame, text="Select Worker:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.worker_combo_var = tk.StringVar()
        self.worker_combo = ttk.Combobox(frame, textvariable=self.worker_combo_var, values=list(self.worker_id_map.keys()), state="readonly", width=30)
        self.worker_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Date
        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.date_entry = ttk.Entry(frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # OT Hours
        ttk.Label(frame, text="OT Hours:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ot_hours_var = tk.StringVar()
        self.ot_hours_entry = ttk.Entry(frame, textvariable=self.ot_hours_var, width=15)
        self.ot_hours_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.ot_hours_entry.bind("<KeyRelease>", self._calculate_ot_amount_live)

        # OT Rate
        ttk.Label(frame, text="OT Rate:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ot_rate_var = tk.StringVar()
        self.ot_rate_entry = ttk.Entry(frame, textvariable=self.ot_rate_var, width=15)
        self.ot_rate_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.ot_rate_entry.bind("<KeyRelease>", self._calculate_ot_amount_live)

        # Calculated OT Amount
        ttk.Label(frame, text="OT Amount:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.calculated_ot_amount_var = tk.StringVar(value="0.00")
        ttk.Label(frame, textvariable=self.calculated_ot_amount_var, font=('Arial', 10, 'bold')).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Save Button
        save_button = ttk.Button(frame, text="Save OT Record", command=self._save_ot_record, style="Accent.TButton")
        save_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Style for the save button
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="dodgerblue")


    def _calculate_ot_amount_live(self, event=None):
        try:
            hours = float(self.ot_hours_var.get())
            rate = float(self.ot_rate_var.get())
            amount = hours * rate
            self.calculated_ot_amount_var.set(f"{amount:.2f}")
        except ValueError:
            self.calculated_ot_amount_var.set("0.00") # Or "Invalid input"

    def _save_ot_record(self):
        worker_display_name = self.worker_combo_var.get()
        if not worker_display_name:
            messagebox.showerror("Validation Error", "Please select a worker.")
            return
        worker_id = self.worker_id_map.get(worker_display_name)

        date_str = self.date_var.get()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        try:
            ot_hours = float(self.ot_hours_var.get())
            ot_rate = float(self.ot_rate_var.get())
            if ot_hours <= 0 or ot_rate < 0: # Rate can be 0, but hours must be > 0
                messagebox.showerror("Validation Error", "OT hours must be positive and rate non-negative.")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "OT hours and rate must be numeric.")
            return

        ot_amount = ot_hours * ot_rate # Recalculate to ensure consistency

        record_id = ot_db.add_ot_record(worker_id, date_str, ot_hours, ot_rate, ot_amount)
        if record_id:
            messagebox.showinfo("Success", f"OT Record added successfully with ID: {record_id}")
            # Clear entry fields
            # self.worker_combo_var.set('') # Don't clear worker, user might add multiple for same worker
            self.ot_hours_var.set('')
            self.ot_rate_var.set('')
            self.calculated_ot_amount_var.set('0.00')
            # Optionally, refresh summary if the saved record falls within current filter
            self._show_ot_summary(auto_refresh=True)
        else:
            messagebox.showerror("Database Error", "Failed to save OT record.")


    def _create_ot_summary_section(self, parent_frame):
        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(fill="x", pady=(0,5))

        # Worker Filter
        ttk.Label(controls_frame, text="Worker:").pack(side="left", padx=(0,2))
        self.filter_worker_var = tk.StringVar(value="All Workers")
        filter_worker_options = ["All Workers"] + list(self.worker_id_map.keys())
        self.filter_worker_combo = ttk.Combobox(controls_frame, textvariable=self.filter_worker_var, values=filter_worker_options, state="readonly", width=25)
        self.filter_worker_combo.pack(side="left", padx=2)

        # Start Date Filter
        ttk.Label(controls_frame, text="From:").pack(side="left", padx=(5,2))
        self.start_date_filter_var = tk.StringVar()
        self.start_date_filter_entry = ttk.Entry(controls_frame, textvariable=self.start_date_filter_var, width=10)
        self.start_date_filter_entry.pack(side="left", padx=2)

        # End Date Filter
        ttk.Label(controls_frame, text="To:").pack(side="left", padx=(5,2))
        self.end_date_filter_var = tk.StringVar()
        self.end_date_filter_entry = ttk.Entry(controls_frame, textvariable=self.end_date_filter_var, width=10)
        self.end_date_filter_entry.pack(side="left", padx=2)

        show_button = ttk.Button(controls_frame, text="Show Summary", command=self._show_ot_summary)
        show_button.pack(side="left", padx=5)

        # Treeview for OT Summary
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill="both", expand=True)

        self.ot_summary_treeview = ttk.Treeview(
            tree_frame,
            columns=("worker_name", "date", "ot_hours", "ot_rate", "ot_amount"),
            show="headings"
        )
        self.ot_summary_treeview.heading("worker_name", text="Worker Name")
        self.ot_summary_treeview.heading("date", text="Date")
        self.ot_summary_treeview.heading("ot_hours", text="OT Hours")
        self.ot_summary_treeview.heading("ot_rate", text="OT Rate")
        self.ot_summary_treeview.heading("ot_amount", text="OT Amount")

        self.ot_summary_treeview.column("worker_name", width=150)
        self.ot_summary_treeview.column("date", width=100, anchor="center")
        self.ot_summary_treeview.column("ot_hours", width=80, anchor="e")
        self.ot_summary_treeview.column("ot_rate", width=80, anchor="e")
        self.ot_summary_treeview.column("ot_amount", width=100, anchor="e")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ot_summary_treeview.yview)
        self.ot_summary_treeview.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.ot_summary_treeview.pack(fill="both", expand=True)

        # Totals Labels
        totals_frame = ttk.Frame(parent_frame, padding=(0,5,0,0))
        totals_frame.pack(fill="x")
        self.total_ot_hours_var = tk.StringVar(value="Total Hours: 0.00")
        self.total_ot_amount_var = tk.StringVar(value="Total Amount: 0.00")
        ttk.Label(totals_frame, textvariable=self.total_ot_hours_var, font=('Arial', 10, 'bold')).pack(side="left", padx=10)
        ttk.Label(totals_frame, textvariable=self.total_ot_amount_var, font=('Arial', 10, 'bold')).pack(side="left", padx=10)

    def _set_default_dates(self):
        today = date.today()
        self.date_var.set(today.isoformat()) # For OT entry

        # For filters: default to current month
        first_day_of_month = today.replace(day=1)
        self.start_date_filter_var.set(first_day_of_month.isoformat())
        self.end_date_filter_var.set(today.isoformat())


    def _show_ot_summary(self, auto_refresh=False):
        start_date_str = self.start_date_filter_var.get()
        end_date_str = self.end_date_filter_var.get()
        worker_filter_display_name = self.filter_worker_var.get()

        try:
            datetime.strptime(start_date_str, "%Y-%m-%d")
            datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            if not auto_refresh: # Don't show error on auto-refresh if dates are bad, just skip
                 messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format for filter dates.")
            return

        # Clear existing Treeview items
        for item in self.ot_summary_treeview.get_children():
            self.ot_summary_treeview.delete(item)

        records = []
        if worker_filter_display_name == "All Workers":
            records = ot_db.get_all_ot_records_in_range(start_date_str, end_date_str)
        else:
            worker_id = self.worker_id_map.get(worker_filter_display_name)
            if worker_id:
                records = ot_db.get_ot_records_for_worker_in_range(worker_id, start_date_str, end_date_str)
            elif not auto_refresh: # Avoid error message if it's an auto-refresh due to save
                messagebox.showwarning("Worker Not Found", f"Could not find ID for worker: {worker_filter_display_name}")


        total_hours = 0.0
        total_amount = 0.0
        for record in records:
            worker_name = self.worker_name_map.get(record['worker_id'], f"ID: {record['worker_id']}") # Fallback to ID if name not found
            self.ot_summary_treeview.insert("", tk.END, values=(
                worker_name,
                record['date'],
                f"{record['ot_hours']:.2f}",
                f"{record['ot_rate']:.2f}",
                f"{record['ot_amount']:.2f}"
            ))
            total_hours += record['ot_hours']
            total_amount += record['ot_amount']

        self.total_ot_hours_var.set(f"Total Hours: {total_hours:.2f}")
        self.total_ot_amount_var.set(f"Total Amount: {total_amount:.2f}")


if __name__ == '__main__':
    # For testing purposes
    # Ensure database_utils.init_db() and worker_db.py population ran
    # from database_utils import init_db
    # init_db()
    # if not worker_db.get_all_workers():
    #     worker_db.add_worker({'first_name': 'OT Main', 'last_name': 'TestUser', 'role':'Dev', 'joining_date':'2024-01-01'})


    root = tk.Tk()
    root.title("OT Management Test")
    root.geometry("800x600")

    # Example style for Accent.TButton, normally in main_app.py
    s = ttk.Style(root)
    s.configure("Accent.TButton", foreground="white", background="dodgerblue")

    ot_page = OTManagementPage(root)
    ot_page.pack(fill="both", expand=True)
    ot_page._show_ot_summary() # Initial load of summary with default dates
    root.mainloop()
