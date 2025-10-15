# MCP Accounting Server

**Sweden's First AI-Powered Unified Accounting System**

A comprehensive MCP (Model Context Protocol) accounting server that provides complete double-entry bookkeeping, Swedish compliance, and professional financial reporting through natural language conversation with Claude Desktop.

## 🏢 System Overview

The MCP Accounting Server transforms traditional accounting into an AI-accessible system where complex financial operations become as simple as natural language commands. Built for Swedish businesses, it provides:

- **Double-Entry Bookkeeping**: Automatic voucher generation with balanced journal entries
- **Swedish Compliance**: BAS 2022 chart of accounts, VAT handling, and legal requirements
- **Professional Reporting**: Trial balance, income statements, and balance sheets
- **Invoice Management**: Complete invoice lifecycle from creation to payment
- **Expense Tracking**: Business expense management with VAT calculations
- **Bank Reconciliation**: Transaction matching and account reconciliation

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-accounting-server

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
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

### Invoice Requirements
- Sequential invoice numbering
- VAT registration number display
- Proper payment terms (30 days standard)
- Interest calculation after due date

### Chart of Accounts
- **BAS 2022 Standard:** 54 predefined Swedish accounts
- **Proper Classifications:** Assets, liabilities, income, expenses, equity
- **VAT Integration:** Automatic posting to correct VAT accounts

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
# Comprehensive test suite
source .venv/bin/activate
python test_comprehensive.py

# Expected output: 9/9 PASSED
```

### Code Quality
```bash
# Format and lint
black src/
ruff check src/

# Run quality checks
ruff check src/ && black src/
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
- Run `python test_comprehensive.py` to validate

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
