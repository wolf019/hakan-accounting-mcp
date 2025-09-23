"""
Invoice Database Operations - Focused on invoice and customer data
"""

from typing import List, Optional
from datetime import date
from src.models.invoice_models import Customer, Invoice, LineItem, InvoiceStatus, PaymentReminder
from .base import DatabaseManager


class InvoiceDatabase:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # Customer CRUD operations
    def create_customer(self, customer: Customer) -> int:
        return self.db.create_customer(customer)
    
    def get_customer_by_company_vat(self, company: str, vat_number: str) -> Optional[Customer]:
        return self.db.get_customer_by_company_vat(company, vat_number)
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        return self.db.get_customer_by_email(email)
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.get_customer_by_id(customer_id)
    
    def list_customers(self) -> List[Customer]:
        return self.db.list_customers()
    
    def update_customer(self, customer: Customer) -> bool:
        return self.db.update_customer(customer)
    
    # Invoice CRUD operations
    def create_invoice(self, invoice: Invoice) -> int:
        return self.db.create_invoice(invoice)
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        return self.db.get_invoice_by_id(invoice_id)
    
    def list_invoices(self, status: Optional[str] = None) -> List[Invoice]:
        return self.db.list_invoices(status)
    
    def update_invoice_status(self, invoice_id: int, status: InvoiceStatus) -> bool:
        return self.db.update_invoice_status(invoice_id, status)
    
    def generate_invoice_number(self) -> str:
        return self.db.generate_invoice_number()
    
    # Line item operations
    def create_line_item(self, line_item: LineItem) -> int:
        return self.db.create_line_item(line_item)
    
    def get_line_items_by_invoice(self, invoice_id: int) -> List[LineItem]:
        return self.db.get_line_items_by_invoice(invoice_id)
    
    # Payment reminder operations
    def create_payment_reminder(self, reminder: PaymentReminder) -> int:
        return self.db.create_payment_reminder(reminder)
    
    def get_payment_reminder_by_id(self, reminder_id: int) -> Optional[PaymentReminder]:
        return self.db.get_payment_reminder_by_id(reminder_id)
    
    def get_payment_reminders_by_invoice(self, invoice_id: int) -> List[PaymentReminder]:
        return self.db.get_payment_reminders_by_invoice(invoice_id)
    
    def update_invoice_reminder_info(self, invoice_id: int, reminder_count: int, reminder_date: date) -> bool:
        return self.db.update_invoice_reminder_info(invoice_id, reminder_count, reminder_date)
    
    def update_reminder_pdf_status(self, reminder_id: int, pdf_generated: bool) -> bool:
        return self.db.update_reminder_pdf_status(reminder_id, pdf_generated)
