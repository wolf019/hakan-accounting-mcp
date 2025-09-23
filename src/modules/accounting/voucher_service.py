"""
Voucher Service - Manages accounting vouchers and their lifecycle
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from src.database import DatabaseManager
from src.models.accounting_models import VoucherType


class VoucherService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_voucher(self, description: str, voucher_type: VoucherType, 
                      total_amount: Decimal, voucher_date: date = None,
                      source_invoice_id: Optional[int] = None,
                      source_expense_id: Optional[int] = None,
                      source_reminder_id: Optional[int] = None,
                      reference: Optional[str] = None) -> int:
        """Create a new voucher"""
        if voucher_date is None:
            voucher_date = date.today()
        
        # Generate voucher number
        voucher_number = self._generate_voucher_number()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vouchers (voucher_number, voucher_date, description, voucher_type,
                                    total_amount, reference, source_invoice_id, source_expense_id,
                                    source_reminder_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                voucher_number, voucher_date, description, voucher_type.value,
                total_amount, reference, source_invoice_id, source_expense_id,
                source_reminder_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def post_voucher(self, voucher_id: int, account_service, journal_service) -> bool:
        """Post a voucher - updates account balances and marks as posted"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify voucher balances
            cursor.execute("""
                SELECT SUM(debit_amount) as total_debit, SUM(credit_amount) as total_credit
                FROM journal_entries WHERE voucher_id = ?
            """, (voucher_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != result[1]:
                raise ValueError("Voucher is not balanced - total debits must equal total credits")
            
            # Get all journal entries for this voucher
            cursor.execute("""
                SELECT je.account_id, je.debit_amount, je.credit_amount, a.account_type
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                WHERE je.voucher_id = ?
            """, (voucher_id,))
            
            entries = cursor.fetchall()
            
            # Update account balances
            for entry in entries:
                account_id, debit, credit, account_type = entry
                
                # Calculate balance change based on account type
                if account_type in ['asset', 'expense']:
                    # Assets and expenses increase with debits
                    balance_change = debit - credit
                else:
                    # Liabilities, equity, and income increase with credits
                    balance_change = credit - debit
                
                account_service.update_account_balance(account_id, balance_change, account_type)
            
            # Mark voucher as posted
            cursor.execute("""
                UPDATE vouchers SET is_posted = TRUE, posted_at = ? WHERE id = ?
            """, (datetime.now(), voucher_id))
            
            conn.commit()
            return True
    
    def _generate_voucher_number(self) -> str:
        """Generate next voucher number"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vouchers")
            count = cursor.fetchone()[0]
            return f"V{count + 1:03d}"