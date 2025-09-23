"""
Accounting Database Operations - Focused on chart of accounts, vouchers, journal entries
"""

from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal
from .base import DatabaseManager


class AccountingDatabase:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_connection(self):
        """Get database connection for accounting operations"""
        return self.db.get_connection()
    
    def create_account(self, account_number: str, account_name: str, account_type: str, 
                     account_category: str, parent_account: Optional[str] = None,
                     requires_vat: bool = False) -> int:
        """Create a new chart of accounts entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (
                    account_number, account_name, account_type, account_category,
                    parent_account, requires_vat
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (account_number, account_name, account_type, account_category, 
                  parent_account, requires_vat))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid
    
    def get_account_by_number(self, account_number: str) -> Optional[Dict[str, Any]]:
        """Get account by account number"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_number = ?", (account_number,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_accounts(self, account_type: Optional[str] = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """List accounts with optional filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM accounts WHERE is_active = ?"
            params = [is_active]
            
            if account_type:
                query += " AND account_type = ?"
                params.append(account_type)
            
            query += " ORDER BY account_number"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_account_balance(self, account_number: str, new_balance: Decimal) -> bool:
        """Update account balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE accounts 
                SET balance = ?
                WHERE account_number = ?
            """, (float(new_balance), account_number))
            conn.commit()
            return cursor.rowcount > 0
    
    def create_voucher(self, voucher_number: str, voucher_date: date, description: str,
                      voucher_type: str, total_amount: Decimal, reference: Optional[str] = None,
                      source_invoice_id: Optional[int] = None, source_expense_id: Optional[int] = None,
                      source_reminder_id: Optional[int] = None) -> int:
        """Create a new voucher"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vouchers (
                    voucher_number, voucher_date, description, voucher_type,
                    total_amount, reference, source_invoice_id, source_expense_id, source_reminder_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (voucher_number, voucher_date, description, voucher_type,
                  float(total_amount), reference, source_invoice_id, source_expense_id, source_reminder_id))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid
    
    def get_voucher_by_id(self, voucher_id: int) -> Optional[Dict[str, Any]]:
        """Get voucher by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vouchers WHERE id = ?", (voucher_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_vouchers(self, voucher_type: Optional[str] = None, start_date: Optional[date] = None, 
                     end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """List vouchers with optional filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM vouchers WHERE 1=1"
            params = []
            
            if voucher_type:
                query += " AND voucher_type = ?"
                params.append(voucher_type)
            
            if start_date:
                query += " AND voucher_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND voucher_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY voucher_date DESC, voucher_number"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def list_vouchers_enhanced(self, start_date: Optional[date] = None, 
                               end_date: Optional[date] = None,
                               include_superseded: bool = False,
                               voucher_type: Optional[str] = None,
                               status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Enhanced voucher listing with status filtering and summary information
        
        Args:
            start_date: Start of period (inclusive)
            end_date: End of period (inclusive)
            include_superseded: Whether to include superseded vouchers
            voucher_type: Optional filter for voucher type
            status_filter: Optional list of statuses to include
        
        Returns:
            List of voucher summaries with key information for period review
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with all necessary fields for period analysis
            query = """
                SELECT 
                    v.id,
                    v.voucher_number,
                    v.voucher_date,
                    v.description,
                    v.voucher_type,
                    v.total_amount,
                    v.status,
                    v.is_posted,
                    v.posted_at,
                    v.reference,
                    v.source_invoice_id,
                    v.source_expense_id,
                    v.source_reminder_id,
                    v.superseded_by,
                    v.created_at,
                    COUNT(je.id) as journal_entries_count,
                    SUM(je.debit_amount) as total_debits,
                    SUM(je.credit_amount) as total_credits
                FROM vouchers v
                LEFT JOIN journal_entries je ON v.id = je.voucher_id
                WHERE 1=1
            """
            params = []
            
            # Apply filters
            if not include_superseded:
                query += " AND (v.status != 'SUPERSEDED' OR v.status IS NULL)"
            
            if status_filter:
                placeholders = ','.join(['?' for _ in status_filter])
                query += f" AND v.status IN ({placeholders})"
                params.extend(status_filter)
            
            if voucher_type:
                query += " AND v.voucher_type = ?"
                params.append(voucher_type)
            
            if start_date:
                query += " AND v.voucher_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND v.voucher_date <= ?"
                params.append(end_date)
            
            # Group by voucher and order by date
            query += """
                GROUP BY v.id
                ORDER BY v.voucher_date DESC, v.voucher_number DESC
            """
            
            cursor.execute(query, params)
            
            # Process results to include balance check
            vouchers = []
            for row in cursor.fetchall():
                voucher = dict(row)
                
                # Add balance check
                total_debits = voucher.get('total_debits', 0) or 0
                total_credits = voucher.get('total_credits', 0) or 0
                voucher['is_balanced'] = abs(total_debits - total_credits) < 0.01
                
                # Add posting status description
                if voucher.get('is_posted'):
                    voucher['posting_status'] = 'Posted'
                elif voucher.get('status') == 'SUPERSEDED':
                    voucher['posting_status'] = 'Superseded'
                elif voucher.get('status') == 'VOIDED':
                    voucher['posting_status'] = 'Voided'
                else:
                    voucher['posting_status'] = 'Pending'
                
                vouchers.append(voucher)
            
            return vouchers
    
    def create_journal_entry(self, voucher_id: int, account_number: str, description: str,
                           debit_amount: Decimal = Decimal('0'), credit_amount: Decimal = Decimal('0'),
                           reference: Optional[str] = None) -> int:
        """Create a journal entry for a voucher"""
        # Get account ID from account number
        account = self.get_account_by_number(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (
                    voucher_id, account_id, description, debit_amount, credit_amount, reference
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (voucher_id, account['id'], description, float(debit_amount), 
                  float(credit_amount), reference))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid
    
    def get_journal_entries_by_voucher(self, voucher_id: int) -> List[Dict[str, Any]]:
        """Get all journal entries for a voucher"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT je.*, a.account_number, a.account_name, a.account_type
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                WHERE je.voucher_id = ?
                ORDER BY je.id
            """, (voucher_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trial_balance(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Generate trial balance report"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Base query for trial balance
            query = """
                SELECT 
                    a.account_number,
                    a.account_name,
                    a.account_type,
                    a.account_category,
                    COALESCE(SUM(je.debit_amount), 0) as total_debit,
                    COALESCE(SUM(je.credit_amount), 0) as total_credit,
                    a.balance as current_balance
                FROM accounts a
                LEFT JOIN journal_entries je ON a.id = je.account_id
            """
            
            params = []
            if as_of_date:
                query += " LEFT JOIN vouchers v ON je.voucher_id = v.id WHERE v.voucher_date <= ?"
                params.append(as_of_date)
            else:
                query += " WHERE a.is_active = TRUE"
            
            query += """
                GROUP BY a.id, a.account_number, a.account_name, a.account_type, a.account_category, a.balance
                ORDER BY a.account_number
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def create_accounting_period(self, year: int, period: int, start_date: date, end_date: date,
                               period_type: str = 'monthly') -> int:
        """Create an accounting period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounting_periods (
                    year, period, start_date, end_date, period_type
                ) VALUES (?, ?, ?, ?, ?)
            """, (year, period, start_date, end_date, period_type))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid
    
    def close_accounting_period(self, period_id: int) -> bool:
        """Close an accounting period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE accounting_periods 
                SET is_closed = TRUE, closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (period_id,))
            conn.commit()
            return cursor.rowcount > 0
