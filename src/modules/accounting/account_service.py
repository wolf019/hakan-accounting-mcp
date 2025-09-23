"""
Account Service - Manages chart of accounts and account balances
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date

from src.database import DatabaseManager
from src.models.accounting_models import Account, AccountType, TrialBalance


class AccountService:
    def __init__(self, db: DatabaseManager):
        self.db = db
        # Note: Accounts should be loaded from database only
        # Use load_complete_chart_of_accounts.py to populate accounts table
    
    def get_account_balance(self, account_number: str, as_of_date: date = None) -> Dict[str, Any]:
        """Get account balance and transaction info"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, account_name, balance FROM accounts WHERE account_number = ?
            """, (account_number,))
            account = cursor.fetchone()
            
            if not account:
                raise ValueError(f"Account {account_number} not found")
            
            # Count transactions
            cursor.execute("""
                SELECT COUNT(*) FROM journal_entries WHERE account_id = ?
            """, (account[0],))
            transaction_count = cursor.fetchone()[0]
            
            # Get last transaction date
            cursor.execute("""
                SELECT MAX(created_at) FROM journal_entries WHERE account_id = ?
            """, (account[0],))
            last_transaction_date = cursor.fetchone()[0]
            
            return {
                "account_number": account_number,
                "account_name": account[1],
                "balance": account[2],
                "transaction_count": transaction_count,
                "last_transaction_date": last_transaction_date
            }
    
    def generate_trial_balance(self, as_of_date: date = None) -> List[TrialBalance]:
        """Generate trial balance showing all account balances"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT account_number, account_name, balance, account_type
                FROM accounts 
                WHERE is_active = TRUE
                ORDER BY account_number
            """)
            
            accounts = cursor.fetchall()
            trial_balance = []
            
            for account in accounts:
                account_number, account_name, balance, account_type = account
                
                # Convert balance to Decimal to avoid float/Decimal type errors
                balance = Decimal(str(balance)) if balance is not None else Decimal("0")
                
                if account_type in ['asset', 'expense']:
                    # Normal debit balance accounts
                    debit_balance = balance if balance > 0 else Decimal("0")
                    credit_balance = abs(balance) if balance < 0 else Decimal("0")
                else:
                    # Normal credit balance accounts
                    credit_balance = balance if balance > 0 else Decimal("0")
                    debit_balance = abs(balance) if balance < 0 else Decimal("0")
                
                trial_balance.append(TrialBalance(
                    account_number=account_number,
                    account_name=account_name,
                    debit_balance=debit_balance,
                    credit_balance=credit_balance
                ))
            
            return trial_balance
    
    def get_account_id(self, account_number: str) -> Optional[int]:
        """Get account ID by account number"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def update_account_balance(self, account_id: int, balance_change: Decimal, account_type: str):
        """Update account balance based on transaction"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate balance change based on account type
            if account_type in ['asset', 'expense']:
                # Assets and expenses increase with debits
                actual_change = balance_change
            else:
                # Liabilities, equity, and income increase with credits
                actual_change = balance_change
            
            cursor.execute("""
                UPDATE accounts SET balance = balance + ? WHERE id = ?
            """, (actual_change, account_id))
            
            conn.commit()