import tkinter as tk
from tkinter import ttk
from data_entry import DataEntryPage
from database_utils import init_db
from worker_management import WorkerManagementPage
from attendance_system import AttendancePage
from ot_management import OTManagementPage # Import OTManagementPage

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sriram Coaters ERP")
        self.geometry("800x600")

        # Create navigation panel
        self.nav_panel = tk.Frame(self, width=200, bg="lightgray")
        self.nav_panel.pack(side="left", fill="y")

        # Add navigation buttons
        self.data_entry_button = ttk.Button(self.nav_panel, text="Data Entry", command=self.show_data_entry_page)
        self.data_entry_button.pack(pady=10)

        self.workers_button = ttk.Button(self.nav_panel, text="Workers", command=self.show_worker_management_page)
        self.workers_button.pack(pady=10)

        self.attendance_button = ttk.Button(self.nav_panel, text="Attendance", command=self.show_attendance_page)
        self.attendance_button.pack(pady=10)

        self.ot_button = ttk.Button(self.nav_panel, text="OT", command=self.show_ot_management_page) # Link button
        self.ot_button.pack(pady=10)

        # Create main content area
        self.main_content = tk.Frame(self, bg="white")
        self.main_content.pack(side="right", fill="both", expand=True)

        # Add placeholder label
        self.placeholder_label = ttk.Label(self.main_content, text="Main Content Area")
        self.placeholder_label.pack(padx=20, pady=20)
        self.current_page = None # To keep track of the current page

    def show_data_entry_page(self):
        # Clear the main content frame
        for widget in self.main_content.winfo_children():
            widget.destroy()
        # Create and show the DataEntryPage
        self.current_page = DataEntryPage(self.main_content)
        self.current_page.pack(fill="both", expand=True)

    def show_worker_management_page(self):
        # Clear the main content frame
        for widget in self.main_content.winfo_children():
            widget.destroy()
        # Create and show the WorkerManagementPage
        self.current_page = WorkerManagementPage(self.main_content)
        self.current_page.pack(fill="both", expand=True)

    def show_attendance_page(self):
        # Clear the main content frame
        for widget in self.main_content.winfo_children():
            widget.destroy()
        # Create and show the AttendancePage
        self.current_page = AttendancePage(self.main_content)
        self.current_page.pack(fill="both", expand=True)

    def show_ot_management_page(self):
        # Clear the main content frame
        for widget in self.main_content.winfo_children():
            widget.destroy()
        # Create and show the OTManagementPage
        self.current_page = OTManagementPage(self.main_content)
        self.current_page.pack(fill="both", expand=True)

if __name__ == "__main__":
    init_db() # Initialize the database
    app = MainApplication()
    app.mainloop()
