"""
Comprehensive documentation data for all MCP accounting tools.
Includes Swedish compliance information and best practices.
"""

from typing import Dict, List, Any

# Swedish Chart of Accounts (BAS 2022) Reference
ACCOUNT_MAPPINGS = {
    "1910": {"name": "Kundfordringar", "usage": "Customer invoices", "vat": False},
    "2611": {"name": "Utgående moms", "usage": "VAT on sales", "vat": True},
    "2610": {"name": "Ingående moms", "usage": "VAT on purchases", "vat": True},
    "3001": {"name": "Konsultintäkter", "usage": "Service revenue", "vat": False},
    "2440": {"name": "Leverantörsskulder", "usage": "Accounts payable", "vat": False},
    "1940": {"name": "Banktillgodohavanden", "usage": "Bank deposits", "vat": False},
    "5410": {"name": "Kontorsmaterial", "usage": "Office supplies", "vat": False},
    "6212": {"name": "Telefon", "usage": "Telephone costs", "vat": False},
    "3740": {"name": "Öres- och kronutjämning", "usage": "Rounding differences", "vat": False},
}

# Swedish VAT Rates
VAT_RATES = {
    "25%": {"description": "Standard rate for most services", "account": "2611"},
    "12%": {"description": "Reduced rate for food, hotels", "account": "2612"},
    "6%": {"description": "Low rate for books, newspapers", "account": "2613"},
    "0%": {"description": "Exports and exempt services", "account": None}
}

# Common Accounting Workflows (Updated for Consolidated Toolbox)
WORKFLOWS = {
    "invoice_to_payment": {
        "description": "Complete invoice lifecycle from creation to payment",
        "steps": [
            "manage_invoice('create', line_items=[...], company='...', vat_number='...')",
            "generate_pdf('invoice', invoice_id)",
            "manage_banking('import_csv', csv_data='...')",
            "manage_payment('reconcile', bank_transaction_id=X, invoice_id=Y)",
            "manage_invoice('update_status', invoice_id=Y, status='paid')"
        ],
        "accounting_impact": "Auto-generates: DR 1510 (A/R), CR 3001 (Revenue) & CR 2650 (VAT), then reverses on payment"
    },

    "expense_recording": {
        "description": "Record business expense with automatic VAT and voucher generation",
        "steps": [
            "record_business_event('expense', 'HP printer ink cartridges', 1250.00, 'Staples Sverige AB')",
            "# Auto-generates: DR 6110 (Expense) + DR 2650 (VAT), CR 1930 (Bank)"
        ],
        "accounting_impact": "Single function call replaces: create_voucher → add_journal_entry × 3 → post_voucher"
    },

    "monthly_closing": {
        "description": "Month-end procedures for clean books with consolidated tools",
        "steps": [
            "audit_voucher('list_period', start_date='2025-01-01', end_date='2025-01-31')",
            "manage_payment('list_unmatched')",
            "generate_report('trial_balance')",
            "record_business_event('adjustment', '...', amount, 'Manual Entry')",
            "generate_report('income_statement', start_date='2025-01-01', end_date='2025-01-31')",
            "generate_report('balance_sheet', as_of_date='2025-01-31')"
        ],
        "accounting_impact": "Comprehensive month-end with period analysis and audit trail"
    }
}

# AI GUIDANCE FOR HANDLING VAGUE QUESTIONS
AI_GUIDANCE = {
    "handle_vague_questions": {
        "principle": "When users provide incomplete information, ALWAYS ask for all required parameters",
        "examples": [
            "User: 'I want to record an expense' → Ask: What was purchased? How much? From which supplier? When?",
            "User: 'Create an invoice' → Ask: Which customer? What services/products? Line items with quantities and prices?",
            "User: 'Generate a report' → Ask: Which type (trial balance, income statement, balance sheet)? What date range?"
        ],
        "required_approach": [
            "Never assume missing parameters",
            "Always ask for counterparty (Swedish legal requirement)",
            "Always ask for detailed descriptions (Swedish legal requirement)",
            "Suggest examples to guide the user",
            "Explain why the information is needed (legal compliance)"
        ]
    }
}

# CONSOLIDATED TOOL DOCUMENTATION (9 Tools)
TOOL_DOCUMENTATION = {
    "record_business_event": {
        "name": "record_business_event",
        "category": "core_accounting",
        "essentials": {
            "description": "🎯 UNIVERSAL business event recorder - replaces create_voucher + add_journal_entry + post_voucher",
            "key_parameters": ["event_type", "description", "amount", "counterparty", "vat_rate"],
            "example": 'record_business_event("expense", "HP printer ink cartridges", 1250.00, "Staples Sverige AB", vat_rate=0.25)',
            "performance": "Single call = automatic voucher + journal entries + posting with Swedish compliance",
            "tips": [
                "event_type: expense|invoice|payment|transfer|adjustment",
                "description: Detailed (min 10 chars) - Swedish legal requirement",
                "counterparty: Business partner - Swedish legal requirement",
                "vat_rate: 0.25 (25%), 0.12 (12%), 0.06 (6%), 0.0 (0%), or None (no VAT)",
                "Auto-calculates VAT, account mappings, and journal entries"
            ],
            "swedish_compliance": [
                "Unbroken voucher numbering per BFL requirements",
                "Detailed business descriptions per NJA 2020 s. 497",
                "Mandatory counterparty documentation",
                "Auto-generates balanced double-entry with Swedish chart of accounts"
            ]
        },
        "full": {
            "description": "Revolutionary single-function business event processor that replaces the complex voucher workflow. Automatically maps business events to Swedish BAS 2022 accounts, calculates VAT, generates vouchers, creates journal entries, and posts transactions. Ensures Swedish legal compliance including detailed descriptions and counterparty documentation.",
            "parameters": {
                "event_type": {
                    "type": "string",
                    "description": "Business event type",
                    "required": True,
                    "options": ["expense", "invoice", "payment", "transfer", "adjustment"]
                },
                "description": {
                    "type": "string",
                    "description": "Detailed business description (min 10 chars, Swedish legal requirement)",
                    "required": True,
                    "example": "HP printer ink cartridges for main office"
                },
                "amount": {
                    "type": "float",
                    "description": "Total amount in SEK",
                    "required": True
                },
                "counterparty": {
                    "type": "string",
                    "description": "Business partner (Swedish legal requirement)",
                    "required": True,
                    "example": "Staples Sverige AB"
                },
                "vat_rate": {
                    "type": "float",
                    "description": "Swedish VAT rate (defaults to None - must specify for VAT transactions)",
                    "required": False,
                    "options": [0.25, 0.12, 0.06, 0.0],
                    "examples": {
                        "0.25": "Standard rate (most services, office supplies)",
                        "0.12": "Reduced rate (food, hotels, transport)",
                        "0.06": "Low rate (books, newspapers)",
                        "0.0": "Zero rate (exports, some services)",
                        "None": "No VAT (default - omit parameter)"
                    }
                }
            },
            "automations": [
                "VAT calculation (multiple Swedish rates supported)",
                "Account mapping (BAS 2022 chart)",
                "Journal entry generation",
                "Voucher posting and balance validation"
            ]
        }
    },

    "manage_invoice": {
        "name": "manage_invoice",
        "category": "invoicing",
        "essentials": {
            "description": "Complete invoice lifecycle management",
            "key_parameters": ["action", "line_items", "company", "vat_number"],
            "example": 'manage_invoice("create", line_items=[{"description": "Web development", "quantity": 40, "unit_price": 1250}], company="Acme Corp AB", vat_number="SE123456789")',
            "performance": "Handles create, update_status, check_overdue, get_details in single function",
            "tips": [
                "action: create|update_status|check_overdue|get_details",
                "Prefer company+vat_number over email for new customers",
                "Auto-generates voucher with Swedish VAT compliance"
            ]
        }
    },

    "manage_payment": {
        "name": "manage_payment",
        "category": "payments",
        "essentials": {
            "description": "Payment processing, reminders, and bank reconciliation",
            "key_parameters": ["action", "invoice_id", "bank_transaction_id"],
            "example": 'manage_payment("reconcile", bank_transaction_id=456, invoice_id=123)',
            "performance": "Handles create_reminder, reconcile, list_unmatched in single function",
            "tips": [
                "action: create_reminder|reconcile|list_unmatched",
                "Swedish interest calculations for payment reminders",
                "Auto-matches bank transactions with invoices"
            ]
        }
    },

    "manage_customer": {
        "name": "manage_customer",
        "category": "customers",
        "essentials": {
            "description": "Customer operations and lookup",
            "key_parameters": ["action", "email"],
            "example": 'manage_customer("list")',
            "performance": "Fast customer listing and detailed lookup",
            "tips": [
                "action: list|get_details",
                "Enhanced address support with structured fields",
                "Backward compatibility with legacy formats"
            ]
        }
    },

    "manage_banking": {
        "name": "manage_banking",
        "category": "banking",
        "essentials": {
            "description": "Bank integration and Swedish VAT reporting",
            "key_parameters": ["action", "csv_data", "quarter", "year"],
            "example": 'manage_banking("vat_report", quarter=3, year=2025)',
            "performance": "Handles CSV import, VAT reports, and PDF generation",
            "tips": [
                "action: import_csv|vat_report|vat_report_pdf",
                "Supports Swedbank, SEB formats",
                "Quarterly VAT reports for Skatteverket"
            ]
        }
    },

    "generate_report": {
        "name": "generate_report",
        "category": "reporting",
        "essentials": {
            "description": "Financial statements with Swedish account codes",
            "key_parameters": ["report_type", "start_date", "end_date"],
            "example": 'generate_report("trial_balance")',
            "performance": "Professional reports with period analysis and account codes",
            "tips": [
                "report_type: trial_balance|income_statement|balance_sheet",
                "Enhanced formatting with Swedish account names",
                "Period analysis shows opening/period/closing balances"
            ]
        }
    },

    "generate_pdf": {
        "name": "generate_pdf",
        "category": "documents",
        "essentials": {
            "description": "Universal document generation (invoices, reminders, VAT reports)",
            "key_parameters": ["document_type", "document_id"],
            "example": 'generate_pdf("invoice", document_id=123)',
            "performance": "Professional PDF generation with Swedish compliance",
            "tips": [
                "document_type: invoice|reminder|vat_report",
                "WeasyPrint engine for professional output",
                "Saves to Desktop for easy access"
            ]
        }
    },

    "get_guidance": {
        "name": "get_guidance",
        "category": "documentation",
        "essentials": {
            "description": "Documentation, workflows, and Swedish compliance guidance",
            "key_parameters": ["topic", "workflow_name", "compliance_topic"],
            "example": 'get_guidance(workflow_name="expense_recording")',
            "performance": "Comprehensive help system with examples",
            "tips": [
                "Always start with get_guidance() for system overview",
                "Get workflow guides for common processes",
                "Swedish compliance information readily available"
            ]
        }
    },

    "audit_voucher": {
        "name": "audit_voucher",
        "category": "security",
        "essentials": {
            "description": "Voucher audit operations with TOTP security",
            "key_parameters": ["action", "voucher_id", "start_date", "end_date"],
            "example": 'audit_voucher("list_period", start_date="2025-01-01", end_date="2025-01-31")',
            "performance": "Secure operations with TOTP verification for sensitive actions",
            "tips": [
                "action: history|list_period|supersede|add_annotation",
                "TOTP required for supersede and add_annotation",
                "Complete audit trail and security logging"
            ]
        }
    }
}

# Tool Categories for Organization
TOOL_CATEGORIES = {
    "core_accounting": ["record_business_event"],
    "invoicing": ["manage_invoice"],
    "payments": ["manage_payment"],
    "customers": ["manage_customer"],
    "banking": ["manage_banking"],
    "reporting": ["generate_report"],
    "documents": ["generate_pdf"],
    "documentation": ["get_guidance"],
    "security": ["audit_voucher"]
}

# Overview Text for get_guidance() with no parameters
SYSTEM_OVERVIEW = """
🎉 UNIFIED ACCOUNTING SYSTEM - CONSOLIDATED TOOLBOX

This MCP server now features a streamlined 9-tool interface (down from 28) designed for business users who want to take responsibility but lack time for complex accounting procedures.

🎯 **Core Philosophy: Less is More**
Each tool represents a complete business function, not a technical accounting step.

📋 **The 9 Powerful Tools:**

1. **record_business_event** - 🔥 UNIVERSAL transaction recorder
   • Replaces: create_voucher + add_journal_entry + post_voucher
   • Examples: "expense", "invoice", "payment", "transfer", "adjustment"
   • Auto-handles: VAT, accounts, journal entries, Swedish compliance

2. **manage_invoice** - Complete invoice lifecycle
   • Actions: create, update_status, check_overdue, get_details
   • Auto-generates vouchers with Swedish VAT compliance

3. **manage_payment** - Payment processing & reminders
   • Actions: create_reminder, reconcile, list_unmatched
   • Swedish law-compliant interest calculations

4. **manage_customer** - Customer operations
   • Actions: list, get_details
   • Enhanced address support with backward compatibility

5. **manage_banking** - Bank integration & VAT reporting
   • Actions: import_csv, vat_report, vat_report_pdf
   • Supports Swedbank, SEB formats

6. **generate_report** - Financial statements
   • Types: trial_balance, income_statement, balance_sheet
   • Enhanced with Swedish account codes and period analysis

7. **generate_pdf** - Universal document generation
   • Types: invoice, reminder, vat_report
   • Professional WeasyPrint output

8. **get_guidance** - This help system
   • Documentation, workflows, Swedish compliance guides

9. **audit_voucher** - Security operations
   • Actions: history, list_period, supersede, add_annotation
   • TOTP-protected for sensitive operations

🇸🇪 **Swedish Compliance Built-In:**
• BAS 2022 chart of accounts (54 IT consultant accounts)
• Unbroken voucher numbering per BFL requirements
• Detailed descriptions per NJA 2020 s. 497 Supreme Court ruling
• Mandatory counterparty documentation
• 25% VAT calculations and reporting

🚀 **Getting Started:**
1. Start with get_guidance() for overview
2. Use record_business_event() for daily transactions
3. Use manage_invoice() for customer billing
4. Use generate_report() for financial analysis

💡 **Pro Tip:** When users ask vague questions, ALWAYS ask for all required parameters. Swedish law requires detailed descriptions and counterparty information.
"""
