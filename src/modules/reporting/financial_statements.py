"""
Financial Statements - Generate professional audit-ready financial reports
Implements Swedish auditing standards with account codes, period analysis, and condensed views
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple

from src.database import DatabaseManager
from src.models.accounting_models import IncomeStatement, BalanceSheet


class FinancialStatementsService:
    """Financial reporting with professional audit trail capabilities"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def generate_income_statement(self, start_date: date, end_date: date, 
                                 detailed: bool = True) -> IncomeStatement:
        """
        Generate income statement for period with optional enhanced detail
        
        Args:
            start_date: Period start date
            end_date: Period end date
            detailed: If True, show account codes and only non-zero accounts
        
        Returns:
            IncomeStatement object with financial data
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if detailed:
                # Get revenue accounts with non-zero balances only
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.credit_amount - je.debit_amount), 0) as balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'income' 
                        AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                        AND v.voucher_date >= ? AND v.voucher_date <= ?
                    GROUP BY a.account_number, a.account_name
                    HAVING COALESCE(SUM(je.credit_amount - je.debit_amount), 0) != 0
                    ORDER BY a.account_number
                """, (start_date, end_date))
                revenue_accounts = cursor.fetchall()
                
                # Get expense accounts with non-zero balances only
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'expense' 
                        AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                        AND v.voucher_date >= ? AND v.voucher_date <= ?
                    GROUP BY a.account_number, a.account_name
                    HAVING COALESCE(SUM(je.debit_amount - je.credit_amount), 0) != 0
                    ORDER BY a.account_number
                """, (start_date, end_date))
                expense_accounts = cursor.fetchall()
            else:
                # Legacy format - get all accounts (including zero balances)
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.credit_amount - je.debit_amount), 0) as balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'income' 
                        AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name
                    ORDER BY a.account_number
                """)
                revenue_accounts = cursor.fetchall()
                
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'expense' 
                        AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name
                    ORDER BY a.account_number
                """)
                expense_accounts = cursor.fetchall()
            
            # Calculate totals
            total_revenue = sum(Decimal(str(acc[2])) for acc in revenue_accounts)
            total_expenses = sum(Decimal(str(acc[2])) for acc in expense_accounts)
            net_income = total_revenue - total_expenses
            
            return IncomeStatement(
                period_start=start_date,
                period_end=end_date,
                generated_at=datetime.now(),
                revenue=total_revenue,
                expenses=total_expenses,
                net_income=net_income,
                revenue_accounts=revenue_accounts,
                expense_accounts=expense_accounts
            )
    
    def generate_balance_sheet(self, as_of_date: Optional[date] = None,
                              start_date: Optional[date] = None,
                              detailed: bool = True) -> BalanceSheet:
        """
        Generate balance sheet with optional period analysis
        
        Args:
            as_of_date: Closing balance date (default: today)
            start_date: Opening balance date for period analysis (default: beginning of year)
            detailed: If True, show account codes and period analysis
        
        Returns:
            BalanceSheet object with financial data
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # For backward compatibility, if start_date not provided, use beginning of year
        if start_date is None:
            start_date = date(as_of_date.year, 1, 1)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if detailed:
                # Get accounts with opening, period changes, and closing balances
                query = """
                    WITH period_movements AS (
                        SELECT 
                            a.id,
                            a.account_number,
                            a.account_name,
                            a.account_type,
                            -- Opening balance (transactions before start_date)
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date < ? THEN je.debit_amount - je.credit_amount
                                ELSE 0 
                            END), 0) as opening_movement,
                            -- Period changes (transactions between start_date and as_of_date)
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date >= ? AND v.voucher_date <= ? 
                                THEN je.debit_amount - je.credit_amount
                                ELSE 0 
                            END), 0) as period_movement,
                            -- Total movement (all transactions up to as_of_date)
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date <= ? THEN je.debit_amount - je.credit_amount
                                ELSE 0 
                            END), 0) as total_movement
                        FROM accounts a
                        LEFT JOIN journal_entries je ON a.id = je.account_id
                        LEFT JOIN vouchers v ON je.voucher_id = v.id
                        WHERE a.is_active = TRUE 
                            AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                            AND (v.is_posted = TRUE OR v.id IS NULL)
                        GROUP BY a.id, a.account_number, a.account_name, a.account_type
                    )
                    SELECT 
                        account_number,
                        account_name,
                        account_type,
                        opening_movement,
                        period_movement,
                        total_movement
                    FROM period_movements
                    WHERE account_type IN ('asset', 'liability', 'equity')
                        AND (opening_movement != 0 OR period_movement != 0 OR total_movement != 0)
                    ORDER BY account_type, account_number
                """
                
                cursor.execute(query, (start_date, start_date, as_of_date, as_of_date))
                accounts = cursor.fetchall()
                
                # Process accounts by type with proper sign handling
                assets = []
                liabilities = []
                equity = []
                
                for account in accounts:
                    account_number, account_name, account_type, opening_mov, period_mov, total_mov = account
                    
                    if account_type == 'asset':
                        # Assets: positive debit balance
                        assets.append((
                            account_number,
                            account_name,
                            float(total_mov),
                            float(opening_mov),  # Store opening balance
                            float(period_mov)    # Store period change
                        ))
                    elif account_type == 'liability':
                        # Liabilities: positive credit balance (invert sign)
                        liabilities.append((
                            account_number,
                            account_name,
                            float(-total_mov),
                            float(-opening_mov),
                            float(-period_mov)
                        ))
                    elif account_type == 'equity':
                        # Equity: positive credit balance (invert sign)
                        equity.append((
                            account_number,
                            account_name,
                            float(-total_mov),
                            float(-opening_mov),
                            float(-period_mov)
                        ))
            else:
                # Legacy format - simple balances without period analysis
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as calculated_balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'asset' AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name
                    HAVING COALESCE(SUM(je.debit_amount - je.credit_amount), 0) != 0
                    ORDER BY a.account_number
                """)
                assets = cursor.fetchall()
                
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.credit_amount - je.debit_amount), 0) as calculated_balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'liability' AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name
                    HAVING COALESCE(SUM(je.credit_amount - je.debit_amount), 0) != 0
                    ORDER BY a.account_number
                """)
                liabilities = cursor.fetchall()
                
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        COALESCE(SUM(je.credit_amount - je.debit_amount), 0) as calculated_balance
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE LOWER(a.account_type) = 'equity' AND a.is_active = TRUE
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                    GROUP BY a.account_number, a.account_name
                    HAVING COALESCE(SUM(je.credit_amount - je.debit_amount), 0) != 0
                    ORDER BY a.account_number
                """)
                equity_accounts = cursor.fetchall()
            
            # Calculate totals
            total_assets = sum((Decimal(str(acc[2])) for acc in assets), Decimal('0'))
            total_liabilities = sum((Decimal(str(acc[2])) for acc in liabilities), Decimal('0'))
            equity_from_accounts = sum((Decimal(str(acc[2])) for acc in equity), Decimal('0')) if detailed else sum((Decimal(str(acc[2])) for acc in equity_accounts), Decimal('0'))
            
            # Calculate net income and add to equity
            net_income = self._calculate_net_income(start_date, as_of_date)
            total_equity = equity_from_accounts + net_income
            
            # Add net income as retained earnings for display
            if detailed:
                equity_with_net_income = list(equity)
            else:
                equity_with_net_income = list(equity_accounts) if not detailed else list(equity)
            
            if net_income != 0:
                if detailed:
                    equity_with_net_income.append((
                        '2019', 
                        'Årets resultat', 
                        float(net_income),
                        0.0,  # No opening balance for current year earnings
                        float(net_income)  # All is period change
                    ))
                else:
                    equity_with_net_income.append(('2019', 'Årets resultat', float(net_income)))
            
            return BalanceSheet(
                period_start=start_date if detailed else as_of_date,
                period_end=as_of_date,
                generated_at=datetime.now(),
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                total_equity=total_equity,
                assets=assets,
                liabilities=liabilities,
                equity=equity_with_net_income
            )
    
    def generate_trial_balance(self, as_of_date: Optional[date] = None,
                              start_date: Optional[date] = None,
                              period_analysis: bool = True) -> Dict[str, Any]:
        """
        Generate trial balance with optional period comparison
        
        Args:
            as_of_date: For closing balance (default: today)
            start_date: For opening balance comparison (default: beginning of year)
            period_analysis: Show opening/debit/credit/closing columns
        
        Returns:
            Dict containing trial balance with period analysis
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        if start_date is None:
            start_date = date(as_of_date.year, 1, 1)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if period_analysis:
                # Get accounts with opening balances and period movements
                query = """
                    WITH period_analysis AS (
                        SELECT 
                            a.id,
                            a.account_number,
                            a.account_name,
                            a.account_type,
                            -- Opening balance (before start_date)
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date < ? THEN je.debit_amount
                                ELSE 0 
                            END), 0) as opening_debits,
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date < ? THEN je.credit_amount
                                ELSE 0 
                            END), 0) as opening_credits,
                            -- Period movements (between dates)
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date >= ? AND v.voucher_date <= ? 
                                THEN je.debit_amount
                                ELSE 0 
                            END), 0) as period_debits,
                            COALESCE(SUM(CASE 
                                WHEN v.voucher_date >= ? AND v.voucher_date <= ? 
                                THEN je.credit_amount
                                ELSE 0 
                            END), 0) as period_credits
                        FROM accounts a
                        LEFT JOIN journal_entries je ON a.id = je.account_id
                        LEFT JOIN vouchers v ON je.voucher_id = v.id
                        WHERE a.is_active = TRUE 
                            AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                            AND (v.is_posted = TRUE OR v.id IS NULL)
                        GROUP BY a.id, a.account_number, a.account_name, a.account_type
                    )
                    SELECT 
                        account_number,
                        account_name,
                        account_type,
                        opening_debits,
                        opening_credits,
                        period_debits,
                        period_credits,
                        opening_debits + period_debits as total_debits,
                        opening_credits + period_credits as total_credits
                    FROM period_analysis
                    WHERE (opening_debits + opening_credits + period_debits + period_credits) > 0
                    ORDER BY account_number
                """
                
                cursor.execute(query, (start_date, start_date, start_date, as_of_date, start_date, as_of_date))
            else:
                # Simple trial balance without period analysis (backward compatibility)
                cursor.execute("""
                    SELECT 
                        a.account_number,
                        a.account_name,
                        a.account_type,
                        0 as opening_debits,
                        0 as opening_credits,
                        COALESCE(SUM(je.debit_amount), 0) as period_debits,
                        COALESCE(SUM(je.credit_amount), 0) as period_credits,
                        COALESCE(SUM(je.debit_amount), 0) as total_debits,
                        COALESCE(SUM(je.credit_amount), 0) as total_credits
                    FROM accounts a
                    LEFT JOIN journal_entries je ON a.id = je.account_id
                    LEFT JOIN vouchers v ON je.voucher_id = v.id
                    WHERE a.is_active = TRUE 
                        AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                        AND (v.is_posted = TRUE OR v.id IS NULL)
                        AND v.voucher_date <= ?
                    GROUP BY a.account_number, a.account_name, a.account_type
                    HAVING (COALESCE(SUM(je.debit_amount), 0) + COALESCE(SUM(je.credit_amount), 0)) > 0
                    ORDER BY a.account_number
                """, (as_of_date,))
            
            accounts = cursor.fetchall()
            
            trial_balance_accounts = []
            total_opening_debit = Decimal("0")
            total_opening_credit = Decimal("0")
            total_period_debit = Decimal("0")
            total_period_credit = Decimal("0")
            total_closing_debit = Decimal("0")
            total_closing_credit = Decimal("0")
            
            for account in accounts:
                (account_number, account_name, account_type, 
                 opening_debits, opening_credits, 
                 period_debits, period_credits,
                 total_debits, total_credits) = account
                
                # Calculate opening balance
                opening_net = Decimal(str(opening_debits)) - Decimal(str(opening_credits))
                
                # Calculate closing balance  
                closing_net = Decimal(str(total_debits)) - Decimal(str(total_credits))
                
                # Determine natural balance side based on account type
                if account_type in ['asset', 'expense']:
                    # Natural debit balance
                    opening_debit = max(opening_net, Decimal("0"))
                    opening_credit = abs(min(opening_net, Decimal("0")))
                    closing_debit = max(closing_net, Decimal("0"))
                    closing_credit = abs(min(closing_net, Decimal("0")))
                else:
                    # Natural credit balance
                    opening_credit = abs(min(opening_net, Decimal("0")))
                    opening_debit = max(opening_net, Decimal("0"))
                    closing_credit = abs(min(closing_net, Decimal("0")))
                    closing_debit = max(closing_net, Decimal("0"))
                
                account_data = {
                    "account_number": account_number,
                    "account_name": account_name,
                    "debit_balance": float(closing_debit),
                    "credit_balance": float(closing_credit)
                }
                
                if period_analysis:
                    account_data.update({
                        "opening_debit": float(opening_debit),
                        "opening_credit": float(opening_credit),
                        "period_debit": float(period_debits),
                        "period_credit": float(period_credits),
                        "closing_debit": float(closing_debit),
                        "closing_credit": float(closing_credit)
                    })
                
                trial_balance_accounts.append(account_data)
                
                total_opening_debit += opening_debit
                total_opening_credit += opening_credit
                total_period_debit += Decimal(str(period_debits))
                total_period_credit += Decimal(str(period_credits))
                total_closing_debit += closing_debit
                total_closing_credit += closing_credit
            
            # Get metadata
            cursor.execute("SELECT COUNT(*) FROM vouchers")
            total_vouchers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vouchers WHERE status IN ('SUPERSEDED', 'VOID')")
            superseded_vouchers = cursor.fetchone()[0]
            
            active_vouchers = total_vouchers - superseded_vouchers
            
            if period_analysis:
                result = {
                    "title": "HUVUDBOK MED PERIODANALYS (Trial Balance with Period Analysis)",
                    "period": f"{start_date.isoformat()} to {as_of_date.isoformat()}",
                    "generated_at": datetime.now().isoformat(),
                    "accounts": trial_balance_accounts,
                    "totals": {
                        "opening": {
                            "debit": float(total_opening_debit),
                            "credit": float(total_opening_credit),
                            "balanced": abs(total_opening_debit - total_opening_credit) < Decimal("0.01")
                        },
                        "period": {
                            "debit": float(total_period_debit),
                            "credit": float(total_period_credit),
                            "balanced": abs(total_period_debit - total_period_credit) < Decimal("0.01")
                        },
                        "closing": {
                            "debit": float(total_closing_debit),
                            "credit": float(total_closing_credit),
                            "balanced": abs(total_closing_debit - total_closing_credit) < Decimal("0.01")
                        }
                    },
                    "metadata": {
                        "total_vouchers": total_vouchers,
                        "active_vouchers": active_vouchers,
                        "superseded_vouchers": superseded_vouchers,
                        "filters": {
                            "period_analysis": period_analysis,
                            "start_date": start_date.isoformat(),
                            "as_of_date": as_of_date.isoformat()
                        }
                    }
                }
            else:
                # Simple format for backward compatibility
                result = {
                    "accounts": trial_balance_accounts,
                    "totals": {
                        "debit": float(total_closing_debit),
                        "credit": float(total_closing_credit)
                    },
                    "balanced": abs(total_closing_debit - total_closing_credit) < Decimal("0.01"),
                    "metadata": {
                        "total_vouchers": total_vouchers,
                        "active_vouchers": active_vouchers,
                        "superseded_vouchers": superseded_vouchers,
                        "filters": {
                            "as_of_date": as_of_date.isoformat()
                        }
                    }
                }
            
            return result
    
    def generate_period_balance_changes(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generate balance sheet showing ONLY changes during the specified period
        
        Args:
            start_date: Period start date
            end_date: Period end date
        
        Returns:
            Dict containing balance sheet movements for the period only
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get ONLY movements within the specified period
            cursor.execute("""
                SELECT 
                    a.account_number,
                    a.account_name,
                    a.account_type,
                    COALESCE(SUM(je.debit_amount), 0) as period_debit,
                    COALESCE(SUM(je.credit_amount), 0) as period_credit,
                    COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as net_movement
                FROM accounts a
                LEFT JOIN journal_entries je ON a.id = je.account_id
                LEFT JOIN vouchers v ON je.voucher_id = v.id
                WHERE v.voucher_date >= ? 
                    AND v.voucher_date <= ?
                    AND v.is_posted = TRUE
                    AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                    AND a.is_active = TRUE
                GROUP BY a.account_number, a.account_name, a.account_type
                HAVING (period_debit != 0 OR period_credit != 0)
                ORDER BY a.account_type, a.account_number
            """, (start_date, end_date))
            
            accounts = cursor.fetchall()
            
            # Organize by account type
            assets = []
            liabilities = []
            equity = []
            
            total_asset_change = Decimal("0")
            total_liability_change = Decimal("0")
            total_equity_change = Decimal("0")
            
            for account in accounts:
                acc_num, acc_name, acc_type, debit, credit, net = account
                
                # Calculate balance change based on account type
                if acc_type == 'asset':
                    # Assets increase with debits, decrease with credits
                    change = Decimal(str(net))
                    if change != 0:
                        assets.append({
                            "account_number": acc_num,
                            "account_name": acc_name,
                            "period_change": float(change),
                            "debit": float(debit),
                            "credit": float(credit)
                        })
                        total_asset_change += change
                        
                elif acc_type == 'liability':
                    # Liabilities increase with credits, decrease with debits
                    change = -Decimal(str(net))
                    if change != 0:
                        liabilities.append({
                            "account_number": acc_num,
                            "account_name": acc_name,
                            "period_change": float(change),
                            "debit": float(debit),
                            "credit": float(credit)
                        })
                        total_liability_change += change
                        
                elif acc_type == 'equity':
                    # Equity increases with credits, decrease with debits
                    change = -Decimal(str(net))
                    if change != 0:
                        equity.append({
                            "account_number": acc_num,
                            "account_name": acc_name,
                            "period_change": float(change),
                            "debit": float(debit),
                            "credit": float(credit)
                        })
                        total_equity_change += change
            
            # Calculate net income for the period
            net_income = self._calculate_net_income(start_date, end_date)
            
            # Add net income as equity change
            if net_income != 0:
                equity.append({
                    "account_number": "2019",
                    "account_name": "Period Net Income",
                    "period_change": float(net_income),
                    "debit": 0.0,
                    "credit": float(net_income) if net_income > 0 else 0.0
                })
                total_equity_change += net_income
            
            return {
                "title": "BALANCE SHEET CHANGES (Period Only)",
                "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
                "generated_at": datetime.now().isoformat(),
                "assets": {
                    "accounts": assets,
                    "total_change": float(total_asset_change)
                },
                "liabilities": {
                    "accounts": liabilities,
                    "total_change": float(total_liability_change)
                },
                "equity": {
                    "accounts": equity,
                    "total_change": float(total_equity_change)
                },
                "balanced": abs(total_asset_change - (total_liability_change + total_equity_change)) < Decimal("0.01")
            }
    
    def _calculate_net_income(self, start_date: date, end_date: date) -> Decimal:
        """Calculate net income for the period"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(je.credit_amount - je.debit_amount), 0) as total_revenue
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                JOIN vouchers v ON je.voucher_id = v.id
                WHERE LOWER(a.account_type) = 'income' 
                    AND a.is_active = TRUE
                    AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                    AND v.is_posted = TRUE
                    AND v.voucher_date >= ? AND v.voucher_date <= ?
            """, (start_date, end_date))
            total_revenue = Decimal(str(cursor.fetchone()[0] or 0))
            
            # Get total expenses
            cursor.execute("""
                SELECT COALESCE(SUM(je.debit_amount - je.credit_amount), 0) as total_expenses
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                JOIN vouchers v ON je.voucher_id = v.id
                WHERE LOWER(a.account_type) = 'expense' 
                    AND a.is_active = TRUE
                    AND (v.status IS NULL OR v.status NOT IN ('SUPERSEDED', 'VOID'))
                    AND v.is_posted = TRUE
                    AND v.voucher_date >= ? AND v.voucher_date <= ?
            """, (start_date, end_date))
            total_expenses = Decimal(str(cursor.fetchone()[0] or 0))
            
            return total_revenue - total_expenses