"""
Manages the Attendance System UI for the ERP application.

This module provides a Tkinter Frame (`AttendancePage`) that allows users to:
- Select a date for attendance marking.
- View a list of workers.
- Mark each worker as "Present" or "Absent".
- Enter punch-in and punch-out times for "Present" workers.
- Save the attendance data for the selected date.
- Load existing attendance data for a selected date.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime # For handling dates, especially today's date
import re # For regular expression-based time validation

import attendance_db # For database operations related to attendance

class AttendancePage(tk.Frame):
    """
    A Tkinter Frame class for managing and marking worker attendance.

    Provides UI elements for date selection, a list of workers with attendance
    options (status, punch-in/out times), and buttons to load/save attendance.
    """
    def __init__(self, master):
        """
        Initializes the AttendancePage.

        Args:
            master: The parent tkinter widget.
        """
        print("AttendancePage __init__ started.")
        print(f"Master widget: {master}")
        super().__init__(master)
        self.configure(bg="white")
        self.worker_widgets = [] # List to store dictionaries of widgets for each worker row

        # --- Top Frame for Date Selection and Action Buttons ---
        top_frame = ttk.Frame(self) # Frame to hold date entry and buttons
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Select Date (YYYY-MM-DD):").pack(side="left", padx=(0, 5))
        self.date_var = tk.StringVar(value=date.today().isoformat()) # Default to today's date
        self.date_entry = ttk.Entry(top_frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side="left", padx=5)

        load_button = ttk.Button(top_frame, text="Load Attendance", command=self._load_attendance_for_date)
        load_button.pack(side="left", padx=5)

        save_button = ttk.Button(top_frame, text="Save Attendance", command=self._save_attendance, style="Accent.TButton")
        save_button.pack(side="left", padx=5)

        # Define Accent.TButton style if not already defined globally
        # This ensures the button style is applied if this page is run standalone.
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="dodgerblue")


        # --- Scrollable Area for Listing Workers and Marking Attendance ---
        # A common pattern for scrollable frames in Tkinter: Canvas + Frame + Scrollbar
        canvas_frame = ttk.Frame(self) # Container for canvas and scrollbar
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.canvas = tk.Canvas(canvas_frame, bg="white") # The canvas widget
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y") # Vertical scrollbar

        self.canvas.configure(yscrollcommand=scrollbar.set) # Link scrollbar to canvas

        # This frame will contain the actual worker rows and will be scrolled by the canvas.
        self.scrollable_frame = ttk.Frame(self.canvas)
        # Add scrollable_frame to the canvas using create_window
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure scrollregion when the scrollable_frame's size changes
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # Adjust the width of the scrollable_frame within the canvas when canvas width changes
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # --- Initial Data Load ---
        self._create_worker_rows() # Create the UI structure for worker rows
        self._load_attendance_for_date() # Populate these rows with data for the default date
        print("AttendancePage __init__ finished.")

    def _on_canvas_configure(self, event):
        """Adjusts the width of the item inside the canvas to match the canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _create_worker_rows(self):
        """
        Creates the UI rows for each worker in the scrollable_frame.
        Each row includes labels for worker name, radio buttons for status,
        and entry fields for punch-in/out times.
        """
        print("_create_worker_rows started.")
        # Clear any existing widgets from previous loads
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.worker_widgets = [] # Reset the list of worker widget references

        workers = attendance_db.get_all_active_workers_for_attendance()
        print(f"Workers fetched: {workers}")
        print(f"Number of workers found: {len(workers)}")
        if not workers:
            # If no workers are found, display a message.
            no_workers_message = "No workers found. Please add workers in Worker Management."
            ttk.Label(self.scrollable_frame, text=no_workers_message, padding=10).pack()
            print(no_workers_message)
            print("_create_worker_rows finished.")
            return

        # --- Header Row for the worker list ---
        header_frame = ttk.Frame(self.scrollable_frame, padding=(0,0,0,5))
        header_frame.pack(fill="x", expand=True)
        # Define column headers
        ttk.Label(header_frame, text="Worker Name", font=('Arial', 10, 'bold'), width=30).pack(side="left", padx=5)
        ttk.Label(header_frame, text="Status", font=('Arial', 10, 'bold'), width=15, anchor="center").pack(side="left", padx=5)
        ttk.Label(header_frame, text="Punch In (HH:MM)", font=('Arial', 10, 'bold'), width=15, anchor="center").pack(side="left", padx=5)
        ttk.Label(header_frame, text="Punch Out (HH:MM)", font=('Arial', 10, 'bold'), width=15, anchor="center").pack(side="left", padx=5)
        # Dummy label to help with layout, pushing other elements to their defined widths.
        ttk.Label(header_frame, text="", font=('Arial', 10, 'bold')).pack(side="left", padx=5, expand=True, fill='x')

        # --- Create a row for each worker ---
        for worker in workers:
            row_frame = ttk.Frame(self.scrollable_frame, padding=2) # Frame for each worker's row
            row_frame.pack(fill="x", expand=True, pady=1)

            worker_name = f"{worker.get('first_name', '')} {worker.get('last_name', '')}".strip()
            ttk.Label(row_frame, text=worker_name, width=30, anchor="w").pack(side="left", padx=5)

            # Attendance status (Present/Absent) using Radiobuttons
            status_var = tk.StringVar(value="Absent") # Default status
            present_rb = ttk.Radiobutton(row_frame, text="Present", variable=status_var, value="Present")
            present_rb.pack(side="left", padx=2)
            absent_rb = ttk.Radiobutton(row_frame, text="Absent", variable=status_var, value="Absent")
            absent_rb.pack(side="left", padx=(0,15))

            # Entry fields for punch-in and punch-out times
            punch_in_var = tk.StringVar()
            punch_in_entry = ttk.Entry(row_frame, textvariable=punch_in_var, width=10)
            punch_in_entry.pack(side="left", padx=5)

            punch_out_var = tk.StringVar()
            punch_out_entry = ttk.Entry(row_frame, textvariable=punch_out_var, width=10)
            punch_out_entry.pack(side="left", padx=5)

            # Add a dummy label to help with layout if needed, or rely on Frame padding
            # ttk.Label(row_frame, text="").pack(side="left", padx=5, expand=True, fill='x')


            self.worker_widgets.append({
                'worker_id': worker['id'],
                'name_label': worker_name, # For reference
                'status_var': status_var,
                'punch_in_var': punch_in_var,
                'punch_out_var': punch_out_var,
                'present_rb': present_rb, # To potentially disable/enable time entries
                'absent_rb': absent_rb,
                'punch_in_entry': punch_in_entry,
                'punch_out_entry': punch_out_entry,
            })

            # Disable time entries if "Absent" is selected by default
            def toggle_time_entries(status_var=status_var, in_entry=punch_in_entry, out_entry=punch_out_entry):
                if status_var.get() == "Absent":
                    in_entry.config(state="disabled")
                    out_entry.config(state="disabled")
                    # punch_in_var.set("") # Optionally clear times when marked absent
                    # punch_out_var.set("")
                else:
                    in_entry.config(state="normal")
                    out_entry.config(state="normal")

            status_var.trace_add("write", lambda *args, sv=status_var, pie=punch_in_entry, poe=punch_out_entry: toggle_time_entries(sv, pie, poe))
            toggle_time_entries(status_var, punch_in_entry, punch_out_entry) # Initial state based on default


    def _load_attendance_for_date(self):
        print("_load_attendance_for_date started.")
        date_str = self.date_var.get()
        print(f"Date string: {date_str}")
        try:
            # Validate date format (basic)
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter the date in YYYY-MM-DD format.")
            return

        # If worker rows haven't been created (e.g. if this is called before _create_worker_rows)
        # or if the worker list might have changed, it's better to recreate them.
        # For simplicity now, we assume _create_worker_rows has run once at init.
        # If worker list can change dynamically, _create_worker_rows should be callable here.

        if not self.worker_widgets: # If no workers were found and rows weren't created
            print("No worker widgets to load attendance into.")
            # Potentially show a message in the UI if scrollable_frame is empty
            if not self.scrollable_frame.winfo_children():
                 ttk.Label(self.scrollable_frame, text="No workers found to load attendance for.", padding=10).pack()
            print("_load_attendance_for_date finished.") # Added here as it's an early exit
            return

        print(f"Processing worker_widgets: {len(self.worker_widgets)} widgets.")
        existing_records = attendance_db.get_attendance_records(date_str)
        print(f"Existing records: {existing_records}")

        for worker_row in self.worker_widgets:
            worker_id = worker_row['worker_id']
            record = existing_records.get(worker_id)

            if record:
                worker_row['status_var'].set(record.get('status', 'Absent'))
                worker_row['punch_in_var'].set(record.get('punch_in_time', ''))
                worker_row['punch_out_var'].set(record.get('punch_out_time', ''))
            else:
                # Default to Absent, clear times
                worker_row['status_var'].set('Absent')
                worker_row['punch_in_var'].set('')
                worker_row['punch_out_var'].set('')

            # Trigger the trace to set initial state of time entries
            worker_row['status_var'].trace_notify_now()
        print("_create_worker_rows finished.") # This was misplaced in the previous diff, should be at the end of _create_worker_rows
        print("_load_attendance_for_date finished.")


    def _validate_time_format(self, time_str):
        if not time_str: # Empty string is valid (means not punched in/out)
            return True
        # Basic HH:MM format check
        if re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", time_str):
            return True
        return False

    def _save_attendance(self):
        date_str = self.date_var.get()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter the date in YYYY-MM-DD format before saving.")
            return

        records_to_save = []
        all_valid = True
        for worker_row in self.worker_widgets:
            worker_id = worker_row['worker_id']
            status = worker_row['status_var'].get()
            punch_in = worker_row['punch_in_var'].get().strip()
            punch_out = worker_row['punch_out_var'].get().strip()

            if status == "Present":
                if not self._validate_time_format(punch_in):
                    messagebox.showerror("Invalid Time", f"Invalid Punch In time for {worker_row['name_label']}. Use HH:MM format or leave blank.")
                    all_valid = False
                    break
                if not self._validate_time_format(punch_out):
                    messagebox.showerror("Invalid Time", f"Invalid Punch Out time for {worker_row['name_label']}. Use HH:MM format or leave blank.")
                    all_valid = False
                    break
            else: # Absent
                punch_in = "" # Force blank times if absent
                punch_out = ""

            records_to_save.append({
                'worker_id': worker_id,
                'date': date_str,
                'status': status,
                'punch_in_time': punch_in if status == "Present" else "",
                'punch_out_time': punch_out if status == "Present" else ""
            })

        if not all_valid:
            return # Stop if validation failed for any worker

        if not records_to_save and self.worker_widgets: # We have workers, but nothing to save (e.g. all left as default absent with no times)
             # This case might be valid if we want to explicitly mark everyone as absent with no times.
             # Or, we might want a confirmation. For now, let's allow saving empty/default states.
             pass # Allow saving default states

        if not self.worker_widgets:
            messagebox.showinfo("No Data", "No worker data to save.")
            return


        if attendance_db.save_attendance_records(records_to_save):
            messagebox.showinfo("Success", f"Attendance for {date_str} saved successfully.")
        else:
            messagebox.showerror("Save Error", f"Failed to save attendance for {date_str}.")

print("AttendancePage class definition loaded.")
if __name__ == '__main__':
    # For testing purposes
    # Ensure database_utils.init_db() has run once to create tables
    # from database_utils import init_db
    # init_db()
    # import worker_db # To potentially add a worker if none exist for testing
    # if not attendance_db.get_all_active_workers_for_attendance():
    #     worker_db.add_worker({'first_name': 'Test', 'last_name': 'WorkerAttendUI', 'role': 'TesterUI', 'joining_date': '2024-01-01'})


    root = tk.Tk()
    root.title("Attendance System Test")
    root.geometry("750x500") # Adjusted size

    # Example style for Accent.TButton, normally in main_app.py
    s = ttk.Style(root)
    s.configure("Accent.TButton", foreground="white", background="dodgerblue")


    attendance_page = AttendancePage(root)
    attendance_page.pack(fill="both", expand=True)
    root.mainloop()
