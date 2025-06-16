import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
import os # For checking file existence
import billing_db # Functions to interact with the billing tables in the database

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

class BillingEntryPage(tk.Frame):
    EXCEL_FILE_NAME = "RANE 2025-2026.xlsx"
    EXCEL_SHEET_NAME = "BillingData"

    def __init__(self, master, main_app_title_var=None):
        super().__init__(master)
        self.main_app_title_var = main_app_title_var
        self.configure(bg="white")
        self.line_items_data = []
        self.next_line_no = 1
        self.selected_invoice_no = None
        self.edit_mode = False
        self.editing_invoice_no = None

        # The local page_title_label previously here has been removed.
        # Title is handled by main_app.py via self.main_app_title_var

        header_frame = ttk.LabelFrame(self, text="Invoice Details", padding=(10, 5))
        header_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(header_frame, text="Invoice Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.invoice_no_var = tk.StringVar()
        self.invoice_no_entry = ttk.Entry(header_frame, textvariable=self.invoice_no_var, width=30)
        self.invoice_no_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(header_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(header_frame, textvariable=self.date_var, width=30)
        self.date_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(header_frame, text="Customer Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.customer_name_var = tk.StringVar()
        self.customer_name_entry = ttk.Entry(header_frame, textvariable=self.customer_name_var, width=30)
        self.customer_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(header_frame, text="Payment Method:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.payment_method_var = tk.StringVar()
        self.payment_method_combo = ttk.Combobox(header_frame, textvariable=self.payment_method_var,
                                                 values=["Cash", "Card", "Online Transfer", "Cheque"], width=27)
        self.payment_method_combo.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.payment_method_combo.set("Cash")

        ttk.Label(header_frame, text="GST % (e.g., 18):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.gst_percentage_var = tk.StringVar()
        self.gst_percentage_entry = ttk.Entry(header_frame, textvariable=self.gst_percentage_var, width=30)
        self.gst_percentage_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(3, weight=1)

        line_item_entry_frame = ttk.LabelFrame(self, text="Add Line Item", padding=(10, 5))
        line_item_entry_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(line_item_entry_frame, text="Item Description:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.item_desc_var = tk.StringVar()
        self.item_desc_entry = ttk.Entry(line_item_entry_frame, textvariable=self.item_desc_var, width=40)
        self.item_desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(line_item_entry_frame, text="Part No:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.part_no_var = tk.StringVar()
        self.part_no_entry = ttk.Entry(line_item_entry_frame, textvariable=self.part_no_var, width=20)
        self.part_no_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(line_item_entry_frame, text="HSN Code:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.hsn_code_var = tk.StringVar()
        self.hsn_code_entry = ttk.Entry(line_item_entry_frame, textvariable=self.hsn_code_var, width=40)
        self.hsn_code_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(line_item_entry_frame, text="Quantity:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(line_item_entry_frame, textvariable=self.quantity_var, width=10)
        self.quantity_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.quantity_var.trace_add("write", self.calculate_line_item_amount)

        ttk.Label(line_item_entry_frame, text="Rate:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.rate_var = tk.StringVar()
        self.rate_entry = ttk.Entry(line_item_entry_frame, textvariable=self.rate_var, width=10)
        self.rate_entry.grid(row=1, column=5, padx=5, pady=5, sticky="w")
        self.rate_var.trace_add("write", self.calculate_line_item_amount)

        ttk.Label(line_item_entry_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.line_item_amount_var = tk.StringVar(value="0.00")
        self.line_item_amount_label = ttk.Label(line_item_entry_frame, textvariable=self.line_item_amount_var, width=15, anchor="w")
        self.line_item_amount_label.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        add_item_button = ttk.Button(line_item_entry_frame, text="Add Item to Invoice",
                                     command=self.add_line_item_to_treeview, style="Accent.TButton")
        add_item_button.grid(row=2, column=2, columnspan=4, padx=5, pady=10, sticky="e")

        line_item_entry_frame.columnconfigure(1, weight=1)
        line_item_entry_frame.columnconfigure(3, weight=1)

        line_items_display_frame = ttk.LabelFrame(self, text="Current Invoice Items", padding=(10, 5))
        line_items_display_frame.pack(padx=20, pady=10, fill="both", expand=True)

        columns = ("line_no", "item_desc", "part_no", "hsn_code", "qty", "rate", "amount")
        self.tree = ttk.Treeview(line_items_display_frame, columns=columns, show="headings", height=5)
        self.tree.heading("line_no", text="Line #")
        self.tree.heading("item_desc", text="Item Desc")
        self.tree.heading("part_no", text="Part No")
        self.tree.heading("hsn_code", text="HSN")
        self.tree.heading("qty", text="Qty")
        self.tree.heading("rate", text="Rate")
        self.tree.heading("amount", text="Amount")
        self.tree.column("line_no", width=50, anchor="center", stretch=tk.NO)
        self.tree.column("item_desc", width=250, anchor="w")
        self.tree.column("part_no", width=100, anchor="w", stretch=tk.NO)
        self.tree.column("hsn_code", width=80, anchor="w", stretch=tk.NO)
        self.tree.column("qty", width=70, anchor="e", stretch=tk.NO)
        self.tree.column("rate", width=80, anchor="e", stretch=tk.NO)
        self.tree.column("amount", width=100, anchor="e", stretch=tk.NO)
        tree_scrollbar = ttk.Scrollbar(line_items_display_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        history_frame = ttk.LabelFrame(self, text="Billing History", padding=(10, 5))
        history_frame.pack(padx=20, pady=10, fill="both", expand=True)

        search_controls_frame = ttk.Frame(history_frame)
        search_controls_frame.pack(fill="x", pady=(0,5))
        ttk.Label(search_controls_frame, text="Search by Invoice No:").pack(side="left", padx=(0,5))
        self.search_invoice_no_var = tk.StringVar()
        self.search_invoice_no_entry = ttk.Entry(search_controls_frame, textvariable=self.search_invoice_no_var, width=25)
        self.search_invoice_no_entry.pack(side="left", padx=5)
        search_button = ttk.Button(search_controls_frame, text="Search", command=self._search_invoices)
        search_button.pack(side="left", padx=5)
        clear_search_button = ttk.Button(search_controls_frame, text="Show All", command=self._load_billing_history)
        clear_search_button.pack(side="left", padx=5)

        history_columns = ("invoice_no", "date", "customer_name", "total_amount", "gst_percentage", "payment_method")
        self.history_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=6)
        self.history_tree.heading("invoice_no", text="Invoice No")
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("customer_name", text="Customer Name")
        self.history_tree.heading("total_amount", text="Total Amount")
        self.history_tree.heading("gst_percentage", text="GST %")
        self.history_tree.heading("payment_method", text="Payment Method")
        self.history_tree.column("invoice_no", width=100, anchor="w")
        self.history_tree.column("date", width=80, anchor="center")
        self.history_tree.column("customer_name", width=200, anchor="w")
        self.history_tree.column("total_amount", width=100, anchor="e")
        self.history_tree.column("gst_percentage", width=60, anchor="e")
        self.history_tree.column("payment_method", width=100, anchor="w")
        history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)

        history_actions_frame = ttk.Frame(history_frame)
        history_actions_frame.pack(fill="x", pady=(5,0))
        self.edit_invoice_button = ttk.Button(history_actions_frame, text="Edit Selected", command=self._edit_selected_invoice, state="disabled")
        self.edit_invoice_button.pack(side="left", padx=5)
        self.delete_invoice_button = ttk.Button(history_actions_frame, text="Delete Selected", command=self._delete_selected_invoice, state="disabled")
        self.delete_invoice_button.pack(side="left", padx=5)
        self.export_pdf_button = ttk.Button(history_actions_frame, text="Export to PDF", command=self._export_selected_to_pdf, state="disabled")
        self.export_pdf_button.pack(side="left", padx=5)

        summary_actions_frame = ttk.Frame(self, padding=(10,5))
        summary_actions_frame.pack(padx=20, pady=(0,10), fill="x")
        ttk.Label(summary_actions_frame, text="Total Invoice Amount:").pack(side="left", padx=(0,5))
        self.total_invoice_amount_var = tk.StringVar(value="0.00")
        total_invoice_amount_label = ttk.Label(summary_actions_frame, textvariable=self.total_invoice_amount_var, font=("Arial", 12, "bold"))
        total_invoice_amount_label.pack(side="left")
        self.save_invoice_button = ttk.Button(summary_actions_frame, text="Save Invoice", command=self.save_invoice, style="Accent.TButton")
        self.save_invoice_button.pack(side="right", padx=5)

        self._load_billing_history()

    def _on_history_select(self, event):
        selected_items = self.history_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            self.selected_invoice_no = self.history_tree.item(selected_item, "values")[0]
            self.edit_invoice_button.config(state="normal")
            self.delete_invoice_button.config(state="normal")
            self.export_pdf_button.config(state="normal")
        else:
            self.selected_invoice_no = None
            self.edit_invoice_button.config(state="disabled")
            self.delete_invoice_button.config(state="disabled")
            self.export_pdf_button.config(state="disabled")

    def _edit_selected_invoice(self):
        if not self.selected_invoice_no:
            messagebox.showwarning("No Selection", "Please select an invoice from the history to edit.")
            return

        self.edit_mode = True
        self.editing_invoice_no = self.selected_invoice_no

        header_data = billing_db.get_invoice_header_by_no(self.editing_invoice_no)
        line_items = billing_db.get_line_items_for_invoice(self.editing_invoice_no)

        if not header_data:
            messagebox.showerror("Error", f"Could not retrieve invoice details for {self.editing_invoice_no}.")
            self._clear_form_and_reset()
            return

        self.invoice_no_var.set(header_data.get('invoice_no', ''))
        self.date_var.set(header_data.get('date', ''))
        self.customer_name_var.set(header_data.get('customer_name', ''))
        self.payment_method_var.set(header_data.get('payment_method', 'Cash'))
        self.gst_percentage_var.set(str(header_data.get('gst_percentage', '')))
        self.invoice_no_entry.config(state="readonly")

        self.line_items_data.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.next_line_no = 1
        if line_items:
            for item_db in line_items:
                item_ui = {
                    "line_no": item_db['line_no'], "item_description": item_db['item_description'],
                    "part_no": item_db['part_no'], "hsn_code": item_db['hsn_code'],
                    "quantity": float(item_db['quantity']), "rate": float(item_db['rate']),
                    "amount": float(item_db['amount'])
                }
                self.line_items_data.append(item_ui)
                self.tree.insert("", tk.END, values=(
                    item_ui["line_no"], item_ui["item_description"], item_ui["part_no"],
                    item_ui["hsn_code"], f"{item_ui['quantity']:.2f}",
                    f"{item_ui['rate']:.2f}", f"{item_ui['amount']:.2f}"
                ))
                self.next_line_no = max(self.next_line_no, item_ui["line_no"] + 1)

        self.update_total_invoice_amount()
        self.save_invoice_button.config(text="Update Invoice")
        if self.main_app_title_var:
            self.main_app_title_var.set(f"Edit Invoice: {self.editing_invoice_no}")


    def _delete_selected_invoice(self):
        if not self.selected_invoice_no:
            messagebox.showwarning("No Selection", "Please select an invoice from the history to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete",
                                     f"Are you sure you want to delete invoice {self.selected_invoice_no}?\n"
                                     "This will also delete all associated line items.")
        if confirm:
            if billing_db.delete_invoice_header(self.selected_invoice_no):
                messagebox.showinfo("Success", f"Invoice {self.selected_invoice_no} deleted successfully.")
                self._load_billing_history()
            else:
                messagebox.showerror("Error", f"Failed to delete invoice {self.selected_invoice_no}.")

        self.selected_invoice_no = None
        self.edit_invoice_button.config(state="disabled")
        self.delete_invoice_button.config(state="disabled")
        self.export_pdf_button.config(state="disabled")

    def _export_selected_to_pdf(self):
        if not self.selected_invoice_no:
            messagebox.showwarning("No Selection", "Please select an invoice from the history to export.")
            return

        header_data = billing_db.get_invoice_header_by_no(self.selected_invoice_no)
        line_items_data = billing_db.get_line_items_for_invoice(self.selected_invoice_no)

        if not header_data:
            messagebox.showerror("Error", f"Could not retrieve data for invoice {self.selected_invoice_no}.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF documents", "*.pdf")],
            initialfile=f"Invoice_{self.selected_invoice_no}.pdf",
            title="Save Invoice PDF"
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter,
                                    rightMargin=0.5*inch, leftMargin=0.5*inch,
                                    topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("INVOICE", styles['h1']))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("SRIRAM COATERS", styles['h3']))
            story.append(Paragraph("Ambal Nagar Boothakudi Village, Viralimalai", styles['Normal']))
            story.append(Paragraph("GSTIN: 33ALQPK2156A1ZG | Cell: 9443410161", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            story.append(Paragraph(f"<b>Invoice No:</b> {header_data['invoice_no']}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {header_data['date']}", styles['Normal']))
            story.append(Paragraph(f"<b>Customer:</b> {header_data['customer_name']}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            table_data = [["#", "Item Description", "Part No", "HSN", "Qty", "Rate", "Amount"]]
            for item in line_items_data:
                table_data.append([
                    item['line_no'], Paragraph(item['item_description'], styles['Normal']),
                    item['part_no'], item['hsn_code'],
                    f"{item['quantity']:.2f}", f"{item['rate']:.2f}", f"{item['amount']:.2f}"
                ])

            col_widths = [0.4*inch, 3*inch, 1*inch, 0.8*inch, 0.7*inch, 0.8*inch, 1*inch]
            line_items_table = Table(table_data, colWidths=col_widths)

            table_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND',(0,1),(-1,-1),colors.HexColor("#DCE6F1")),
                ('TEXTCOLOR',(0,1),(-1,-1),colors.black),
                ('FONTNAME', (0,1),(-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,1),(-1,-1), 9),
                ('GRID',(0,0),(-1,-1),1,colors.black),
                ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
            ])
            line_items_table.setStyle(table_style)
            story.append(line_items_table)
            story.append(Spacer(1, 0.2*inch))

            total_amount = float(header_data.get('total_amount', 0))
            gst_percentage = float(header_data.get('gst_percentage', 0))
            gst_amount = (total_amount * gst_percentage) / 100 if gst_percentage else 0.0
            grand_total = total_amount + gst_amount

            totals_data = [
                [Paragraph("Subtotal:", styles['Normal']), Paragraph(f"{total_amount:.2f}", styles['Normal'])],
                [Paragraph(f"GST ({gst_percentage:.2f}%):", styles['Normal']), Paragraph(f"{gst_amount:.2f}", styles['Normal'])],
                [Paragraph("<b>Grand Total:</b>", styles['h3']), Paragraph(f"<b>{grand_total:.2f}</b>", styles['h3'])],
            ]
            totals_table = Table(totals_data, colWidths=[5.7*inch, 1*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,-1), 'RIGHT'), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(totals_table)
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(f"<b>Payment Method:</b> {header_data.get('payment_method', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 0.4*inch))
            story.append(Paragraph("Thank you for your business!", styles['Italic']))

            doc.build(story)
            messagebox.showinfo("Success", f"PDF saved to {file_path}")
        except Exception as e:
            messagebox.showerror("PDF Export Error", f"Failed to generate PDF: {e}")

    def add_line_item_to_treeview(self):
        item_desc = self.item_desc_var.get()
        quantity_str = self.quantity_var.get()
        rate_str = self.rate_var.get()

        if not item_desc or not quantity_str or not rate_str:
            messagebox.showwarning("Missing Information", "Item Description, Quantity, and Rate are required to add an item.")
            return

        try:
            qty = float(quantity_str)
            rate = float(rate_str)
            if qty <= 0 or rate < 0:
                 messagebox.showwarning("Invalid Value", "Quantity must be positive and Rate must be non-negative.")
                 return
        except ValueError:
            messagebox.showerror("Invalid Input", "Quantity and Rate must be valid numbers.")
            return

        current_line_no = self.next_line_no

        item_data = {
            "line_no": current_line_no, "item_description": item_desc,
            "part_no": self.part_no_var.get(), "hsn_code": self.hsn_code_var.get(),
            "quantity": qty, "rate": rate, "amount": qty * rate
        }
        self.line_items_data.append(item_data)
        self.tree.insert("", tk.END, values=(
            item_data["line_no"], item_data["item_description"], item_data["part_no"],
            item_data["hsn_code"], f"{item_data['quantity']:.2f}",
            f"{item_data['rate']:.2f}", f"{item_data['amount']:.2f}"
        ))
        self.next_line_no += 1
        self.update_total_invoice_amount()

        self.item_desc_var.set("")
        self.part_no_var.set("")
        self.hsn_code_var.set("")
        self.quantity_var.set("")
        self.rate_var.set("")
        self.line_item_amount_var.set("0.00")
        self.item_desc_entry.focus()

    def calculate_line_item_amount(self, *args):
        try:
            qty = float(self.quantity_var.get() or 0)
            rate = float(self.rate_var.get() or 0)
            amount = qty * rate
            self.line_item_amount_var.set(f"{amount:.2f}")
        except ValueError:
            pass

    def update_total_invoice_amount(self):
        total = sum(item['amount'] for item in self.line_items_data)
        self.total_invoice_amount_var.set(f"{total:.2f}")

    def _save_line_items_to_excel(self, invoice_no, line_items):
        try:
            if os.path.exists(self.EXCEL_FILE_NAME):
                workbook = openpyxl.load_workbook(self.EXCEL_FILE_NAME)
                if self.EXCEL_SHEET_NAME in workbook.sheetnames:
                    sheet = workbook[self.EXCEL_SHEET_NAME]
                else:
                    sheet = workbook.create_sheet(title=self.EXCEL_SHEET_NAME)
                    headers = ["Invoice No", "Line No", "Item Description", "Part No", "HSN Code", "Quantity", "Rate", "Amount"]
                    sheet.append(headers)
            else:
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = self.EXCEL_SHEET_NAME
                headers = ["Invoice No", "Line No", "Item Description", "Part No", "HSN Code", "Quantity", "Rate", "Amount"]
                sheet.append(headers)

            for item in line_items:
                row_data = [
                    invoice_no, item['line_no'], item['item_description'], item['part_no'],
                    item['hsn_code'], item['quantity'], item['rate'], item['amount']
                ]
                sheet.append(row_data)

            workbook.save(self.EXCEL_FILE_NAME)
            return True
        except InvalidFileException:
            messagebox.showerror("Excel Error", f"File '{self.EXCEL_FILE_NAME}' is corrupted or not a valid Excel file. Please check or delete the file and try again.")
            return False
        except Exception as e:
            messagebox.showerror("Excel Error", f"Failed to save line items to Excel: {e}")
            return False

    def save_invoice(self):
        if self.edit_mode:
            self._update_invoice_logic()
        else:
            self._create_new_invoice_logic()

    def _create_new_invoice_logic(self):
        invoice_no = self.invoice_no_var.get().strip()
        invoice_date = self.date_var.get().strip()
        customer_name = self.customer_name_var.get().strip()
        payment_method = self.payment_method_var.get()
        gst_percentage_str = self.gst_percentage_var.get().strip()

        if not invoice_no or not invoice_date or not customer_name:
            messagebox.showerror("Validation Error", "Invoice Number, Date, and Customer Name are required.")
            return
        if not self.line_items_data:
            messagebox.showerror("Validation Error", "Cannot save an empty invoice. Please add line items.")
            return
        try:
            gst_percentage = float(gst_percentage_str) if gst_percentage_str else 0.0
        except ValueError:
            messagebox.showerror("Validation Error", "GST % must be a valid number.")
            return

        total_invoice_amount = sum(item['amount'] for item in self.line_items_data)
        header_data = {
            'invoice_no': invoice_no, 'date': invoice_date, 'customer_name': customer_name,
            'total_amount': total_invoice_amount, 'gst_percentage': gst_percentage,
            'payment_method': payment_method
        }

        if not billing_db.add_invoice_header(header_data):
            messagebox.showerror("Database Error", f"Failed to save invoice header for {invoice_no}. It might already exist.")
            return

        line_items_for_db = [{'invoice_no': invoice_no, **item} for item in self.line_items_data]
        if not billing_db.add_invoice_line_items_batch(line_items_for_db):
            messagebox.showerror("Database Error", f"Failed to save line items for {invoice_no}.")
            billing_db.delete_invoice_header(invoice_no)
            return

        excel_save_success = self._save_line_items_to_excel(invoice_no, self.line_items_data)
        if excel_save_success:
            messagebox.showinfo("Success", f"Invoice {invoice_no} saved successfully to database and Excel!")
        else:
            messagebox.showwarning("Partial Success", f"Invoice {invoice_no} saved to database, but FAILED to save to Excel.")

        self._clear_form_and_reset()
        self._load_billing_history()

    def _update_invoice_logic(self):
        if not self.editing_invoice_no:
            messagebox.showerror("Error", "No invoice selected for update.")
            return

        invoice_date = self.date_var.get().strip()
        customer_name = self.customer_name_var.get().strip()
        payment_method = self.payment_method_var.get()
        gst_percentage_str = self.gst_percentage_var.get().strip()

        if not invoice_date or not customer_name:
            messagebox.showerror("Validation Error", "Date and Customer Name are required.")
            return
        if not self.line_items_data:
            messagebox.showerror("Validation Error", "Invoice must have at least one line item.")
            return
        try:
            gst_percentage = float(gst_percentage_str) if gst_percentage_str else 0.0
        except ValueError:
            messagebox.showerror("Validation Error", "GST % must be a valid number.")
            return

        total_invoice_amount = sum(item['amount'] for item in self.line_items_data)
        updated_header_data = {
            'date': invoice_date, 'customer_name': customer_name,
            'total_amount': total_invoice_amount, 'gst_percentage': gst_percentage,
            'payment_method': payment_method
        }

        if not billing_db.update_invoice_header(self.editing_invoice_no, updated_header_data):
            messagebox.showerror("Database Error", f"Failed to update invoice header for {self.editing_invoice_no}.")
            return

        if not billing_db.delete_line_items_for_invoice(self.editing_invoice_no):
            messagebox.showerror("Database Error", f"Failed to delete old line items for {self.editing_invoice_no}. Update aborted.")
            return

        line_items_for_db = [{'invoice_no': self.editing_invoice_no, **item} for item in self.line_items_data]
        if not billing_db.add_invoice_line_items_batch(line_items_for_db):
            messagebox.showerror("Database Error", f"Failed to save updated line items for {self.editing_invoice_no}.")
            return

        messagebox.showinfo("Invoice Updated",
                            f"Invoice {self.editing_invoice_no} updated in database. "
                            "Excel file was NOT updated with these changes.")

        self._clear_form_and_reset()
        self._load_billing_history()

    def _clear_form_and_reset(self):
        self.invoice_no_var.set("")
        self.date_var.set("")
        self.customer_name_var.set("")
        self.payment_method_combo.set("Cash")
        self.gst_percentage_var.set("")

        self.line_items_data.clear()
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.next_line_no = 1

        self.item_desc_var.set("")
        self.part_no_var.set("")
        self.hsn_code_var.set("")
        self.quantity_var.set("")
        self.rate_var.set("")
        self.line_item_amount_var.set("0.00")
        self.total_invoice_amount_var.set("0.00")

        self.edit_mode = False
        self.editing_invoice_no = None
        self.invoice_no_entry.config(state="normal")
        self.save_invoice_button.config(text="Save Invoice")

        if self.main_app_title_var:
            self.main_app_title_var.set("Billing Management")

        self.invoice_no_entry.focus()

    def _load_billing_history(self, headers_to_load=None):
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)

        self.selected_invoice_no = None
        self.edit_invoice_button.config(state="disabled")
        self.delete_invoice_button.config(state="disabled")
        self.export_pdf_button.config(state="disabled")


        if headers_to_load is None:
            invoice_headers = billing_db.get_all_invoice_headers()
        else:
            invoice_headers = headers_to_load

        if invoice_headers:
            for header in invoice_headers:
                self.history_tree.insert("", tk.END, values=(
                    header['invoice_no'], header['date'], header['customer_name'],
                    f"{header['total_amount']:.2f}", f"{header['gst_percentage']:.2f}", header['payment_method']
                ))
        else:
            if headers_to_load is not None:
                 print("No matching billing history found for the criteria.")
            else:
                 print("No billing history found or an error occurred during initial load.")

    def _search_invoices(self):
        search_term = self.search_invoice_no_var.get().strip()
        if not search_term:
            self._load_billing_history()
            return

        results = billing_db.get_all_invoice_headers(invoice_no_filter=search_term)
        if not results:
            messagebox.showinfo("Search Result", f"No invoices found matching '{search_term}'.")
        self._load_billing_history(headers_to_load=results)


# --- Existing BillingPreviewWindow Class (remains unchanged) ---
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
        preview_canvas = tk.Canvas(self, bg="#eeeeee")
        preview_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=preview_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        preview_canvas.configure(yscrollcommand=scrollbar.set)

        content_frame = tk.Frame(preview_canvas, bg="white")
        preview_canvas.create_window((0,0), window=content_frame, anchor="nw")

        content_frame.bind("<Configure>", lambda e: preview_canvas.configure(scrollregion=preview_canvas.bbox("all")))

        outer_big = tk.Frame(content_frame, bd=2, relief="solid", padx=10, pady=10, bg="white")
        outer_big.pack(padx=10, pady=10)

        outer = tk.Frame(outer_big, bd=2, relief="solid", padx=10, pady=10, bg="white")
        outer.pack(padx=5, pady=5)

        header_frame = tk.Frame(outer, bg="white")
        header_frame.pack(fill='x')
        tk.Label(header_frame, text="GSTIN : 33ALQPK2156A1ZG", font=("Arial", 10, "bold"), bg="white").pack(side="left")
        tk.Label(header_frame, text="Cell : 9443410161", font=("Arial", 10, "bold"), bg="white").pack(side="right")
        tk.Label(outer, text="Customer ID : 17124", font=("Arial", 9), bg="white").pack(anchor='w')

        outer_challan_frame = tk.Frame(outer, bg="white")
        outer_challan_frame.pack(pady=(10, 0))
        outer_box = tk.Frame(outer_challan_frame, bd=2, relief="solid", bg="white", padx=5, pady=5)
        outer_box.pack()
        inner_box = tk.Frame(outer_box, bd=1, relief="solid", bg="white", padx=10, pady=2)
        inner_box.pack()
        tk.Label(inner_box, text="DELIVERY CHALLAN", font=("Arial", 10, "bold"), bg="white").pack()

        tk.Label(outer, text="SRIRAM       COATERS", font=("Arial", 18, "bold"), bg="white").pack(pady=(10, 0))
        tk.Label(outer, text="Ambal Nagar Boothakudi Village, Viralimalai", font=("Arial", 10), bg="white").pack(pady=(0, 10))

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

        doc_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        doc_frame.pack(fill="x", pady=(5, 0))
        for label_text, value_key in [
            ("Po.No. :", "PO No"), ("DC.No. & Date", "DC No & Date"), ("CHALLAN No.", "Challan No")
        ]:
            f = tk.Frame(doc_frame, width=200, height=80, bd=1, relief="solid", bg="white")
            f.pack(side="left", expand=True, fill="both", ipady=10)
            tk.Label(f, text=label_text, font=("Arial", 10), bg="white").pack(anchor="n", pady=2)
            tk.Label(f, text=self.form_data.get(value_key, ""), font=("Arial", 10), bg="white").pack(anchor="center")

        table_frame = tk.Frame(outer, bd=1, relief="solid", bg="white")
        table_frame.pack(fill="x", pady=(10, 0))
        headers = ["Sl. No.", "SAC Code", "Customer Part No.", "Description", "Qty", "Rate", "Amount"]

        for col_index, header in enumerate(headers):
            cell = tk.Frame(table_frame, bd=1, relief="solid", bg="white", height=30)
            cell.grid(row=0, column=col_index, sticky="nsew")
            tk.Label(cell, text=header, font=("Arial", 9, "bold"), bg="white").pack(expand=True, fill="both")

        items_to_display = []
        if isinstance(self.item_data, list):
            for i, item in enumerate(self.item_data):
                 items_to_display.append([
                    str(i + 1), item.get("sac_code", ""), item.get("customer_part_no", ""),
                    item.get("description", ""), str(item.get("qty", "")),
                    str(item.get("rate", "")), str(item.get("amount", ""))
                 ])
        elif isinstance(self.item_data, dict):
            items_to_display.append([
                "1", self.item_data.get("sac_code", ""), self.item_data.get("customer_part_no", ""),
                self.item_data.get("description", ""), str(self.item_data.get("qty", "")),
                str(self.item_data.get("rate", "")), str(self.item_data.get("amount", ""))
            ])

        total_rows_to_display = max(8, len(items_to_display))

        for row_idx in range(total_rows_to_display):
            row_data = items_to_display[row_idx] if row_idx < len(items_to_display) else [""] * len(headers)
            for col_idx, val in enumerate(row_data):
                cell = tk.Frame(table_frame, bd=1, relief="solid", bg="white", height=40 if row_idx < len(items_to_display) else 30)
                cell.grid(row=row_idx + 1, column=col_idx, sticky="nsew")
                tk.Label(cell, text=val, bg="white", font=("Arial", 9)).pack(expand=True, fill="both", padx=2, pady=2)

        for col_index in range(len(headers)):
            table_frame.grid_columnconfigure(col_index, weight=1)

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
        for label_text in ["Signature of Receiver", "Labour Charges Only", "Signature"]:
            l = tk.Label(sign_frame, text=label_text, font=("Arial", 9), bg="white")
            l.pack(side="left", expand=True)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Billing Entry Test")
    root.geometry("800x750")
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="dodgerblue")
    billing_page = BillingEntryPage(root)
    billing_page.pack(fill="both", expand=True)

    root.mainloop()

[end of billing.py]
