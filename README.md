# MCP Accounting Server

**Version 1.0.0 - Sweden's First AI-Powered Unified Accounting System**

A comprehensive MCP (Model Context Protocol) accounting server that provides complete double-entry bookkeeping, Swedish compliance, and professional financial reporting through natural language conversation with Claude Desktop.

**🎉 Version 1.0.0 Release:** Production-ready with Swedish VAT rounding compliance, comprehensive pytest suite, and bank-level security. Fully tested and client-verified.

## 🏢 System Overview

The MCP Accounting Server transforms traditional accounting into an AI-accessible system where complex financial operations become as simple as natural language commands. Built for Swedish businesses, it provides:

- **Double-Entry Bookkeeping**: Automatic voucher generation with balanced journal entries
- **Swedish Compliance**: BAS 2022 chart of accounts, multi-rate VAT (25%, 12%, 6%, 0%), legal requirements
- **VAT Rounding**: Automatic whole-number VAT per Skatteverket (22 kap. 1 § SFF) with account 3740 adjustments
- **Professional Reporting**: Trial balance, income statements, and balance sheets
- **Invoice Management**: Complete invoice lifecycle from creation to payment
- **Expense Tracking**: Business expense management with VAT calculations
- **Bank Reconciliation**: Transaction matching and account reconciliation
- **Test Suite**: Comprehensive pytest suite with in-memory databases (zero production risk)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/tomaxberg/mcp-accounting-server.git
cd mcp-accounting-server

# Install dependencies (uv handles venv automatically)
uv sync

# For development with tests
uv sync --extra dev
```

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "accounting-server": {
      "command": "~/mcp-accounting-server/.venv/bin/python3",
      "args": ["~/mcp-accounting-server/run_server.py"]
    }
  }
}
```

### First Steps

**Always start with the documentation system:**

```
tools_documentation()
```

This provides a complete overview of available tools and workflows.

## 📋 How to Interact with the System

### 1. Getting Started - The Documentation System

**IMPORTANT:** Always begin any accounting session with:

```
tools_documentation()
```

This shows you:
- Available tools by category
- Common workflows
- Swedish compliance requirements
- Quick start examples

### 2. Understanding Tools

Get detailed help for any tool:

```
# Quick reference
tools_documentation("create_invoice")

# Complete documentation
tools_documentation("create_invoice", "full")

# Browse by category
tools_documentation(category="invoicing")
```

### 3. Common Workflows

Get step-by-step guides for common processes:

```
# Complete invoice process
workflow_guide("invoice_to_payment")

# Expense recording
workflow_guide("expense_recording")

# Month-end closing
workflow_guide("monthly_closing")
```

### 4. Swedish Compliance

Get compliance information:

```
# VAT reporting requirements
swedish_compliance_guide("vat_reporting")

# Invoice legal requirements
swedish_compliance_guide("invoice_requirements")

# Audit trail requirements
swedish_compliance_guide("audit_trail")
```

## 🛠️ Available Tools by Category

### 📄 Invoicing Tools
- **create_invoice** - Create customer invoices with automatic VAT and voucher generation
- **generate_pdf** - Generate professional PDF invoices
- **update_invoice_status** - Update invoice status (draft, sent, paid, overdue, cancelled)
- **check_overdue_invoices** - Find invoices needing payment reminders
- **create_payment_reminder** - Swedish law-compliant payment reminders with interest
- **generate_reminder_pdf** - Generate payment reminder PDFs

### 💰 Expense Management
- **add_expense** - Record business expenses with VAT calculation
- **list_expenses** - Filter and list expenses by category/date
- **import_bank_transactions** - Import bank data for reconciliation
- **reconcile_transaction** - Match bank transactions with invoices/expenses

### 📊 Core Accounting
- **create_accounting_voucher** - Manual voucher creation with journal entries
- **get_account_balance** - Individual account balance and transaction history
- **generate_trial_balance** - Complete trial balance with all accounts
- **post_accounting_period** - Close accounting periods

### 📈 Financial Reporting
- **generate_income_statement** - Profit & loss statement for specified period
- **generate_balance_sheet** - Balance sheet with assets, liabilities, equity
- **generate_vat_report** - Swedish quarterly VAT reporting
- **export_financial_data** - Export data for external accounting software

### 📚 Documentation & Help
- **tools_documentation** - Get tool help and system overview
- **workflow_guide** - Step-by-step workflow documentation
- **swedish_compliance_guide** - Swedish compliance requirements

## 💡 Usage Examples

### Creating an Invoice

```
# Start with documentation
tools_documentation("create_invoice")

# Create the invoice
create_invoice("customer@company.se", [
    {"description": "Consulting services", "quantity": 20, "unit_price": 1500}
], 30)

# Generate PDF
generate_pdf(invoice_id)
```

### Recording Expenses

```
# Get expense documentation
tools_documentation("add_expense")

# Record the expense
add_expense("Office supplies", 625, "office_supplies", "2025-01-15")

# List expenses by category
list_expenses("office_supplies")
```

### Month-End Closing

```
# Get workflow guide
workflow_guide("monthly_closing")

# Generate trial balance
generate_trial_balance()

# Generate financial statements
generate_income_statement("2025-01-01", "2025-01-31")
generate_balance_sheet("2025-01-31")
```

### VAT Reporting

```
# Get VAT compliance info
swedish_compliance_guide("vat_reporting")

# Generate VAT report
generate_vat_report(1, 2025)  # Q1 2025
```

## 🗂️ Data Storage & File Management

### Database Location
- **Database File:** `~/.mcp-accounting-server/invoices.db`
- **Contains:** Customers, invoices, expenses, accounting entries (12 tables)
- **Format:** SQLite with full transaction history

### PDF Output Location
- **PDF Files:** `~/Desktop/`
- **Format:** `invoice_YYYY-NNN.pdf` and `reminder_YYYY-NNN-REM.pdf`
- **Content:** Professional Swedish business documents

### Account Structure (BAS 2022)
- **1xxx:** Assets (Tillgångar)
- **2xxx:** Liabilities (Skulder)
- **3xxx:** Revenue (Intäkter)
- **5xxx-8xxx:** Expenses (Kostnader)

## 🇸🇪 Swedish Compliance Features

### VAT Handling
- **Standard Rate:** 25% (most services)
- **Reduced Rate:** 12% (food, hotels)
- **Low Rate:** 6% (books, newspapers)
- **Zero Rate:** 0% (exports)
- **Automatic Rounding:** VAT amounts rounded to whole SEK per Skatteverket requirement (22 kap. 1 § SFF)
- **Rounding Adjustments:** Account 3740 (Öres- och kronutjämning) used for precision differences

### Invoice Requirements
- Sequential invoice numbering
- VAT registration number display
- Proper payment terms (30 days standard)
- Interest calculation after due date

### Chart of Accounts
- **BAS 2022 Standard:** 54 predefined Swedish accounts for IT consultants
- **Proper Classifications:** Assets, liabilities, income, expenses, equity
- **VAT Integration:** Automatic posting to correct VAT accounts (2640 input, 2650 output)
- **Rounding Account:** Account 3740 (Öres- och kronutjämning) for VAT rounding adjustments

### Audit Trail
- Complete transaction history
- Voucher-based double-entry system
- 7-year retention compliance
- Searchable electronic records

## 🔄 Common Workflows

### Invoice to Payment
1. Create invoice → 2. Generate PDF → 3. Send to customer → 4. Import bank data → 5. Reconcile payment

### Expense Recording
1. Add expense → 2. Categorize → 3. Auto-generate voucher → 4. Post to accounts

### Monthly Closing
1. Reconcile accounts → 2. Generate trial balance → 3. Create adjusting entries → 4. Close period

## 🧪 Testing & Quality Assurance

### Run Tests
```bash
# Install test dependencies
uv sync --extra dev

# Run pytest suite (recommended - in-memory databases, zero production risk)
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_vat_rounding.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run integration test suite
uv run python test_comprehensive.py
# Expected output: 9/9 PASSED
```

**Testing Features:**
- ✅ In-memory SQLite databases (`:memory:`)
- ✅ Zero impact on production database
- ✅ Fast execution (milliseconds per test)
- ✅ Perfect isolation (fresh database per test)
- ✅ See `tests/README.md` for detailed documentation

### Code Quality
```bash
# Format and lint
uv run ruff check src/ --fix
uv run ruff format src/

# Type checking
uv run mypy src/

# Run all quality checks
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/
```

## 🔧 Development & Customization

### Company Information
Edit `DEFAULT_COMPANY_INFO` in `src/server.py` for your business:
- Company name and address
- VAT registration number
- Banking details
- Contact information

### Chart of Accounts
Modify `STANDARD_ACCOUNTS` in `src/models/accounting_models.py` to add custom accounts while maintaining BAS 2022 compliance.

### Database Schema
The system uses 12 tables for complete accounting:
- customers, invoices, line_items, payment_reminders
- expenses, bank_transactions, reconciliations
- accounts, vouchers, journal_entries
- accounting_periods, vat_periods

## 🛡️ Security & Compliance

### Data Protection
- Customer data stored locally in SQLite
- No external data transmission
- Proper file permissions recommended
- Regular backup procedures essential

### Swedish Legal Compliance
- **Bokföringslagen (BFL):** Swedish Accounting Act compliance
- **Momslagen:** VAT law compliance
- **Skatteverket:** Tax authority reporting standards
- **GDPR:** EU data protection regulations

### Audit Requirements
- Complete transaction history maintained
- Voucher-based double-entry system
- 7-year record retention
- Searchable electronic format

## 🆘 Troubleshooting

### Common Issues

**Server won't start:**
- Check Python path in Claude Desktop config
- Verify virtual environment is activated
- Ensure all dependencies installed

**Database errors:**
- Check `~/.mcp-accounting-server/` directory exists
- Verify SQLite file permissions
- Run `uv run pytest tests/` or `uv run python test_comprehensive.py` to validate

**PDF generation fails:**
- Install WeasyPrint dependencies
- Check write permissions to Desktop
- Verify HTML template rendering

**Tools not working:**
- Always start with `tools_documentation()`
- Check parameter format in tool documentation
- Verify Swedish compliance requirements

### Getting Help

1. **System Overview:** `tools_documentation()`
2. **Specific Tool:** `tools_documentation("tool_name", "full")`
3. **Workflow Help:** `workflow_guide("workflow_name")`
4. **Compliance Info:** `swedish_compliance_guide("topic")`

## 🎯 Best Practices

### For AI Assistants
1. **Always start with:** `tools_documentation()`
2. **Understand before acting:** Review tool documentation
3. **Follow workflows:** Use documented patterns
4. **Check compliance:** Verify Swedish requirements
5. **Validate results:** Check account balances and reports

### For Users
1. **Learn the system:** Start with documentation tools
2. **Follow workflows:** Use established accounting processes
3. **Maintain compliance:** Keep Swedish requirements in mind
4. **Regular reporting:** Generate monthly financial statements
5. **Backup data:** Protect your business information

This system provides Sweden's first AI-powered accounting platform accessible through natural language commands while maintaining professional accounting standards and regulatory compliance.
