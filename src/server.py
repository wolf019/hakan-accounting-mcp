from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .database import DatabaseManager
from .models.invoice_models import CompanyInfo, Customer, Invoice, LineItem, InvoiceStatus, CustomerType
from .models.expense_models import Expense, BankTransaction, Reconciliation, EXPENSE_CATEGORIES
from .modules.invoicing import PDFGenerator
from .modules.invoicing import PaymentReminderManager, SwedishInterestCalculator
from .modules.accounting import AccountingService
from .models.accounting_models import VoucherType
from .modules.documentation import AccountingDocumentationService
from .modules.accounting.secure_voucher_service import SecureVoucherService
from .modules.accounting.voucher_annotation_service import VoucherAnnotationService


# Default company information - in a real implementation, this would be configurable
DEFAULT_COMPANY_INFO = CompanyInfo(
    name="Kaare Consulting",
    address="FISKSÄTRAVÄGEN 26 A LGH 1504\n133 45 SALTSJÖBADEN, SWEDEN",
    org_number="920119-0197",
    vat_number="SE920119019701",
    email="consulting@tomkaare.tech",
    phone="+46 768 79 90 58"
)


class InvoiceServer:
    def __init__(self):
        self.db = DatabaseManager()
        self.pdf_generator = PDFGenerator()
        self.company_info = DEFAULT_COMPANY_INFO
        self.reminder_manager = PaymentReminderManager(self.db)
        self.accounting = AccountingService(self.db)
        self.documentation = AccountingDocumentationService()
        self.secure_voucher = SecureVoucherService(self.db)
        self.voucher_annotation = VoucherAnnotationService(self.db)

    async def record_business_event(
        self,
        event_type: str,
        description: str,
        amount: float,
        counterparty: str,
        event_date: Optional[str] = None,
        reference: Optional[str] = None,
        invoice_id: Optional[int] = None,
        expense_id: Optional[int] = None,
        auto_post: bool = True,
        vat_rate: Optional[float] = None
    ) -> str:
        """Universal business event recorder with Swedish compliance

        Args:
            event_type: expense|invoice|payment|transfer|adjustment
            description: Detailed business description (Swedish legal requirement)
            amount: Total amount in SEK
            counterparty: Business partner (Swedish legal requirement)
            event_date: When event occurred (YYYY-MM-DD, defaults to today)
            reference: External reference (invoice number, receipt, etc.)
            invoice_id: Link to existing invoice (for payments)
            expense_id: Link to existing expense
            auto_post: Automatically post voucher (default: True)
            vat_rate: Swedish VAT rate (0.25, 0.12, 0.06, 0.0) - defaults to None (no VAT)

        Returns:
            Success message with voucher details
        """
        try:
            from datetime import date
            from decimal import Decimal

            # Parse event date
            if event_date:
                try:
                    event_date_obj = date.fromisoformat(event_date)
                except ValueError:
                    return "❌ Invalid date format. Use YYYY-MM-DD"
            else:
                event_date_obj = date.today()

            # Validate required Swedish compliance fields
            if not description or len(description.strip()) < 10:
                return "❌ Description must be detailed (min 10 chars) per Swedish law"

            if not counterparty or len(counterparty.strip()) < 2:
                return "❌ Counterparty required for Swedish compliance"

            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return "❌ Amount must be positive"

            # Validate Swedish VAT rate (if provided)
            if vat_rate is not None:
                valid_vat_rates = [0.25, 0.12, 0.06, 0.0]
                if vat_rate not in valid_vat_rates:
                    return f"❌ Invalid VAT rate. Swedish rates: 25% (0.25), 12% (0.12), 6% (0.06), 0% (0.0)"
            # Note: vat_rate defaults to None, requiring explicit specification for VAT transactions

            # Map event type to voucher type and generate journal entries
            if event_type == "expense":
                return await self._record_expense_event(
                    description, amount_decimal, counterparty, event_date_obj, reference, auto_post, vat_rate
                )
            elif event_type == "invoice":
                return await self._record_invoice_event(
                    description, amount_decimal, counterparty, event_date_obj, reference, invoice_id, auto_post
                )
            elif event_type == "payment":
                return await self._record_payment_event(
                    description, amount_decimal, counterparty, event_date_obj, reference, invoice_id, auto_post
                )
            elif event_type == "transfer":
                return await self._record_transfer_event(
                    description, amount_decimal, counterparty, event_date_obj, reference, auto_post
                )
            elif event_type == "adjustment":
                return await self._record_adjustment_event(
                    description, amount_decimal, counterparty, event_date_obj, reference, auto_post
                )
            else:
                return f"❌ Invalid event_type. Use: expense|invoice|payment|transfer|adjustment"

        except Exception as e:
            return f"❌ Error recording business event: {str(e)}"

    async def _record_expense_event(self, description: str, amount: Decimal, counterparty: str,
                                   event_date: date, reference: Optional[str], auto_post: bool, vat_rate: Optional[float]) -> str:
        """Record expense with Swedish VAT compliance"""
        try:
            # Create voucher
            voucher_id = self.accounting.create_voucher(
                description=f"{description} - {counterparty}",
                voucher_type=VoucherType.PURCHASE,
                total_amount=amount,
                voucher_date=event_date,
                reference=reference
            )

            # Add VAT entries using AccountingService (handles Swedish compliance)
            if vat_rate is not None and vat_rate > 0:
                vat_rate_decimal = Decimal(str(vat_rate))
                vat_percentage = int(vat_rate * 100)

                # Use AccountingService method for Swedish VAT compliance
                vat_result = self.accounting.add_swedish_vat_entries(
                    voucher_id=voucher_id,
                    gross_amount=amount,
                    vat_rate=vat_rate_decimal,
                    net_account="6110",  # Office supplies/general expenses
                    vat_account="2640",  # Ingående moms (Input VAT)
                    net_description=f"{description} ex VAT",
                    vat_description=f"VAT {vat_percentage}%",
                    transaction_type="expense"
                )

                # Store for reporting
                net_amount = vat_result["net_amount"]
                vat_amount = vat_result["vat_amount"]
                vat_rounding_diff = vat_result["rounding_diff"]
                has_rounding = vat_result["has_rounding"]
            else:
                # VAT-exempt transaction
                vat_result = self.accounting.add_swedish_vat_entries(
                    voucher_id=voucher_id,
                    gross_amount=amount,
                    vat_rate=Decimal("0"),
                    net_account="6110",
                    vat_account="2640",  # Not used for zero VAT
                    net_description=description,
                    vat_description="",  # Not used
                    transaction_type="expense"
                )

                net_amount = amount
                vat_amount = Decimal('0')
                vat_rounding_diff = Decimal('0')
                has_rounding = False

            # Credit: Bank account (always full amount paid)
            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1930",  # Business bank account
                description=f"Payment to {counterparty}",
                credit_amount=amount
            )

            # Post voucher if requested
            if auto_post:
                self.accounting.post_voucher(voucher_id)
                status = "POSTED"
            else:
                status = "PENDING"

            # Format result with VAT information
            if vat_rate is not None and vat_rate > 0:
                vat_percentage = int(vat_rate * 100)
                booking_msg = f"DR 6110 (Expense): {net_amount:.2f} SEK + DR 2640 (VAT {vat_percentage}%): {vat_amount:.2f} SEK"
                if has_rounding:
                    rounding_type = "DR" if vat_rounding_diff > 0 else "CR"
                    booking_msg += f" + {rounding_type} 3740 (Rounding): {abs(vat_rounding_diff):.2f} SEK"
                booking_msg += f" = CR 1930 (Bank): {amount:.2f} SEK"
                return f"✅ Expense successfully processed and posted to ledger\nVoucher ID: {voucher_id} ({status})\nBooking: {booking_msg}"
            else:
                return f"✅ Expense successfully processed and posted to ledger\nVoucher ID: {voucher_id} ({status})\nBooking: DR 6110 (Expense): {amount:.2f} SEK = CR 1930 (Bank): {amount:.2f} SEK (VAT exempt)"

        except Exception as e:
            return f"❌ Error recording expense: {str(e)}"

    async def _record_invoice_event(self, description: str, amount: Decimal, counterparty: str,
                                   event_date: date, reference: Optional[str], invoice_id: Optional[int], auto_post: bool) -> str:
        """Record invoice/sales with Swedish VAT"""
        try:
            voucher_id = self.accounting.create_voucher(
                description=f"Invoice: {description} - {counterparty}",
                voucher_type=VoucherType.SALES_INVOICE,
                total_amount=amount,
                voucher_date=event_date,
                reference=reference,
                source_invoice_id=invoice_id
            )

            # Debit: Customer receivables (full amount)
            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1510",
                description=f"Invoice {counterparty}",
                debit_amount=amount
            )

            # Add VAT entries using AccountingService (handles Swedish compliance)
            vat_rate = Decimal('0.25')
            vat_result = self.accounting.add_swedish_vat_entries(
                voucher_id=voucher_id,
                gross_amount=amount,
                vat_rate=vat_rate,
                net_account="3001",  # Consulting revenue
                vat_account="2650",  # Utgående moms (Output VAT)
                net_description=f"{description} ex VAT",
                vat_description="VAT 25%",
                transaction_type="revenue"
            )

            net_amount = vat_result["net_amount"]
            vat_amount = vat_result["vat_amount"]
            has_rounding = vat_result["has_rounding"]
            rounding_diff = vat_result["rounding_diff"]

            if auto_post:
                self.accounting.post_voucher(voucher_id)
                status = "POSTED"
            else:
                status = "PENDING"

            result_msg = f"✅ Invoice recorded - Voucher ID: {voucher_id} ({status})\nNet: {net_amount:.2f} SEK, VAT: {vat_amount:.2f} SEK"
            if has_rounding:
                result_msg += f" (rounded), Rounding: {abs(rounding_diff):.2f} SEK"
            result_msg += f", Total: {amount:.2f} SEK"

            return result_msg

        except Exception as e:
            return f"❌ Error recording invoice: {str(e)}"

    async def _record_payment_event(self, description: str, amount: Decimal, counterparty: str,
                                   event_date: date, reference: Optional[str], invoice_id: Optional[int], auto_post: bool) -> str:
        """Record payment received"""
        try:
            voucher_id = self.accounting.create_voucher(
                description=f"Payment: {description} - {counterparty}",
                voucher_type=VoucherType.PAYMENT,
                total_amount=amount,
                voucher_date=event_date,
                reference=reference,
                source_invoice_id=invoice_id
            )

            # Debit: Bank account
            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1930",
                description=f"Payment from {counterparty}",
                debit_amount=amount
            )

            # Credit: Customer receivables
            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1510",
                description=f"Payment {counterparty}",
                credit_amount=amount
            )

            if auto_post:
                self.accounting.post_voucher(voucher_id)
                status = "POSTED"
            else:
                status = "PENDING"

            return f"✅ Payment recorded - Voucher ID: {voucher_id} ({status})\nAmount: {amount:.2f} SEK"

        except Exception as e:
            return f"❌ Error recording payment: {str(e)}"

    async def _record_transfer_event(self, description: str, amount: Decimal, counterparty: str,
                                    event_date: date, reference: Optional[str], auto_post: bool) -> str:
        """Record bank transfer or account transfer"""
        try:
            voucher_id = self.accounting.create_voucher(
                description=f"Transfer: {description} - {counterparty}",
                voucher_type=VoucherType.ADJUSTMENT,
                total_amount=amount,
                voucher_date=event_date,
                reference=reference
            )

            # Simple bank-to-bank transfer example
            # From main account to savings account
            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1940",  # Other bank accounts
                description=f"Transfer to {counterparty}",
                debit_amount=amount
            )

            self.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number="1930",  # Main bank account
                description=f"Transfer from main account",
                credit_amount=amount
            )

            if auto_post:
                self.accounting.post_voucher(voucher_id)
                status = "POSTED"
            else:
                status = "PENDING"

            return f"✅ Transfer recorded - Voucher ID: {voucher_id} ({status})\nAmount: {amount:.2f} SEK"

        except Exception as e:
            return f"❌ Error recording transfer: {str(e)}"

    async def _record_adjustment_event(self, description: str, amount: Decimal, counterparty: str,
                                      event_date: date, reference: Optional[str], auto_post: bool) -> str:
        """Record manual adjustment (requires manual journal entries)"""
        try:
            voucher_id = self.accounting.create_voucher(
                description=f"Adjustment: {description} - {counterparty}",
                voucher_type=VoucherType.ADJUSTMENT,
                total_amount=amount,
                voucher_date=event_date,
                reference=reference
            )

            # For adjustments, we don't auto-post since they need manual entries
            return f"✅ Adjustment voucher created - Voucher ID: {voucher_id} (PENDING)\nUse add_journal_entry to complete the adjustment\nAmount: {amount:.2f} SEK"

        except Exception as e:
            return f"❌ Error creating adjustment: {str(e)}"

    async def create_invoice(
        self,
        line_items: List[Dict[str, Any]],
        due_days: int = 30,
        notes: Optional[str] = None,
        customer_email: Optional[str] = None,
        recipient: Optional[Dict[str, Any]] = None,
        company: Optional[str] = None,
        vat_number: Optional[str] = None
    ) -> str:
        """Create a new invoice with line items

        Args:
            line_items: List of invoice line items
            due_days: Days until payment is due (default 30)
            notes: Optional invoice notes
            customer_email: Legacy parameter - customer email for simple invoicing
            recipient: Enhanced recipient object with full company details
            company: Company name for lookup
            vat_number: VAT number for lookup
        """
        try:
            # Validate parameters - must have either customer_email, recipient, or company+vat_number
            param_count = sum(1 for x in [customer_email, recipient, (company and vat_number)] if x)
            if param_count == 0:
                return "Error: Must provide either customer_email, recipient, or company+vat_number"
            if param_count > 1:
                return "Error: Cannot provide multiple customer identification methods"

            # Handle company+vat_number parameter (preferred)
            if company and vat_number:
                customer = self.db.get_customer_by_company_vat(company, vat_number)
                if not customer:
                    return f"Error: Customer with company '{company}' and VAT '{vat_number}' not found"

            # Handle legacy customer_email parameter
            elif customer_email:
                customer = self.db.get_customer_by_email(customer_email)
                if not customer:
                    return f"Error: Customer with email '{customer_email}' not found. Use company+vat_number for new customers."

            # Handle new recipient object parameter
            else:
                if recipient is None:
                    return "Error: recipient object cannot be None"

                company_name = recipient.get('company_name')
                vat_num = recipient.get('vat_number')
                if not company_name or not vat_num:
                    return "Error: recipient object must include company_name and vat_number fields"

                customer = self.db.get_customer_by_company_vat(company_name, vat_num)
                if not customer:
                    # Extract data from recipient object
                    name = recipient.get('contact_person', company_name)
                    address_obj = recipient.get('address', {})

                    customer = Customer(
                        name=name,
                        company=company_name,
                        vat_number=vat_num,
                        email=recipient.get('email'),
                        contact_person=recipient.get('contact_person'),
                        street=address_obj.get('street') if address_obj else None,
                        postal_code=address_obj.get('postal_code') if address_obj else None,
                        city=address_obj.get('city') if address_obj else None,
                        country=address_obj.get('country', 'Sweden') if address_obj else 'Sweden'
                    )
                    customer_id = self.db.create_customer(customer)
                    customer.id = customer_id
                else:
                    # Update existing customer with new recipient data if provided
                    updated = False
                    company_name = recipient.get('company_name')
                    if company_name and customer.company != company_name:
                        customer.company = company_name
                        updated = True

                    vat_number = recipient.get('vat_number')
                    if vat_number and customer.vat_number != vat_number:
                        customer.vat_number = vat_number
                        updated = True

                    contact_person = recipient.get('contact_person')
                    if contact_person and customer.contact_person != contact_person:
                        customer.contact_person = contact_person
                        updated = True

                    address_obj = recipient.get('address', {})
                    if address_obj:
                        street = address_obj.get('street')
                        if street and customer.street != street:
                            customer.street = street
                            updated = True

                        postal_code = address_obj.get('postal_code')
                        if postal_code and customer.postal_code != postal_code:
                            customer.postal_code = postal_code
                            updated = True

                        city = address_obj.get('city')
                        if city and customer.city != city:
                            customer.city = city
                            updated = True

                        country = address_obj.get('country')
                        if country and customer.country != country:
                            customer.country = country
                            updated = True

                    # Update customer in database if needed
                    if updated:
                        self.db.update_customer(customer)

            # Calculate dates
            issue_date = date.today()
            due_date = issue_date + timedelta(days=due_days)

            # Calculate totals
            subtotal = Decimal('0')
            invoice_line_items = []

            for item_data in line_items:
                quantity = Decimal(str(item_data['quantity']))
                unit_price = Decimal(str(item_data['unit_price']))
                total = quantity * unit_price
                subtotal += total

                invoice_line_items.append({
                    'description': item_data['description'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })

            # Calculate tax
            tax_rate = Decimal('0.25')  # 25% Swedish VAT
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount

            # Generate invoice number
            invoice_number = self.db.generate_invoice_number()

            # Ensure customer has a valid ID
            if customer.id is None:
                return "Error: Customer ID is required but not available"

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                customer_id=customer.id,
                issue_date=issue_date,
                due_date=due_date,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total=total_amount,
                notes=notes
            )

            invoice_id = self.db.create_invoice(invoice)
            invoice.id = invoice_id

            # Create line items
            for item_data in invoice_line_items:
                line_item = LineItem(
                    invoice_id=invoice_id,
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total=item_data['total']
                )
                self.db.create_line_item(line_item)

            return f"Invoice {invoice_number} created successfully with total {total_amount:.2f} kr (ID: {invoice_id})"

        except Exception as e:
            return f"Error creating invoice: {str(e)}"

    async def generate_pdf(self, invoice_id: int) -> str:
        """Generate PDF for an existing invoice"""
        try:
            # Get invoice
            invoice = self.db.get_invoice_by_id(invoice_id)
            if not invoice:
                return f"Invoice with ID {invoice_id} not found"

            # Get customer
            customer = self.db.get_customer_by_id(invoice.customer_id)
            if not customer:
                return f"Customer not found for invoice {invoice_id}"

            # Get line items
            line_items = self.db.get_line_items_by_invoice(invoice_id)

            # Generate PDF
            pdf_bytes = self.pdf_generator.generate_invoice_pdf(
                invoice, customer, line_items, self.company_info
            )

            # Save PDF
            filename = f"invoice_{invoice.invoice_number}.pdf"
            pdf_path = self.pdf_generator.save_pdf(pdf_bytes, filename)

            return f"PDF generated successfully: {pdf_path}"

        except Exception as e:
            return f"Error generating PDF: {str(e)}"


    async def update_invoice_status(self, invoice_id: int, status: str) -> str:
        """Update invoice status"""
        try:
            # Validate status
            try:
                invoice_status = InvoiceStatus(status.lower())
            except ValueError:
                valid_statuses = [s.value for s in InvoiceStatus]
                return f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}"

            # Update status
            success = self.db.update_invoice_status(invoice_id, invoice_status)
            if success:
                return f"Invoice {invoice_id} status updated to {status}"
            else:
                return f"Invoice with ID {invoice_id} not found"

        except Exception as e:
            return f"Error updating invoice status: {str(e)}"

    async def list_invoices(self, status: Optional[str] = None) -> str:
        """List invoices, optionally filtered by status"""
        try:
            invoices = self.db.list_invoices(status)

            if not invoices:
                status_filter = f" with status '{status}'" if status else ""
                return f"No invoices found{status_filter}"

            result = []
            for invoice in invoices:
                customer = self.db.get_customer_by_id(invoice.customer_id)
                result.append(
                    f"Invoice {invoice.invoice_number}: {customer.name if customer else 'Unknown'} - "
                    f"{invoice.total:.2f} kr ({invoice.status.value})"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error listing invoices: {str(e)}"

    async def get_invoice_details(self, invoice_id: int) -> str:
        """Get detailed invoice information"""
        try:
            invoice = self.db.get_invoice_by_id(invoice_id)
            if not invoice:
                return f"Invoice with ID {invoice_id} not found"

            customer = self.db.get_customer_by_id(invoice.customer_id)
            line_items = self.db.get_line_items_by_invoice(invoice_id)

            details = [
                f"Invoice: {invoice.invoice_number}",
                f"Customer: {customer.name if customer else 'Unknown'} ({customer.email if customer else 'N/A'})",
                f"Date: {invoice.issue_date}",
                f"Due: {invoice.due_date}",
                f"Status: {invoice.status.value}",
                f"Subtotal: {invoice.subtotal:.2f} kr",
                f"VAT ({invoice.tax_rate * 100:.0f}%): {invoice.tax_amount:.2f} kr",
                f"Total: {invoice.total:.2f} kr",
                "",
                "Line Items:"
            ]

            for item in line_items:
                details.append(
                    f"  - {item.description}: {item.quantity} × {item.unit_price:.2f} kr = {item.total:.2f} kr"
                )

            if invoice.notes:
                details.extend(["", f"Notes: {invoice.notes}"])

            return "\n".join(details)

        except Exception as e:
            return f"Error getting invoice details: {str(e)}"

    async def list_customers(self) -> str:
        """List all customers"""
        try:
            customers = self.db.list_customers()

            if not customers:
                return "No customers found"

            result = []
            for customer in customers:
                company_info = f" ({customer.company})" if customer.company else ""
                result.append(f"{customer.name}{company_info} - {customer.email}")

            return "\n".join(result)

        except Exception as e:
            return f"Error listing customers: {str(e)}"

    async def get_customer_by_email(self, email: str) -> str:
        """Get customer information by email"""
        try:
            customer = self.db.get_customer_by_email(email)
            if not customer:
                return f"Customer with email {email} not found"

            details = [
                f"Name: {customer.name}",
                f"Email: {customer.email}",
            ]

            if customer.company:
                details.append(f"Company: {customer.company}")
            if customer.address:
                details.append(f"Address: {customer.address}")
            if customer.org_number:
                details.append(f"Org Number: {customer.org_number}")
            if customer.vat_number:
                details.append(f"VAT Number: {customer.vat_number}")

            return "\n".join(details)

        except Exception as e:
            return f"Error getting customer: {str(e)}"

    async def check_overdue_invoices(self, grace_days: int = 5) -> str:
        """Check for overdue invoices that need payment reminders"""
        try:
            overdue_invoices = self.reminder_manager.find_overdue_invoices(grace_days)

            if not overdue_invoices:
                return "No overdue invoices found that need reminders"

            result = [f"Found {len(overdue_invoices)} overdue invoice(s):"]
            for invoice in overdue_invoices:
                customer = self.db.get_customer_by_id(invoice.customer_id)
                days_overdue = (date.today() - invoice.due_date).days
                result.append(
                    f"- Invoice {invoice.invoice_number}: {customer.name if customer else 'Unknown'} "
                    f"({days_overdue} days overdue, {invoice.reminder_count} reminders sent)"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error checking overdue invoices: {str(e)}"

    async def create_payment_reminder(
        self,
        invoice_id: int,
        customer_type: str = "business",
        reference_rate: float = 2.0
    ) -> str:
        """Create payment reminder with Swedish law calculations"""
        try:
            # Get invoice
            invoice = self.db.get_invoice_by_id(invoice_id)
            if not invoice:
                return f"Invoice with ID {invoice_id} not found"

            # Validate customer type
            try:
                cust_type = CustomerType(customer_type.lower())
            except ValueError:
                return "Invalid customer type. Use 'business' or 'consumer'"

            # Set up calculator with reference rate
            calculator = SwedishInterestCalculator(Decimal(str(reference_rate)))
            reminder_manager = PaymentReminderManager(self.db, calculator)

            # Create reminder
            reminder = reminder_manager.create_payment_reminder(invoice, cust_type)

            # Save to database
            reminder_id = reminder_manager.save_payment_reminder(reminder)
            reminder.id = reminder_id

            return (
                f"Payment reminder #{reminder.reminder_number} created for invoice {invoice.invoice_number}\n"
                f"Original amount: {reminder.original_amount:.2f} SEK\n"
                f"Interest ({reminder.interest_rate:.1f}%, {reminder.days_overdue} days): {reminder.interest_amount:.2f} SEK\n"
                f"Reminder fee: {reminder.reminder_fee:.2f} SEK\n"
                f"Delay compensation: {reminder.delay_compensation:.2f} SEK\n"
                f"Total amount due: {reminder.total_amount:.2f} SEK\n"
                f"Reminder ID: {reminder_id}"
            )

        except Exception as e:
            return f"Error creating payment reminder: {str(e)}"

    async def generate_reminder_pdf(self, reminder_id: int) -> str:
        """Generate PDF for a payment reminder"""
        try:
            # Get reminder
            reminder = self.db.get_payment_reminder_by_id(reminder_id)
            if not reminder:
                return f"Payment reminder with ID {reminder_id} not found"

            # Get related data
            invoice = self.db.get_invoice_by_id(reminder.invoice_id)
            if not invoice:
                return f"Original invoice not found for reminder {reminder_id}"

            customer = self.db.get_customer_by_id(invoice.customer_id)
            if not customer:
                return f"Customer not found for reminder {reminder_id}"

            # Generate PDF
            pdf_bytes = self.pdf_generator.generate_reminder_pdf(
                reminder, invoice, customer, self.company_info
            )

            # Save PDF
            filename = f"reminder_{invoice.invoice_number}_#{reminder.reminder_number}.pdf"
            pdf_path = self.pdf_generator.save_pdf(pdf_bytes, filename)

            # Update reminder status
            self.db.update_reminder_pdf_status(reminder_id, True)

            return f"Reminder PDF generated successfully: {pdf_path}"

        except Exception as e:
            return f"Error generating reminder PDF: {str(e)}"

    # Expense tracking methods
    async def add_expense(
        self,
        description: str,
        amount: float,
        category: str,
        expense_date: str,
        vat_rate: float = 0.25,
        notes: Optional[str] = None
    ) -> str:
        """Add a new business expense with VAT calculation"""
        try:
            # Validate category
            if category not in EXPENSE_CATEGORIES:
                valid_categories = list(EXPENSE_CATEGORIES.keys())
                return f"Invalid category. Valid categories are: {', '.join(valid_categories)}"

            # Parse date
            from datetime import datetime
            try:
                parsed_date = datetime.fromisoformat(expense_date).date()
            except ValueError:
                return "Invalid date format. Use YYYY-MM-DD format"

            # Calculate VAT amount
            total_amount = Decimal(str(amount))
            vat_rate_decimal = Decimal(str(vat_rate))

            # Amount includes VAT, so calculate VAT portion
            vat_amount = total_amount * vat_rate_decimal / (1 + vat_rate_decimal)

            # Create expense
            expense = Expense(
                description=description,
                amount=total_amount,
                vat_amount=vat_amount,
                vat_rate=vat_rate_decimal,
                category=category,
                expense_date=parsed_date,
                notes=notes
            )

            expense_id = self.db.create_expense(expense)

            return (
                f"Expense added successfully (ID: {expense_id})\n"
                f"Description: {description}\n"
                f"Category: {EXPENSE_CATEGORIES[category]}\n"
                f"Total amount: {total_amount:.2f} SEK\n"
                f"VAT amount: {vat_amount:.2f} SEK\n"
                f"Net amount: {(total_amount - vat_amount):.2f} SEK"
            )

        except Exception as e:
            return f"Error adding expense: {str(e)}"

    async def list_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """List expenses with optional filters"""
        try:
            # Parse dates if provided
            parsed_start_date = None
            parsed_end_date = None

            if start_date:
                from datetime import datetime
                try:
                    parsed_start_date = datetime.fromisoformat(start_date).date()
                except ValueError:
                    return "Invalid start_date format. Use YYYY-MM-DD format"

            if end_date:
                from datetime import datetime
                try:
                    parsed_end_date = datetime.fromisoformat(end_date).date()
                except ValueError:
                    return "Invalid end_date format. Use YYYY-MM-DD format"

            # Validate category if provided
            if category and category not in EXPENSE_CATEGORIES:
                valid_categories = list(EXPENSE_CATEGORIES.keys())
                return f"Invalid category. Valid categories are: {', '.join(valid_categories)}"

            expenses = self.db.list_expenses(category, parsed_start_date, parsed_end_date)

            if not expenses:
                filter_text = ""
                if category:
                    filter_text += f" in category '{category}'"
                if start_date or end_date:
                    date_filter = f" between {start_date or 'start'} and {end_date or 'end'}"
                    filter_text += date_filter
                return f"No expenses found{filter_text}"

            result = [f"Found {len(expenses)} expense(s):"]
            total_amount = Decimal('0')
            total_vat = Decimal('0')

            for expense in expenses:
                total_amount += expense.amount
                total_vat += expense.vat_amount
                category_name = EXPENSE_CATEGORIES.get(expense.category, expense.category)
                result.append(
                    f"- {expense.expense_date}: {expense.description} "
                    f"({category_name}) - {expense.amount:.2f} SEK"
                )

            result.extend([
                "",
                f"Total expenses: {total_amount:.2f} SEK",
                f"Total VAT: {total_vat:.2f} SEK",
                f"Net expenses: {(total_amount - total_vat):.2f} SEK"
            ])

            return "\n".join(result)

        except Exception as e:
            return f"Error listing expenses: {str(e)}"

    async def get_expense_details(self, expense_id: int) -> str:
        """Get detailed expense information"""
        try:
            expense = self.db.get_expense_by_id(expense_id)
            if not expense:
                return f"Expense with ID {expense_id} not found"

            category_name = EXPENSE_CATEGORIES.get(expense.category, expense.category)

            details = [
                f"Expense ID: {expense.id}",
                f"Description: {expense.description}",
                f"Category: {category_name} ({expense.category})",
                f"Date: {expense.expense_date}",
                f"Total amount: {expense.amount:.2f} SEK",
                f"VAT amount: {expense.vat_amount:.2f} SEK",
                f"Net amount: {(expense.amount - expense.vat_amount):.2f} SEK",
                f"VAT rate: {(expense.vat_rate * 100):.1f}%",
                f"Deductible: {'Yes' if expense.is_deductible else 'No'}"
            ]

            if expense.notes:
                details.append(f"Notes: {expense.notes}")

            if expense.receipt_image_path:
                details.append(f"Receipt: {expense.receipt_image_path}")

            return "\n".join(details)

        except Exception as e:
            return f"Error getting expense details: {str(e)}"

    async def generate_vat_report(self, quarter: int, year: int = 2025) -> str:
        """Generate VAT report for quarterly declaration"""
        try:
            if quarter not in [1, 2, 3, 4]:
                return "Quarter must be 1, 2, 3, or 4"

            if year < 2020 or year > 2030:
                return "Year must be between 2020 and 2030"

            report_data = self.db.get_vat_report_data(year, quarter)

            result = [
                f"VAT Report - Q{quarter} {year}",
                f"Period: {report_data['start_date']} to {report_data['end_date']}",
                "",
                "SALES (Försäljning):",
                f"  Invoices: {report_data['invoice_count']}",
                f"  Total sales (excl. VAT): {report_data['total_sales']:.2f} SEK",
                f"  Output VAT (utgående moms): {report_data['output_vat']:.2f} SEK",
                "",
                "PURCHASES (Inköp):",
                f"  Expenses: {report_data['expense_count']}",
                f"  Total purchases (excl. VAT): {report_data['total_purchases']:.2f} SEK",
                f"  Input VAT (ingående moms): {report_data['input_vat']:.2f} SEK",
                "",
                "SUMMARY:",
                f"  Output VAT: {report_data['output_vat']:.2f} SEK",
                f"  Input VAT: {report_data['input_vat']:.2f} SEK",
                f"  Net VAT to pay: {report_data['net_vat']:.2f} SEK"
            ]

            if report_data['net_vat'] < 0:
                result[-1] = f"  Net VAT to receive: {abs(report_data['net_vat']):.2f} SEK"

            return "\n".join(result)

        except Exception as e:
            return f"Error generating VAT report: {str(e)}"

    async def import_bank_csv(self, csv_data: str, account_type: str = "swedbank") -> str:
        """Import bank transactions from CSV export"""
        try:
            import csv
            import io
            from datetime import datetime

            # Parse CSV data
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            imported_count = 0

            for row in csv_reader:
                try:
                    # This is a basic CSV parser - would need to be customized for specific bank formats
                    # Assuming columns: date, amount, description, reference, counterparty, balance

                    # Parse date (adjust format as needed for different banks)
                    if account_type.lower() == "swedbank":
                        date_str = row.get('Datum', row.get('Date', ''))
                        amount_str = row.get('Belopp', row.get('Amount', ''))
                        description = row.get('Text', row.get('Description', ''))
                        reference = row.get('Referens', row.get('Reference', ''))
                        balance_str = row.get('Saldo', row.get('Balance', ''))
                    else:
                        # Generic format
                        date_str = row.get('date', row.get('Date', ''))
                        amount_str = row.get('amount', row.get('Amount', ''))
                        description = row.get('description', row.get('Description', ''))
                        reference = row.get('reference', row.get('Reference', ''))
                        balance_str = row.get('balance', row.get('Balance', ''))

                    if not date_str or not amount_str:
                        continue

                    # Parse date
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Parse amount
                    amount = Decimal(amount_str.replace(',', '.').replace(' ', ''))

                    # Determine transaction type
                    transaction_type = "incoming" if amount > 0 else "outgoing"

                    # Parse balance if available
                    balance = None
                    if balance_str:
                        try:
                            balance = Decimal(balance_str.replace(',', '.').replace(' ', ''))
                        except:
                            pass

                    # Create transaction
                    transaction = BankTransaction(
                        transaction_date=transaction_date,
                        amount=abs(amount),  # Store absolute value, type indicates direction
                        description=description,
                        reference=reference,
                        transaction_type=transaction_type,
                        account_balance=balance
                    )

                    # Save to database
                    self.db.create_bank_transaction(transaction)
                    imported_count += 1

                except Exception:
                    continue  # Skip problematic rows

            return f"Successfully imported {imported_count} bank transactions"

        except Exception as e:
            return f"Error importing bank CSV: {str(e)}"

    async def reconcile_payment(
        self,
        bank_transaction_id: int,
        invoice_id: Optional[int] = None,
        expense_id: Optional[int] = None,
        amount: Optional[float] = None
    ) -> str:
        """Match bank transaction with invoice payment or expense"""
        try:
            # Validate that either invoice_id or expense_id is provided
            if not invoice_id and not expense_id:
                return "Must specify either invoice_id or expense_id for reconciliation"

            if invoice_id and expense_id:
                return "Cannot specify both invoice_id and expense_id - choose one"

            # Get bank transaction
            transaction = self.db.get_bank_transaction_by_id(bank_transaction_id)
            if not transaction:
                return f"Bank transaction with ID {bank_transaction_id} not found"

            # Determine reconciliation type and amount
            reconciliation_type = "invoice_payment" if invoice_id else "expense_payment"
            reconciled_amount = Decimal(str(amount)) if amount else transaction.amount

            # Validate the referenced invoice or expense exists
            if invoice_id:
                invoice = self.db.get_invoice_by_id(invoice_id)
                if not invoice:
                    return f"Invoice with ID {invoice_id} not found"

            if expense_id:
                expense = self.db.get_expense_by_id(expense_id)
                if not expense:
                    return f"Expense with ID {expense_id} not found"

            # Create reconciliation
            reconciliation = Reconciliation(
                invoice_id=invoice_id,
                expense_id=expense_id,
                bank_transaction_id=bank_transaction_id,
                reconciled_amount=reconciled_amount,
                reconciliation_type=reconciliation_type
            )

            reconciliation_id = self.db.create_reconciliation(reconciliation)

            return (
                f"Reconciliation created successfully (ID: {reconciliation_id})\n"
                f"Bank transaction: {transaction.description} ({transaction.amount:.2f} SEK)\n"
                f"Matched with: {reconciliation_type.replace('_', ' ').title()}\n"
                f"Reconciled amount: {reconciled_amount:.2f} SEK"
            )

        except Exception as e:
            return f"Error creating reconciliation: {str(e)}"

    async def list_unmatched_transactions(self) -> str:
        """List bank transactions that haven't been reconciled yet"""
        try:
            transactions = self.db.get_unreconciled_transactions()

            if not transactions:
                return "No unmatched bank transactions found"

            result = [f"Found {len(transactions)} unmatched transaction(s):"]

            for transaction in transactions:
                type_symbol = "+" if transaction.transaction_type == "incoming" else "-"
                result.append(
                    f"- ID {transaction.id}: {transaction.transaction_date} "
                    f"{type_symbol}{transaction.amount:.2f} SEK - {transaction.description}"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error listing unmatched transactions: {str(e)}"

    async def generate_vat_report_pdf(self, quarter: int, year: int = 2025) -> str:
        """Generate VAT report PDF for quarterly declaration"""
        try:
            if quarter not in [1, 2, 3, 4]:
                return "Quarter must be 1, 2, 3, or 4"

            if year < 2020 or year > 2030:
                return "Year must be between 2020 and 2030"

            # Get VAT report data
            report_data = self.db.get_vat_report_data(year, quarter)

            # Get detailed invoice and expense data for the period
            from datetime import date
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2

            if end_month == 12:
                end_day = 31
            elif end_month in [4, 6, 9, 11]:
                end_day = 30
            else:
                end_day = 31

            start_date = date(year, start_month, 1)
            end_date = date(year, end_month, end_day)

            # Get invoices for the period
            invoices = self.db.list_invoices()
            period_invoices = []
            for invoice in invoices:
                if (invoice.issue_date >= start_date and
                    invoice.issue_date <= end_date and
                    invoice.status.value != 'draft'):
                    customer = self.db.get_customer_by_id(invoice.customer_id)
                    period_invoices.append({
                        'invoice_number': invoice.invoice_number,
                        'customer_name': customer.name if customer else 'Unknown',
                        'issue_date': invoice.issue_date,
                        'subtotal': invoice.subtotal,
                        'tax_amount': invoice.tax_amount,
                        'total': invoice.total
                    })

            # Get expenses for the period
            expenses = self.db.list_expenses(start_date=start_date, end_date=end_date)
            period_expenses = []
            expenses_by_category = {}

            for expense in expenses:
                if expense.is_deductible:
                    category_name = EXPENSE_CATEGORIES.get(expense.category, expense.category)

                    period_expenses.append({
                        'expense_date': expense.expense_date,
                        'description': expense.description,
                        'category': expense.category,
                        'category_name': category_name,
                        'amount': expense.amount,
                        'vat_amount': expense.vat_amount
                    })

                    # Group by category
                    if expense.category not in expenses_by_category:
                        expenses_by_category[expense.category] = {
                            'category_name': category_name,
                            'count': 0,
                            'total_amount': Decimal('0'),
                            'vat_amount': Decimal('0'),
                            'net_amount': Decimal('0')
                        }

                    cat_data = expenses_by_category[expense.category]
                    cat_data['count'] += 1
                    cat_data['total_amount'] += expense.amount
                    cat_data['vat_amount'] += expense.vat_amount
                    cat_data['net_amount'] += (expense.amount - expense.vat_amount)

            # Generate PDF
            pdf_bytes = self.pdf_generator.generate_vat_report_pdf(
                report_data=report_data,
                company_info=self.company_info,
                invoices=period_invoices,
                expenses=period_expenses,
                expenses_by_category=expenses_by_category
            )

            # Save PDF
            filename = f"vat_report_Q{quarter}_{year}.pdf"
            pdf_path = self.pdf_generator.save_pdf(pdf_bytes, filename)

            return f"VAT report PDF generated successfully: {pdf_path}"

        except Exception as e:
            return f"Error generating VAT report PDF: {str(e)}"


# Initialize the MCP server
mcp = FastMCP("Invoice Generator")
invoice_server = InvoiceServer()

# CONSOLIDATED TOOLBOX - 8 POWERFUL TOOLS

@mcp.tool()
async def record_business_event(
    event_type: str,
    description: str,
    amount: float,
    counterparty: str,
    event_date: Optional[str] = None,
    reference: Optional[str] = None,
    invoice_id: Optional[int] = None,
    expense_id: Optional[int] = None,
    auto_post: bool = True,
    vat_rate: Optional[float] = None
) -> str:
    """Universal business event recorder with Swedish compliance

    Args:
        event_type: expense|invoice|payment|transfer|adjustment
        description: Detailed business description (Swedish legal requirement)
        amount: Total amount in SEK
        counterparty: Business partner (Swedish legal requirement)
        event_date: When event occurred (YYYY-MM-DD, defaults to today)
        reference: External reference (invoice number, receipt, etc.)
        invoice_id: Link to existing invoice (for payments)
        expense_id: Link to existing expense
        auto_post: Automatically post voucher (default: True)
        vat_rate: Swedish VAT rate (0.25, 0.12, 0.06, 0.0) - defaults to None (must specify for VAT)

    Examples:
        record_business_event("expense", "HP printer ink cartridges", 1250.00, "Staples Sverige AB", vat_rate=0.25)  # 25% VAT
        record_business_event("expense", "Business dinner", 800.00, "Restaurant AB", vat_rate=0.12)                  # 12% VAT
        record_business_event("expense", "Industry magazine", 200.00, "Publisher", vat_rate=0.06)                    # 6% VAT
        record_business_event("expense", "AWS services", 500.00, "Amazon Web Services", vat_rate=0.0)                # 0% VAT
        record_business_event("payment", "Bank transfer", 5000.00, "Supplier AB")                                    # No VAT (default)
    """
    return await invoice_server.record_business_event(event_type, description, amount, counterparty, event_date, reference, invoice_id, expense_id, auto_post, vat_rate)

@mcp.tool()
async def manage_invoice(
    action: str,
    invoice_id: Optional[int] = None,
    line_items: Optional[List[Dict[str, Any]]] = None,
    due_days: int = 30,
    notes: Optional[str] = None,
    customer_email: Optional[str] = None,
    recipient: Optional[Dict[str, Any]] = None,
    company: Optional[str] = None,
    vat_number: Optional[str] = None,
    status: Optional[str] = None,
    grace_days: int = 5
) -> str:
    """Complete invoice lifecycle management

    Args:
        action: create|update_status|check_overdue|get_details
        invoice_id: Invoice ID (for update_status, get_details)
        line_items: Invoice line items (for create)
        due_days: Payment terms in days (for create)
        notes: Invoice notes (for create)
        customer_email: Customer email (for create)
        recipient: Full customer object (for create)
        company: Company name (for create)
        vat_number: VAT number (for create)
        status: New status (for update_status: draft|sent|paid|overdue|cancelled)
        grace_days: Grace period for overdue check (for check_overdue)

    Examples:
        manage_invoice("create", line_items=[...], company="Acme Corp", vat_number="SE123")
        manage_invoice("update_status", invoice_id=123, status="paid")
        manage_invoice("check_overdue", grace_days=7)
    """
    if action == "create":
        return await invoice_server.create_invoice(line_items, due_days, notes, customer_email, recipient, company, vat_number)
    elif action == "update_status":
        return await invoice_server.update_invoice_status(invoice_id, status)
    elif action == "check_overdue":
        return await invoice_server.check_overdue_invoices(grace_days)
    elif action == "get_details":
        return await invoice_server.get_invoice_details(invoice_id)
    else:
        return "❌ Invalid action. Use: create|update_status|check_overdue|get_details"

@mcp.tool()
async def manage_payment(
    action: str,
    invoice_id: Optional[int] = None,
    customer_type: str = "business",
    reference_rate: float = 2.0,
    reminder_id: Optional[int] = None,
    bank_transaction_id: Optional[int] = None,
    expense_id: Optional[int] = None,
    amount: Optional[float] = None
) -> str:
    """Payment processing and reminders

    Args:
        action: create_reminder|reconcile|list_unmatched
        invoice_id: Invoice needing reminder or payment (for create_reminder, reconcile)
        customer_type: business|consumer (for create_reminder)
        reference_rate: Swedish interest rate % (for create_reminder)
        reminder_id: Reminder ID (for actions requiring it)
        bank_transaction_id: Bank transaction to reconcile
        expense_id: Expense to reconcile with transaction
        amount: Override reconciliation amount

    Examples:
        manage_payment("create_reminder", invoice_id=123, customer_type="business")
        manage_payment("reconcile", bank_transaction_id=456, invoice_id=123)
        manage_payment("list_unmatched")
    """
    if action == "create_reminder":
        return await invoice_server.create_payment_reminder(invoice_id, customer_type, reference_rate)
    elif action == "reconcile":
        return await invoice_server.reconcile_payment(bank_transaction_id, invoice_id, expense_id, amount)
    elif action == "list_unmatched":
        return await invoice_server.list_unmatched_transactions()
    else:
        return "❌ Invalid action. Use: create_reminder|reconcile|list_unmatched"

@mcp.tool()
async def manage_customer(
    action: str = "list",
    email: Optional[str] = None
) -> str:
    """Customer operations

    Args:
        action: list|get_details
        email: Customer email (for get_details)

    Examples:
        manage_customer("list")
        manage_customer("get_details", email="john@company.com")
    """
    if action == "list":
        return await invoice_server.list_customers()
    elif action == "get_details":
        return await invoice_server.get_customer_by_email(email)
    else:
        return "❌ Invalid action. Use: list|get_details"

@mcp.tool()
async def manage_banking(
    action: str,
    csv_data: Optional[str] = None,
    account_type: str = "swedbank",
    quarter: Optional[int] = None,
    year: int = 2025
) -> str:
    """Bank integration and VAT reporting

    Args:
        action: import_csv|vat_report|vat_report_pdf
        csv_data: CSV content from bank export (for import_csv)
        account_type: Bank type - swedbank|seb|etc (for import_csv)
        quarter: Quarter 1-4 (for vat_report, vat_report_pdf)
        year: Report year (for vat_report, vat_report_pdf)

    Examples:
        manage_banking("import_csv", csv_data="Date,Amount,Description...", account_type="swedbank")
        manage_banking("vat_report", quarter=3, year=2025)
        manage_banking("vat_report_pdf", quarter=3, year=2025)
    """
    if action == "import_csv":
        return await invoice_server.import_bank_csv(csv_data, account_type)
    elif action == "vat_report":
        return await invoice_server.generate_vat_report(quarter, year)
    elif action == "vat_report_pdf":
        return await invoice_server.generate_vat_report_pdf(quarter, year)
    else:
        return "❌ Invalid action. Use: import_csv|vat_report|vat_report_pdf"

@mcp.tool()
async def generate_report(
    report_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    as_of_date: Optional[str] = None,
    detailed: bool = True,
    period_analysis: bool = True,
    period_only: bool = False,
    include_superseded: bool = False,
    security_audit: bool = False
) -> str:
    """Financial statements and reports

    Args:
        report_type: trial_balance|income_statement|balance_sheet
        start_date: Period start (YYYY-MM-DD) for income_statement, balance_sheet
        end_date: Period end (YYYY-MM-DD) for income_statement
        as_of_date: Balance date (YYYY-MM-DD) for balance_sheet, trial_balance
        detailed: Show account codes and enhanced formatting
        period_analysis: Show opening/period/closing columns (balance_sheet, trial_balance)
        period_only: Show only period changes (balance_sheet)
        include_superseded: Include superseded vouchers (trial_balance)
        security_audit: Include security audit info (trial_balance)

    Examples:
        generate_report("trial_balance")
        generate_report("income_statement", start_date="2025-01-01", end_date="2025-03-31")
        generate_report("balance_sheet", as_of_date="2025-03-31", start_date="2025-01-01")
    """
    try:
        if report_type == "trial_balance":
            from datetime import date

            # Parse dates if provided
            as_of_date_obj = date.fromisoformat(as_of_date) if as_of_date else None
            start_date_obj = date.fromisoformat(start_date) if start_date else None

            # Always use the standard method for now (enhanced method may have different structure)
            trial_balance = invoice_server.accounting.generate_trial_balance(
                as_of_date=as_of_date_obj,
                include_superseded=include_superseded,
                security_audit=security_audit
            )

            result = ["TRIAL BALANCE", "=" * 60]
            result.append(f"{'Account':<10} {'Name':<30} {'Debit':>12} {'Credit':>12}")
            result.append("-" * 60)

            for account in trial_balance["accounts"]:
                debit_str = f"{account['debit_balance']:,.2f}" if account['debit_balance'] > 0 else ""
                credit_str = f"{account['credit_balance']:,.2f}" if account['credit_balance'] > 0 else ""
                result.append(
                    f"{account['account_number']:<10} {account['account_name'][:30]:<30} "
                    f"{debit_str:>12} {credit_str:>12}"
                )

            result.append("-" * 60)
            result.append(
                f"{'TOTALS':<40} "
                f"{trial_balance['totals']['debit']:>12,.2f} "
                f"{trial_balance['totals']['credit']:>12,.2f}"
            )

            balanced = "✅ BALANCED" if trial_balance["balanced"] else "❌ UNBALANCED"
            result.append(f"\n{balanced}")

            return "\n".join(result)

        elif report_type == "income_statement":
            from datetime import date

            if not start_date or not end_date:
                return "❌ Income statement requires start_date and end_date"

            start_date_obj = date.fromisoformat(start_date)
            end_date_obj = date.fromisoformat(end_date)

            income_statement = invoice_server.accounting.generate_income_statement(
                start_date_obj, end_date_obj, detailed=detailed
            )

            result = [
                "INCOME STATEMENT (Resultaträkning)",
                f"Period: {start_date} to {end_date}",
                "=" * 50,
                "",
                "REVENUE:",
            ]

            for account in income_statement.revenue_accounts:
                if detailed and account[2] != 0:  # Only non-zero if detailed
                    result.append(f"  {account[0]:<8} {account[1][:30]:<30} {account[2]:>12.2f}")
                elif not detailed:
                    result.append(f"  {account[1]:<30} {account[2]:>12.2f}")

            result.extend([
                "-" * 50,
                f"Total Revenue: {income_statement.revenue:>26.2f}",
                "",
                "EXPENSES:",
            ])

            for account in income_statement.expense_accounts:
                if detailed and account[2] != 0:  # Only non-zero if detailed
                    result.append(f"  {account[0]:<8} {account[1][:30]:<30} {account[2]:>12.2f}")
                elif not detailed:
                    result.append(f"  {account[1]:<30} {account[2]:>12.2f}")

            result.extend([
                "-" * 50,
                f"Total Expenses: {income_statement.expenses:>25.2f}",
                "",
                "=" * 50,
                f"NET INCOME: {income_statement.net_income:>29.2f}",
                "=" * 50
            ])

            return "\n".join(result)

        elif report_type == "balance_sheet":
            from datetime import date

            as_of_date_obj = date.fromisoformat(as_of_date) if as_of_date else None
            start_date_obj = date.fromisoformat(start_date) if start_date else None

            balance_sheet = invoice_server.accounting.generate_balance_sheet(
                as_of_date=as_of_date_obj,
                start_date=start_date_obj,
                detailed=detailed
            )

            result = [
                "BALANCE SHEET (Balansräkning)",
                f"As of: {balance_sheet.period_end}",
                "=" * 50,
                "",
                "ASSETS:",
            ]

            for account in balance_sheet.assets:
                if detailed and len(account) > 2 and account[2] != 0:
                    result.append(f"  {account[0]:<8} {account[1][:30]:<30} {account[2]:>12.2f}")
                elif not detailed:
                    result.append(f"  {account[1]:<30} {account[2]:>12.2f}")

            result.extend([
                "-" * 50,
                f"Total Assets: {balance_sheet.total_assets:>27.2f}",
                "",
                "LIABILITIES:",
            ])

            for account in balance_sheet.liabilities:
                if detailed and len(account) > 2 and account[2] != 0:
                    result.append(f"  {account[0]:<8} {account[1][:30]:<30} {account[2]:>12.2f}")
                elif not detailed:
                    result.append(f"  {account[1]:<30} {account[2]:>12.2f}")

            result.extend([
                "-" * 50,
                f"Total Liabilities: {balance_sheet.total_liabilities:>21.2f}",
                "",
                "EQUITY:",
            ])

            for account in balance_sheet.equity:
                if detailed and len(account) > 2 and account[2] != 0:
                    result.append(f"  {account[0]:<8} {account[1][:30]:<30} {account[2]:>12.2f}")
                elif not detailed:
                    result.append(f"  {account[1]:<30} {account[2]:>12.2f}")

            result.extend([
                "-" * 50,
                f"Total Equity: {balance_sheet.total_equity:>25.2f}",
                "",
                "=" * 50,
                f"TOTAL LIAB. + EQUITY: {balance_sheet.total_liabilities + balance_sheet.total_equity:>14.2f}",
                "=" * 50
            ])

            return "\n".join(result)

        else:
            return "❌ Invalid report_type. Use: trial_balance|income_statement|balance_sheet"

    except Exception as e:
        return f"❌ Error generating {report_type}: {str(e)}"

@mcp.tool()
async def generate_pdf(
    document_type: str,
    document_id: int,
    quarter: Optional[int] = None,
    year: Optional[int] = None
) -> str:
    """Universal document generation

    Args:
        document_type: invoice|reminder|vat_report
        document_id: Invoice ID, reminder ID (not used for vat_report)
        quarter: Quarter 1-4 (for vat_report)
        year: Year (for vat_report)

    Examples:
        generate_pdf("invoice", document_id=123)
        generate_pdf("reminder", document_id=456)
        generate_pdf("vat_report", document_id=0, quarter=3, year=2025)
    """
    if document_type == "invoice":
        return await invoice_server.generate_pdf(document_id)
    elif document_type == "reminder":
        return await invoice_server.generate_reminder_pdf(document_id)
    elif document_type == "vat_report":
        return await invoice_server.generate_vat_report_pdf(quarter or 1, year or 2025)
    else:
        return "❌ Invalid document_type. Use: invoice|reminder|vat_report"

@mcp.tool()
async def get_guidance(
    topic: Optional[str] = None,
    depth: str = "essentials",
    category: Optional[str] = None,
    workflow_name: Optional[str] = None,
    compliance_topic: Optional[str] = None
) -> str:
    """Documentation, workflows, and Swedish compliance guidance

    Args:
        topic: Specific tool or topic for documentation
        depth: essentials|full (for documentation)
        category: invoicing|expenses|accounting|reporting (for documentation)
        workflow_name: invoice_to_payment|expense_recording|monthly_closing (for workflows)
        compliance_topic: vat_reporting|invoice_requirements|audit_trail (for compliance)

    Examples:
        get_guidance()  # General overview
        get_guidance(topic="record_business_event", depth="full")
        get_guidance(workflow_name="invoice_to_payment")
        get_guidance(compliance_topic="vat_reporting")
    """
    if workflow_name:
        return invoice_server.documentation.get_workflow_guide(workflow_name)
    elif compliance_topic:
        return invoice_server.documentation.get_compliance_info(compliance_topic)
    else:
        return invoice_server.documentation.get_documentation(topic, depth, category)

# Keep only audit tools that aren't consolidated
@mcp.tool()
async def audit_voucher(
    action: str,
    voucher_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_superseded: bool = False,
    voucher_type: Optional[str] = None,
    original_voucher_id: Optional[int] = None,
    replacement_voucher_id: Optional[int] = None,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
    totp_code: Optional[str] = None,
    annotation_type: Optional[str] = None,
    message: Optional[str] = None,
    related_voucher_id: Optional[int] = None
) -> str:
    """Voucher audit operations with TOTP security

    Args:
        action: history|list_period|supersede|add_annotation
        voucher_id: Target voucher ID (for history, supersede, add_annotation)
        start_date: Period start (YYYY-MM-DD) for list_period
        end_date: Period end (YYYY-MM-DD) for list_period
        include_superseded: Include superseded vouchers for list_period
        voucher_type: Filter by type for list_period
        original_voucher_id: Voucher being replaced (for supersede)
        replacement_voucher_id: Replacement voucher (for supersede)
        reason: Business justification (for supersede, add_annotation)
        user_id: User email (for supersede, add_annotation)
        totp_code: 6-digit TOTP or 8-digit backup code (for supersede, add_annotation)
        annotation_type: CORRECTION|REVERSAL|NOTE (for add_annotation)
        message: Annotation message (for add_annotation)
        related_voucher_id: Related voucher (for add_annotation)

    Examples:
        audit_voucher("history", voucher_id=123)
        audit_voucher("list_period", start_date="2025-01-01", end_date="2025-01-31")
        audit_voucher("supersede", original_voucher_id=21, replacement_voucher_id=22, reason="Balance error", user_id="user@example.com", totp_code="123456")
    """
    if action == "history":
        return await get_voucher_history(voucher_id)
    elif action == "list_period":
        return await list_vouchers_by_period(start_date, end_date, include_superseded, voucher_type)
    elif action == "supersede":
        return await supersede_voucher(original_voucher_id, replacement_voucher_id, reason, user_id, totp_code)
    elif action == "add_annotation":
        return await add_secure_voucher_annotation(voucher_id, annotation_type, message, user_id, totp_code, related_voucher_id)
    else:
        return "❌ Invalid action. Use: history|list_period|supersede|add_annotation"

# Register resources
@mcp.resource("invoices://list")
async def list_invoices() -> str:
    """List all invoices"""
    return await invoice_server.list_invoices()

@mcp.resource("invoices://list/{status}")
async def list_invoices_by_status(status: str) -> str:
    """List invoices filtered by status"""
    return await invoice_server.list_invoices(status)

@mcp.resource("invoice://{invoice_id}")
async def get_invoice_details(invoice_id: int) -> str:
    """Get detailed invoice information"""
    return await invoice_server.get_invoice_details(invoice_id)

@mcp.resource("customers://list")
async def list_customers() -> str:
    """List all customers"""
    return await invoice_server.list_customers()

@mcp.resource("customer://{email}")
async def get_customer_by_email(email: str) -> str:
    """Get customer information by email"""
    return await invoice_server.get_customer_by_email(email)

# Expense tracking resources
@mcp.resource("expenses://list")
async def list_all_expenses() -> str:
    """List all expenses"""
    return await invoice_server.list_expenses()

@mcp.resource("expenses://list/{category}")
async def list_expenses_by_category(category: str) -> str:
    """List expenses filtered by category"""
    return await invoice_server.list_expenses(category=category)

@mcp.resource("expenses://quarter/{year}/{quarter}")
async def quarterly_expenses(year: int, quarter: int) -> str:
    """Get expenses for specific quarter"""
    from datetime import date

    # Calculate quarter dates
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2

    if end_month == 12:
        end_day = 31
    elif end_month in [4, 6, 9, 11]:
        end_day = 30
    else:
        end_day = 31

    start_date = date(year, start_month, 1)
    end_date = date(year, end_month, end_day)

    return await invoice_server.list_expenses(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

@mcp.resource("expense://{expense_id}")
async def get_expense_details(expense_id: int) -> str:
    """Get detailed expense information"""
    return await invoice_server.get_expense_details(expense_id)

@mcp.resource("vat://report/{year}/{quarter}")
async def vat_report_data(year: int, quarter: int) -> str:
    """VAT report data for specific quarter"""
    return await invoice_server.generate_vat_report(quarter, year)

@mcp.resource("reconciliation://unmatched")
async def unmatched_transactions() -> str:
    """List bank transactions not yet reconciled"""
    return await invoice_server.list_unmatched_transactions()


# End of consolidated toolbox


def main():
    """Entry point for uvx"""
    mcp.run()


if __name__ == "__main__":
    main()
