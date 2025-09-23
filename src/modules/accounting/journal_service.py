"""
Journal Service - Manages journal entries for double-entry bookkeeping
"""

from decimal import Decimal
from typing import Optional

from src.database import DatabaseManager
from src.models.accounting_models import validate_amount, ValidationError


class JournalService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def add_journal_entry(self, voucher_id: int, account_id: int, 
                         description: str, debit_amount: Decimal = Decimal("0"),
                         credit_amount: Decimal = Decimal("0"),
                         reference: Optional[str] = None) -> int:
        """Add a journal entry to a voucher"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (voucher_id, account_id, description,
                                           debit_amount, credit_amount, reference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (voucher_id, account_id, description, debit_amount, credit_amount, reference))
            conn.commit()
            return cursor.lastrowid
    
    def add_journal_entry_by_account_number(self, voucher_id: int, account_number: str, 
                                           description: str, debit_amount: Decimal = Decimal("0"),
                                           credit_amount: Decimal = Decimal("0"),
                                           reference: Optional[str] = None) -> int:
        """Add a journal entry using account number"""
        # Validate amounts for tax accounts
        if debit_amount > 0:
            validate_amount(account_number, float(debit_amount))
        if credit_amount > 0:
            validate_amount(account_number, float(credit_amount))
        
        # Get account ID
        account_id = self._get_account_id(account_number)
        if not account_id:
            raise ValueError(f"Account {account_number} not found")
        
        return self.add_journal_entry(voucher_id, account_id, description, 
                                    debit_amount, credit_amount, reference)
    
    def _get_account_id(self, account_number: str) -> Optional[int]:
        """Get account ID by account number"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
            result = cursor.fetchone()
            return result[0] if result else None