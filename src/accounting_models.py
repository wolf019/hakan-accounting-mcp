from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


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


# Swedish Chart of Accounts - IT Consultant specific (from kontoplan.md)
STANDARD_ACCOUNTS = {
    # Assets - Immateriella anläggningstillgångar
    "1030": {"name": "Patent", "type": AccountType.ASSET, "category": "intangible_assets", "requires_vat": False},
    "1040": {"name": "Licenser", "type": AccountType.ASSET, "category": "intangible_assets", "requires_vat": False},
    "1050": {"name": "Varumärken", "type": AccountType.ASSET, "category": "intangible_assets", "requires_vat": False},
    
    # Assets - Maskiner och inventarier  
    "1220": {"name": "Inventarier och verktyg", "type": AccountType.ASSET, "category": "fixed_assets", "requires_vat": False},
    "1250": {"name": "Datorer", "type": AccountType.ASSET, "category": "fixed_assets", "requires_vat": False},
    
    # Assets - Kundfordringar
    "1510": {"name": "Kundfordringar", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    
    # Assets - Övriga kortfristiga fordringar
    "1630": {"name": "Avräkning för skatter och avgifter", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    "1650": {"name": "Momsfordran", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    
    # Assets - Förutbetalda kostnader
    "1730": {"name": "Förutbetalda försäkringspremier", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    "1790": {"name": "Övriga förutbetalda kostnader", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    
    # Assets - Kassa och bank
    "1930": {"name": "Företagskonto", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    "1940": {"name": "Övriga bankkonton", "type": AccountType.ASSET, "category": "current_assets", "requires_vat": False},
    
    # Equity - Eget kapital
    "2010": {"name": "Eget kapital", "type": AccountType.EQUITY, "category": "equity", "requires_vat": False},
    "2019": {"name": "Årets resultat", "type": AccountType.EQUITY, "category": "retained_earnings", "requires_vat": False},
    
    # Liabilities - Kortfristiga skulder
    "2440": {"name": "Leverantörsskulder", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    "2510": {"name": "Skatteskulder", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    
    # Liabilities - Moms
    "2610": {"name": "Utgående moms, 25%", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    "2640": {"name": "Ingående moms", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    "2650": {"name": "Redovisningskonto för moms", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    
    # Liabilities - Personal
    "2710": {"name": "Personalskatt", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    "2730": {"name": "Lagstadgade sociala avgifter", "type": AccountType.LIABILITY, "category": "current_liabilities", "requires_vat": False},
    
    # Income - Huvudintäkter
    "3001": {"name": "Försäljning inom Sverige, 25% moms", "type": AccountType.INCOME, "category": "operating_income", "requires_vat": True},
    
    # Income - Tjänster
    "3300": {"name": "Försäljning av tjänster utanför Sverige", "type": AccountType.INCOME, "category": "operating_income", "requires_vat": False},
    
    # Income - Övriga rörelseintäkter
    "3920": {"name": "Provisionsintäkter, licensintäkter", "type": AccountType.INCOME, "category": "other_income", "requires_vat": True},
    
    # Expenses - Legoarbeten
    "4600": {"name": "Legoarbeten och underentreprenader", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Lokalkostnader
    "5010": {"name": "Lokalhyra", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Hyra av anläggningstillgångar
    "5250": {"name": "Hyra av datorer", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "5252": {"name": "Leasing av datorer", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Förbrukningsinventarier
    "5410": {"name": "Förbrukningsinventarier", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "5420": {"name": "Programvaror", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Transportmedel
    "5611": {"name": "Drivmedel för personbilar", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "5612": {"name": "Försäkring och skatt för personbilar", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Resekostnader
    "5831": {"name": "Kost och logi i Sverige", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "5832": {"name": "Kost och logi i utlandet", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Kontorsmateriel
    "6110": {"name": "Kontorsmateriel", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Tele och post
    "6210": {"name": "Telekommunikation", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6212": {"name": "Mobiltelefon", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6230": {"name": "Datakommunikation", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Företagsförsäkringar
    "6310": {"name": "Företagsförsäkringar", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Förvaltningskostnader
    "6420": {"name": "Ersättningar till revisor", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6530": {"name": "Redovisningstjänster", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Övriga externa tjänster
    "6540": {"name": "IT-tjänster", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6550": {"name": "Konsultarvoden", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6570": {"name": "Bankkostnader", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Övriga externa kostnader
    "6910": {"name": "Licensavgifter och royalties", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6970": {"name": "Tidningar, tidskrifter och facklitteratur", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    "6980": {"name": "Föreningsavgifter", "type": AccountType.EXPENSE, "category": "operating_expenses", "requires_vat": True},
    
    # Expenses - Personal
    "7210": {"name": "Löner till tjänstemän", "type": AccountType.EXPENSE, "category": "personnel_expenses", "requires_vat": False},
    "7510": {"name": "Arbetsgivaravgifter 31,42%", "type": AccountType.EXPENSE, "category": "personnel_expenses", "requires_vat": False},
    
    # Expenses - Avskrivningar
    "7810": {"name": "Avskrivningar på immateriella tillgångar", "type": AccountType.EXPENSE, "category": "depreciation", "requires_vat": False},
    "7835": {"name": "Avskrivningar på datorer", "type": AccountType.EXPENSE, "category": "depreciation", "requires_vat": False},
    
    # Financial - Ränteintäkter
    "8310": {"name": "Ränteintäkter från omsättningstillgångar", "type": AccountType.INCOME, "category": "financial_income", "requires_vat": False},
    
    # Financial - Räntekostnader
    "8410": {"name": "Räntekostnader för långfristiga skulder", "type": AccountType.EXPENSE, "category": "financial_expenses", "requires_vat": False},
    "8420": {"name": "Räntekostnader för kortfristiga skulder", "type": AccountType.EXPENSE, "category": "financial_expenses", "requires_vat": False},
}


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