import tkinter as tk

class BillingPreviewWindow(tk.Toplevel):
    def __init__(self, master, form_data, item_data):
        super().__init__(master)
        self.title("Challan Preview")
        self.geometry("1000x1000")
        self.configure(bg="#eeeeee")

        self.form_data = form_data
        self.item_data = item_data

        self.create_widgets()

    def create_widgets(self):
        outer_big = tk.Frame(self, bd=2, relief="solid", padx=10, pady=10, bg="white")
        outer_big.place(x=90, y=10, width=770, height=770)
        outer = tk.Frame(self, bd=2, relief="solid", padx=10, pady=10, bg="white")
        outer.place(x=100, y=20, width=750, height=750)

        # Header
        header_frame = tk.Frame(outer, bg="white")
        header_frame.pack(fill='x')
        tk.Label(header_frame, text="GSTIN : 33ALQPK2156A1ZG", font=("Arial", 10, "bold"), bg="white").pack(side="left")
        tk.Label(header_frame, text="Cell : 9443410161", font=("Arial", 10, "bold"), bg="white").pack(side="right")
        tk.Label(outer, text="Customer ID : 17124", font=("Arial", 9), bg="white").pack(anchor='w')

        # Delivery Challan Box
        outer_challan_frame = tk.Frame(outer, bg="white")
        outer_challan_frame.pack(pady=(10, 0))
        outer_box = tk.Frame(outer_challan_frame, bd=2, relief="solid", bg="white", padx=5, pady=5)
        outer_box.pack()
        inner_box = tk.Frame(outer_box, bd=1, relief="solid", bg="white", padx=10, pady=2)
        inner_box.pack()
        tk.Label(inner_box, text="DELIVERY CHALLAN", font=("Arial", 10, "bold"), bg="white").pack()

        # Company info
        tk.Label(outer, text="SRIRAM       COATERS", font=("Arial", 18, "bold"), bg="white").pack(pady=(10, 0))
        tk.Label(outer, text="Ambal Nagar Boothakudi Village, Viralimalai", font=("Arial", 10), bg="white").pack(pady=(0, 10))

        # TO block
        block_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        block_frame.pack(fill="x", pady=5)
        left = tk.Frame(block_frame, bg="white")
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=5)
        tk.Label(left, text="TO,", font=("Arial", 8), bg="white").pack(anchor="w")
        tk.Label(left, text="M/s, ZF RANE AUTOMOTIVE INDIA PVT . LTD.,", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        tk.Label(left, text="Boothakudi Village, Viralimalai - 621316", font=("Arial", 9), bg="white").pack(anchor="w")
        tk.Label(left, text="Pudukkottai District - 62316", font=("Arial", 9), bg="white").pack(anchor="w")
        tk.Label(left, text="GSTIN : 33AAACR3147C1ZY", font=("Arial", 8, "bold"), bg="white").pack(anchor="w")

        separator = tk.Frame(block_frame, bg="black", width=1)
        separator.pack(side="left", fill="y")

        right = tk.Frame(block_frame, bg="white")
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=5)
        tk.Label(right, text=f"DC.No.  : {self.form_data.get('DC No', '')}", font=("Arial", 12), bg="white").pack(anchor="w", padx=(15, 0))
        tk.Label(right, text=f"Date      : {self.form_data.get('Date (YYYY-MM-DD)', '')}", font=("Arial", 12), bg="white").pack(anchor="w", padx=(15, 0))

        # PO/DC/Challan No row
        doc_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        doc_frame.pack(fill="x", pady=(5, 0))
        for label_text, value in [
            ("Po.No. :", self.form_data.get("PO No", "")),
            ("DC.No. & Date", self.form_data.get("DC No & Date", "")),
            ("CHALLAN No.", self.form_data.get("Challan No", ""))
        ]:
            f = tk.Frame(doc_frame, width=200, height=80, bd=1, relief="solid", bg="white")
            f.pack(side="left", expand=True, fill="both", ipady=10)
            tk.Label(f, text=label_text, font=("Arial", 10), bg="white").pack(anchor="n", pady=2)
            tk.Label(f, text=value, font=("Arial", 10), bg="white").pack(anchor="center")

        # Table
        table_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        table_frame.pack(fill="x", pady=(10, 0))
        headers = ["Sl. No.", "SAC Code", "Customer Part No.", "Description", "Qty", "Rate", "Amount"]
        values = [
            "1",
            self.item_data.get("sac_code", ""),
            self.item_data.get("customer_part_no", ""),
            self.item_data.get("description", ""),
            self.item_data.get("qty", ""),
            self.item_data.get("rate", ""),
            self.item_data.get("amount", "")
        ]

        # Header Row
        for col_index, header in enumerate(headers):
            cell = tk.Frame(table_frame, bd=1, relief="solid", bg="white", height=30)
            cell.grid(row=0, column=col_index, sticky="nsew")
            tk.Label(cell, text=header, font=("Arial", 9), bg="white").pack(expand=True, fill="both")

        # Total 8 rows
        total_rows = 8

        # First row: with actual item data
        data_rows = [values] + [["" for _ in headers] for _ in range(total_rows - 1)]

        for row_index, row_data in enumerate(data_rows, start=1):
            for col_index, val in enumerate(row_data):
                cell = tk.Frame(table_frame, bd=1, relief="solid", bg="white", height=40)
                cell.grid(row=row_index, column=col_index, sticky="nsew")
                tk.Label(cell, text=val, bg="white").pack(expand=True, fill="both")

        # Make all columns expand evenly
        for col_index in range(len(headers)):
            table_frame.grid_columnconfigure(col_index, weight=1)

        # Declaration
        declaration_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        declaration_frame.pack(fill="x", pady=10)
        tk.Label(declaration_frame, text="Recieved the above Material in good condition",
                 font=("Arial", 10, "bold"), bg="white").pack(pady=(5, 2))

        bottom = tk.Frame(declaration_frame, bg="white")
        bottom.pack(fill="x", padx=10)
        left_txt = "We Hearby Declare that the above mentioned goods are returned\nafter processing and no material transactions are invloved."
        tk.Label(bottom, text=left_txt, font=("Arial", 8), bg="white", justify="left").pack(side="left", anchor="w")
        tk.Label(bottom, text="For SRIRAM COATERS", font=("Arial", 9, "bold"), bg="white").pack(side="right", anchor="e", pady=(5, 0))

        sign_frame = tk.Frame(declaration_frame, bg="white")
        sign_frame.pack(fill="x", pady=10)
        for label in ["Signature of Receiver", "Labour Charges Only", "Signature"]:
            l = tk.Label(sign_frame, text=label, font=("Arial", 9), bg="white")
            l.pack(side="left", expand=True)
