from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Expense:
    description: str
    amount: Decimal
    category: str
    expense_date: date
    vat_amount: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("0.25")
    receipt_image_path: Optional[str] = None
    notes: Optional[str] = None
    is_deductible: bool = True
    voucher_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BankTransaction:
    transaction_date: date
    amount: Decimal
    transaction_type: str  # 'incoming', 'outgoing'
    description: Optional[str] = None
    reference: Optional[str] = None
    counterparty: Optional[str] = None
    account_balance: Optional[Decimal] = None
    id: Optional[int] = None
    imported_at: Optional[datetime] = None


@dataclass
class Reconciliation:
    bank_transaction_id: int
    reconciled_amount: Decimal
    reconciliation_type: str  # 'invoice_payment', 'expense_payment'
    invoice_id: Optional[int] = None
    expense_id: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    reconciled_at: Optional[datetime] = None


@dataclass
class VATReport:
    year: int
    quarter: int
    start_date: date
    end_date: date
    total_sales: Decimal
    total_purchases: Decimal
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    invoice_count: int
    expense_count: int


# Swedish expense categories for tax compliance
EXPENSE_CATEGORIES = {
    "office_supplies": "Kontorsmaterial",
    "software": "Programvara och licenser", 
    "hosting_cloud": "Hosting och molntjänster",
    "travel": "Resor",
    "meals_client": "Representation",
    "education": "Utbildning och kurser",
    "equipment": "Inventarier och utrustning",
    "phone_internet": "Telefon och internet",
    "insurance": "Försäkringar",
    "accounting": "Bokföring och revision",
    "marketing": "Marknadsföring",
    "office_rent": "Kontorshyra",
    "other": "Övrigt"
}

# VAT rates used in Sweden
VAT_RATES = {
    "standard": Decimal("0.25"),    # 25% - most goods/services
    "reduced": Decimal("0.12"),     # 12% - food, hotels
    "low": Decimal("0.06"),         # 6% - books, newspapers
    "zero": Decimal("0.00"),        # 0% - exports, some services
}