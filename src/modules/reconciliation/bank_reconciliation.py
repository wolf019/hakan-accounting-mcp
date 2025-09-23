"""
Bank Reconciliation - Match bank transactions with invoices and expenses
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from src.database import DatabaseManager
from src.models.expense_models import BankTransaction, Reconciliation


class BankReconciliationService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def import_bank_transactions(self, transactions_data: List[dict]) -> int:
        """Import bank transactions from external data"""
        imported_count = 0
        
        for transaction_data in transactions_data:
            try:
                transaction = BankTransaction(
                    transaction_date=transaction_data['date'],
                    amount=Decimal(str(transaction_data['amount'])),
                    transaction_type=transaction_data['type'],
                    description=transaction_data.get('description'),
                    reference=transaction_data.get('reference'),
                    counterparty=transaction_data.get('counterparty'),
                    account_balance=Decimal(str(transaction_data.get('balance', 0)))
                )
                
                self.db.create_bank_transaction(transaction)
                imported_count += 1
                
            except Exception as e:
                print(f"Failed to import transaction: {e}")
                continue
        
        return imported_count
    
    def get_unmatched_transactions(self) -> List[BankTransaction]:
        """Get bank transactions that haven't been reconciled"""
        return self.db.get_unreconciled_transactions()
    
    def create_reconciliation(self, bank_transaction_id: int, 
                            reconciled_amount: Decimal,
                            reconciliation_type: str,
                            invoice_id: Optional[int] = None,
                            expense_id: Optional[int] = None,
                            notes: Optional[str] = None) -> int:
        """Create a reconciliation between bank transaction and invoice/expense"""
        
        # Validate that referenced items exist
        if invoice_id:
            invoice = self.db.get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice with ID {invoice_id} not found")
        
        if expense_id:
            expense = self.db.get_expense_by_id(expense_id)
            if not expense:
                raise ValueError(f"Expense with ID {expense_id} not found")
        
        reconciliation = Reconciliation(
            bank_transaction_id=bank_transaction_id,
            reconciled_amount=reconciled_amount,
            reconciliation_type=reconciliation_type,
            invoice_id=invoice_id,
            expense_id=expense_id,
            notes=notes
        )
        
        return self.db.create_reconciliation(reconciliation)