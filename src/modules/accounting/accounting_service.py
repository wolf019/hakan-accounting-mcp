from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from ...database import DatabaseManager
from ...models.accounting_models import (
    Voucher, JournalEntry, AccountingPeriod, 
    AccountType, VoucherType,
    TrialBalance, IncomeStatement, BalanceSheet
)
from .idempotency_service import JournalEntryIdempotency


class AccountingService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_voucher(self, description: str, voucher_type: VoucherType, 
                      total_amount: Decimal, voucher_date: Optional[date] = None,
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
                float(total_amount), reference, source_invoice_id, source_expense_id,
                source_reminder_id
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create voucher record")
            return cursor.lastrowid
    
    def add_journal_entry(self, voucher_id: int, account_number: str,
                         description: str, debit_amount: Decimal = Decimal("0"),
                         credit_amount: Decimal = Decimal("0"),
                         reference: Optional[str] = None) -> int:
        """Add a journal entry to a voucher with duplicate prevention"""

        # Initialize idempotency service (30-second window)
        idempotency = JournalEntryIdempotency(self.db, window_seconds=30)

        # Generate request hash for duplicate detection
        request_hash = idempotency.generate_request_hash(
            voucher_id, account_number, description, debit_amount, credit_amount, reference
        )

        # Check for duplicate request
        existing_entry_id = idempotency.check_duplicate(request_hash)
        if existing_entry_id:
            # Return existing entry ID - this is idempotent behavior
            return existing_entry_id

        # Validate journal entry
        if debit_amount < 0 or credit_amount < 0:
            raise ValueError("Debit and credit amounts cannot be negative")
        if debit_amount > 0 and credit_amount > 0:
            raise ValueError("Journal entry cannot have both debit and credit amounts")
        if debit_amount == 0 and credit_amount == 0:
            raise ValueError("Journal entry must have either debit or credit amount")

        # Get account ID
        account_id = self._get_account_id(account_number)
        if not account_id:
            raise ValueError(f"Account {account_number} not found")

        # Create the journal entry
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (voucher_id, account_id, description,
                                           debit_amount, credit_amount, reference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (voucher_id, account_id, description, float(debit_amount), float(credit_amount), reference))
            conn.commit()

            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create journal entry record")

            entry_id = cursor.lastrowid

            # Record the request for future duplicate detection
            idempotency.record_request(request_hash, entry_id, voucher_id, account_number)

            return entry_id

    def add_swedish_vat_entries(
        self,
        voucher_id: int,
        gross_amount: Decimal,
        vat_rate: Decimal,
        net_account: str,
        vat_account: str,
        net_description: str,
        vat_description: str,
        transaction_type: str = "expense"
    ) -> Dict[str, Any]:
        """
        Add journal entries for VAT transactions with Swedish compliance.

        Handles Swedish Skatteverket requirement per 22 kap. 1 § SFF that VAT amounts
        must be whole numbers (no decimals). Automatically adds rounding adjustments
        to account 3740 (Öres- och kronutjämning) when needed.

        Args:
            voucher_id: Voucher to add entries to
            gross_amount: Total amount including VAT
            vat_rate: VAT rate as decimal (0.25, 0.12, 0.06, 0.0)
            net_account: Account number for net amount (e.g., "6110" for expenses, "3001" for revenue)
            vat_account: Account number for VAT ("2640" for input VAT, "2650" for output VAT)
            net_description: Description for net amount entry
            vat_description: Description for VAT entry
            transaction_type: "expense" or "revenue" (determines debit/credit direction)

        Returns:
            Dict with calculation details:
            {
                "net_amount": Decimal,
                "vat_amount": Decimal (rounded to whole SEK),
                "vat_theoretical": Decimal (before rounding),
                "rounding_diff": Decimal,
                "has_rounding": bool
            }

        Example:
            # Expense with 25% VAT
            result = accounting.add_swedish_vat_entries(
                voucher_id=123,
                gross_amount=Decimal("1006.53"),
                vat_rate=Decimal("0.25"),
                net_account="6110",
                vat_account="2640",
                net_description="Claude Max subscription",
                vat_description="VAT 25%",
                transaction_type="expense"
            )
            # Creates entries: DR 6110: 805.22, DR 2640: 201.00, DR 3740: 0.31
        """
        if vat_rate < 0 or vat_rate > 1:
            raise ValueError(f"Invalid VAT rate {vat_rate}. Must be between 0 and 1.")

        if vat_rate == 0:
            # No VAT - simple entry
            if transaction_type == "expense":
                self.add_journal_entry(
                    voucher_id=voucher_id,
                    account_number=net_account,
                    description=f"{net_description} (VAT exempt)",
                    debit_amount=gross_amount
                )
            else:  # revenue
                self.add_journal_entry(
                    voucher_id=voucher_id,
                    account_number=net_account,
                    description=f"{net_description} (VAT exempt)",
                    credit_amount=gross_amount
                )

            return {
                "net_amount": gross_amount,
                "vat_amount": Decimal("0"),
                "vat_theoretical": Decimal("0"),
                "rounding_diff": Decimal("0"),
                "has_rounding": False
            }

        # Calculate theoretical VAT and net amounts
        vat_theoretical = gross_amount * vat_rate / (Decimal("1") + vat_rate)
        net_theoretical = gross_amount - vat_theoretical

        # Round VAT to whole SEK (Swedish Skatteverket requirement per 22 kap. 1 § SFF)
        vat_rounded = Decimal(round(vat_theoretical))

        # Calculate rounding difference for account 3740
        rounding_diff = vat_theoretical - vat_rounded
        has_rounding = abs(rounding_diff) >= Decimal("0.01")

        # Add net amount entry
        if transaction_type == "expense":
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number=net_account,
                description=net_description,
                debit_amount=net_theoretical
            )
        else:  # revenue
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number=net_account,
                description=net_description,
                credit_amount=net_theoretical
            )

        # Add VAT entry (always rounded to whole SEK)
        if transaction_type == "expense":
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number=vat_account,
                description=vat_description,
                debit_amount=vat_rounded
            )
        else:  # revenue
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number=vat_account,
                description=vat_description,
                credit_amount=vat_rounded
            )

        # Add rounding adjustment if needed (account 3740)
        if has_rounding:
            # For expenses: if VAT rounded down, debit 3740 (we absorb the difference)
            # For revenue: if VAT rounded down, credit 3740 (customer pays less VAT)
            if transaction_type == "expense":
                self.add_journal_entry(
                    voucher_id=voucher_id,
                    account_number="3740",  # Öres- och kronutjämning
                    description=f"VAT rounding adjustment ({vat_theoretical:.2f} → {vat_rounded:.0f})",
                    debit_amount=abs(rounding_diff) if rounding_diff > 0 else Decimal("0"),
                    credit_amount=abs(rounding_diff) if rounding_diff < 0 else Decimal("0")
                )
            else:  # revenue
                self.add_journal_entry(
                    voucher_id=voucher_id,
                    account_number="3740",
                    description=f"VAT rounding adjustment ({vat_theoretical:.2f} → {vat_rounded:.0f})",
                    # Opposite direction for revenue
                    credit_amount=abs(rounding_diff) if rounding_diff > 0 else Decimal("0"),
                    debit_amount=abs(rounding_diff) if rounding_diff < 0 else Decimal("0")
                )

        return {
            "net_amount": net_theoretical,
            "vat_amount": vat_rounded,
            "vat_theoretical": vat_theoretical,
            "rounding_diff": rounding_diff,
            "has_rounding": has_rounding
        }
    
    def post_voucher(self, voucher_id: int) -> bool:
        """Post a voucher - updates account balances and marks as posted"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify voucher balances
            cursor.execute("""
                SELECT SUM(debit_amount) as total_debit, SUM(credit_amount) as total_credit
                FROM journal_entries WHERE voucher_id = ?
            """, (voucher_id,))
            result = cursor.fetchone()

            if not result:
                raise ValueError("No journal entries found for voucher")

            # Use tolerance for floating point comparison (allow 1 öre difference)
            if abs(result[0] - result[1]) > 0.01:
                raise ValueError(f"Voucher is not balanced - total debits must equal total credits (diff: {abs(result[0] - result[1]):.4f})")
            
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
                
                cursor.execute("""
                    UPDATE accounts SET balance = balance + ? WHERE id = ?
                """, (balance_change, account_id))
            
            # Mark voucher as posted
            cursor.execute("""
                UPDATE vouchers SET is_posted = TRUE, posted_at = ? WHERE id = ?
            """, (datetime.now(), voucher_id))
            
            conn.commit()
            return True
    
    def get_account_balance(self, account_number: str, as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """Get account balance and transaction info"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, account_name, account_type FROM accounts WHERE account_number = ?
            """, (account_number,))
            account = cursor.fetchone()
            
            if not account:
                raise ValueError(f"Account {account_number} not found")
            
            account_id, account_name, account_type = account
            
            # Calculate current balance from journal entries (excluding superseded vouchers)
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(je.debit_amount), 0) as total_debits,
                    COALESCE(SUM(je.credit_amount), 0) as total_credits,
                    COUNT(*) as transaction_count,
                    MAX(je.created_at) as last_transaction_date
                FROM journal_entries je
                JOIN vouchers v ON je.voucher_id = v.id
                WHERE je.account_id = ?
                    AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                    AND v.is_posted = TRUE
            """, (account_id,))
            
            result = cursor.fetchone()
            total_debits = Decimal(str(result[0])) if result[0] else Decimal("0")
            total_credits = Decimal(str(result[1])) if result[1] else Decimal("0")
            transaction_count = result[2] if result[2] else 0
            last_transaction_date = result[3] if result[3] else None
            
            # Calculate balance based on account type (same logic as trial balance)
            if account_type in ['asset', 'expense']:
                # Assets and expenses: positive = debit balance
                balance = total_debits - total_credits
            else:
                # Income, liability, equity: positive = credit balance  
                balance = total_credits - total_debits
            
            return {
                "account_number": account_number,
                "account_name": account_name,
                "balance": float(balance),
                "transaction_count": transaction_count,
                "last_transaction_date": last_transaction_date,
                "account_type": account_type,
                "total_debits": float(total_debits),
                "total_credits": float(total_credits)
            }
    
    def generate_trial_balance_enhanced(self, as_of_date: Optional[date] = None,
                                       start_date: Optional[date] = None,
                                       period_analysis: bool = True) -> Dict[str, Any]:
        """Generate enhanced trial balance with period comparison"""
        from src.modules.reporting.financial_statements import FinancialStatementsService
        fs_service = FinancialStatementsService(self.db)
        return fs_service.generate_trial_balance(as_of_date, start_date, period_analysis)
    
    def generate_trial_balance(self, as_of_date: Optional[date] = None, 
                              include_superseded: bool = False,
                              security_audit: bool = False) -> Dict[str, Any]:
        """
        Generate trial balance with superseded voucher filtering
        
        Args:
            as_of_date: Date to generate balance as of (None = current)
            include_superseded: Include SUPERSEDED/VOID vouchers (default: False)
            security_audit: Include security verification details (default: False)
        
        Returns:
            Dict with trial balance and metadata
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate actual debit and credit totals for trial balance
            if not include_superseded:
                # Calculate balances excluding superseded vouchers
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        a.account_type,
                        COALESCE(SUM(je.debit_amount), 0) as total_debits,
                        COALESCE(SUM(je.credit_amount), 0) as total_credits,
                        COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as net_balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE a.is_active = TRUE 
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name, a.account_type
                    ORDER BY a.account_number
                """)
            else:
                # Include all vouchers
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        a.account_type,
                        COALESCE(SUM(je.debit_amount), 0) as total_debits,
                        COALESCE(SUM(je.credit_amount), 0) as total_credits,
                        COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as net_balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE a.is_active = TRUE
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name, a.account_type
                    ORDER BY a.account_number
                """)
            
            accounts = cursor.fetchall()
            trial_balance_accounts = []
            total_debit = Decimal("0")
            total_credit = Decimal("0")
            
            for account in accounts:
                account_number, account_name, account_type, account_debits, account_credits, net_balance = account
                
                # Convert to Decimal
                account_debits = Decimal(str(account_debits)) if account_debits is not None else Decimal("0")
                account_credits = Decimal(str(account_credits)) if account_credits is not None else Decimal("0")
                net_balance = Decimal(str(net_balance)) if net_balance is not None else Decimal("0")
                
                # For trial balance, show accounts on their NATURAL side based on account type
                if account_type in ['asset', 'expense']:
                    # Assets and expenses have natural DEBIT balances
                    if net_balance >= 0:
                        debit_balance = net_balance
                        credit_balance = Decimal("0")
                    else:
                        debit_balance = Decimal("0")
                        credit_balance = abs(net_balance)  # Show negative asset as credit
                else:
                    # Income, liability, equity have natural CREDIT balances  
                    if net_balance <= 0:
                        credit_balance = abs(net_balance)
                        debit_balance = Decimal("0")
                    else:
                        credit_balance = Decimal("0")
                        debit_balance = net_balance  # Show positive liability as debit (unusual)
                
                # Only include accounts with non-zero balances
                if debit_balance > 0 or credit_balance > 0:
                    total_debit += debit_balance
                    total_credit += credit_balance
                    
                    trial_balance_accounts.append({
                        "account_number": account_number,
                        "account_name": account_name,
                        "debit_balance": float(debit_balance),
                        "credit_balance": float(credit_balance)
                    })
            
            # Get metadata
            cursor.execute("SELECT COUNT(*) FROM vouchers")
            total_vouchers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vouchers WHERE status IN ('SUPERSEDED', 'VOID')")
            superseded_vouchers = cursor.fetchone()[0]
            
            active_vouchers = total_vouchers - superseded_vouchers
            
            # Get security protected operations count if requested
            security_protected_count = 0
            if security_audit:
                cursor.execute("""
                    SELECT COUNT(DISTINCT va.voucher_id)
                    FROM voucher_annotations va
                    WHERE va.security_verified = TRUE
                """)
                security_protected_count = cursor.fetchone()[0]
            
            result = {
                "accounts": trial_balance_accounts,
                "totals": {
                    "debit": float(total_debit),
                    "credit": float(total_credit)
                },
                "balanced": abs(total_debit - total_credit) < Decimal("0.01"),
                "metadata": {
                    "total_vouchers": total_vouchers,
                    "active_vouchers": active_vouchers,
                    "superseded_vouchers": superseded_vouchers,
                    "filters": {
                        "include_superseded": include_superseded,
                        "as_of_date": as_of_date.isoformat() if as_of_date else None
                    }
                }
            }
            
            if security_audit:
                result["metadata"]["security_protected_operations"] = security_protected_count
            
            return result
    
    def generate_income_statement(self, start_date: date, end_date: date, detailed: bool = True) -> IncomeStatement:
        """Generate income statement for period with optional enhanced detail"""
        # Use the FinancialStatementsService for actual implementation
        from src.modules.reporting.financial_statements import FinancialStatementsService
        fs_service = FinancialStatementsService(self.db)
        return fs_service.generate_income_statement(start_date, end_date, detailed)
    
    def generate_balance_sheet(self, as_of_date: Optional[date] = None, 
                              start_date: Optional[date] = None,
                              detailed: bool = True) -> BalanceSheet:
        """Generate balance sheet with optional period analysis"""
        # Use the FinancialStatementsService for actual implementation
        from src.modules.reporting.financial_statements import FinancialStatementsService
        fs_service = FinancialStatementsService(self.db)
        return fs_service.generate_balance_sheet(as_of_date, start_date, detailed)
    
    def auto_generate_invoice_voucher(self, invoice_id: int) -> int:
        """Automatically generate voucher for invoice"""
        # Get invoice details
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT invoice_number, issue_date, subtotal, tax_amount, total
                FROM invoices WHERE id = ?
            """, (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            invoice_number, issue_date, subtotal, tax_amount, total = invoice
            
            # Create voucher
            voucher_id = self.create_voucher(
                description=f"Sales Invoice {invoice_number}",
                voucher_type=VoucherType.SALES_INVOICE,
                total_amount=total,
                voucher_date=issue_date,
                source_invoice_id=invoice_id,
                reference=invoice_number
            )
            
            # Add journal entries
            # Debit: Accounts Receivable
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1510",  # Kundfordringar
                description=f"Invoice {invoice_number}",
                debit_amount=total
            )
            
            # Credit: VAT Out
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="2610",  # Utgående moms, 25%
                description=f"VAT on Invoice {invoice_number}",
                credit_amount=tax_amount
            )
            
            # Credit: Revenue
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="3001",  # Försäljning inom Sverige, 25% moms
                description=f"Revenue from Invoice {invoice_number}",
                credit_amount=subtotal
            )
            
            # Validate voucher is balanced before completing
            self.validate_voucher_balance(voucher_id)
            
            # Update invoice with voucher reference
            cursor.execute("UPDATE invoices SET voucher_id = ? WHERE id = ?", (voucher_id, invoice_id))
            conn.commit()
            
            return voucher_id
    
    def auto_generate_expense_voucher(self, expense_id: int) -> int:
        """Automatically generate voucher for expense"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT description, amount, vat_amount, expense_date, category
                FROM expenses WHERE id = ?
            """, (expense_id,))
            expense = cursor.fetchone()
            
            if not expense:
                raise ValueError(f"Expense {expense_id} not found")
            
            description, amount, vat_amount, expense_date, category = expense
            net_amount = amount - vat_amount
            
            # Map expense category to account
            account_mapping = {
                "software": "5420",      # Programvaror
                "phone_internet": "6212", # Mobiltelefon
                "office_supplies": "6110", # Kontorsmateriel
                "hosting_cloud": "6540",  # IT-tjänster
            }
            
            expense_account = account_mapping.get(category, "6540")  # Default to IT-tjänster
            
            # Create voucher
            voucher_id = self.create_voucher(
                description=f"Expense: {description}",
                voucher_type=VoucherType.PURCHASE,
                total_amount=amount,
                voucher_date=expense_date,
                source_expense_id=expense_id,
                reference=f"EXP-{expense_id}"
            )
            
            # Add journal entries
            # Debit: Expense account
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number=expense_account,
                description=description,
                debit_amount=net_amount
            )
            
            # Debit: VAT In
            if vat_amount > 0:
                self.add_journal_entry(
                    voucher_id=voucher_id,
                    account_number="2640",  # Ingående moms
                    description=f"VAT on {description}",
                    debit_amount=vat_amount
                )
            
            # Credit: Accounts Payable
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="2440",  # Leverantörsskulder
                description=f"Payable for {description}",
                credit_amount=amount
            )
            
            # Validate voucher is balanced before completing
            self.validate_voucher_balance(voucher_id)
            
            # Update expense with voucher reference
            cursor.execute("UPDATE expenses SET voucher_id = ? WHERE id = ?", (voucher_id, expense_id))
            conn.commit()
            
            return voucher_id
    
    def auto_generate_payment_voucher(self, invoice_id: int, payment_amount: Decimal, 
                                     payment_date: date = None, reference: str = None) -> int:
        """Automatically generate voucher for invoice payment"""
        if payment_date is None:
            payment_date = date.today()
            
        # Get invoice details
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT invoice_number, total
                FROM invoices WHERE id = ?
            """, (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            invoice_number, invoice_total = invoice
            
            # Create voucher
            voucher_id = self.create_voucher(
                description=f"Payment received for Invoice {invoice_number}",
                voucher_type=VoucherType.PAYMENT,
                total_amount=payment_amount,
                voucher_date=payment_date,
                source_invoice_id=invoice_id,
                reference=reference or f"PAY-{invoice_number}"
            )
            
            # Add journal entries
            # Debit: Bank Account (cash received)
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1930",  # Företagskonto/checkkonto/affärskonto
                description=f"Payment received for Invoice {invoice_number}",
                debit_amount=payment_amount
            )
            
            # Credit: Accounts Receivable (clear the receivable)
            self.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1510",  # Kundfordringar
                description=f"Payment for Invoice {invoice_number}",
                credit_amount=payment_amount
            )
            
            # Validate voucher is balanced before completing
            self.validate_voucher_balance(voucher_id)
            
            return voucher_id
    
    def validate_voucher_balance(self, voucher_id: int) -> bool:
        """Validate that a voucher's journal entries are balanced"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(debit_amount), 0) as total_debits,
                    COALESCE(SUM(credit_amount), 0) as total_credits
                FROM journal_entries WHERE voucher_id = ?
            """, (voucher_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"No journal entries found for voucher {voucher_id}")
            
            total_debits, total_credits = result
            difference = abs(total_debits - total_credits)
            
            if difference > 0.01:  # Allow for small rounding differences
                raise ValueError(f"UNBALANCED VOUCHER {voucher_id}: {total_debits:.2f} debits ≠ {total_credits:.2f} credits (difference: {difference:.2f})")
            
            return True
    
    def get_voucher_by_number(self, voucher_number: str) -> Optional[Dict[str, Any]]:
        """Get voucher by voucher number (V001, V002, etc.)"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, voucher_number, voucher_date, description, voucher_type,
                       total_amount, reference, source_invoice_id, source_expense_id,
                       is_posted, created_at, status
                FROM vouchers WHERE voucher_number = ?
            """, (voucher_number,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            return {
                "id": result[0],
                "voucher_number": result[1],
                "voucher_date": result[2],
                "description": result[3],
                "voucher_type": result[4],
                "total_amount": result[5],
                "reference": result[6],
                "source_invoice_id": result[7],
                "source_expense_id": result[8],
                "is_posted": result[9],
                "created_at": result[10],
                "status": result[11]
            }
    
    def get_voucher_id_by_number(self, voucher_number: str) -> Optional[int]:
        """Get voucher ID by voucher number"""
        voucher = self.get_voucher_by_number(voucher_number)
        return voucher["id"] if voucher else None
    
    def resolve_voucher_identifier(self, identifier: str) -> Optional[int]:
        """Resolve voucher identifier - accepts either ID (as string) or voucher number (V001, etc.)"""
        # If it looks like a voucher number (starts with V), look it up
        if identifier.upper().startswith('V'):
            return self.get_voucher_id_by_number(identifier.upper())
        
        # Otherwise, try to parse as integer ID
        try:
            voucher_id = int(identifier)
            # Verify this voucher ID exists
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM vouchers WHERE id = ?", (voucher_id,))
                result = cursor.fetchone()
                return voucher_id if result else None
        except ValueError:
            return None
    
    def _generate_voucher_number(self) -> str:
        """Generate next voucher number"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vouchers")
            count = cursor.fetchone()[0]
            return f"V{count + 1:03d}"
    
    def _get_account_id(self, account_number: str) -> Optional[int]:
        """Get account ID by account number"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
            result = cursor.fetchone()
            return result[0] if result else None