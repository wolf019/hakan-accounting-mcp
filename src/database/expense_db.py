"""
Expense Database Operations - Focused on expense and transaction data
"""

from typing import List, Optional
from datetime import date
from src.models.expense_models import Expense, BankTransaction, Reconciliation
from .base import DatabaseManager


class ExpenseDatabase:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # Expense CRUD operations
    def create_expense(self, expense: Expense) -> int:
        return self.db.create_expense(expense)
    
    def get_expense_by_id(self, expense_id: int) -> Optional[Expense]:
        return self.db.get_expense_by_id(expense_id)
    
    def list_expenses(self, category: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Expense]:
        return self.db.list_expenses(category, start_date, end_date)
    
    def update_expense(self, expense: Expense) -> bool:
        return self.db.update_expense(expense)
    
    def delete_expense(self, expense_id: int) -> bool:
        return self.db.delete_expense(expense_id)
    
    # Bank transaction CRUD operations
    def create_bank_transaction(self, transaction: BankTransaction) -> int:
        return self.db.create_bank_transaction(transaction)
    
    def get_bank_transaction_by_id(self, transaction_id: int) -> Optional[BankTransaction]:
        return self.db.get_bank_transaction_by_id(transaction_id)
    
    def list_bank_transactions(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[BankTransaction]:
        return self.db.list_bank_transactions(start_date, end_date)
    
    def get_unreconciled_transactions(self) -> List[BankTransaction]:
        return self.db.get_unreconciled_transactions()
    
    # Reconciliation CRUD operations
    def create_reconciliation(self, reconciliation: Reconciliation) -> int:
        return self.db.create_reconciliation(reconciliation)
    
    def get_reconciliation_by_id(self, reconciliation_id: int) -> Optional[Reconciliation]:
        return self.db.get_reconciliation_by_id(reconciliation_id)
    
    def list_reconciliations(self) -> List[Reconciliation]:
        return self.db.list_reconciliations()
    
    # VAT reporting operations
    def get_vat_report_data(self, year: int, quarter: int) -> dict:
        return self.db.get_vat_report_data(year, quarter)
