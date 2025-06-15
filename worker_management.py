import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk # Ensure Pillow is imported
import os # For path joining

# Assuming image_utils.py and worker_db.py are in the same directory or accessible in PYTHONPATH
import image_utils
import worker_db

# Define constants for image folders (relative to the script's location or a defined base path)
# For now, let's assume they are relative to the main app's execution directory.
WORKER_PHOTOS_DIR = "data/worker_photos"
WORKER_ID_PROOFS_DIR = "data/worker_id_proofs"

class WorkerManagementPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg="white")
        self.editing_worker_id = None # To track if we are editing or adding a new worker

        # Ensure image directories exist
        os.makedirs(WORKER_PHOTOS_DIR, exist_ok=True)
        os.makedirs(WORKER_ID_PROOFS_DIR, exist_ok=True)

        # --- Main layout ---
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill="both", expand=True)

        # Left frame for the form
        self.form_frame = ttk.LabelFrame(self.main_frame, text="Add/Edit Worker", padding="10")
        self.form_frame.pack(side="left", fill="y", padx=10, pady=10, anchor="nw")

        # Right frame for the list and actions
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Worker List", padding="10")
        self.list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self._create_worker_form()
        self._create_worker_list_view()
        self.refresh_worker_list()

    def _create_worker_form(self):
        frame = ttk.Frame(self.form_frame)
        frame.pack(fill="x", expand=True)

        fields = [
            ("First Name:", "first_name_entry", tk.Entry),
            ("Last Name:", "last_name_entry", tk.Entry),
            ("Address:", "address_text", tk.Text, {"height": 3, "width": 30}),
            ("Contact Number:", "contact_number_entry", tk.Entry),
            ("Previous Experience (Years):", "previous_experience_text", tk.Text, {"height": 2, "width": 30}),
            ("Salary Amount:", "salary_amount_entry", tk.Entry),
            ("Salary Frequency:", "salary_frequency_combo", ttk.Combobox, {"values": ["Monthly", "Weekly", "Daily"], "state": "readonly"}),
            ("Role:", "role_entry", tk.Entry),
            ("Joining Date (YYYY-MM-DD):", "joining_date_entry", tk.Entry)
        ]

        self.form_widgets = {}
        for i, (label_text, widget_name, widget_class, *widget_options) in enumerate(fields):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2, padx=5)
            options = widget_options[0] if widget_options else {}
            if widget_class == ttk.Combobox and 'values' in options:
                 widget = widget_class(frame, **options)
            elif widget_class == tk.Text:
                widget = widget_class(frame, **options) # width, height for Text
            else:
                widget = widget_class(frame, width=30) # Default width for Entry

            widget.grid(row=i, column=1, sticky="ew", pady=2, padx=5)
            self.form_widgets[widget_name] = widget

        frame.grid_columnconfigure(1, weight=1) # Make entry widgets expandable

        # --- Photo Upload ---
        self.photo_path_var = tk.StringVar()
        ttk.Label(frame, text="Photo:").grid(row=len(fields), column=0, sticky="w", pady=5, padx=5)
        self.photo_label = ttk.Label(frame, text="No Photo", relief="solid", width=15, anchor="center") # Fixed width
        self.photo_label.grid(row=len(fields), column=1, sticky="w", pady=2, padx=5)
        self.photo_label.image = None # Keep a reference to avoid garbage collection

        upload_photo_btn = ttk.Button(frame, text="Upload Photo", command=self._upload_photo)
        upload_photo_btn.grid(row=len(fields) + 1, column=1, sticky="ew", pady=2, padx=5)
        clear_photo_btn = ttk.Button(frame, text="Clear Photo", command=self._clear_photo)
        clear_photo_btn.grid(row=len(fields) + 1, column=0, sticky="w", pady=2, padx=5)


        # --- ID Proof Upload ---
        self.id_proof_path_var = tk.StringVar()
        ttk.Label(frame, text="ID Proof:").grid(row=len(fields) + 2, column=0, sticky="w", pady=5, padx=5) # Adjusted row
        self.id_proof_label = ttk.Label(frame, text="No ID Proof", relief="solid", width=15, anchor="center")
        self.id_proof_label.grid(row=len(fields) + 2, column=1, sticky="w", pady=2, padx=5) # Adjusted row
        self.id_proof_label.image = None # Keep a reference

        upload_id_btn = ttk.Button(frame, text="Upload ID Proof", command=self._upload_id_proof)
        upload_id_btn.grid(row=len(fields) + 3, column=1, sticky="ew", pady=2, padx=5) # Adjusted row
        clear_id_btn = ttk.Button(frame, text="Clear ID Proof", command=self._clear_id_proof)
        clear_id_btn.grid(row=len(fields) + 3, column=0, sticky="w", pady=2, padx=5) # Adjusted row


        # --- Save/Update Button ---
        self.save_update_button = ttk.Button(frame, text="Save Worker", command=self._save_worker, style="Accent.TButton")
        self.save_update_button.grid(row=len(fields) + 4, column=0, columnspan=2, pady=10, padx=5) # Adjusted row

        clear_form_button = ttk.Button(frame, text="Clear Form / Cancel Edit", command=self._clear_form) # Renamed for clarity
        clear_form_button.grid(row=len(fields) + 5, column=0, columnspan=2, pady=5, padx=5) # Adjusted row


    def _upload_photo(self):
        filepath = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if filepath:
            saved_path = image_utils.save_uploaded_file(filepath, WORKER_PHOTOS_DIR, "worker_photo")
            if saved_path:
                self.photo_path_var.set(saved_path)
                img = image_utils.get_image_for_display(saved_path, size=(100, 100))
                if img:
                    self.photo_label.config(image=img, text="")
                    self.photo_label.image = img # Keep reference
                else:
                    self.photo_label.config(image=None, text="Error")
            else:
                messagebox.showerror("Upload Error", "Failed to save photo.")

    def _upload_id_proof(self):
        filepath = filedialog.askopenfilename(
            title="Select ID Proof",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.pdf"), ("All files", "*.*"))
        )
        if filepath:
            # For non-image ID proofs, we might not display them, just store the path
            saved_path = image_utils.save_uploaded_file(filepath, WORKER_ID_PROOFS_DIR, "worker_id")
            if saved_path:
                self.id_proof_path_var.set(saved_path)
                # Check if it's an image to display
                if saved_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    img = image_utils.get_image_for_display(saved_path, size=(100,100))
                    if img:
                        self.id_proof_label.config(image=img, text="")
                        self.id_proof_label.image = img
                    else:
                        self.id_proof_label.config(image=None, text="Preview Error")
                else: # For PDF or other types
                    self.id_proof_label.config(image=None, text=os.path.basename(saved_path))
            else:
                messagebox.showerror("Upload Error", "Failed to save ID proof.")

    def _clear_photo(self):
        self.photo_path_var.set("")
        self.photo_label.config(image=None, text="No Photo")
        self.photo_label.image = None # Clear reference

    def _clear_id_proof(self):
        self.id_proof_path_var.set("")
        self.id_proof_label.config(image=None, text="No ID Proof")
        self.id_proof_label.image = None # Clear reference

    def _clear_form(self, clear_images=True):
        for widget_name, widget in self.form_widgets.items():
            if isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                if isinstance(widget, tk.Text):
                    widget.delete("1.0", tk.END)
                else:
                    widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set('')

        if clear_images:
            self.photo_path_var.set("")
            self.photo_label.config(image=None, text="No Photo")
            self.photo_label.image = None
            self.id_proof_path_var.set("")
            self.id_proof_label.config(image=None, text="No ID Proof")
            self.id_proof_label.image = None

        self.editing_worker_id = None
        self.form_frame.config(text="Add Worker") # Reset form title
        self.save_update_button.config(text="Save Worker") # Reset button text


    def _save_worker(self):
        data = {}
        for name, widget in self.form_widgets.items():
            key_name = name.replace("_entry", "").replace("_text", "").replace("_combo","")
            if isinstance(widget, tk.Text):
                data[key_name] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, ttk.Combobox):
                data[key_name] = widget.get()
            else: # tk.Entry
                data[key_name] = widget.get().strip()

        data['photo_path'] = self.photo_path_var.get()
        data['id_proof_path'] = self.id_proof_path_var.get()

        # Basic Validation (can be expanded)
        # Joining Date: YYYY-MM-DD is expected by convention, no strict format enforcement here yet.
        if not data.get('first_name') or not data.get('role') or not data.get('joining_date'):
            messagebox.showerror("Validation Error", "First Name, Role, and Joining Date are required.")
            return

        try:
            # Ensure salary is float if provided, or None if empty
            salary_str = data.get('salary_amount', '').strip()
            if salary_str:
                data['salary_amount'] = float(salary_str)
            else:
                data['salary_amount'] = None
        except ValueError:
            messagebox.showerror("Validation Error", "Salary amount must be a valid number.")
            return

        if self.editing_worker_id:
            success = worker_db.update_worker(self.editing_worker_id, data)
            if success:
                messagebox.showinfo("Success", "Worker details updated successfully.")
                self._clear_form() # Also resets editing_worker_id and button text
            else:
                messagebox.showerror("Error", "Failed to update worker.")
        else:
            worker_id = worker_db.add_worker(data)
            if worker_id:
                messagebox.showinfo("Success", f"Worker added successfully with ID: {worker_id}")
                self._clear_form()
            else:
                messagebox.showerror("Error", "Failed to add worker.")

        # Refresh list only if an operation was attempted (even if it failed, to reflect any partial state)
        self.refresh_worker_list()

    def _create_worker_list_view(self):
        self.worker_tree = ttk.Treeview(
            self.list_frame,
            columns=("id", "full_name", "role", "contact", "joining_date"),
            show="headings"
        )
        self.worker_tree.heading("id", text="ID")
        self.worker_tree.heading("full_name", text="Full Name")
        self.worker_tree.heading("role", text="Role")
        self.worker_tree.heading("contact", text="Contact")
        self.worker_tree.heading("joining_date", text="Joining Date")

        self.worker_tree.column("id", width=50, anchor="center")
        self.worker_tree.column("full_name", width=150)
        self.worker_tree.column("role", width=100)
        self.worker_tree.column("contact", width=100)
        self.worker_tree.column("joining_date", width=100, anchor="center")

        self.worker_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.worker_tree.bind("<<TreeviewSelect>>", self._on_worker_select)

        # --- Action Buttons for List ---
        action_button_frame = ttk.Frame(self.list_frame)
        action_button_frame.pack(fill="x", pady=5)

        edit_button = ttk.Button(action_button_frame, text="Edit Selected", command=self._edit_selected_worker)
        edit_button.pack(side="left", padx=5)

        delete_button = ttk.Button(action_button_frame, text="Delete Selected", command=self._delete_selected_worker, style="Danger.TButton")
        delete_button.pack(side="left", padx=5)

        # Add a style for Danger.TButton if not present (usually in main app)
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="red")
        style.configure("Accent.TButton", foreground="blue") # Example for save

    def refresh_worker_list(self):
        for item in self.worker_tree.get_children():
            self.worker_tree.delete(item)

        workers = worker_db.get_all_workers()
        for worker in workers:
            full_name = f"{worker.get('first_name', '')} {worker.get('last_name', '')}".strip()
            self.worker_tree.insert("", tk.END, values=(
                worker['id'],
                full_name,
                worker.get('role', ''),
                worker.get('contact_number', ''),
                worker.get('joining_date', '')
            ))

    def _on_worker_select(self, event):
        selected_items = self.worker_tree.selection()
        if selected_items:
            # For now, just print. Edit functionality will load this to form.
            item = self.worker_tree.item(selected_items[0])
            worker_id = item['values'][0]
            print(f"Selected worker ID: {worker_id}")
            # self._load_worker_for_editing(worker_id) # Implement this next

    def _load_worker_for_editing(self, worker_id):
        worker = worker_db.get_worker_by_id(worker_id)
        if not worker:
            messagebox.showerror("Error", "Could not fetch worker details.")
            return

        self._clear_form(clear_images=False) # Clear form but keep current images until new ones are uploaded
        self.editing_worker_id = worker_id
        self.form_frame.config(text=f"Edit Worker (ID: {worker_id})") # Update form title
        self.save_update_button.config(text="Update Worker") # Update button text

        self.form_widgets["first_name_entry"].insert(0, worker.get("first_name", ""))
        self.form_widgets["last_name_entry"].insert(0, worker.get("last_name", ""))
        self.form_widgets["address_text"].insert("1.0", worker.get("address", ""))
        self.form_widgets["contact_number_entry"].insert(0, worker.get("contact_number", ""))
        self.form_widgets["previous_experience_text"].insert("1.0", worker.get("previous_experience", ""))
        self.form_widgets["salary_amount_entry"].insert(0, str(worker.get("salary_amount", "")))
        self.form_widgets["salary_frequency_combo"].set(worker.get("salary_frequency", ""))
        self.form_widgets["role_entry"].insert(0, worker.get("role", ""))
        self.form_widgets["joining_date_entry"].insert(0, worker.get("joining_date", ""))

        # Load photo
        photo_path = worker.get("photo_path")
        self.photo_path_var.set(photo_path or "")
        if photo_path and os.path.exists(photo_path):
            img = image_utils.get_image_for_display(photo_path, size=(100, 100))
            if img:
                self.photo_label.config(image=img, text="")
                self.photo_label.image = img
            else:
                self.photo_label.config(image=None, text="Load Error")
        else:
            self.photo_label.config(image=None, text="No Photo")

        # Load ID proof
        id_proof_path = worker.get("id_proof_path")
        self.id_proof_path_var.set(id_proof_path or "")
        if id_proof_path and os.path.exists(id_proof_path):
            if id_proof_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img = image_utils.get_image_for_display(id_proof_path, size=(100,100))
                if img:
                    self.id_proof_label.config(image=img, text="")
                    self.id_proof_label.image = img
                else:
                    self.id_proof_label.config(image=None, text="Preview Error")
            else:
                self.id_proof_label.config(image=None, text=os.path.basename(id_proof_path))
        else:
            self.id_proof_label.config(image=None, text="No ID Proof")


    def _edit_selected_worker(self):
        selected_items = self.worker_tree.selection()
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select a worker from the list to edit.")
            return
        item = self.worker_tree.item(selected_items[0])
        worker_id = item['values'][0]
        self._load_worker_for_editing(worker_id)

    def _delete_selected_worker(self):
        selected_items = self.worker_tree.selection()
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select a worker from the list to delete.")
            return

        item = self.worker_tree.item(selected_items[0])
        worker_id = item['values'][0]
        worker_name = item['values'][1]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete worker '{worker_name}' (ID: {worker_id})?\n"
            "This action cannot be undone."
        )
        if confirm:
            # Consider deleting files:
            # worker_details = worker_db.get_worker_by_id(worker_id)
            # if worker_details:
            #     if worker_details.get('photo_path') and os.path.exists(worker_details['photo_path']):
            #         try: os.remove(worker_details['photo_path'])
            #         except OSError as e: print(f"Error deleting photo file: {e}")
            #     if worker_details.get('id_proof_path') and os.path.exists(worker_details['id_proof_path']):
            #         try: os.remove(worker_details['id_proof_path'])
            #         except OSError as e: print(f"Error deleting ID proof file: {e}")

            success = worker_db.delete_worker(worker_id)
            if success:
                messagebox.showinfo("Success", f"Worker '{worker_name}' deleted successfully.")
                self.refresh_worker_list()
                self._clear_form() # Clear form if the deleted worker was being edited
            else:
                messagebox.showerror("Error", f"Failed to delete worker '{worker_name}'.")


if __name__ == '__main__':
    # For testing purposes
    # Ensure database is initialized first
    from database_utils import init_db
    init_db()

    root = tk.Tk()
    root.title("Worker Management Test")
    root.geometry("1000x700") # Increased size for better view

    # Add a style for Accent.TButton if it's not globally available in your main app
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="dodgerblue")


    worker_page = WorkerManagementPage(root)
    worker_page.pack(fill="both", expand=True)
    root.mainloop()
