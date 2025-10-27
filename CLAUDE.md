# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**🎉 UNIFIED ACCOUNTING SYSTEM - VERSION 1.0.0**

This is a comprehensive MCP (Model Context Protocol) Invoice Server with a **unified accounting system** featuring Swedish compliance, double-entry bookkeeping, and professional financial reporting.

**Current System Status:**
- ✅ **Unified Accounting System**: OPERATIONAL
- ✅ **Swedish Chart of Accounts**: LOADED (54 BAS 2022 IT Consultant accounts)
- ✅ **Double-Entry Bookkeeping**: WORKING with Swedish VAT compliance
- ✅ **Financial Reporting**: FUNCTIONAL (Trial Balance, Income Statement, Balance Sheet)
- ✅ **Invoice Management**: READY
- ✅ **Project Structure**: REORGANIZED (Modular Architecture)
- ✅ **Test Infrastructure**: COMPLETE (pytest with in-memory databases)
- ✅ **Email Parser**: REMOVED (Clean codebase)

**Key Business Features:**
- **Swedish Compliance**: BAS 2022 chart of accounts, multi-rate VAT (25%, 12%, 6%, 0%), Swedish payment reminders
- **VAT Rounding**: Automatic whole-number VAT per Skatteverket (22 kap. 1 § SFF) with account 3740 adjustments
- **Double-Entry Bookkeeping**: Automatic voucher generation with journal entries
- **Financial Reporting**: Trial balance, income statements, balance sheets
- **Invoice System**: Professional PDF generation with Swedish business requirements
- **Expense Tracking**: Comprehensive expense management with VAT handling
- **Bank Reconciliation**: Transaction matching and reconciliation tools
- **Modern Architecture**: Modular, service-oriented design with comprehensive testing
- **Test Suite**: pytest with in-memory databases, zero production data risk

**Data Storage:**
- SQLite database at `~/.mcp-accounting-server/invoices.db`
- 12 database tables for comprehensive accounting
- PDF output to `~/Desktop/` with WeasyPrint

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

### Testing
```bash
# Set up environment with uv (recommended)
uv sync --extra dev

# Run pytest suite (recommended - in-memory databases, no production impact)
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_vat_rounding.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run comprehensive integration test suite
uv run python test_comprehensive.py

# Test server directly
uv run python run_server.py
```

**Testing Philosophy:**
- All tests use in-memory SQLite databases (`:memory:`)
- Zero impact on production database
- Fresh database for each test (perfect isolation)
- Fast execution (milliseconds per test)
- See `tests/README.md` and `ai/docs/best-practices.md` for details

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff check src/

# Run all quality checks
ruff check src/ && black src/
```

## Architecture Overview

### 🏗️ Modular Service-Oriented Architecture

**Server (`src/server.py`):**
- Main MCP server using FastMCP framework
- Exposes 20+ tools (AI-controlled actions) and resources (data access)
- Integrates all modules: invoicing, accounting, expenses, reporting, reconciliation

**Database Layer (`src/database/`):**
- **base.py**: Core DatabaseManager with SQLite storage and fallback locations
- **invoice_db.py**: Invoice and customer operations
- **expense_db.py**: Expense and transaction operations  
- **accounting_db.py**: Chart of accounts, vouchers, journal entries

**Models Layer (`src/models/`):**
- **invoice_models.py**: Invoice, Customer, LineItem, PaymentReminder models
- **expense_models.py**: Expense, BankTransaction, Reconciliation models
- **accounting_models.py**: Account, Voucher, JournalEntry, Financial statement models

**Service Modules (`src/modules/`):**
- **invoicing/**: PDF generation, payment reminders, invoice services
- **accounting/**: Chart of accounts, voucher system, journal entries, financial reporting
- **expenses/**: Expense tracking and management
- **reporting/**: Financial statements, VAT reporting
- **reconciliation/**: Bank reconciliation services

**Templates (`src/templates/`):**
- Embedded Jinja2 templates organized by functionality
- Invoice, reminder, and report layouts
- Swedish compliance formatting

### Key Features

**Enhanced Address Support:**
- Legacy customers: simple email + optional address string
- Enhanced customers: structured fields (street, postal_code, city, country, company, VAT number)
- Backward compatibility maintained through `get_formatted_address()` method

**Swedish Business Compliance:**
- 25% VAT rate (configurable via tax_rate)
- Swedish interest calculation for payment reminders
- Proper org numbers and VAT numbers

**Payment Reminders:**
- Swedish law-compliant interest calculations
- Configurable reminder fees and delay compensation
- Supports business vs consumer customer types

## MCP Integration

### 🛠️ Comprehensive Tool Suite (20+ Tools)

**Invoice Management:**
- `create_invoice` - Create invoices with line items and automatic voucher generation
- `generate_pdf` - Generate professional PDF invoices
- `update_invoice_status` - Update invoice status (draft, sent, paid, overdue, cancelled)
- `check_overdue_invoices` - Find invoices needing payment reminders
- `create_payment_reminder` - Swedish law-compliant payment reminders with interest
- `generate_reminder_pdf` - Generate payment reminder PDFs

**Accounting System:**
- `generate_trial_balance` - Complete trial balance with all accounts
- `generate_income_statement` - Profit & loss statement for specified period
- `generate_balance_sheet` - Balance sheet with assets, liabilities, equity
- `create_accounting_voucher` - Manual voucher creation with journal entries
- `get_account_balance` - Individual account balance and transaction history
- `post_accounting_period` - Close accounting periods

**Expense Management:**
- `add_expense` - Record business expenses with VAT calculation
- `list_expenses` - Filter and list expenses by category/date
- `import_bank_transactions` - Import bank data for reconciliation
- `reconcile_transaction` - Match bank transactions with invoices/expenses

**Financial Reporting:**
- `generate_vat_report` - Swedish quarterly VAT reporting
- `export_financial_data` - Export data for external accounting software

**Documentation & Help:**
- `tools_documentation` - Get comprehensive tool help and system overview
- `workflow_guide` - Step-by-step workflow documentation
- `swedish_compliance_guide` - Swedish compliance requirements

**Resources (Data Access):**
- `invoices://list` - List all invoices with filtering
- `invoices://list/{status}` - List invoices by status
- `invoice://{invoice_id}` - Detailed invoice information
- `customers://list` - All customers with structured data
- `customer://{email}` - Customer lookup by email
- `expenses://list` - Expense data access
- `accounts://chart` - Swedish chart of accounts

## Getting Started with the System

### IMPORTANT: Always Start with Documentation

**Before using any accounting tools, ALWAYS begin with:**

```
tools_documentation()
```

This provides:
- Complete overview of available tools
- Common workflows and best practices
- Swedish compliance requirements
- Quick start examples

### Understanding Tools

Get detailed help for specific tools:

```
# Quick reference
tools_documentation("create_invoice")

# Complete documentation
tools_documentation("create_invoice", "full")

# Browse by category
tools_documentation(category="invoicing")
```

### Workflow Guidance

Get step-by-step guides for common processes:

```
# Complete invoice lifecycle
workflow_guide("invoice_to_payment")

# Expense recording process
workflow_guide("expense_recording")

# Month-end closing procedures
workflow_guide("monthly_closing")
```

### Swedish Compliance

Get compliance-specific information:

```
# VAT reporting requirements
swedish_compliance_guide("vat_reporting")

# Invoice legal requirements
swedish_compliance_guide("invoice_requirements")
```

## Development Guidelines

### Customer Data Handling
- Always use `customer.get_formatted_address()` for address display
- Support both legacy and enhanced customer formats
- When creating customers from recipient objects, extract structured data properly

### Invoice Creation
- Use either `customer_email` (legacy) OR `recipient` (enhanced) parameter, never both
- Validate recipient objects have required email field
- Auto-generate invoice numbers using `db.generate_invoice_number()`
- Default to 30-day payment terms and 25% Swedish VAT

### Database Operations
- Use context manager `with db.get_connection()` for all database operations
- Handle date formatting properly (ISO format for storage)
- Update invoice reminder counts when creating payment reminders

### PDF Generation
- All templates are embedded in `src/templates.py`
- Use WeasyPrint for professional PDF output
- Save PDFs to Desktop by default for easy access
- Support both invoice and payment reminder PDFs

## Testing

### Pytest Suite (Primary)

**Location:** `tests/`

The project uses pytest with in-memory SQLite databases for fast, isolated testing:

**Run Tests:**
```bash
uv sync --extra dev
uv run pytest tests/ -v
```

**Test Coverage:**
- Swedish VAT rounding compliance (all rates: 25%, 12%, 6%, 0%)
- Floating-point precision handling
- In-memory database fixtures
- Edge cases (tiny amounts, large amounts, rounding thresholds)

**Key Features:**
- ✅ **Zero Production Risk**: All tests use `:memory:` databases
- ✅ **Fast**: No disk I/O, runs in milliseconds
- ✅ **Isolated**: Fresh database per test
- ✅ **Repeatable**: Same starting state every time
- ✅ **CI/CD Ready**: No external dependencies

**Documentation:**
- See `tests/README.md` for detailed usage
- See `ai/docs/best-practices.md` for development workflow
- Tests serve as usage examples for the accounting service

### Integration Test Suite

The `test_comprehensive.py` file provides complete system testing:

**Core System Tests:**
- Module imports and project structure
- Database initialization and table creation
- Swedish Chart of Accounts (54 accounts)
- Double-entry bookkeeping system
- Voucher creation and journal entries
- Financial reporting (trial balance, income statement, balance sheet)

**Business Logic Tests:**
- Customer model functionality and address formatting
- Expense category validation
- Invoice status handling
- Email parser removal verification

**How to Run Tests:**
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  
uv pip install -e .
python test_comprehensive.py

# Or with system Python
python3 test_comprehensive.py

# Expected output on success:
# 🎉 ALL TESTS PASSED! 🎉
# TEST RESULTS: 9/9 PASSED
```

**Test Coverage:**
- ✅ Database: SQLite schema and data integrity
- ✅ Accounting: Swedish BAS 2022 compliance
- ✅ Models: Customer, Invoice, Expense, Accounting
- ✅ Services: Invoice, Accounting, Reporting
- ✅ Structure: Modular organization verification

Run tests before making changes to ensure system compatibility and integrity.

## Common Development Tasks

- **Adding new invoice fields**: Update models in `src/models/`, database schema in `src/database/`, and templates
- **Modifying PDF layout**: Edit embedded templates in `src/templates/all_templates.py`
- **Adding new MCP tools**: Define function in `server.py` and register with `@mcp.tool()` decorator
- **Extending accounting**: Add new accounts to `src/models/accounting_models.py` STANDARD_ACCOUNTS
- **New service modules**: Create in appropriate `src/modules/` subdirectory with proper `__init__.py`
- **Database changes**: Update schema in `src/database/base.py` and add migration logic

## 🚀 Recent Major Updates (Version 0.2.0)

### ✅ **Unified Accounting System Implementation**
- **Swedish Chart of Accounts**: 54 BAS 2022 IT consultant-specific accounts loaded
- **Double-Entry Bookkeeping**: Automatic voucher generation with balanced journal entries
- **Financial Reporting**: Trial balance, income statement, balance sheet generation
- **Accounting Periods**: Support for monthly/quarterly closing with Swedish compliance

### ✅ **Project Structure Reorganization**
- **Modular Architecture**: Service-oriented design with clear separation of concerns
- **Database Layer**: Split into focused modules (invoice_db, expense_db, accounting_db)
- **Service Modules**: Organized by functionality (invoicing, accounting, expenses, reporting, reconciliation)
- **Models**: Separated by domain (invoice_models, expense_models, accounting_models)

### ✅ **Code Quality & Testing**
- **Comprehensive Test Suite**: `test_comprehensive.py` with 9 test categories
- **Email Parser Removal**: Clean codebase with unused functionality removed
- **Type Safety**: Fixed all Pyright issues with proper type annotations
- **uv Integration**: Modern Python development with pyproject.toml configuration

### ✅ **Development Environment**
- **uv Package Management**: Fast, reliable dependency management
- **Production Ready**: Server starts successfully with all dependencies
- **Template System**: Proper template organization and imports
- **Swedish Compliance**: All VAT, accounting, and legal requirements met

The system is now a **production-ready unified accounting platform** with Swedish compliance, suitable for IT consultants and small businesses requiring professional invoicing and accounting capabilities.

## Important Documentation

**Always read these files when working on this project:**

1. **`ai/hist/diary.mdx`** - Complete development history, bug fixes, architectural decisions
2. **`ai/docs/best-practices.md`** - Development workflow, testing guidelines, uv commands
3. **`tests/README.md`** - Test suite usage and fixture documentation

**Latest Major Changes (v1.0.0):**
- Swedish VAT rounding with account 3740 (Öresutjämning)
- Floating-point comparison fix in `post_voucher()`
- In-memory database testing infrastructure
- Service layer refactoring for VAT calculations
