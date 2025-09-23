from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict


class ValidationError(Exception):
    """Custom exception for account validation errors"""
    pass


class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


class VoucherType(Enum):
    SALES_INVOICE = "sales_invoice"
    PURCHASE = "purchase"
    PAYMENT = "payment"
    PAYMENT_REMINDER = "payment_reminder"
    ADJUSTMENT = "adjustment"
    OPENING_BALANCE = "opening_balance"
    CLOSING_ENTRY = "closing_entry"


@dataclass
class Account:
    account_number: str
    account_name: str
    account_type: AccountType
    account_category: str
    parent_account: Optional[str] = None
    is_active: bool = True
    requires_vat: bool = False
    balance: Decimal = Decimal("0")
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Voucher:
    voucher_number: str
    voucher_date: date
    description: str
    voucher_type: VoucherType
    total_amount: Decimal
    reference: Optional[str] = None
    source_invoice_id: Optional[int] = None
    source_expense_id: Optional[int] = None
    source_reminder_id: Optional[int] = None
    is_posted: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None


@dataclass
class JournalEntry:
    voucher_id: int
    account_id: int
    description: str
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")
    reference: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class AccountingPeriod:
    year: int
    period: int
    start_date: date
    end_date: date
    period_type: str = "monthly"
    is_closed: bool = False
    id: Optional[int] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# Note: Chart of accounts is now stored in the database accounts table.
# Use load_complete_chart_of_accounts.py to populate from specs/kontoplan.md


@dataclass
class TrialBalance:
    """Trial balance data structure"""
    account_number: str
    account_name: str
    debit_balance: Decimal
    credit_balance: Decimal
    
    
@dataclass
class FinancialStatement:
    """Base class for financial statements"""
    period_start: date
    period_end: date
    generated_at: datetime
    
    
@dataclass
class IncomeStatement(FinancialStatement):
    """Income statement data"""
    revenue: Decimal
    expenses: Decimal
    net_income: Decimal
    revenue_accounts: list
    expense_accounts: list
    
    
@dataclass
class BalanceSheet(FinancialStatement):
    """Balance sheet data"""
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    assets: list
    liabilities: list
    equity: list


# Svenska Kontotypning - Skatteverkets Krav på Hela Kronor
# Baserat på 22 kap. 1 § SFF: "Belopp som avser skatt enligt SFL ska anges i hela kronor"

# Skatterelaterade konton som kräver hela kronor enligt Skatteverkets regler
WHOLE_NUMBER_ACCOUNTS: Dict[str, Dict[str, str]] = {
    "2510": {
        "name": "Skatteskulder",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2518": {
        "name": "Skatteskulder (alternativ)",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2650": {
        "name": "Redovisningskonto för moms",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for VAT rounding as required by Skatteverket"
    },
    "2710": {
        "name": "Personalskatt/källskatt",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2730": {
        "name": "Arbetsgivaravgifter",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2731": {
        "name": "Arbetsgivaravgifter (alternativ)",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2940": {
        "name": "Upplupna personalskatter",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    },
    "2941": {
        "name": "Upplupna personalskatter (alternativ)",
        "suggestion": "Use account 3740 (Öres- och kronutjämning) for the decimal amount"
    }
}


def validate_amount(account_number: str, amount: float) -> None:
    """
    Validates that tax-related accounts only accept whole numbers (SEK) as required by Skatteverket.
    
    Args:
        account_number: The BAS account number (e.g., "2650")
        amount: The monetary amount to validate
        
    Raises:
        ValidationError: If a tax account contains decimal amounts
        
    Example:
        >>> validate_amount("2650", 2772.68)  # Raises ValidationError
        >>> validate_amount("2650", 2772.00)  # OK
        >>> validate_amount("3001", 12500.50)  # OK (not a tax account)
    """
    if account_number in WHOLE_NUMBER_ACCOUNTS:
        if amount != round(amount):
            account_info = WHOLE_NUMBER_ACCOUNTS[account_number]
            decimal_amount = round(amount - int(amount), 2)
            
            error_message = (
                f"❌ VALIDATION ERROR: Account {account_number} ({account_info['name']}) "
                f"requires whole numbers according to Skatteverket regulations (22 kap. 1 § SFF).\n\n"
                f"💡 SOLUTION: {account_info['suggestion']}\n\n"
                f"📊 SUGGESTED CORRECTION:\n"
                f"   Account {account_number}: {int(amount):.2f} SEK (whole amount)\n"
                f"   Account 3740: {decimal_amount:.2f} SEK (decimal rounding)\n\n"
                f"📋 LEGAL REQUIREMENT: All tax-related amounts must be declared in whole SEK to Skatteverket."
            )
            
            raise ValidationError(error_message)


def get_rounding_suggestion(account_number: str, amount: float) -> dict:
    """
    Provides detailed rounding suggestions for tax accounts.
    
    Args:
        account_number: The BAS account number
        amount: The original amount with decimals
        
    Returns:
        dict: Suggested journal entries for proper rounding
    """
    if account_number not in WHOLE_NUMBER_ACCOUNTS:
        return {"suggestion": "No rounding needed - not a tax account"}
    
    whole_amount = int(amount)
    decimal_amount = round(amount - whole_amount, 2)
    
    return {
        "original_amount": amount,
        "whole_amount": whole_amount,
        "decimal_amount": decimal_amount,
        "journal_entries": [
            {
                "account": account_number,
                "amount": whole_amount,
                "description": f"{WHOLE_NUMBER_ACCOUNTS[account_number]['name']} (whole SEK)"
            },
            {
                "account": "3740",
                "amount": decimal_amount,
                "description": "Öres- och kronutjämning (decimal rounding)"
            }
        ],
        "legal_note": "Required by Skatteverket according to 22 kap. 1 § SFF"
    }