import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from .models import Customer, Invoice, LineItem, InvoiceStatus, PaymentReminder, CustomerType, Expense, BankTransaction, Reconciliation


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        import os
        import sys
        import tempfile
        
        if db_path is None:
            # Try different database locations in order of preference
            locations = [
                # User home directory
                os.path.join(os.path.expanduser("~"), ".mcp-invoice-server", "invoices.db"),
                # Temp directory 
                os.path.join(tempfile.gettempdir(), "mcp-invoice-server.db"),
                # In-memory database as last resort
                ":memory:"
            ]
            
            self.db_path = None
            for location in locations:
                try:
                    if location != ":memory:":
                        # Try to create directory
                        db_dir = os.path.dirname(location)
                        os.makedirs(db_dir, exist_ok=True)
                        
                        # Test if we can create a database file
                        test_conn = sqlite3.connect(location)
                        test_conn.close()
                        
                    self.db_path = location
                    print(f"Using database: {location}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"Cannot use database location {location}: {e}", file=sys.stderr)
                    continue
            
            if self.db_path is None:
                raise RuntimeError("Cannot initialize database in any location")
        else:
            self.db_path = db_path
            
        self.init_database()

    @contextmanager
    def get_connection(self):
        if self.db_path is None:
            raise RuntimeError("Database path is None")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        import sys
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create customers table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT,
                        address TEXT,
                        company TEXT NOT NULL,
                        org_number TEXT,
                        vat_number TEXT NOT NULL,
                        street TEXT,
                        postal_code TEXT,
                        city TEXT,
                        country TEXT,
                        contact_person TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(company, vat_number)
                    )
                """)
                
                # Create invoices table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_number TEXT UNIQUE NOT NULL,
                        customer_id INTEGER NOT NULL,
                        issue_date DATE NOT NULL,
                        due_date DATE NOT NULL,
                        status TEXT DEFAULT 'draft',
                        subtotal DECIMAL(10,2) NOT NULL,
                        tax_rate DECIMAL(5,4) DEFAULT 0.25,
                        tax_amount DECIMAL(10,2) NOT NULL,
                        total DECIMAL(10,2) NOT NULL,
                        notes TEXT,
                        reminder_count INTEGER DEFAULT 0,
                        last_reminder_date DATE,
                        customer_type TEXT DEFAULT 'business',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers (id)
                    )
                """)
                
                # Create line items table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS line_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        quantity DECIMAL(10,3) NOT NULL,
                        unit_price DECIMAL(10,2) NOT NULL,
                        total DECIMAL(10,2) NOT NULL,
                        FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
                    )
                """)
                
                # Create payment reminders table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payment_reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER NOT NULL,
                        reminder_number INTEGER NOT NULL,
                        reminder_date DATE NOT NULL,
                        original_amount DECIMAL(10,2) NOT NULL,
                        interest_amount DECIMAL(10,2) DEFAULT 0,
                        reminder_fee DECIMAL(10,2) DEFAULT 0,
                        delay_compensation DECIMAL(10,2) DEFAULT 0,
                        total_amount DECIMAL(10,2) NOT NULL,
                        reference_rate DECIMAL(5,4) NOT NULL,
                        interest_rate DECIMAL(5,4) NOT NULL,
                        days_overdue INTEGER NOT NULL,
                        customer_type TEXT NOT NULL,
                        pdf_generated BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
                    )
                """)
                
                # Create expenses table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        vat_amount DECIMAL(10,2) DEFAULT 0,
                        vat_rate DECIMAL(5,4) DEFAULT 0.25,
                        category TEXT NOT NULL,
                        expense_date DATE NOT NULL,
                        receipt_image_path TEXT,
                        notes TEXT,
                        is_deductible BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create bank transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bank_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_date DATE NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        description TEXT,
                        reference TEXT,
                        counterparty TEXT,
                        transaction_type TEXT NOT NULL,
                        account_balance DECIMAL(10,2),
                        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create reconciliations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reconciliations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER,
                        expense_id INTEGER,
                        bank_transaction_id INTEGER,
                        reconciled_amount DECIMAL(10,2),
                        reconciled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reconciliation_type TEXT NOT NULL,
                        notes TEXT,
                        FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                        FOREIGN KEY (expense_id) REFERENCES expenses (id),
                        FOREIGN KEY (bank_transaction_id) REFERENCES bank_transactions (id)
                    )
                """)
                
                # Create VAT periods table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vat_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        year INTEGER NOT NULL,
                        quarter INTEGER NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        output_vat DECIMAL(10,2) DEFAULT 0,
                        input_vat DECIMAL(10,2) DEFAULT 0,
                        net_vat DECIMAL(10,2) DEFAULT 0,
                        submitted_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(year, quarter)
                    )
                """)
                
                # Create accounts table (Swedish Chart of Accounts - BAS 2022)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_number TEXT UNIQUE NOT NULL,
                        account_name TEXT NOT NULL,
                        account_type TEXT NOT NULL,
                        account_category TEXT NOT NULL,
                        parent_account TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        requires_vat BOOLEAN DEFAULT FALSE,
                        balance DECIMAL(15,2) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create vouchers table (Verifikationer)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vouchers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        voucher_number TEXT UNIQUE NOT NULL,
                        voucher_date DATE NOT NULL,
                        description TEXT NOT NULL,
                        voucher_type TEXT NOT NULL,
                        source_invoice_id INTEGER,
                        source_expense_id INTEGER,
                        source_reminder_id INTEGER,
                        total_amount DECIMAL(15,2) NOT NULL,
                        reference TEXT,
                        is_posted BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        posted_at TIMESTAMP,
                        FOREIGN KEY (source_invoice_id) REFERENCES invoices (id),
                        FOREIGN KEY (source_expense_id) REFERENCES expenses (id),
                        FOREIGN KEY (source_reminder_id) REFERENCES payment_reminders (id)
                    )
                """)
                
                # Create journal entries table (Bokföringsposter)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        voucher_id INTEGER NOT NULL,
                        account_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        debit_amount DECIMAL(15,2) DEFAULT 0,
                        credit_amount DECIMAL(15,2) DEFAULT 0,
                        reference TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (voucher_id) REFERENCES vouchers (id) ON DELETE CASCADE,
                        FOREIGN KEY (account_id) REFERENCES accounts (id)
                    )
                """)
                
                # Create accounting periods table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounting_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        year INTEGER NOT NULL,
                        period INTEGER NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        is_closed BOOLEAN DEFAULT FALSE,
                        period_type TEXT DEFAULT 'monthly',
                        closed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(year, period, period_type)
                    )
                """)
                
                # Add accounting integration columns to existing tables
                try:
                    cursor.execute("ALTER TABLE invoices ADD COLUMN voucher_id INTEGER")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE expenses ADD COLUMN voucher_id INTEGER")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE payment_reminders ADD COLUMN voucher_id INTEGER")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                conn.commit()
                print("Database initialized successfully", file=sys.stderr)
        except Exception as e:
            print(f"Database initialization error: {e}", file=sys.stderr)
            raise

    def create_customer(self, customer: Customer) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, company, vat_number, email, address, org_number, 
                                     street, postal_code, city, country, contact_person)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.name, customer.company, customer.vat_number,
                customer.email, customer.address, customer.org_number,
                customer.street, customer.postal_code, customer.city, 
                customer.country, customer.contact_person
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_customer_by_company_vat(self, company: str, vat_number: str) -> Optional[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE company = ? AND vat_number = ?", (company, vat_number))
            row = cursor.fetchone()
            if row:
                return Customer(
                    id=row["id"],
                    name=row["name"],
                    company=row["company"],
                    vat_number=row["vat_number"],
                    email=row["email"],
                    address=row["address"],
                    org_number=row["org_number"],
                    street=row["street"],
                    postal_code=row["postal_code"],
                    city=row["city"],
                    country=row["country"],
                    contact_person=row["contact_person"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                )
            return None

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return Customer(
                    id=row["id"],
                    name=row["name"],
                    company=row["company"],
                    vat_number=row["vat_number"],
                    email=row["email"],
                    address=row["address"],
                    org_number=row["org_number"],
                    street=row["street"],
                    postal_code=row["postal_code"],
                    city=row["city"],
                    country=row["country"],
                    contact_person=row["contact_person"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                )
            return None

    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            if row:
                return Customer(
                    id=row["id"],
                    name=row["name"],
                    company=row["company"],
                    vat_number=row["vat_number"],
                    email=row["email"],
                    address=row["address"],
                    org_number=row["org_number"],
                    street=row["street"],
                    postal_code=row["postal_code"],
                    city=row["city"],
                    country=row["country"],
                    contact_person=row["contact_person"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                )
            return None

    def list_customers(self) -> List[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY name")
            return [
                Customer(
                    id=row["id"],
                    name=row["name"],
                    company=row["company"],
                    vat_number=row["vat_number"],
                    email=row["email"],
                    address=row["address"],
                    org_number=row["org_number"],
                    street=row["street"],
                    postal_code=row["postal_code"],
                    city=row["city"],
                    country=row["country"],
                    contact_person=row["contact_person"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                )
                for row in cursor.fetchall()
            ]

    def update_customer(self, customer: Customer) -> bool:
        """Update an existing customer with new information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers 
                SET name = ?, address = ?, company = ?, org_number = ?, vat_number = ?,
                    street = ?, postal_code = ?, city = ?, country = ?, contact_person = ?
                WHERE id = ?
            """, (
                customer.name, customer.address, customer.company, customer.org_number, 
                customer.vat_number, customer.street, customer.postal_code, customer.city, 
                customer.country, customer.contact_person, customer.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def create_invoice(self, invoice: Invoice) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_id, issue_date, due_date, status,
                    subtotal, tax_rate, tax_amount, total, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice.invoice_number, invoice.customer_id, invoice.issue_date,
                invoice.due_date, invoice.status.value, float(invoice.subtotal),
                float(invoice.tax_rate), float(invoice.tax_amount), float(invoice.total), invoice.notes
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            if row:
                from datetime import date
                return Invoice(
                    id=row["id"],
                    invoice_number=row["invoice_number"],
                    customer_id=row["customer_id"],
                    issue_date=date.fromisoformat(row["issue_date"]) if isinstance(row["issue_date"], str) else row["issue_date"],
                    due_date=date.fromisoformat(row["due_date"]) if isinstance(row["due_date"], str) else row["due_date"],
                    status=InvoiceStatus(row["status"]),
                    subtotal=row["subtotal"],
                    tax_rate=row["tax_rate"],
                    tax_amount=row["tax_amount"],
                    total=row["total"],
                    notes=row["notes"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
            return None

    def list_invoices(self, status: Optional[str] = None) -> List[Invoice]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM invoices WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM invoices ORDER BY created_at DESC")
            
            from datetime import date
            return [
                Invoice(
                    id=row["id"],
                    invoice_number=row["invoice_number"],
                    customer_id=row["customer_id"],
                    issue_date=date.fromisoformat(row["issue_date"]) if isinstance(row["issue_date"], str) else row["issue_date"],
                    due_date=date.fromisoformat(row["due_date"]) if isinstance(row["due_date"], str) else row["due_date"],
                    status=InvoiceStatus(row["status"]),
                    subtotal=row["subtotal"],
                    tax_rate=row["tax_rate"],
                    tax_amount=row["tax_amount"],
                    total=row["total"],
                    notes=row["notes"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
                for row in cursor.fetchall()
            ]

    def update_invoice_status(self, invoice_id: int, status: InvoiceStatus) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE invoices 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status.value, invoice_id))
            conn.commit()
            return cursor.rowcount > 0

    def create_line_item(self, line_item: LineItem) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
                VALUES (?, ?, ?, ?, ?)
            """, (
                line_item.invoice_id, line_item.description,
                float(line_item.quantity), float(line_item.unit_price), float(line_item.total)
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_line_items_by_invoice(self, invoice_id: int) -> List[LineItem]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM line_items WHERE invoice_id = ?", (invoice_id,))
            return [
                LineItem(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    description=row["description"],
                    quantity=row["quantity"],
                    unit_price=row["unit_price"],
                    total=row["total"]
                )
                for row in cursor.fetchall()
            ]

    def generate_invoice_number(self) -> str:
        """Generate a unique invoice number in format YYYY-NNN"""
        from datetime import datetime
        
        current_year = datetime.now().year
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT invoice_number FROM invoices 
                WHERE invoice_number LIKE ? 
                ORDER BY invoice_number DESC 
                LIMIT 1
            """, (f"{current_year}-%",))
            
            row = cursor.fetchone()
            if row:
                last_number = int(row["invoice_number"].split("-")[1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            return f"{current_year}-{new_number:03d}"
    
    def create_payment_reminder(self, reminder: PaymentReminder) -> int:
        """Create a payment reminder record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payment_reminders (
                    invoice_id, reminder_number, reminder_date, original_amount,
                    interest_amount, reminder_fee, delay_compensation, total_amount,
                    reference_rate, interest_rate, days_overdue, customer_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reminder.invoice_id, reminder.reminder_number, reminder.reminder_date,
                float(reminder.original_amount), float(reminder.interest_amount),
                float(reminder.reminder_fee), float(reminder.delay_compensation),
                float(reminder.total_amount), float(reminder.reference_rate),
                float(reminder.interest_rate), reminder.days_overdue,
                reminder.customer_type.value
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid
    
    def get_payment_reminder_by_id(self, reminder_id: int) -> Optional[PaymentReminder]:
        """Get payment reminder by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payment_reminders WHERE id = ?", (reminder_id,))
            row = cursor.fetchone()
            if row:
                from datetime import date
                return PaymentReminder(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    reminder_number=row["reminder_number"],
                    reminder_date=date.fromisoformat(row["reminder_date"]) if isinstance(row["reminder_date"], str) else row["reminder_date"],
                    original_amount=row["original_amount"],
                    interest_amount=row["interest_amount"],
                    reminder_fee=row["reminder_fee"],
                    delay_compensation=row["delay_compensation"],
                    total_amount=row["total_amount"],
                    reference_rate=row["reference_rate"],
                    interest_rate=row["interest_rate"],
                    days_overdue=row["days_overdue"],
                    customer_type=CustomerType(row["customer_type"]),
                    pdf_generated=bool(row["pdf_generated"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                )
            return None
    
    def get_payment_reminders_by_invoice(self, invoice_id: int) -> List[PaymentReminder]:
        """Get all payment reminders for an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payment_reminders WHERE invoice_id = ? ORDER BY reminder_number",
                (invoice_id,)
            )
            
            reminders = []
            for row in cursor.fetchall():
                from datetime import date
                reminders.append(PaymentReminder(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    reminder_number=row["reminder_number"],
                    reminder_date=date.fromisoformat(row["reminder_date"]) if isinstance(row["reminder_date"], str) else row["reminder_date"],
                    original_amount=row["original_amount"],
                    interest_amount=row["interest_amount"],
                    reminder_fee=row["reminder_fee"],
                    delay_compensation=row["delay_compensation"],
                    total_amount=row["total_amount"],
                    reference_rate=row["reference_rate"],
                    interest_rate=row["interest_rate"],
                    days_overdue=row["days_overdue"],
                    customer_type=CustomerType(row["customer_type"]),
                    pdf_generated=bool(row["pdf_generated"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                ))
            return reminders
    
    def update_invoice_reminder_info(self, invoice_id: int, reminder_count: int, reminder_date: date) -> bool:
        """Update invoice reminder count and last reminder date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE invoices 
                SET reminder_count = ?, last_reminder_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reminder_count, reminder_date, invoice_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_reminder_pdf_status(self, reminder_id: int, pdf_generated: bool) -> bool:
        """Update PDF generation status for a reminder"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE payment_reminders 
                SET pdf_generated = ?
                WHERE id = ?
            """, (pdf_generated, reminder_id))
            conn.commit()
            return cursor.rowcount > 0

    # Expense CRUD operations
    def create_expense(self, expense: Expense) -> int:
        """Create a new expense"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (
                    description, amount, vat_amount, vat_rate, category, 
                    expense_date, receipt_image_path, notes, is_deductible
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                expense.description, float(expense.amount), float(expense.vat_amount),
                float(expense.vat_rate), expense.category, expense.expense_date,
                expense.receipt_image_path, expense.notes, expense.is_deductible
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_expense_by_id(self, expense_id: int) -> Optional[Expense]:
        """Get expense by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            if row:
                return Expense(
                    id=row["id"],
                    description=row["description"],
                    amount=row["amount"],
                    vat_amount=row["vat_amount"],
                    vat_rate=row["vat_rate"],
                    category=row["category"],
                    expense_date=date.fromisoformat(row["expense_date"]) if isinstance(row["expense_date"], str) else row["expense_date"],
                    receipt_image_path=row["receipt_image_path"],
                    notes=row["notes"],
                    is_deductible=bool(row["is_deductible"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
            return None

    def list_expenses(self, category: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Expense]:
        """List expenses with optional filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM expenses WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if start_date:
                query += " AND expense_date >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND expense_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY expense_date DESC"
            
            cursor.execute(query, params)
            return [
                Expense(
                    id=row["id"],
                    description=row["description"],
                    amount=row["amount"],
                    vat_amount=row["vat_amount"],
                    vat_rate=row["vat_rate"],
                    category=row["category"],
                    expense_date=date.fromisoformat(row["expense_date"]) if isinstance(row["expense_date"], str) else row["expense_date"],
                    receipt_image_path=row["receipt_image_path"],
                    notes=row["notes"],
                    is_deductible=bool(row["is_deductible"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
                for row in cursor.fetchall()
            ]

    def update_expense(self, expense: Expense) -> bool:
        """Update an existing expense"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses 
                SET description = ?, amount = ?, vat_amount = ?, vat_rate = ?, 
                    category = ?, expense_date = ?, receipt_image_path = ?, 
                    notes = ?, is_deductible = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                expense.description, float(expense.amount), float(expense.vat_amount),
                float(expense.vat_rate), expense.category, expense.expense_date,
                expense.receipt_image_path, expense.notes, expense.is_deductible, expense.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Bank transaction CRUD operations
    def create_bank_transaction(self, transaction: BankTransaction) -> int:
        """Create a new bank transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bank_transactions (
                    transaction_date, amount, description, reference, 
                    counterparty, transaction_type, account_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.transaction_date, float(transaction.amount),
                transaction.description, transaction.reference,
                transaction.counterparty, transaction.transaction_type,
                float(transaction.account_balance) if transaction.account_balance else None
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_bank_transaction_by_id(self, transaction_id: int) -> Optional[BankTransaction]:
        """Get bank transaction by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bank_transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            if row:
                return BankTransaction(
                    id=row["id"],
                    transaction_date=date.fromisoformat(row["transaction_date"]) if isinstance(row["transaction_date"], str) else row["transaction_date"],
                    amount=row["amount"],
                    description=row["description"],
                    reference=row["reference"],
                    counterparty=row["counterparty"],
                    transaction_type=row["transaction_type"],
                    account_balance=row["account_balance"],
                    imported_at=datetime.fromisoformat(row["imported_at"]) if row["imported_at"] else None
                )
            return None

    def list_bank_transactions(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[BankTransaction]:
        """List bank transactions with optional date filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM bank_transactions WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND transaction_date >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND transaction_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY transaction_date DESC"
            
            cursor.execute(query, params)
            return [
                BankTransaction(
                    id=row["id"],
                    transaction_date=date.fromisoformat(row["transaction_date"]) if isinstance(row["transaction_date"], str) else row["transaction_date"],
                    amount=row["amount"],
                    description=row["description"],
                    reference=row["reference"],
                    counterparty=row["counterparty"],
                    transaction_type=row["transaction_type"],
                    account_balance=row["account_balance"],
                    imported_at=datetime.fromisoformat(row["imported_at"]) if row["imported_at"] else None
                )
                for row in cursor.fetchall()
            ]

    # Reconciliation CRUD operations
    def create_reconciliation(self, reconciliation: Reconciliation) -> int:
        """Create a new reconciliation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reconciliations (
                    invoice_id, expense_id, bank_transaction_id, 
                    reconciled_amount, reconciliation_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reconciliation.invoice_id, reconciliation.expense_id,
                reconciliation.bank_transaction_id, float(reconciliation.reconciled_amount),
                reconciliation.reconciliation_type, reconciliation.notes
            ))
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create record")
            return cursor.lastrowid

    def get_reconciliation_by_id(self, reconciliation_id: int) -> Optional[Reconciliation]:
        """Get reconciliation by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reconciliations WHERE id = ?", (reconciliation_id,))
            row = cursor.fetchone()
            if row:
                return Reconciliation(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    expense_id=row["expense_id"],
                    bank_transaction_id=row["bank_transaction_id"],
                    reconciled_amount=row["reconciled_amount"],
                    reconciliation_type=row["reconciliation_type"],
                    notes=row["notes"],
                    reconciled_at=datetime.fromisoformat(row["reconciled_at"]) if row["reconciled_at"] else None
                )
            return None

    def list_reconciliations(self) -> List[Reconciliation]:
        """List all reconciliations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reconciliations ORDER BY reconciled_at DESC")
            return [
                Reconciliation(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    expense_id=row["expense_id"],
                    bank_transaction_id=row["bank_transaction_id"],
                    reconciled_amount=row["reconciled_amount"],
                    reconciliation_type=row["reconciliation_type"],
                    notes=row["notes"],
                    reconciled_at=datetime.fromisoformat(row["reconciled_at"]) if row["reconciled_at"] else None
                )
                for row in cursor.fetchall()
            ]

    def get_unreconciled_transactions(self) -> List[BankTransaction]:
        """Get bank transactions that haven't been reconciled yet"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bt.* FROM bank_transactions bt
                LEFT JOIN reconciliations r ON bt.id = r.bank_transaction_id
                WHERE r.id IS NULL
                ORDER BY bt.transaction_date DESC
            """)
            return [
                BankTransaction(
                    id=row["id"],
                    transaction_date=date.fromisoformat(row["transaction_date"]) if isinstance(row["transaction_date"], str) else row["transaction_date"],
                    amount=row["amount"],
                    description=row["description"],
                    reference=row["reference"],
                    counterparty=row["counterparty"],
                    transaction_type=row["transaction_type"],
                    account_balance=row["account_balance"],
                    imported_at=datetime.fromisoformat(row["imported_at"]) if row["imported_at"] else None
                )
                for row in cursor.fetchall()
            ]

    # VAT reporting methods
    def get_vat_report_data(self, year: int, quarter: int) -> dict:
        """Get VAT report data for a specific quarter"""
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
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get sales data (invoices)
            cursor.execute("""
                SELECT 
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(subtotal), 0) as total_sales,
                    COALESCE(SUM(tax_amount), 0) as output_vat
                FROM invoices 
                WHERE issue_date >= ? AND issue_date <= ?
                AND status != 'draft'
            """, (start_date, end_date))
            
            sales_data = cursor.fetchone()
            
            # Get expense data (purchases)
            cursor.execute("""
                SELECT 
                    COUNT(*) as expense_count,
                    COALESCE(SUM(amount - vat_amount), 0) as total_purchases,
                    COALESCE(SUM(vat_amount), 0) as input_vat
                FROM expenses 
                WHERE expense_date >= ? AND expense_date <= ?
                AND is_deductible = 1
            """, (start_date, end_date))
            
            expense_data = cursor.fetchone()
            
            return {
                'year': year,
                'quarter': quarter,
                'start_date': start_date,
                'end_date': end_date,
                'invoice_count': sales_data['invoice_count'],
                'expense_count': expense_data['expense_count'],
                'total_sales': sales_data['total_sales'],
                'total_purchases': expense_data['total_purchases'],
                'output_vat': sales_data['output_vat'],
                'input_vat': expense_data['input_vat'],
                'net_vat': sales_data['output_vat'] - expense_data['input_vat']
            }