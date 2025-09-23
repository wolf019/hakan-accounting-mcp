from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from ...models.invoice_models import Invoice, PaymentReminder, CustomerType


class SwedishInterestCalculator:
    """
    Swedish interest calculation according to commercial law.
    Reference rate + 8% annually for business customers.
    """

    def __init__(self, reference_rate: Decimal = Decimal("2.0")):
        """
        Initialize with Swedish Central Bank reference rate.
        Default: 2.0% (manual input, can be updated)
        """
        self.reference_rate = reference_rate

    def calculate_interest_rate(self, customer_type: CustomerType) -> Decimal:
        """Calculate annual interest rate according to Swedish law"""
        # Swedish law: reference rate + 8% for business customers
        return self.reference_rate + Decimal("8.0")

    def calculate_days_overdue(self, invoice: Invoice, calculation_date: Optional[date] = None) -> int:
        """
        Calculate days overdue from invoice date + 30 days (not due date).
        Swedish law: interest starts 30 days after invoice date.
        """
        if calculation_date is None:
            calculation_date = date.today()

        # Interest starts 30 days after invoice date
        interest_start_date = invoice.issue_date.replace(
            day=min(invoice.issue_date.day, 28)  # Handle month-end dates
        )
        # Add 30 days
        if invoice.issue_date.month == 12:
            interest_start_date = interest_start_date.replace(
                year=invoice.issue_date.year + 1, month=1
            )
        else:
            interest_start_date = interest_start_date.replace(
                month=invoice.issue_date.month + 1
            )

        # Calculate days overdue
        if calculation_date > interest_start_date:
            return (calculation_date - interest_start_date).days
        return 0

    def calculate_interest_amount(
        self,
        principal: Decimal,
        days_overdue: int,
        customer_type: CustomerType
    ) -> Decimal:
        """
        Calculate interest amount according to Swedish law.
        Formula: (amount × annual_rate) / 365 × days_overdue
        """
        if days_overdue <= 0:
            return Decimal("0")

        annual_rate = self.calculate_interest_rate(customer_type)
        daily_rate = annual_rate / Decimal("100") / Decimal("365")

        return (principal * daily_rate * Decimal(str(days_overdue))).quantize(
            Decimal("0.01")
        )

    def calculate_reminder_fees(
        self,
        reminder_number: int,
        customer_type: CustomerType
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate reminder fee and delay compensation according to Swedish law.

        Returns: (reminder_fee, delay_compensation)

        Business customers:
        - Reminder fee: 60 SEK (if contractually agreed)
        - Delay compensation: 450 SEK (automatic right)

        Consumer customers:
        - Reminder fee: Only if agreed in advance
        - Delay compensation: Not allowed
        """
        reminder_fee = Decimal("0")
        delay_compensation = Decimal("0")

        if customer_type == CustomerType.BUSINESS:
            # Business customers
            reminder_fee = Decimal("60.00")  # Standard reminder fee
            if reminder_number == 1:  # Only on first reminder
                delay_compensation = Decimal("450.00")
        else:
            # Consumer customers - no automatic fees
            # Only if contractually agreed (implementation would check contract)
            pass

        return reminder_fee, delay_compensation


class PaymentReminderManager:
    """Manages payment reminders and integrates with database"""

    def __init__(self, db_manager, interest_calculator: Optional[SwedishInterestCalculator] = None):
        self.db = db_manager
        self.calculator = interest_calculator or SwedishInterestCalculator()

    def find_overdue_invoices(self, grace_days: int = 5) -> List[Invoice]:
        """
        Find invoices that are overdue and need reminders.
        Grace period: wait a few days after due date before first reminder.
        """
        from datetime import timedelta
        overdue_cutoff = date.today() - timedelta(days=grace_days)

        # Get all sent invoices that are past due date + grace period
        invoices = self.db.list_invoices(status="sent")
        overdue = []

        for invoice in invoices:
            if invoice.due_date < overdue_cutoff:
                # Check if we need to send a reminder
                days_since_last_reminder = 0
                if invoice.last_reminder_date:
                    days_since_last_reminder = (date.today() - invoice.last_reminder_date).days

                # Send reminder if:
                # - No previous reminders, OR
                # - 14+ days since last reminder
                if invoice.reminder_count == 0 or days_since_last_reminder >= 14:
                    overdue.append(invoice)

        return overdue

    def create_payment_reminder(
        self,
        invoice: Invoice,
        customer_type: Optional[CustomerType] = None,
        calculation_date: Optional[date] = None
    ) -> PaymentReminder:
        """
        Create a payment reminder with all Swedish law calculations.
        """
        if calculation_date is None:
            calculation_date = date.today()

        if customer_type is None:
            customer_type = invoice.customer_type or CustomerType.BUSINESS

        # Calculate reminder details
        reminder_number = invoice.reminder_count + 1
        days_overdue = self.calculator.calculate_days_overdue(invoice, calculation_date)

        # Calculate amounts
        original_amount = invoice.total
        interest_amount = self.calculator.calculate_interest_amount(
            original_amount, days_overdue, customer_type
        )

        reminder_fee, delay_compensation = self.calculator.calculate_reminder_fees(
            reminder_number, customer_type
        )

        total_amount = original_amount + interest_amount + reminder_fee + delay_compensation

        # Create reminder object
        if invoice.id is None:
            raise ValueError("Invoice must have an ID to create reminder")

        reminder = PaymentReminder(
            invoice_id=invoice.id,
            reminder_number=reminder_number,
            reminder_date=calculation_date,
            original_amount=original_amount,
            interest_amount=interest_amount,
            reminder_fee=reminder_fee,
            delay_compensation=delay_compensation,
            total_amount=total_amount,
            reference_rate=self.calculator.reference_rate,
            interest_rate=self.calculator.calculate_interest_rate(customer_type),
            days_overdue=days_overdue,
            customer_type=customer_type
        )

        return reminder

    def save_payment_reminder(self, reminder: PaymentReminder) -> int:
        """Save payment reminder to database and update invoice"""
        # Save reminder
        reminder_id = self.db.create_payment_reminder(reminder)

        # Update invoice reminder count and date
        self.db.update_invoice_reminder_info(
            reminder.invoice_id,
            reminder.reminder_number,
            reminder.reminder_date
        )

        return reminder_id
