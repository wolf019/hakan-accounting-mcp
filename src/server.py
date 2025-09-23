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

# Register tools
@mcp.tool()
async def create_invoice(
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
        line_items: List of invoice line items with description, quantity, unit_price
        due_days: Days until payment is due (default 30)
        notes: Optional notes for the invoice
        customer_email: (Legacy) Customer email address for simple invoicing
        recipient: Enhanced recipient object with full company details:
            {
                "company_name": "Company AB",
                "contact_person": "John Doe",
                "email": "john@company.com",
                "address": {
                    "street": "Street 123",
                    "postal_code": "12345",
                    "city": "Stockholm",
                    "country": "Sweden"
                },
                "vat_number": "SE123456789"
            }
        company: Company name for customer lookup (preferred method)
        vat_number: VAT number for customer lookup (must be used with company)

    Note: Provide either customer_email, recipient, or company+vat_number.
    """
    return await invoice_server.create_invoice(line_items, due_days, notes, customer_email, recipient, company, vat_number)

@mcp.tool()
async def list_customers() -> str:
    """List all customers in the database"""
    try:
        customers = invoice_server.db.list_customers()

        if not customers:
            return "No customers found in the database"

        result = [f"Found {len(customers)} customer(s):"]

        for customer in customers:
            result.append(f"\n- {customer.name}")
            result.append(f"  Company: {customer.company}")
            result.append(f"  VAT Number: {customer.vat_number}")
            if customer.email:
                result.append(f"  Email: {customer.email}")
            if customer.contact_person:
                result.append(f"  Contact: {customer.contact_person}")
            formatted_address = customer.get_formatted_address()
            if formatted_address:
                result.append(f"  Address: {formatted_address}")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing customers: {str(e)}"

@mcp.tool()
async def generate_pdf(invoice_id: int) -> str:
    """Generate PDF for an existing invoice"""
    return await invoice_server.generate_pdf(invoice_id)


@mcp.tool()
async def update_invoice_status(invoice_id: int, status: str) -> str:
    """Update invoice status (draft, sent, paid, overdue)"""
    return await invoice_server.update_invoice_status(invoice_id, status)

@mcp.tool()
async def check_overdue_invoices(grace_days: int = 5) -> str:
    """Check for overdue invoices that need payment reminders"""
    return await invoice_server.check_overdue_invoices(grace_days)

@mcp.tool()
async def create_payment_reminder(
    invoice_id: int,
    customer_type: str = "business",
    reference_rate: float = 2.0
) -> str:
    """Create payment reminder with Swedish law calculations"""
    return await invoice_server.create_payment_reminder(invoice_id, customer_type, reference_rate)

@mcp.tool()
async def generate_reminder_pdf(reminder_id: int) -> str:
    """Generate PDF for a payment reminder"""
    return await invoice_server.generate_reminder_pdf(reminder_id)

# Expense tracking tools
@mcp.tool()
async def add_expense(
    description: str,
    amount: float,
    category: str,
    expense_date: str,
    vat_rate: float = 0.25,
    notes: Optional[str] = None
) -> str:
    """Add a new business expense with VAT calculation

    Args:
        description: What was purchased/paid for
        amount: Total amount including VAT
        category: Expense category (office_supplies, software, hosting_cloud, travel, meals_client, education, equipment, phone_internet, insurance, accounting, marketing, office_rent, other)
        expense_date: Date of expense (YYYY-MM-DD)
        vat_rate: VAT rate (0.25 for 25%, 0.12 for 12%, etc.)
        notes: Optional additional notes

    Returns:
        Success message with expense ID and VAT details
    """
    return await invoice_server.add_expense(description, amount, category, expense_date, vat_rate, notes)

@mcp.tool()
async def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """List expenses with optional filters

    Args:
        category: Filter by expense category (optional)
        start_date: Start date filter (YYYY-MM-DD, optional)
        end_date: End date filter (YYYY-MM-DD, optional)

    Returns:
        List of expenses with totals
    """
    return await invoice_server.list_expenses(category, start_date, end_date)

@mcp.tool()
async def generate_vat_report(quarter: int, year: int = 2025) -> str:
    """Generate VAT report for quarterly declaration to Skatteverket

    Args:
        quarter: Quarter number (1-4)
        year: Year for report

    Returns:
        VAT report summary with amounts for declaration
    """
    return await invoice_server.generate_vat_report(quarter, year)

@mcp.tool()
async def import_bank_csv(csv_data: str, account_type: str = "swedbank") -> str:
    """Import bank transactions from CSV export

    Args:
        csv_data: CSV content from bank export
        account_type: Bank type for parsing format (swedbank, seb, etc.)

    Returns:
        Import summary with transaction count
    """
    return await invoice_server.import_bank_csv(csv_data, account_type)

@mcp.tool()
async def reconcile_payment(
    bank_transaction_id: int,
    invoice_id: Optional[int] = None,
    expense_id: Optional[int] = None,
    amount: Optional[float] = None
) -> str:
    """Match bank transaction with invoice payment or expense

    Args:
        bank_transaction_id: Bank transaction to match
        invoice_id: Invoice that was paid (for incoming payments)
        expense_id: Expense that was paid (for outgoing payments)
        amount: Override amount if partial payment

    Returns:
        Reconciliation confirmation
    """
    return await invoice_server.reconcile_payment(bank_transaction_id, invoice_id, expense_id, amount)

@mcp.tool()
async def generate_vat_report_pdf(quarter: int, year: int = 2025) -> str:
    """Generate VAT report PDF for quarterly declaration to Skatteverket

    Args:
        quarter: Quarter number (1-4)
        year: Year for report

    Returns:
        Path to generated VAT report PDF
    """
    return await invoice_server.generate_vat_report_pdf(quarter, year)

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


# Accounting MCP Tools

@mcp.tool()
async def create_voucher(
    description: str,
    voucher_type: str,
    total_amount: float,
    voucher_date: Optional[str] = None
) -> str:
    """Create accounting voucher with automatic journal entries"""
    try:
        from datetime import date
        from decimal import Decimal
        
        # Parse voucher type
        try:
            voucher_type_enum = VoucherType(voucher_type)
        except ValueError:
            return f"Invalid voucher type. Valid types: {[vt.value for vt in VoucherType]}"
        
        # Parse date
        if voucher_date:
            try:
                voucher_date_obj = date.fromisoformat(voucher_date)
            except ValueError:
                return "Invalid date format. Use YYYY-MM-DD format"
        else:
            voucher_date_obj = None
        
        voucher_id = invoice_server.accounting.create_voucher(
            description=description,
            voucher_type=voucher_type_enum,
            total_amount=Decimal(str(total_amount)),
            voucher_date=voucher_date_obj
        )
        
        return f"Voucher created successfully (ID: {voucher_id})"
        
    except Exception as e:
        return f"Error creating voucher: {str(e)}"


@mcp.tool()
async def add_journal_entry(
    voucher_identifier: str,
    account_number: str,
    description: str,
    debit_amount: float = 0,
    credit_amount: float = 0
) -> str:
    """Add journal entry to a voucher
    
    Args:
        voucher_identifier: Either voucher number (V001, V002, etc.) or voucher ID as string
        account_number: Account number (1510, 3001, etc.)
        description: Description of the journal entry
        debit_amount: Debit amount (default: 0)
        credit_amount: Credit amount (default: 0)
    
    Returns:
        Success or error message
    """
    try:
        from decimal import Decimal
        from src.models.accounting_models import ValidationError
        
        # Resolve voucher identifier to ID
        voucher_id = invoice_server.accounting.resolve_voucher_identifier(voucher_identifier)
        if not voucher_id:
            return f"❌ Voucher {voucher_identifier} does not exist"
        
        try:
            entry_id = invoice_server.accounting.add_journal_entry(
                voucher_id=voucher_id,
                account_number=account_number,
                description=description,
                debit_amount=Decimal(str(debit_amount)),
                credit_amount=Decimal(str(credit_amount))
            )
            
            return f"✅ Journal entry added successfully to {voucher_identifier} (Entry ID: {entry_id})"
            
        except ValidationError as ve:
            # Return the validation error message directly
            return str(ve)
        
    except Exception as e:
        return f"❌ Error adding journal entry: {str(e)}"


@mcp.tool()
async def post_voucher(voucher_identifier: str) -> str:
    """Post voucher and update account balances
    
    Args:
        voucher_identifier: Either voucher number (V001, V002, etc.) or voucher ID as string
    
    Returns:
        Success or error message
    """
    try:
        # Resolve voucher identifier to ID
        voucher_id = invoice_server.accounting.resolve_voucher_identifier(voucher_identifier)
        if not voucher_id:
            return f"❌ Voucher {voucher_identifier} does not exist"
        
        success = invoice_server.accounting.post_voucher(voucher_id)
        if success:
            return f"✅ Voucher {voucher_identifier} (ID: {voucher_id}) posted successfully"
        else:
            return f"❌ Failed to post voucher {voucher_identifier}"
            
    except Exception as e:
        return f"❌ Error posting voucher: {str(e)}"


@mcp.tool()
async def get_account_balance(account_number: str) -> str:
    """Get account balance and transaction information"""
    try:
        balance_info = invoice_server.accounting.get_account_balance(account_number)
        
        result = [
            f"Account: {balance_info['account_number']} - {balance_info['account_name']}",
            f"Balance: {balance_info['balance']:.2f} SEK",
            f"Transaction count: {balance_info['transaction_count']}",
        ]
        
        if balance_info['last_transaction_date']:
            result.append(f"Last transaction: {balance_info['last_transaction_date']}")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error getting account balance: {str(e)}"


@mcp.tool()
async def generate_trial_balance_old() -> str:
    """[DEPRECATED - Use generate_trial_balance with parameters] Generate trial balance showing all account balances"""
    try:
        trial_balance = invoice_server.accounting.generate_trial_balance(include_superseded=False, security_audit=False)
        
        if not trial_balance:
            return "No accounts found"
        
        result = ["TRIAL BALANCE", "=" * 60, ""]
        result.append(f"{'Account':<20} {'Name':<30} {'Debit':<12} {'Credit':<12}")
        result.append("-" * 60)
        
        total_debits = Decimal("0")
        total_credits = Decimal("0")
        
        for account in trial_balance:
            result.append(f"{account.account_number:<20} {account.account_name:<30} "
                         f"{account.debit_balance:>11.2f} {account.credit_balance:>11.2f}")
            total_debits += account.debit_balance
            total_credits += account.credit_balance
        
        result.append("-" * 60)
        result.append(f"{'TOTALS':<50} {total_debits:>11.2f} {total_credits:>11.2f}")
        
        if total_debits == total_credits:
            result.append("\n✓ Trial balance is balanced")
        else:
            result.append(f"\n❌ Trial balance is NOT balanced (difference: {total_debits - total_credits:.2f})")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error generating trial balance: {str(e)}"


@mcp.tool()
async def generate_income_statement(start_date: str, end_date: str, detailed: bool = True) -> str:
    """
    Generate income statement for period with optional enhanced detail
    
    Args:
        start_date: Period start date (YYYY-MM-DD)
        end_date: Period end date (YYYY-MM-DD)
        detailed: If True, show account codes and only non-zero accounts (default: True)
    
    Returns:
        Income statement with account codes and condensed view
    """
    try:
        from datetime import date
        
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
        
        income_statement = invoice_server.accounting.generate_income_statement(
            start_date_obj, end_date_obj, detailed=detailed
        )
        
        if detailed:
            # Enhanced format with account codes, only non-zero accounts
            result = [
                "=" * 70,
                "RESULTATRÄKNING (Income Statement)",
                f"Period: {start_date} to {end_date}",
                "=" * 70,
                f"{'ACCOUNT':<8} {'ACCOUNT NAME':<45} {'AMOUNT':>15}",
                "=" * 70,
                "",
                "INTÄKTER (Revenue):",
                "-" * 70,
            ]
            
            for account in income_statement.revenue_accounts:
                if account[2] != 0:  # Only show non-zero accounts
                    result.append(
                        f"{account[0]:<8} {account[1][:45]:<45} {account[2]:>15,.2f}"
                    )
            
            result.extend([
                "-" * 70,
                f"{'Total Revenue':<54} {income_statement.revenue:>15,.2f}",
                "",
                "KOSTNADER (Expenses):",
                "-" * 70,
            ])
            
            for account in income_statement.expense_accounts:
                if account[2] != 0:  # Only show non-zero accounts
                    result.append(
                        f"{account[0]:<8} {account[1][:45]:<45} {account[2]:>15,.2f}"
                    )
            
            result.extend([
                "-" * 70,
                f"{'Total Expenses':<54} {income_statement.expenses:>15,.2f}",
                "",
                "=" * 70,
                f"{'NETTORESULTAT (Net Income)':<54} {income_statement.net_income:>15,.2f}",
                "=" * 70
            ])
        else:
            # Legacy format - simple, includes all accounts
            result = [
                "INCOME STATEMENT (Resultaträkning)",
                f"Period: {start_date} to {end_date}",
                "=" * 50,
                "",
                "REVENUE:",
            ]
            
            for account in income_statement.revenue_accounts:
                result.append(f"  {account[1]:<30} {account[2]:>12.2f}")
            
            result.extend([
                "-" * 50,
                f"Total Revenue: {income_statement.revenue:>26.2f}",
                "",
                "EXPENSES:",
            ])
            
            for account in income_statement.expense_accounts:
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
        
    except Exception as e:
        return f"Error generating income statement: {str(e)}"


@mcp.tool()
async def generate_balance_sheet(
    as_of_date: Optional[str] = None,
    start_date: Optional[str] = None, 
    detailed: bool = True,
    period_only: bool = False
) -> str:
    """
    Generate balance sheet with optional period analysis
    
    Args:
        as_of_date: Closing balance date (YYYY-MM-DD, default: today)
        start_date: Opening balance date for period analysis (YYYY-MM-DD, default: beginning of year)
        detailed: If True, show account codes and period analysis (default: True)
        period_only: If True, show ONLY changes during the period (default: False)
    
    Returns:
        Balance sheet with opening/period/closing columns and account codes
        OR period-only changes if period_only=True
    """
    try:
        from datetime import date
        
        as_of_date_obj = date.fromisoformat(as_of_date) if as_of_date else None
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        
        # If period_only is True, use the new period-specific method
        if period_only and start_date_obj and as_of_date_obj:
            from src.modules.reporting.financial_statements import FinancialStatementsService
            fs_service = FinancialStatementsService(invoice_server.db)
            period_changes = fs_service.generate_period_balance_changes(start_date_obj, as_of_date_obj)
            
            # Format the period-only output
            result = [
                "=" * 80,
                period_changes["title"],
                f"Period: {period_changes['period']}",
                "=" * 80,
                f"{'ACCOUNT':<8} {'ACCOUNT NAME':<40} {'CHANGE':>15}",
                "=" * 80,
            ]
            
            # Assets section
            if period_changes["assets"]["accounts"]:
                result.append("\nASSETS:")
                result.append("-" * 80)
                for acc in period_changes["assets"]["accounts"]:
                    result.append(
                        f"{acc['account_number']:<8} {acc['account_name'][:40]:<40} "
                        f"{acc['period_change']:>15,.2f}"
                    )
                result.append("-" * 80)
                result.append(f"{'Total Asset Changes':<49} {period_changes['assets']['total_change']:>15,.2f}")
            
            # Liabilities section
            if period_changes["liabilities"]["accounts"]:
                result.append("\nLIABILITIES:")
                result.append("-" * 80)
                for acc in period_changes["liabilities"]["accounts"]:
                    result.append(
                        f"{acc['account_number']:<8} {acc['account_name'][:40]:<40} "
                        f"{acc['period_change']:>15,.2f}"
                    )
                result.append("-" * 80)
                result.append(f"{'Total Liability Changes':<49} {period_changes['liabilities']['total_change']:>15,.2f}")
            
            # Equity section (including net income)
            if period_changes["equity"]["accounts"]:
                result.append("\nEQUITY:")
                result.append("-" * 80)
                for acc in period_changes["equity"]["accounts"]:
                    result.append(
                        f"{acc['account_number']:<8} {acc['account_name'][:40]:<40} "
                        f"{acc['period_change']:>15,.2f}"
                    )
                result.append("-" * 80)
                result.append(f"{'Total Equity Changes':<49} {period_changes['equity']['total_change']:>15,.2f}")
            
            # Summary
            result.append("\n" + "=" * 80)
            result.append(f"{'NET CHANGE IN ASSETS':<49} {period_changes['assets']['total_change']:>15,.2f}")
            result.append(f"{'NET CHANGE IN LIABILITIES + EQUITY':<49} "
                         f"{period_changes['liabilities']['total_change'] + period_changes['equity']['total_change']:>15,.2f}")
            result.append("=" * 80)
            
            if period_changes['balanced']:
                result.append("✓ Period changes are BALANCED")
            else:
                result.append("⚠ Period changes are NOT BALANCED")
            
            return "\n".join(result)
        
        # Otherwise use the standard balance sheet
        balance_sheet = invoice_server.accounting.generate_balance_sheet(
            as_of_date=as_of_date_obj,
            start_date=start_date_obj,
            detailed=detailed
        )
        
        if detailed and len(balance_sheet.assets) > 0 and len(balance_sheet.assets[0]) > 3:
            # Enhanced format with account codes and period analysis
            result = [
                "=" * 80,
                "BALANSRÄKNING (Balance Sheet)",
                f"Period: {balance_sheet.period_start} to {balance_sheet.period_end}",
                "=" * 80,
                f"{'ACCOUNT':<8} {'ACCOUNT NAME':<35} {'OPENING':>12} {'PERIOD':>12} {'CLOSING':>12}",
                "=" * 80,
                "",
                "TILLGÅNGAR (Assets):",
                "-" * 80,
            ]
            
            total_assets_opening = 0
            total_assets_period = 0
            total_assets_closing = 0
            
            for account in balance_sheet.assets:
                # account format: (account_number, account_name, closing, opening, period)
                account_num = account[0]
                account_name = account[1]
                closing = account[2]
                opening = account[3] if len(account) > 3 else 0
                period = account[4] if len(account) > 4 else closing
                
                result.append(
                    f"{account_num:<8} {account_name[:35]:<35} "
                    f"{opening:>12,.2f} {period:>12,.2f} {closing:>12,.2f}"
                )
                total_assets_opening += opening
                total_assets_period += period
                total_assets_closing += closing
            
            result.extend([
                "-" * 80,
                f"{'Total Assets':<44} {total_assets_opening:>12,.2f} "
                f"{total_assets_period:>12,.2f} {total_assets_closing:>12,.2f}",
                "",
                "SKULDER (Liabilities):",
                "-" * 80,
            ])
            
            total_liab_opening = 0
            total_liab_period = 0
            total_liab_closing = 0
            
            for account in balance_sheet.liabilities:
                account_num = account[0]
                account_name = account[1]
                closing = account[2]
                opening = account[3] if len(account) > 3 else 0
                period = account[4] if len(account) > 4 else closing
                
                result.append(
                    f"{account_num:<8} {account_name[:35]:<35} "
                    f"{opening:>12,.2f} {period:>12,.2f} {closing:>12,.2f}"
                )
                total_liab_opening += opening
                total_liab_period += period
                total_liab_closing += closing
            
            result.extend([
                "-" * 80,
                f"{'Total Liabilities':<44} {total_liab_opening:>12,.2f} "
                f"{total_liab_period:>12,.2f} {total_liab_closing:>12,.2f}",
                "",
                "EGET KAPITAL (Equity):",
                "-" * 80,
            ])
            
            total_equity_opening = 0
            total_equity_period = 0
            total_equity_closing = 0
            
            for account in balance_sheet.equity:
                account_num = account[0]
                account_name = account[1]
                closing = account[2]
                opening = account[3] if len(account) > 3 else 0
                period = account[4] if len(account) > 4 else closing
                
                result.append(
                    f"{account_num:<8} {account_name[:35]:<35} "
                    f"{opening:>12,.2f} {period:>12,.2f} {closing:>12,.2f}"
                )
                total_equity_opening += opening
                total_equity_period += period
                total_equity_closing += closing
            
            result.extend([
                "-" * 80,
                f"{'Total Equity':<44} {total_equity_opening:>12,.2f} "
                f"{total_equity_period:>12,.2f} {total_equity_closing:>12,.2f}",
                "",
                "=" * 80,
                f"{'TOTAL ASSETS':<44} {total_assets_opening:>12,.2f} "
                f"{total_assets_period:>12,.2f} {balance_sheet.total_assets:>12,.2f}",
                f"{'TOTAL LIABILITIES & EQUITY':<44} {total_liab_opening + total_equity_opening:>12,.2f} "
                f"{total_liab_period + total_equity_period:>12,.2f} "
                f"{balance_sheet.total_liabilities + balance_sheet.total_equity:>12,.2f}",
                "=" * 80,
            ])
            
            if abs(balance_sheet.total_assets - (balance_sheet.total_liabilities + balance_sheet.total_equity)) < 0.01:
                result.append("✓ Balance Sheet is BALANCED")
            else:
                result.append("⚠ Balance Sheet is NOT BALANCED")
        else:
            # Legacy simple format
            result = [
                "BALANCE SHEET (Balansräkning)",
                f"As of: {balance_sheet.period_end}",
                "=" * 50,
                "",
                "ASSETS:",
            ]
            
            for account in balance_sheet.assets:
                result.append(f"  {account[1]:<30} {account[2]:>12.2f}")
            
            result.extend([
                "-" * 50,
                f"Total Assets: {balance_sheet.total_assets:>27.2f}",
                "",
                "LIABILITIES:",
            ])
            
            for account in balance_sheet.liabilities:
                result.append(f"  {account[1]:<30} {account[2]:>12.2f}")
            
            result.extend([
                "-" * 50,
                f"Total Liabilities: {balance_sheet.total_liabilities:>21.2f}",
                "",
                "EQUITY:",
            ])
            
            for account in balance_sheet.equity:
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
        
    except Exception as e:
        return f"Error generating balance sheet: {str(e)}"


@mcp.tool()
async def auto_generate_invoice_voucher(invoice_id: int) -> str:
    """Automatically generate accounting voucher for invoice"""
    try:
        voucher_id = invoice_server.accounting.auto_generate_invoice_voucher(invoice_id)
        return f"Invoice voucher generated successfully (Voucher ID: {voucher_id})"
        
    except Exception as e:
        return f"Error generating invoice voucher: {str(e)}"


@mcp.tool()
async def auto_generate_expense_voucher(expense_id: int) -> str:
    """Automatically generate accounting voucher for expense"""
    try:
        voucher_id = invoice_server.accounting.auto_generate_expense_voucher(expense_id)
        return f"Expense voucher generated successfully (Voucher ID: {voucher_id})"
        
    except Exception as e:
        return f"Error generating expense voucher: {str(e)}"


@mcp.tool()
async def auto_generate_payment_voucher(
    invoice_id: int,
    payment_amount: float,
    payment_date: Optional[str] = None,
    reference: Optional[str] = None
) -> str:
    """Automatically generate accounting voucher for invoice payment
    
    Args:
        invoice_id: Invoice that was paid
        payment_amount: Amount received
        payment_date: Date payment was received (YYYY-MM-DD, defaults to today)
        reference: Payment reference/description
    
    Returns:
        Success message with voucher ID
    """
    try:
        from datetime import date
        from decimal import Decimal
        
        # Parse payment date
        if payment_date:
            payment_date = date.fromisoformat(payment_date)
        
        voucher_id = invoice_server.accounting.auto_generate_payment_voucher(
            invoice_id=invoice_id,
            payment_amount=Decimal(str(payment_amount)),
            payment_date=payment_date,
            reference=reference
        )
        return f"Payment voucher generated successfully (Voucher ID: {voucher_id})"
        
    except Exception as e:
        return f"Error generating payment voucher: {str(e)}"


# Documentation tools
@mcp.tool()
async def tools_documentation(
    topic: Optional[str] = None,
    depth: str = "essentials",
    category: Optional[str] = None
) -> str:
    """
    Get comprehensive documentation for accounting tools and workflows.
    
    ALWAYS START WITH THIS TOOL when working with the accounting system!
    
    Args:
        topic: Specific tool name or "overview" for general guidance
        depth: "essentials" (quick reference) or "full" (complete details)
        category: Filter by category (invoicing, expenses, accounting, reporting)
    
    Returns:
        Formatted documentation with examples and best practices
    """
    return invoice_server.documentation.get_documentation(topic, depth, category)


@mcp.tool()
async def workflow_guide(workflow_name: str) -> str:
    """
    Get step-by-step workflow documentation for common accounting processes.
    
    Args:
        workflow_name: Workflow to get guide for (invoice_to_payment, expense_recording, monthly_closing)
    
    Returns:
        Step-by-step workflow guide with accounting impact
    """
    return invoice_server.documentation.get_workflow_guide(workflow_name)


@mcp.tool()
async def swedish_compliance_guide(topic: str) -> str:
    """
    Get Swedish-specific compliance information for accounting requirements.
    
    Args:
        topic: Compliance topic (vat_reporting, invoice_requirements, audit_trail, chart_of_accounts)
    
    Returns:
        Swedish compliance requirements and best practices
    """
    return invoice_server.documentation.get_compliance_info(topic)


# TOTP-Protected Voucher Operations
@mcp.tool()
async def supersede_voucher(
    original_voucher_id: int,
    replacement_voucher_id: int,
    reason: str,
    user_id: str,
    totp_code: str
) -> str:
    """
    Mark voucher as superseded with TOTP security verification.
    
    **CRITICAL**: Requires TOTP code from Google Authenticator.
    
    Args:
        original_voucher_id: Voucher being replaced
        replacement_voucher_id: Correct replacement voucher
        reason: Business justification (max 200 chars)
        user_id: User performing operation (e.g., 'tkaxberg@gmail.com')
        totp_code: 6-digit TOTP from authenticator app or 8-digit backup code
    
    Returns:
        Success message with security verification details or error
    
    Example:
        supersede_voucher(21, 22, "Balance error corrected", "tkaxberg@gmail.com", "123456")
    """
    try:
        result = invoice_server.secure_voucher.supersede_voucher_with_totp(
            original_voucher_id=original_voucher_id,
            replacement_voucher_id=replacement_voucher_id,
            reason=reason,
            user_id=user_id,
            totp_code=totp_code
        )
        
        if result["success"]:
            return (
                f"✅ Voucher {original_voucher_id} successfully superseded by {replacement_voucher_id}\n"
                f"Security: TOTP verified at {result['security']['verification_time']}\n"
                f"Audit log ID: {result['security']['audit_log_id']}\n"
                f"Annotations created: {result['annotations_created']}"
            )
        else:
            error_msg = f"❌ Failed: {result.get('error_message', 'Unknown error')}"
            if result.get('retry_after'):
                error_msg += f"\nRetry after: {result['retry_after']} seconds"
            if result.get('attempts_remaining'):
                error_msg += f"\nAttempts remaining: {result['attempts_remaining']}"
            return error_msg
    except Exception as e:
        return f"Error superseding voucher: {str(e)}"



@mcp.tool()
async def list_vouchers_by_period(
    start_date: str,
    end_date: str,
    include_superseded: bool = False,
    voucher_type: Optional[str] = None
) -> str:
    """
    List all vouchers for a period with summary information for efficient review.
    
    This function enables efficient period analysis by retrieving all vouchers
    within a date range in a single call, eliminating the need for multiple
    individual get_voucher_history calls.
    
    Args:
        start_date: Start of period in YYYY-MM-DD format (e.g., "2025-07-01")
        end_date: End of period in YYYY-MM-DD format (e.g., "2025-07-31")
        include_superseded: Include superseded vouchers (default: False)
        voucher_type: Optional filter by type (e.g., "INVOICE", "EXPENSE", "MANUAL")
    
    Returns:
        Formatted list of vouchers with:
        - ID, number, date, description, amount, status
        - Posting status (Posted/Pending/Superseded/Voided)
        - Balance check (Balanced/Unbalanced)
        - Summary statistics for the period
    
    Example:
        # Review all July 2025 vouchers for monthly closing
        list_vouchers_by_period("2025-07-01", "2025-07-31")
        
        # Include superseded vouchers for audit trail
        list_vouchers_by_period("2025-07-01", "2025-07-31", include_superseded=True)
        
        # Filter by voucher type
        list_vouchers_by_period("2025-07-01", "2025-07-31", voucher_type="INVOICE")
    """
    try:
        result = invoice_server.voucher_annotation.list_vouchers_by_period(
            start_date=start_date,
            end_date=end_date,
            include_superseded=include_superseded,
            voucher_type=voucher_type
        )
        
        if not result.get("success"):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        vouchers = result.get("vouchers", [])
        summary = result.get("summary", {})
        period = result.get("period", {})
        
        if not vouchers:
            return f"No vouchers found for period {start_date} to {end_date}"
        
        # Build formatted output
        output = [
            f"📊 Voucher List for Period: {period['start_date']} to {period['end_date']}",
            f"{'='*70}",
            ""
        ]
        
        # Summary statistics
        output.append("📈 SUMMARY")
        output.append(f"Total vouchers: {summary['total_vouchers']}")
        output.append(f"Total amount: {summary['total_amount']:,.2f} SEK")
        output.append(f"Posted: {summary['posted']} | Pending: {summary['pending']} | Superseded: {summary['superseded']}")
        
        if summary.get('unbalanced', 0) > 0:
            output.append(f"⚠️  Unbalanced vouchers: {summary['unbalanced']}")
        
        # Type breakdown
        if summary.get('by_type'):
            output.append("\nBy Type:")
            for vtype, stats in summary['by_type'].items():
                output.append(f"  {vtype}: {stats['count']} vouchers, {stats['amount']:,.2f} SEK")
        
        output.append(f"\n{'='*70}")
        output.append("VOUCHER DETAILS\n")
        
        # Voucher list with key information
        for v in vouchers:
            # Status indicators
            status_icon = "✅" if v['is_posted'] else "⏳"
            if v['status'] == 'SUPERSEDED':
                status_icon = "🔄"
            elif v['status'] == 'VOIDED':
                status_icon = "❌"
            
            balance_icon = "✓" if v.get('is_balanced') else "⚠️"
            
            # Format voucher line
            output.append(
                f"{status_icon} #{v['id']:3d} | {v.get('voucher_number', 'N/A'):8s} | {v['date']} | "
                f"{v['amount']:10,.2f} SEK | {balance_icon} | {v['posting_status']:10s}"
            )
            output.append(f"   {v['description'][:60]}")
            
            # Add source reference if available
            source = v.get('source', {})
            if source.get('invoice_id'):
                output.append(f"   Source: Invoice #{source['invoice_id']}")
            elif source.get('expense_id'):
                output.append(f"   Source: Expense #{source['expense_id']}")
            elif source.get('reminder_id'):
                output.append(f"   Source: Reminder #{source['reminder_id']}")
            
            # Note if superseded
            if v.get('superseded_by'):
                output.append(f"   ➜ Superseded by voucher #{v['superseded_by']}")
            
            output.append("")  # Blank line between vouchers
        
        # Footer with filter information
        output.append(f"{'='*70}")
        filters = result.get('filters', {})
        filter_info = []
        if not filters.get('include_superseded'):
            filter_info.append("Excluding superseded")
        else:
            filter_info.append("Including superseded")
        if filters.get('voucher_type'):
            filter_info.append(f"Type: {filters['voucher_type']}")
        
        output.append(f"Filters: {', '.join(filter_info)}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error listing vouchers: {str(e)}"


@mcp.tool()
async def get_voucher_history(voucher_id: int) -> str:
    """
    Get complete history, relationships, and security audit for a single voucher.
    
    Use this for detailed analysis of a specific voucher. For period analysis,
    use list_vouchers_by_period instead.
    
    Args:
        voucher_id: Voucher to analyze
    
    Returns:
        Complete voucher history with annotations and security audit
    
    Example:
        get_voucher_history(21)
    """
    try:
        history = invoice_server.voucher_annotation.get_voucher_history(voucher_id)
        
        if not history.get("voucher"):
            return f"❌ Voucher {voucher_id} does not exist"
        
        voucher = history["voucher"]
        result = [
            f"📋 Voucher History for #{voucher_id}",
            f"{'='*50}",
            f"Number: {voucher.get('voucher_number', 'N/A')}",
            f"Description: {voucher.get('description', 'N/A')}",
            f"Status: {voucher.get('status', 'ACTIVE')}",
            f"Amount: {voucher.get('total_amount', 0):.2f}",
            f"Created: {voucher.get('created_at', 'N/A')}",
            f"Posted: {'Yes' if voucher.get('is_posted') else 'No'}",
            ""
        ]
        
        # Relationships
        relationships = history.get("relationships", {})
        if relationships.get("superseded_by"):
            result.append(f"⚠️ SUPERSEDED BY: Voucher #{relationships['superseded_by']['id']}")
        if relationships.get("supersedes"):
            result.append(f"✅ SUPERSEDES: Voucher(s) {relationships['supersedes']}")
        
        # Annotations
        annotations = history.get("annotations", [])
        if annotations:
            result.append(f"\n📝 Annotations ({len(annotations)}):")
            result.append("-" * 40)
            for ann in annotations:
                security = "🔐" if ann.get("security_verified") else ""
                result.append(
                    f"{security} [{ann['type']}] {ann['created_at']}\n"
                    f"   {ann['message']}\n"
                    f"   By: {ann['created_by']}"
                )
        
        # Security audit
        security_audit = history.get("security_audit", [])
        if security_audit:
            result.append(f"\n🔐 Security Audit ({len(security_audit)}):")
            result.append("-" * 40)
            for audit in security_audit:
                verified = "✅" if audit.get("totp_verified") else "❌"
                result.append(
                    f"{verified} {audit['operation']} by {audit['user']} at {audit['timestamp']}"
                )
        
        return "\n".join(result)
    except Exception as e:
        return f"Error getting voucher history: {str(e)}"


@mcp.tool()
async def add_secure_voucher_annotation(
    voucher_id: int,
    annotation_type: str,
    message: str,
    user_id: str,
    totp_code: str,
    related_voucher_id: Optional[int] = None
) -> str:
    """
    Add annotation to voucher with TOTP security verification.
    
    **CRITICAL**: ALL voucher annotations affect audit trail and require TOTP protection.
    
    Args:
        voucher_id: Target voucher ID
        annotation_type: CORRECTION | REVERSAL | NOTE (SUPERSEDED/VOID use dedicated methods)
        message: Annotation message
        user_id: User performing operation (e.g., 'tkaxberg@gmail.com')
        totp_code: 6-digit TOTP from authenticator app or 8-digit backup code
        related_voucher_id: Optional related voucher
    
    Returns:
        Success/failure status with TOTP verification details
    
    Example:
        add_secure_voucher_annotation(21, "NOTE", "Pending approval", "tkaxberg@gmail.com", "123456")
    """
    try:
        result = invoice_server.secure_voucher.add_secure_annotation(
            voucher_id=voucher_id,
            annotation_type=annotation_type,
            message=message,
            user_id=user_id,
            totp_code=totp_code,
            related_voucher_id=related_voucher_id
        )
        
        if result["success"]:
            return (
                f"✅ Secure annotation added to voucher {voucher_id}\n"
                f"Type: {result['annotation_type']}\n"
                f"Security: TOTP verified at {result['security']['verification_time']}\n"
                f"Annotation ID: {result['annotation_id']}"
            )
        else:
            error_msg = f"❌ Failed: {result.get('error', 'Unknown error')}"
            if result.get('retry_after'):
                error_msg += f"\nRetry after: {result['retry_after']} seconds"
            return error_msg
    except Exception as e:
        return f"Error adding secure annotation: {str(e)}"


@mcp.tool()
async def generate_trial_balance(
    as_of_date: Optional[str] = None,
    start_date: Optional[str] = None,
    period_analysis: bool = True,
    include_superseded: bool = False,
    security_audit: bool = False
) -> str:
    """
    Generate trial balance with optional period comparison
    
    Args:
        as_of_date: For closing balance (YYYY-MM-DD, default: today)
        start_date: For opening balance comparison (YYYY-MM-DD, default: beginning of year)
        period_analysis: Show opening/debit/credit/closing columns (default: True)
        include_superseded: Include SUPERSEDED/VOID vouchers (default: False)
        security_audit: Include security verification details (default: False)
    
    Returns:
        Trial balance with period analysis and account codes
    
    Example:
        generate_trial_balance()  # Enhanced trial balance with period analysis
        generate_trial_balance(period_analysis=False)  # Simple trial balance
        generate_trial_balance(include_superseded=True, security_audit=True)  # Full audit view
    """
    try:
        from datetime import date
        
        # If using enhanced period analysis, use the new method
        if period_analysis or as_of_date or start_date:
            as_of_date_obj = date.fromisoformat(as_of_date) if as_of_date else None
            start_date_obj = date.fromisoformat(start_date) if start_date else None
            
            trial_balance = invoice_server.accounting.generate_trial_balance_enhanced(
                as_of_date=as_of_date_obj,
                start_date=start_date_obj,
                period_analysis=period_analysis
            )
        else:
            # Use legacy method for backward compatibility
            trial_balance = invoice_server.accounting.generate_trial_balance(
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
        
        # Metadata
        metadata = trial_balance["metadata"]
        result.append(f"\n📊 Metadata:")
        result.append(f"   Total vouchers: {metadata['total_vouchers']}")
        result.append(f"   Active vouchers: {metadata['active_vouchers']}")
        result.append(f"   Superseded vouchers: {metadata['superseded_vouchers']}")
        
        if security_audit and 'security_protected_operations' in metadata:
            result.append(f"   🔐 Security-protected operations: {metadata['security_protected_operations']}")
        
        if metadata['filters']['include_superseded']:
            result.append("   ⚠️ INCLUDING superseded vouchers")
        else:
            result.append("   ✅ EXCLUDING superseded vouchers (clean view)")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error generating trial balance: {str(e)}"


def main():
    """Entry point for uvx"""
    mcp.run()


if __name__ == "__main__":
    main()
