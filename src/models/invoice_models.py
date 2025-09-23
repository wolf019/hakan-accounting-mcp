from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class CustomerType(Enum):
    BUSINESS = "business"
    CONSUMER = "consumer"


@dataclass
class Address:
    street: str
    postal_code: str
    city: str
    country: str = "Sweden"


@dataclass
class Customer:
    name: str
    company: str
    vat_number: str
    email: Optional[str] = None
    address: Optional[str] = None  # Legacy single address field
    org_number: Optional[str] = None
    # Enhanced address fields
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    contact_person: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def get_formatted_address(self) -> Optional[str]:
        """Get formatted address, preferring structured fields over legacy address"""
        if self.street and self.city:
            address_parts = []
            if self.street:
                address_parts.append(self.street)
            if self.postal_code and self.city:
                address_parts.append(f"{self.postal_code} {self.city}")
            elif self.city:
                address_parts.append(self.city)
            if self.country and self.country.lower() != "sweden":
                address_parts.append(self.country)
            return "\n".join(address_parts)
        return self.address  # Fall back to legacy address field


@dataclass
class LineItem:
    invoice_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    id: Optional[int] = None


@dataclass
class Invoice:
    invoice_number: str
    customer_id: int
    issue_date: date
    due_date: date
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    status: InvoiceStatus = InvoiceStatus.DRAFT
    tax_rate: Decimal = Decimal("0.25")
    notes: Optional[str] = None
    reminder_count: int = 0
    last_reminder_date: Optional[date] = None
    customer_type: CustomerType = CustomerType.BUSINESS
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PaymentReminder:
    invoice_id: int
    reminder_number: int
    reminder_date: date
    original_amount: Decimal
    interest_amount: Decimal
    reminder_fee: Decimal
    delay_compensation: Decimal
    total_amount: Decimal
    reference_rate: Decimal
    interest_rate: Decimal
    days_overdue: int
    customer_type: CustomerType
    pdf_generated: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class CompanyInfo:
    name: str
    address: str
    org_number: str
    vat_number: str
    email: str
    phone: Optional[str] = None


