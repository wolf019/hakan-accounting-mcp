# MCP Accounting Server - Full Bookkeeping System Implementation

## Project Overview

Transform the existing `mcp-invoice-server` into a comprehensive `mcp-accounting-server` that provides complete bookkeeping automation for Swedish businesses. This unified MCP server will handle invoicing, expense tracking, double-entry bookkeeping, and financial reporting in a single, integrated system.

## Current State

The existing system successfully handles:
- ✅ Invoice creation and PDF generation
- ✅ Customer management  
- ✅ Payment reminders with Swedish legal compliance
- ✅ Basic expense tracking
- ✅ Bank transaction import
- ✅ VAT calculations

## Implementation Goals

### Phase 1: Core Accounting Foundation
1. **Project Rename**: `mcp-invoice-server` → `mcp-accounting-server`
2. **Chart of Accounts**: Swedish standard account structure (BAS 2022)
3. **Voucher System**: Complete audit trail for all transactions
4. **Double-Entry Bookkeeping**: Automatic journal entries for all transactions
5. **Modular Architecture**: Organize code into logical accounting modules

### Phase 2: Advanced Financial Features  
1. **Financial Statements**: Income statement, balance sheet, cash flow
2. **Automated Bookkeeping**: Auto-generate vouchers from invoices/expenses
3. **Account Reconciliation**: Match transactions across accounts
4. **Closing Procedures**: Period-end processes and year-end closing

## Database Schema Extensions

### New Core Tables

```sql
-- Swedish Chart of Accounts (BAS 2022 standard)
accounts {
    int id PK
    text account_number UK     -- 1910, 2641, 3001, etc.
    text account_name          -- "Kundfordringar", "Utgående moms"
    text account_type          -- "asset", "liability", "income", "expense", "equity"
    text account_category      -- "current_assets", "operating_income", etc.
    text parent_account        -- For account hierarchies
    boolean is_active
    boolean requires_vat       -- Auto-calculate VAT for this account
    decimal balance            -- Current account balance
    timestamp created_at
}

-- Vouchers (Verifikationer) - audit trail container
vouchers {
    int id PK
    text voucher_number UK     -- V001, V002, V003, etc.
    date voucher_date
    text description
    text voucher_type          -- "sales_invoice", "purchase", "payment", "adjustment"
    int source_invoice_id FK   -- Link to originating invoice
    int source_expense_id FK   -- Link to originating expense
    int source_reminder_id FK  -- Link to payment reminder
    decimal total_amount
    text reference             -- External reference (invoice number, receipt, etc.)
    boolean is_posted          -- Whether journal entries are finalized
    timestamp created_at
    timestamp posted_at
}

-- Journal Entries (Bokföringsposter) - double-entry records
journal_entries {
    int id PK
    int voucher_id FK
    int account_id FK
    text description
    decimal debit_amount       -- Debit side of entry
    decimal credit_amount      -- Credit side of entry
    text reference             -- Additional reference info
    timestamp created_at
}

-- Accounting Periods for closing procedures
accounting_periods {
    int id PK
    int year
    int period                 -- 1-12 for months, or 1-4 for quarters
    date start_date
    date end_date
    boolean is_closed
    text period_type           -- "monthly", "quarterly", "yearly"
    timestamp closed_at
    timestamp created_at
}
```

### Enhanced Existing Tables

```sql
-- Add accounting integration to existing tables
ALTER TABLE invoices ADD COLUMN voucher_id INTEGER;
ALTER TABLE expenses ADD COLUMN voucher_id INTEGER;
ALTER TABLE payment_reminders ADD COLUMN voucher_id INTEGER;
```

## Swedish Chart of Accounts (BAS 2022)

Implement standard Swedish account structure:

```python
STANDARD_ACCOUNTS = {
    # Assets (Tillgångar)
    "1910": {"name": "Kundfordringar", "type": "asset", "category": "current_assets"},
    "1920": {"name": "Övriga kortfristiga fordringar", "type": "asset", "category": "current_assets"},
    "1930": {"name": "Förutbetalda kostnader", "type": "asset", "category": "current_assets"},
    "1940": {"name": "Banktillgodohavanden", "type": "asset", "category": "current_assets"},
    
    # Liabilities (Skulder)
    "2440": {"name": "Leverantörsskulder", "type": "liability", "category": "current_liabilities"},
    "2610": {"name": "Ingående moms", "type": "liability", "category": "current_liabilities"},
    "2611": {"name": "Utgående moms", "type": "liability", "category": "current_liabilities"},
    
    # Income (Intäkter)
    "3001": {"name": "Konsultintäkter", "type": "income", "category": "operating_income"},
    "3002": {"name": "Utvecklingsintäkter", "type": "income", "category": "operating_income"},
    
    # Expenses (Kostnader)
    "5410": {"name": "IT-tjänster", "type": "expense", "category": "operating_expenses"},
    "5611": {"name": "Programvaror", "type": "expense", "category": "operating_expenses"},
    "6212": {"name": "Telefon", "type": "expense", "category": "operating_expenses"},
    
    # Equity (Eget kapital)
    "2018": {"name": "Årets resultat", "type": "equity", "category": "retained_earnings"},
}
```

## New MCP Tools Implementation

### Core Accounting Tools

```python
@mcp.tool()
def create_voucher(
    description: str,
    voucher_type: str,
    source_id: Optional[int] = None,
    journal_entries: List[Dict] = None
) -> str:
    """
    Create accounting voucher with journal entries.
    Automatically generates voucher number and ensures debit = credit.
    """

@mcp.tool()
def post_journal_entries(voucher_id: int) -> str:
    """
    Post journal entries to accounts and update balances.
    Makes the voucher final and updates all affected account balances.
    """

@mcp.tool()
def get_account_balance(account_number: str, as_of_date: str = None) -> Dict:
    """
    Get current balance for specific account.
    Returns: {balance, last_transaction_date, transaction_count}
    """

@mcp.tool()
def generate_trial_balance(as_of_date: str = None) -> str:
    """
    Generate trial balance showing all account balances.
    Verifies that total debits equal total credits.
    """
```

### Financial Reporting Tools

```python
@mcp.tool()
def generate_income_statement(
    start_date: str,
    end_date: str,
    format: str = "summary"
) -> str:
    """
    Generate income statement (resultaträkning) for period.
    Shows revenue, expenses, and net income.
    """

@mcp.tool()
def generate_balance_sheet(as_of_date: str = None) -> str:
    """
    Generate balance sheet (balansräkning) as of specific date.
    Shows assets, liabilities, and equity.
    """

@mcp.tool()
def generate_cash_flow_statement(
    start_date: str,
    end_date: str
) -> str:
    """
    Generate cash flow statement for period.
    Shows operating, investing, and financing activities.
    """

@mcp.tool()
def close_accounting_period(
    year: int,
    period: int,
    period_type: str = "monthly"
) -> str:
    """
    Close accounting period and calculate period results.
    Prevents further modifications to closed period.
    """
```

### Automated Bookkeeping Tools

```python
@mcp.tool()
def auto_generate_vouchers(
    start_date: str = None,
    end_date: str = None,
    transaction_types: List[str] = None
) -> str:
    """
    Automatically generate vouchers for unprocessed transactions.
    Handles invoices, expenses, payments, and reminders.
    """

@mcp.tool()
def reconcile_account(
    account_number: str,
    statement_balance: float,
    statement_date: str
) -> str:
    """
    Reconcile account balance with external statement.
    Identifies discrepancies and suggests corrections.
    """
```

## Automatic Voucher Generation

### Invoice Voucher Example
When invoice is created, automatically generate:

```
Voucher V001: Sales Invoice 2025-004
├── Debit:  1910 (Kundfordringar)     31,250.00
├── Credit: 2611 (Utgående moms)       6,250.00
└── Credit: 3001 (Konsultintäkter)    25,000.00
```

### Expense Voucher Example
When expense is added, automatically generate:

```
Voucher V002: Office Supplies Purchase
├── Debit:  5410 (Kontorsmaterial)       400.00
├── Debit:  2610 (Ingående moms)         100.00
└── Credit: 2440 (Leverantörsskulder)    500.00
```

## Project Structure Reorganization

```
mcp-accounting-server/
├── src/
│   ├── modules/
│   │   ├── invoicing/
│   │   │   ├── invoice_service.py
│   │   │   ├── reminder_service.py
│   │   │   └── pdf_generator.py
│   │   ├── expenses/
│   │   │   ├── expense_service.py
│   │   │   └── receipt_processor.py
│   │   ├── accounting/
│   │   │   ├── voucher_service.py
│   │   │   ├── journal_service.py
│   │   │   ├── account_service.py
│   │   │   └── chart_of_accounts.py
│   │   ├── reporting/
│   │   │   ├── financial_statements.py
│   │   │   ├── vat_reporting.py
│   │   │   └── analytics.py
│   │   └── reconciliation/
│   │       ├── bank_reconciliation.py
│   │       └── account_reconciliation.py
│   ├── models/
│   │   ├── accounting_models.py
│   │   ├── invoice_models.py
│   │   └── expense_models.py
│   ├── database/
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   └── database.py
│   ├── templates/
│   │   ├── financial_reports/
│   │   ├── invoices/
│   │   └── vouchers/
│   └── server.py
```

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. **Rename project** and update all references
2. **Add new database tables** with migration scripts
3. **Implement chart of accounts** with Swedish standards
4. **Create voucher and journal entry services**
5. **Add basic accounting MCP tools**

### Phase 2: Integration (Week 2)  
1. **Auto-generate vouchers** for existing invoices/expenses
2. **Implement financial statement generation**
3. **Add account reconciliation features**
4. **Create comprehensive test suite**
5. **Update documentation and examples**

### Phase 3: Enhancement (Week 3)
1. **Advanced reporting and analytics**
2. **Period closing procedures**
3. **Performance optimization**
4. **Extended Swedish compliance features**
5. **User experience improvements**

## Swedish Compliance Features

- **BAS 2022 Chart of Accounts**: Standard Swedish account structure
- **SIE Export**: Standard format for Swedish accounting software
- **VAT Integration**: Automatic VAT posting to correct accounts
- **Annual Closing**: Swedish year-end procedures
- **Audit Trail**: Complete transaction history for tax compliance

## Success Criteria

1. **Complete Double-Entry**: All transactions automatically generate balanced journal entries
2. **Financial Statements**: Generate accurate income statement, balance sheet, and cash flow
3. **Swedish Compliance**: Full compliance with Swedish accounting standards
4. **Unified Interface**: Single MCP server handles all accounting functions
5. **Automatic Workflows**: Minimal manual intervention for routine bookkeeping
6. **Audit Trail**: Complete history of all financial transactions

## Usage Examples

```
"Create invoice for Pål, 20 hours at 1250 SEK" 
→ Invoice created, voucher generated, accounts updated

"Show me the income statement for Q2"
→ Professional financial statement with all revenue and expenses

"What's my current cash position?"
→ Real-time balance from bank account and outstanding receivables

"Generate all missing vouchers from last month"
→ Automatic processing of unrecorded transactions

"Close the books for June 2025"
→ Period closing with automated journal entries
```

This implementation will create Sweden's first AI-powered, fully integrated accounting system accessible through natural language commands via Claude Desktop.
