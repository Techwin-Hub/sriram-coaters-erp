"""
Manages the Worker Management UI for the ERP application.

This module provides a Tkinter Frame (`WorkerManagementPage`) that allows users to:
- Add new workers with their details, photo, and ID proof.
- View a list of existing workers.
- Edit details of existing workers.
- Delete workers.
- Upload and clear photos and ID proofs for workers.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk # Used by image_utils, but good to acknowledge for context
import os # For path joining, checking file existence

import image_utils # For handling image saving and loading for display
import worker_db     # For database operations related to workers

# Define constants for image storage directories.
# These directories are relative to where the main application is run.
WORKER_PHOTOS_DIR = "data/worker_photos"
WORKER_ID_PROOFS_DIR = "data/worker_id_proofs"

class WorkerManagementPage(tk.Frame):
    """
    A Tkinter Frame class that provides the UI for worker management.

    This includes a form for adding/editing worker details and a treeview
    for displaying the list of workers.
    """
    def __init__(self, master):
        """
        Initializes the WorkerManagementPage.

        Args:
            master: The parent tkinter widget.
        """
        super().__init__(master)
        self.configure(bg="white")
        self.editing_worker_id = None # Stores the ID of the worker being edited, if any.

        # Ensure image storage directories exist, create them if they don't.
        os.makedirs(WORKER_PHOTOS_DIR, exist_ok=True)
        os.makedirs(WORKER_ID_PROOFS_DIR, exist_ok=True)

        # --- Main layout ---
        # Main frame to hold both the form and the list sections.
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill="both", expand=True)

        # Left frame for the worker data entry/edit form.
        self.form_frame = ttk.LabelFrame(self.main_frame, text="Add/Edit Worker", padding="10")
        self.form_frame.pack(side="left", fill="y", padx=10, pady=10, anchor="nw")

        # Right frame for displaying the list of workers and action buttons for the list.
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Worker List", padding="10")
        self.list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self._create_worker_form() # Sets up the input fields and buttons in form_frame.
        self._create_worker_list_view() # Sets up the Treeview and action buttons in list_frame.
        self.refresh_worker_list() # Populates the worker list on initial load.

    def _create_worker_form(self):
        """
        Creates and lays out the widgets for the worker data entry form.
        This includes input fields for worker attributes, photo/ID upload, and save/clear buttons.
        """
        frame = ttk.Frame(self.form_frame) # Inner frame for form elements
        frame.pack(fill="x", expand=True)

        # Define form fields: (Label text, widget variable name, widget class, options_dict (optional))
        fields = [
            ("First Name:", "first_name_entry", tk.Entry),
            ("Last Name:", "last_name_entry", tk.Entry),
            ("Address:", "address_text", tk.Text, {"height": 3, "width": 30}), # tk.Text for multi-line
            ("Contact Number:", "contact_number_entry", tk.Entry),
            ("Previous Experience (Years):", "previous_experience_text", tk.Text, {"height": 2, "width": 30}),
            ("Salary Amount:", "salary_amount_entry", tk.Entry),
            ("Salary Frequency:", "salary_frequency_combo", ttk.Combobox, {"values": ["Monthly", "Weekly", "Daily"], "state": "readonly"}),
            ("Role:", "role_entry", tk.Entry),
            ("Joining Date (YYYY-MM-DD):", "joining_date_entry", tk.Entry) # User expected to follow format
        ]

        self.form_widgets = {} # Dictionary to store references to the created widgets
        for i, (label_text, widget_name, widget_class, *widget_options) in enumerate(fields):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2, padx=5)
            options = widget_options[0] if widget_options else {}

            # Instantiate widget based on class and options
            if widget_class == ttk.Combobox: # Combobox needs values passed
                 widget = widget_class(frame, **options)
            elif widget_class == tk.Text: # Text widget needs height/width
                widget = widget_class(frame, **options)
            else: # Default for tk.Entry
                widget = widget_class(frame, width=30)

            widget.grid(row=i, column=1, sticky="ew", pady=2, padx=5)
            self.form_widgets[widget_name] = widget # Store widget reference

        frame.grid_columnconfigure(1, weight=1) # Make entry widgets expand horizontally

        # --- Photo Upload Section ---
        self.photo_path_var = tk.StringVar() # Stores path to the worker's photo
        ttk.Label(frame, text="Photo:").grid(row=len(fields), column=0, sticky="w", pady=5, padx=5)
        self.photo_label = ttk.Label(frame, text="No Photo", relief="solid", width=15, anchor="center")
        self.photo_label.grid(row=len(fields), column=1, sticky="w", pady=2, padx=5)
        self.photo_label.image = None # Keep a reference to PhotoImage to prevent garbage collection

        upload_photo_btn = ttk.Button(frame, text="Upload Photo", command=self._upload_photo)
        upload_photo_btn.grid(row=len(fields) + 1, column=1, sticky="ew", pady=2, padx=5)
        clear_photo_btn = ttk.Button(frame, text="Clear Photo", command=self._clear_photo)
        clear_photo_btn.grid(row=len(fields) + 1, column=0, sticky="w", pady=2, padx=5)

        # --- ID Proof Upload Section ---
        self.id_proof_path_var = tk.StringVar() # Stores path to the ID proof file
        ttk.Label(frame, text="ID Proof:").grid(row=len(fields) + 2, column=0, sticky="w", pady=5, padx=5)
        self.id_proof_label = ttk.Label(frame, text="No ID Proof", relief="solid", width=15, anchor="center")
        self.id_proof_label.grid(row=len(fields) + 2, column=1, sticky="w", pady=2, padx=5)
        self.id_proof_label.image = None # Keep reference for PhotoImage

        upload_id_btn = ttk.Button(frame, text="Upload ID Proof", command=self._upload_id_proof)
        upload_id_btn.grid(row=len(fields) + 3, column=1, sticky="ew", pady=2, padx=5)
        clear_id_btn = ttk.Button(frame, text="Clear ID Proof", command=self._clear_id_proof)
        clear_id_btn.grid(row=len(fields) + 3, column=0, sticky="w", pady=2, padx=5)

        # --- Action Buttons for Form ---
        # Save/Update button text changes based on whether adding or editing
        self.save_update_button = ttk.Button(frame, text="Save Worker", command=self._save_worker, style="Accent.TButton")
        self.save_update_button.grid(row=len(fields) + 4, column=0, columnspan=2, pady=10, padx=5)

        clear_form_button = ttk.Button(frame, text="Clear Form / Cancel Edit", command=self._clear_form)
        clear_form_button.grid(row=len(fields) + 5, column=0, columnspan=2, pady=5, padx=5)


    def _upload_photo(self):
        """Handles the photo upload process.
        Opens a file dialog, saves the selected file using image_utils,
        and updates the photo path variable and preview label.
        """
        filepath = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if filepath: # If a file was selected
            # Save the uploaded file to a designated directory with a unique name
            saved_path = image_utils.save_uploaded_file(filepath, WORKER_PHOTOS_DIR, "worker_photo")
            if saved_path:
                self.photo_path_var.set(saved_path) # Store the path
                # Get and display the image preview
                img = image_utils.get_image_for_display(saved_path, size=(100, 100))
                if img:
                    self.photo_label.config(image=img, text="")
                    self.photo_label.image = img # Keep reference
                else:
                    self.photo_label.config(image=None, text="Preview Error") # If image loading failed
            else:
                messagebox.showerror("Upload Error", "Failed to save photo.")

    def _upload_id_proof(self):
        """Handles the ID proof upload process.
        Similar to photo upload but saves to a different directory and handles
        non-image files by displaying their name.
        """
        filepath = filedialog.askopenfilename(
            title="Select ID Proof",
            filetypes=(("Image/PDF files", "*.jpg *.jpeg *.png *.pdf"), ("All files", "*.*")) # Common ID proof types
        )
        if filepath:
            saved_path = image_utils.save_uploaded_file(filepath, WORKER_ID_PROOFS_DIR, "worker_id")
            if saved_path:
                self.id_proof_path_var.set(saved_path)
                # Display preview if it's an image, otherwise display filename for non-images (like PDF)
                if saved_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    img = image_utils.get_image_for_display(saved_path, size=(100,100))
                    if img:
                        self.id_proof_label.config(image=img, text="")
                        self.id_proof_label.image = img
                    else:
                        self.id_proof_label.config(image=None, text="Preview Error")
                else:
                    self.id_proof_label.config(image=None, text=os.path.basename(saved_path)) # Show filename
            else:
                messagebox.showerror("Upload Error", "Failed to save ID proof.")

    def _clear_photo(self):
        """Clears the selected photo path and resets the photo preview label."""
        self.photo_path_var.set("") # Clear stored path
        self.photo_label.config(image=None, text="No Photo") # Reset UI
        self.photo_label.image = None

    def _clear_id_proof(self):
        """Clears the selected ID proof path and resets the ID proof preview label."""
        self.id_proof_path_var.set("") # Clear stored path
        self.id_proof_label.config(image=None, text="No ID Proof") # Reset UI
        self.id_proof_label.image = None

    def _clear_form(self, clear_images=True):
        """
        Clears all input fields in the worker form.
        Also resets the form to "Add Worker" mode if it was in "Edit Worker" mode.

        Args:
            clear_images (bool): If True, also clears photo and ID proof paths and previews.
        """
        # Clear all text entries and comboboxes
        for widget_name, widget in self.form_widgets.items():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END) # For tk.Text widgets
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END) # For tk.Entry widgets
            elif isinstance(widget, ttk.Combobox):
                widget.set('') # Clear combobox selection

        if clear_images:
            self._clear_photo()
            self._clear_id_proof()

        # Reset edit mode state
        self.editing_worker_id = None
        self.form_frame.config(text="Add Worker") # Reset form title
        self.save_update_button.config(text="Save Worker") # Reset button text

    def _save_worker(self):
        """
        Handles saving worker data (either adding a new worker or updating an existing one).
        Collects data from form fields, performs validation, calls database functions,
        and provides user feedback.
        """
        data = {} # Dictionary to hold worker data from form
        for name, widget in self.form_widgets.items():
            # Convert widget name to a more generic key name for the data dict
            key_name = name.replace("_entry", "").replace("_text", "").replace("_combo","")
            if isinstance(widget, tk.Text):
                data[key_name] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, ttk.Combobox):
                data[key_name] = widget.get()
            else: # tk.Entry
                data[key_name] = widget.get().strip()

        # Get paths for photo and ID proof
        data['photo_path'] = self.photo_path_var.get()
        data['id_proof_path'] = self.id_proof_path_var.get()

        # --- Validation ---
        # Check for required fields
        if not data.get('first_name') or not data.get('role') or not data.get('joining_date'):
            messagebox.showerror("Validation Error", "First Name, Role, and Joining Date are required.")
            return

        # Validate salary amount (must be a number if provided)
        try:
            salary_str = data.get('salary_amount', '').strip()
            if salary_str: # If something is entered
                data['salary_amount'] = float(salary_str)
            else: # If empty, store as None (or 0.0 if preferred by DB schema/logic)
                data['salary_amount'] = None
        except ValueError:
            messagebox.showerror("Validation Error", "Salary amount must be a valid number.")
            return

        # --- Database Operation (Add or Update) ---
        if self.editing_worker_id: # If an ID is stored, we are updating
            success = worker_db.update_worker(self.editing_worker_id, data)
            if success:
                messagebox.showinfo("Success", "Worker details updated successfully.")
                self._clear_form() # Clear form and reset edit mode
            else:
                messagebox.showerror("Error", "Failed to update worker.")
        else: # No ID, so we are adding a new worker
            worker_id = worker_db.add_worker(data)
            if worker_id:
                messagebox.showinfo("Success", f"Worker added successfully with ID: {worker_id}")
                self._clear_form() # Clear form for next entry
            else:
                messagebox.showerror("Error", "Failed to add worker.")

        self.refresh_worker_list() # Update the list view to reflect changes

    def _create_worker_list_view(self):
        """
        Creates the Treeview widget to display the list of workers
        and action buttons (Edit, Delete) for the list.
        """
        # ttk.Treeview widget setup
        self.worker_tree = ttk.Treeview(
            self.list_frame,
            columns=("id", "full_name", "role", "contact", "joining_date"), # Define columns
            show="headings" # Hide the default first empty column
        )
        # Define column headings
        self.worker_tree.heading("id", text="ID")
        self.worker_tree.heading("full_name", text="Full Name")
        self.worker_tree.heading("role", text="Role")
        self.worker_tree.heading("contact", text="Contact")
        self.worker_tree.heading("joining_date", text="Joining Date")

        # Configure column properties (width, anchor for text alignment)
        self.worker_tree.column("id", width=50, anchor="center")
        self.worker_tree.column("full_name", width=150)
        self.worker_tree.column("role", width=100)
        self.worker_tree.column("contact", width=100)
        self.worker_tree.column("joining_date", width=100, anchor="center")

        self.worker_tree.pack(fill="both", expand=True, padx=5, pady=5)
        # Bind selection event to _on_worker_select (currently only prints, could enable buttons)
        self.worker_tree.bind("<<TreeviewSelect>>", self._on_worker_select)

        # --- Action Buttons below the List ---
        action_button_frame = ttk.Frame(self.list_frame)
        action_button_frame.pack(fill="x", pady=5)

        edit_button = ttk.Button(action_button_frame, text="Edit Selected", command=self._edit_selected_worker)
        edit_button.pack(side="left", padx=5)

        delete_button = ttk.Button(action_button_frame, text="Delete Selected", command=self._delete_selected_worker, style="Danger.TButton")
        delete_button.pack(side="left", padx=5)

        # Define custom styles if not defined globally in main_app.py
        # This ensures buttons look as intended even if run standalone.
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="red") # For delete button
        style.configure("Accent.TButton", foreground="blue") # For save/update button (example)

    def refresh_worker_list(self):
        """
        Reloads the list of workers from the database and updates the Treeview.
        """
        # Clear existing items in the treeview
        for item in self.worker_tree.get_children():
            self.worker_tree.delete(item)

        workers = worker_db.get_all_workers() # Fetch all workers
        for worker in workers:
            full_name = f"{worker.get('first_name', '')} {worker.get('last_name', '')}".strip()
            # Insert worker data into the treeview
            self.worker_tree.insert("", tk.END, values=(
                worker['id'],
                full_name,
                worker.get('role', ''),
                worker.get('contact_number', ''),
                worker.get('joining_date', '')
            ))

    def _on_worker_select(self, event):
        """
        Handles the event when a worker is selected in the Treeview.
        Currently, it just prints the selected worker's ID for debugging.
        Could be expanded to enable/disable edit/delete buttons.
        """
        selected_items = self.worker_tree.selection()
        if selected_items: # If something is selected
            item = self.worker_tree.item(selected_items[0]) # Get selected item's data
            worker_id = item['values'][0] # Assuming ID is the first value
            print(f"Selected worker ID from Treeview: {worker_id}")

    def _load_worker_for_editing(self, worker_id):
        """
        Loads the details of a selected worker into the form for editing.

        Args:
            worker_id (int): The ID of the worker to load.
        """
        worker = worker_db.get_worker_by_id(worker_id) # Fetch worker data
        if not worker:
            messagebox.showerror("Error", "Could not fetch worker details.")
            return

        self._clear_form(clear_images=False) # Clear form fields but keep existing images initially
        self.editing_worker_id = worker_id # Set edit mode
        self.form_frame.config(text=f"Edit Worker (ID: {worker_id})") # Update form title
        self.save_update_button.config(text="Update Worker") # Change button text

        # Populate form fields with worker's data
        self.form_widgets["first_name_entry"].insert(0, worker.get("first_name", ""))
        self.form_widgets["last_name_entry"].insert(0, worker.get("last_name", ""))
        self.form_widgets["address_text"].insert("1.0", worker.get("address", ""))
        self.form_widgets["contact_number_entry"].insert(0, worker.get("contact_number", ""))
        self.form_widgets["previous_experience_text"].insert("1.0", worker.get("previous_experience", ""))
        self.form_widgets["salary_amount_entry"].insert(0, str(worker.get("salary_amount", "")))
        self.form_widgets["salary_frequency_combo"].set(worker.get("salary_frequency", ""))
        self.form_widgets["role_entry"].insert(0, worker.get("role", ""))
        self.form_widgets["joining_date_entry"].insert(0, worker.get("joining_date", ""))

        # Load and display photo
        photo_path = worker.get("photo_path")
        self.photo_path_var.set(photo_path or "") # Store path
        if photo_path and os.path.exists(photo_path):
            img = image_utils.get_image_for_display(photo_path, size=(100, 100))
            if img:
                self.photo_label.config(image=img, text="")
                self.photo_label.image = img
            else:
                self.photo_label.config(image=None, text="Load Error")
        else:
            self.photo_label.config(image=None, text="No Photo")

        # Load and display ID proof (image or filename)
        id_proof_path = worker.get("id_proof_path")
        self.id_proof_path_var.set(id_proof_path or "") # Store path
        if id_proof_path and os.path.exists(id_proof_path):
            if id_proof_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')): # If it's an image
                img = image_utils.get_image_for_display(id_proof_path, size=(100,100))
                if img:
                    self.id_proof_label.config(image=img, text="")
                    self.id_proof_label.image = img
                else:
                    self.id_proof_label.config(image=None, text="Preview Error")
            else: # Not an image, show filename
                self.id_proof_label.config(image=None, text=os.path.basename(id_proof_path))
        else:
            self.id_proof_label.config(image=None, text="No ID Proof")


    def _edit_selected_worker(self):
        """
        Handles the action for the "Edit Selected" button.
        Loads the selected worker from the Treeview into the form for editing.
        """
        selected_items = self.worker_tree.selection() # Get selected item(s)
        if not selected_items: # Check if anything is selected
            messagebox.showwarning("Selection Error", "Please select a worker from the list to edit.")
            return
        item = self.worker_tree.item(selected_items[0]) # Get data of the first selected item
        worker_id = item['values'][0] # Assuming ID is the first value
        self._load_worker_for_editing(worker_id) # Load this worker's data into the form

    def _delete_selected_worker(self):
        """
        Handles the action for the "Delete Selected" button.
        Confirms deletion and then removes the worker from the database.
        """
        selected_items = self.worker_tree.selection()
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select a worker from the list to delete.")
            return

        item = self.worker_tree.item(selected_items[0])
        worker_id = item['values'][0] # Worker ID
        worker_name = item['values'][1] # Worker's full name for confirmation message

        # Confirmation dialog before deleting
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete worker '{worker_name}' (ID: {worker_id})?\n"
            "This action cannot be undone. Associated attendance and OT records will also be deleted."
        )
        if confirm:
            # Note: Physical file deletion is not handled here but in worker_db.py (if uncommented).
            # The ON DELETE CASCADE in DB handles related attendance/OT records.
            success = worker_db.delete_worker(worker_id)
            if success:
                messagebox.showinfo("Success", f"Worker '{worker_name}' deleted successfully.")
                self.refresh_worker_list() # Refresh list to show deletion
                self._clear_form() # Clear form if the deleted worker was being edited
            else:
                messagebox.showerror("Error", f"Failed to delete worker '{worker_name}'.")


if __name__ == '__main__':
    # This block allows testing this module standalone.
    # Ensure database is initialized (e.g., by running main_app.py once or database_utils.init_db())
    from database_utils import init_db
    init_db() # Create tables if they don't exist

    root = tk.Tk()
    root.title("Worker Management Test Standalone")
    root.geometry("1000x700")

    # Define styles for buttons if testing standalone
    # In the full app, these might be defined in main_app.py
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="dodgerblue")
    style.configure("Danger.TButton", foreground="white", background="red")


    worker_page = WorkerManagementPage(root)
    worker_page.pack(fill="both", expand=True)
    root.mainloop()
