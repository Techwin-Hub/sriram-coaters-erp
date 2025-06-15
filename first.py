import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from typing import Callable
from billing import BillingPreviewWindow

def init_db():
    conn = sqlite3.connect("description.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS description_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT UNIQUE NOT NULL,
            customer_part_no TEXT,
            sac_code TEXT,
            rate REAL,
            po_no TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = sqlite3.connect("description.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM description_master")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO description_master (description, customer_part_no, sac_code, rate, po_no)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Paint Coating", "PC-001", "998873", 100, "fc0001-1/12"),
            ("Powder Coating", "PC-002", "998874", 120, "fc0000-1/12"),
        ])
        conn.commit()
    conn.close()


def get_all_descriptions():
    conn = sqlite3.connect("description.db")
    cur = conn.cursor()
    cur.execute("SELECT description FROM description_master")
    results = [row[0] for row in cur.fetchall()]
    conn.close()
    return results


def get_description_details(desc):
    conn = sqlite3.connect("description.db")
    cur = conn.cursor()
    cur.execute("SELECT customer_part_no, sac_code, rate, po_no FROM description_master WHERE description = ?", (desc,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"customer_part_no": row[0], "sac_code": row[1], "rate": row[2], "po_no": row[3]}
    return {}


def insert_description_to_db(data):
    conn = sqlite3.connect("description.db")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO description_master (description, customer_part_no, sac_code, rate, po_no)
            VALUES (?, ?, ?, ?, ?)
        """, (data["Description"], data["Customer Part No."], data["SAC Code"], float(data["Rate"]), data["PO No"]))
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Description already exists.")
    conn.close()


class AddDescriptionPopup(tk.Toplevel):
    def __init__(self, master, on_submit_callback):
        super().__init__(master)
        self.title("Add Description")
        self.geometry("400x350")
        self.configure(bg="white")
        self.on_submit = on_submit_callback
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Add Description Entry", font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        fields = ["Description", "Customer Part No.", "SAC Code", "Rate", "PO No"]
        self.entries = {}

        for field in fields:
            tk.Label(self, text=field + ":", font=("Arial", 10), bg="white").pack(anchor="w", padx=20, pady=(5, 0))
            entry = tk.Entry(self, width=30, font=("Arial", 10))
            entry.pack(padx=20, pady=5)
            self.entries[field] = entry

        tk.Button(self, text="Save", bg="green", fg="white", command=self.submit).pack(pady=20)

    def submit(self):
        data = {key: entry.get() for key, entry in self.entries.items()}
        try:
            insert_description_to_db(data)
            self.on_submit(data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

class DataEntryPage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Delivery Challan - Data Entry")
        self.geometry("800x700")
        self.configure(bg="#f0f0f0")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Delivery Challan Entry Form", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        form_frame = tk.Frame(self, bg="white", bd=2, relief="solid", padx=20, pady=20)
        form_frame.pack(padx=20, pady=10, fill="x")

        labels = ["DC No", "Date (YYYY-MM-DD)", "PO No", "DC No & Date", "Challan No"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(form_frame, text=label + ":", font=("Arial", 10), anchor="w", bg="white").grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(form_frame, width=30, font=("Arial", 10))
            entry.grid(row=i, column=1, pady=5, padx=5)
            if label == "Date (YYYY-MM-DD)":
                entry.insert(0, str(date.today()))
            self.entries[label] = entry

        # --- Item Frame ---
        item_frame = tk.Frame(self, bg="white", bd=2, relief="solid", padx=20, pady=20)
        item_frame.pack(padx=20, pady=10, fill="x")

        tk.Label(item_frame, text="Description:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w")
        self.description_cb = ttk.Combobox(item_frame, values=get_all_descriptions(), width=30, state="readonly")
        self.description_cb.grid(row=0, column=1, padx=5, pady=5)
        self.description_cb.bind("<<ComboboxSelected>>", self.fill_auto_fields)

        self.part_entry = self._create_field(item_frame, "Customer Part No.", 1)
        self.sac_entry = self._create_field(item_frame, "SAC Code", 2)
        self.rate_entry = self._create_field(item_frame, "Rate", 3)
        self.qty_entry = self._create_field(item_frame, "Qty", 4)
        self.amount_entry = self._create_field(item_frame, "Amount", 5, readonly=True)

        self.qty_entry.bind("<KeyRelease>", self.calculate_amount)
        self.rate_entry.bind("<KeyRelease>", self.calculate_amount)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="➕ Add Description", font=("Arial", 10), command=self.add_description_popup).pack(side="left", padx=10)
        tk.Button(btn_frame, text="🧾 Generate", font=("Arial", 10, "bold"), bg="green", fg="white", command=self.generate_ui).pack(side="left", padx=10)

    def _create_field(self, parent, label, row, readonly=False):
        tk.Label(parent, text=f"{label}:", font=("Arial", 10), bg="white").grid(row=row, column=0, sticky="w")
        entry = tk.Entry(parent, width=30, font=("Arial", 10), state="readonly" if readonly else "normal")
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def fill_auto_fields(self, event=None):
        desc = self.description_cb.get()
        data = get_description_details(desc)
        self.part_entry.delete(0, tk.END)
        self.sac_entry.delete(0, tk.END)
        self.rate_entry.delete(0, tk.END)
        self.entries["PO No"].delete(0, tk.END)  # Clear PO No

        if data:
            self.part_entry.insert(0, data["customer_part_no"])
            self.sac_entry.insert(0, data["sac_code"])
            self.rate_entry.insert(0, str(data["rate"]))
            self.entries["PO No"].insert(0, data["po_no"])  # ✅ use actual DB value

    def calculate_amount(self, event=None):
        try:
            qty = float(self.qty_entry.get())
            rate = float(self.rate_entry.get())
            amount = qty * rate
            self.amount_entry.config(state="normal")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, f"{amount:.2f}")
            self.amount_entry.config(state="readonly")
        except ValueError:
            self.amount_entry.config(state="normal")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, "")
            self.amount_entry.config(state="readonly")

    def add_description_popup(self):
        def on_submit(data):
            messagebox.showinfo("Saved", "New description added.")
            self.description_cb["values"] = get_all_descriptions()

        AddDescriptionPopup(self, on_submit)

    def generate_ui(self):
        form_data = {k: e.get() for k, e in self.entries.items()}
        item_data = {
            "description": self.description_cb.get(),
            "customer_part_no": self.part_entry.get(),
            "sac_code": self.sac_entry.get(),
            "rate": self.rate_entry.get(),
            "qty": self.qty_entry.get(),
            "amount": self.amount_entry.get()
        }

        BillingPreviewWindow(self, form_data, item_data)

# At the bottom
if __name__ == "__main__":
    init_db()
    insert_sample_data()
    app = DataEntryPage()
    app.mainloop()
