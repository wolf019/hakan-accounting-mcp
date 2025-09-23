"""
Expense Service - Expense tracking and management functionality
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from src.database import DatabaseManager
from src.models.expense_models import Expense


class ExpenseService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_expense_with_accounting(self, description: str, amount: Decimal, 
                                     category: str, expense_date: date = None,
                                     vat_rate: Decimal = Decimal("0.25"),
                                     notes: Optional[str] = None) -> int:
        """Create expense and return expense ID for accounting integration"""
        if expense_date is None:
            expense_date = date.today()
        
        # Calculate VAT
        total_amount = amount
        vat_amount = total_amount * vat_rate / (1 + vat_rate)  # VAT included in amount
        net_amount = total_amount - vat_amount
        
        expense = Expense(
            description=description,
            amount=total_amount,
            vat_amount=vat_amount,
            vat_rate=vat_rate,
            category=category,
            expense_date=expense_date,
            notes=notes
        )
        
        expense_id = self.db.create_expense(expense)
        return expense_id