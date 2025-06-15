"""
Main application file for the Sriram Coaters ERP.

This file initializes the main Tkinter window, sets up navigation,
and handles switching between different modules (Data Entry, Worker Management, etc.).
"""
import tkinter as tk
from tkinter import ttk
from data_entry import DataEntryPage # Assuming DataEntryPage is appropriately commented
from database_utils import init_db # For initializing DB on startup
from worker_management import WorkerManagementPage # Worker management UI module
from attendance_system import AttendancePage # Attendance UI module
from ot_management import OTManagementPage # Overtime UI module

class MainApplication(tk.Tk):
    """
    The main application window class.

    Inherits from tk.Tk and sets up the main UI structure, including
    a navigation panel on the left and a content display area on the right.
    """
    def __init__(self):
        """
        Initializes the MainApplication.

        Sets window title, size, and creates the navigation panel
        with buttons for each module, and the main content frame.
        """
        super().__init__()
        self.title("Sriram Coaters ERP")
        self.geometry("800x600") # Default window size

        # --- Navigation Panel ---
        # This frame holds the buttons to switch between different modules.
        self.nav_panel = tk.Frame(self, width=200, bg="lightgray")
        self.nav_panel.pack(side="left", fill="y") # Packed to the left, fills vertically

        # Navigation buttons for each module
        # Each button calls a specific method to show the corresponding page.
        self.data_entry_button = ttk.Button(self.nav_panel, text="Data Entry", command=self.show_data_entry_page)
        self.data_entry_button.pack(pady=10)

        self.workers_button = ttk.Button(self.nav_panel, text="Workers", command=self.show_worker_management_page)
        self.workers_button.pack(pady=10)

        self.attendance_button = ttk.Button(self.nav_panel, text="Attendance", command=self.show_attendance_page)
        self.attendance_button.pack(pady=10)

        self.ot_button = ttk.Button(self.nav_panel, text="OT", command=self.show_ot_management_page)
        self.ot_button.pack(pady=10)

        # --- Main Content Area ---
        # This frame is where the content of each module/page will be displayed.
        self.main_content = tk.Frame(self, bg="white")
        self.main_content.pack(side="right", fill="both", expand=True) # Fills remaining space

        # Placeholder label initially shown in the main content area
        self.placeholder_label = ttk.Label(self.main_content, text="Welcome to Sriram Coaters ERP. Select a module to begin.")
        self.placeholder_label.pack(padx=20, pady=20, anchor="center", expand=True)

        self.current_page_widget = None # Holds the currently displayed page widget


    def _clear_content_frame(self):
        """
        Clears all widgets from the main content frame.
        This is called before loading a new page into the content area.
        """
        if self.current_page_widget:
            self.current_page_widget.destroy()
            self.current_page_widget = None
        # Fallback if placeholder_label was not cleared by current_page_widget.destroy()
        # or if current_page_widget was None but placeholder still exists
        if self.placeholder_label.winfo_exists():
             self.placeholder_label.destroy()


    def show_data_entry_page(self):
        """Displays the Data Entry page in the main content area."""
        self._clear_content_frame()
        self.current_page_widget = DataEntryPage(self.main_content)
        self.current_page_widget.pack(fill="both", expand=True)

    def show_worker_management_page(self):
        """Displays the Worker Management page in the main content area."""
        self._clear_content_frame()
        self.current_page_widget = WorkerManagementPage(self.main_content)
        self.current_page_widget.pack(fill="both", expand=True)

    def show_attendance_page(self):
        """Displays the Attendance System page in the main content area."""
        self._clear_content_frame()
        self.current_page_widget = AttendancePage(self.main_content)
        self.current_page_widget.pack(fill="both", expand=True)

    def show_ot_management_page(self):
        """Displays the OT Management page in the main content area."""
        self._clear_content_frame()
        self.current_page_widget = OTManagementPage(self.main_content)
        self.current_page_widget.pack(fill="both", expand=True)

if __name__ == "__main__":
    # This block runs when the script is executed directly.
    init_db() # Initialize the database (creates tables if they don't exist)
    app = MainApplication() # Create an instance of the main application
    app.mainloop() # Start the Tkinter event loop
