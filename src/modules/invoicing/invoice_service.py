"""
Invoice Service - Core invoice creation and management functionality
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from src.database import DatabaseManager
from src.models.invoice_models import Invoice, LineItem, InvoiceStatus, Customer


class InvoiceService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_invoice_with_accounting(self, customer: Customer, line_items: List[Dict[str, Any]], 
                                     due_days: int = 30, notes: Optional[str] = None) -> int:
        """Create invoice and return invoice ID for accounting integration"""
        # Calculate dates
        issue_date = date.today()
        due_date = issue_date + timedelta(days=due_days)
        
        # Calculate totals
        subtotal = Decimal('0')
        invoice_line_items = []
        
        for item_data in line_items:
            if not all(k in item_data for k in ['description', 'quantity', 'unit_price']):
                raise ValueError("Each line item must have description, quantity, and unit_price")
            
            description = item_data['description']
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data['unit_price']))
            total = quantity * unit_price
            
            subtotal += total
            invoice_line_items.append({
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                'total': total
            })
        
        # Calculate tax (Swedish 25% VAT)
        tax_rate = Decimal('0.25')
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        # Generate invoice number
        invoice_number = self.db.generate_invoice_number()
        
        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=customer.id,
            issue_date=issue_date,
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            tax_rate=tax_rate,
            notes=notes
        )
        
        invoice_id = self.db.create_invoice(invoice)
        
        # Create line items
        for item in invoice_line_items:
            line_item = LineItem(
                invoice_id=invoice_id,
                description=item['description'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total=item['total']
            )
            self.db.create_line_item(line_item)
        
        return invoice_id
    
    def update_invoice_status(self, invoice_id: int, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        return self.db.update_invoice_status(invoice_id, status)