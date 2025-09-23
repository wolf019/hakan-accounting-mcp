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

# Common Accounting Workflows
WORKFLOWS = {
    "invoice_to_payment": {
        "description": "Complete invoice lifecycle from creation to payment",
        "steps": [
            "create_invoice",
            "generate_pdf",
            "auto_create_voucher",
            "send_to_customer",
            "import_bank_transactions",
            "reconcile_transaction",
            "mark_paid"
        ],
        "accounting_impact": "Debits A/R, Credits Revenue & VAT, then reverses on payment"
    },
    
    "expense_recording": {
        "description": "Record business expense with proper VAT handling",
        "steps": [
            "add_expense",
            "categorize_expense",
            "auto_create_voucher",
            "post_journal_entries"
        ],
        "accounting_impact": "Debits expense account & VAT, Credits A/P or Cash"
    },
    
    "monthly_closing": {
        "description": "Month-end procedures for clean books",
        "steps": [
            "reconcile_all_accounts",
            "review_unmatched_transactions",
            "generate_trial_balance",
            "create_adjusting_entries",
            "post_accounting_period"
        ],
        "accounting_impact": "Ensures all transactions recorded, accounts balanced"
    }
}

# Comprehensive Tool Documentation
TOOL_DOCUMENTATION = {
    "create_invoice": {
        "name": "create_invoice",
        "category": "invoicing",
        "essentials": {
            "description": "Create customer invoice with automatic VAT calculation and voucher generation",
            "key_parameters": ["customer_email", "line_items", "due_days"],
            "example": 'create_invoice("pal.brattberg@intersolia.se", [{"description": "Programming", "quantity": 20, "unit_price": 1250}], 30)',
            "performance": "Fast - creates invoice, voucher, and journal entries in single transaction",
            "tips": [
                "Customer must exist in database first",
                "VAT automatically calculated at 25% for Swedish B2B",
                "Due date calculated from invoice date + due_days",
                "Voucher auto-generated: DR A/R, CR Revenue & VAT"
            ],
            "swedish_compliance": [
                "Invoice number sequential per Swedish law",
                "VAT registration number included",
                "Payment terms clearly stated"
            ]
        },
        "full": {
            "description": "Creates a sales invoice with complete accounting integration. Automatically generates voucher with journal entries for Accounts Receivable (1910), Revenue (3001), and Output VAT (2611). Follows Swedish invoicing regulations.",
            "parameters": {
                "customer_email": {
                    "type": "string",
                    "description": "Customer email (must exist in customers table)",
                    "required": True
                },
                "line_items": {
                    "type": "array",
                    "description": "Invoice line items with description, quantity, unit_price",
                    "required": True
                },
                "due_days": {
                    "type": "number",
                    "description": "Payment due in X days from invoice date (default: 30)",
                    "required": False,
                    "swedish_rule": "Swedish law allows interest charges after 30 days for B2B"
                }
            },
            "returns": "Invoice object with invoice_number, total amount, voucher_id, and PDF path",
            "examples": [
                'create_invoice("client@company.se", [{"description": "Consulting", "quantity": 10, "unit_price": 1500}])',
                'create_invoice("customer@business.com", [{"description": "Software license", "quantity": 1, "unit_price": 12000}], 14)'
            ],
            "use_cases": [
                "Billing customers for services rendered",
                "Product sales with proper VAT handling",
                "Recurring billing automation",
                "International B2B invoicing"
            ],
            "performance": "Creates invoice + voucher + 3 journal entries in ~50ms",
            "best_practices": [
                "Verify customer exists before invoicing",
                "Use descriptive line item descriptions for audit trail",
                "Set appropriate due_days based on customer agreement",
                "Check PDF generation completes successfully"
            ],
            "pitfalls": [
                "Customer email must match exactly with database",
                "Line items must have positive quantities and prices",
                "VAT rate changes require system update",
                "Invoice numbers cannot be modified once created"
            ],
            "related_tools": ["generate_pdf", "create_accounting_voucher", "check_overdue_invoices"],
            "accounting_impact": "DR 1910 (A/R) total, CR 2611 (VAT) tax_amount, CR 3001 (Revenue) subtotal",
            "vat_considerations": [
                "25% VAT rate applied automatically for Swedish B2B",
                "VAT recorded in account 2611 (Utgående moms)",
                "Net amount recorded in appropriate revenue account"
            ],
            "audit_trail": "Creates invoice record, voucher, and 3 journal entries with full timestamp trail"
        }
    },
    
    "generate_pdf": {
        "name": "generate_pdf",
        "category": "invoicing",
        "essentials": {
            "description": "Generate professional PDF invoice with Swedish formatting",
            "key_parameters": ["invoice_id"],
            "example": 'generate_pdf(123)',
            "performance": "Moderate - PDF rendering takes 200-500ms",
            "tips": [
                "PDF saved to ~/Desktop/ for easy access",
                "WeasyPrint used for professional rendering",
                "Swedish formatting with proper VAT display"
            ],
            "swedish_compliance": [
                "VAT number prominently displayed",
                "Payment terms in Swedish",
                "Bank details for Swedish payments"
            ]
        },
        "full": {
            "description": "Generates professional PDF invoice using WeasyPrint with Swedish business formatting. Includes all required Swedish compliance elements.",
            "parameters": {
                "invoice_id": {
                    "type": "integer",
                    "description": "Invoice ID from database",
                    "required": True
                }
            },
            "returns": "PDF file path and success status",
            "examples": [
                'generate_pdf(123)',
                'generate_pdf(456)'
            ],
            "use_cases": [
                "Send professional invoices to customers",
                "Archive invoices for records",
                "Print invoices for physical delivery"
            ],
            "performance": "PDF generation takes 200-500ms depending on complexity",
            "best_practices": [
                "Generate PDF immediately after creating invoice",
                "Verify PDF file exists before sending to customer",
                "Keep PDF copies for audit purposes"
            ],
            "pitfalls": [
                "Invoice must exist in database",
                "PDF overwrites existing file with same name",
                "WeasyPrint requires proper HTML template"
            ],
            "related_tools": ["create_invoice", "create_payment_reminder"],
            "accounting_impact": "No direct accounting impact - reporting tool only",
            "audit_trail": "PDF generation logged with timestamp"
        }
    },
    
    "add_expense": {
        "name": "add_expense",
        "category": "expenses",
        "essentials": {
            "description": "Record business expense with automatic VAT calculation",
            "key_parameters": ["description", "amount", "category", "expense_date"],
            "example": 'add_expense("Office supplies", 500, "office", "2025-01-15")',
            "performance": "Fast - creates expense and voucher in single transaction",
            "tips": [
                "Amount should include VAT",
                "Category determines account mapping",
                "VAT automatically calculated at 25%",
                "Voucher auto-generated: DR Expense & VAT, CR A/P"
            ],
            "swedish_compliance": [
                "VAT deductible for business expenses",
                "Receipt required for audit",
                "Proper expense categorization"
            ]
        },
        "full": {
            "description": "Records business expense with automatic VAT separation and voucher generation. Creates journal entries for expense account, input VAT, and accounts payable.",
            "parameters": {
                "description": {
                    "type": "string",
                    "description": "Description of the expense",
                    "required": True
                },
                "amount": {
                    "type": "number",
                    "description": "Total amount including VAT",
                    "required": True
                },
                "category": {
                    "type": "string",
                    "description": "Expense category (office, travel, equipment, etc.)",
                    "required": True
                },
                "expense_date": {
                    "type": "string",
                    "description": "Date of expense (YYYY-MM-DD format)",
                    "required": True
                }
            },
            "returns": "Expense object with voucher_id and calculated VAT amounts",
            "examples": [
                'add_expense("Office rent", 12500, "rent", "2025-01-01")',
                'add_expense("Software license", 2500, "software", "2025-01-15")'
            ],
            "use_cases": [
                "Record monthly recurring expenses",
                "Track one-time business purchases",
                "Import expenses from receipt scanning"
            ],
            "performance": "Creates expense + voucher + 3 journal entries in ~50ms",
            "best_practices": [
                "Include detailed description for audit trail",
                "Use consistent category names",
                "Enter expense date when incurred, not when paid",
                "Keep receipt for documentation"
            ],
            "pitfalls": [
                "Amount must be positive",
                "Date format must be YYYY-MM-DD",
                "Category affects account mapping",
                "VAT may not be deductible for all expenses"
            ],
            "related_tools": ["list_expenses", "create_accounting_voucher"],
            "accounting_impact": "DR expense account (net), DR 2610 (VAT), CR 2440 (A/P)",
            "vat_considerations": [
                "25% VAT automatically calculated and separated",
                "VAT recorded as deductible input VAT",
                "Some expenses may have different VAT rates"
            ],
            "audit_trail": "Creates expense record, voucher, and 3 journal entries"
        }
    },
    
    "generate_trial_balance": {
        "name": "generate_trial_balance",
        "category": "reporting",
        "essentials": {
            "description": "Generate complete trial balance showing all account balances",
            "key_parameters": ["as_of_date"],
            "example": 'generate_trial_balance("2025-01-31")',
            "performance": "Moderate - processes all accounts and transactions",
            "tips": [
                "Shows all accounts with balances",
                "Verifies debit = credit total",
                "Use for month-end verification",
                "Basis for financial statements"
            ],
            "swedish_compliance": [
                "BAS 2022 account structure",
                "Required for audit trail",
                "Monthly closing verification"
            ]
        },
        "full": {
            "description": "Generates comprehensive trial balance report showing all account balances as of specified date. Verifies that total debits equal total credits.",
            "parameters": {
                "as_of_date": {
                    "type": "string",
                    "description": "Date for balance calculation (YYYY-MM-DD, optional)",
                    "required": False
                }
            },
            "returns": "Formatted trial balance report with account balances",
            "examples": [
                'generate_trial_balance()',
                'generate_trial_balance("2025-01-31")'
            ],
            "use_cases": [
                "Month-end closing verification",
                "Preparation for financial statements",
                "Audit trail documentation",
                "Balance sheet preparation"
            ],
            "performance": "Processes all accounts and transactions in 100-300ms",
            "best_practices": [
                "Run monthly before closing period",
                "Verify debit/credit totals balance",
                "Review unusual account balances",
                "Keep for audit documentation"
            ],
            "pitfalls": [
                "Large date ranges may be slow",
                "Unposted transactions not included",
                "Account balances may be unexpected"
            ],
            "related_tools": ["generate_balance_sheet", "generate_income_statement"],
            "accounting_impact": "No direct impact - reporting tool only",
            "audit_trail": "Trial balance generation logged with timestamp"
        }
    },
    
    "generate_balance_sheet": {
        "name": "generate_balance_sheet",
        "category": "reporting",
        "essentials": {
            "description": "Generate balance sheet with period analysis and account codes",
            "key_parameters": ["as_of_date", "start_date", "detailed", "period_only"],
            "example": 'generate_balance_sheet(start_date="2025-08-01", as_of_date="2025-08-31", period_only=True)',
            "performance": "Fast - optimized SQL with period analysis",
            "tips": [
                "Shows BAS 2022 account codes",
                "Period analysis: opening/period/closing",
                "period_only=True for monthly changes",
                "Includes account 2894 (owner loan)"
            ],
            "swedish_compliance": [
                "BAS 2022 account structure",
                "Swedish balance sheet format",
                "Professional audit trail"
            ]
        },
        "full": {
            "description": "Generates professional balance sheet with account codes, period analysis, and multiple viewing options. Supports both cumulative and period-only views.",
            "parameters": {
                "as_of_date": {
                    "type": "string",
                    "description": "Closing balance date (YYYY-MM-DD)",
                    "required": False,
                    "default": "today"
                },
                "start_date": {
                    "type": "string",
                    "description": "Opening balance date for period analysis (YYYY-MM-DD)",
                    "required": False,
                    "default": "beginning of year"
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Show account codes and period analysis",
                    "required": False,
                    "default": True
                },
                "period_only": {
                    "type": "boolean",
                    "description": "Show ONLY changes during the period (not cumulative)",
                    "required": False,
                    "default": False
                }
            },
            "returns": "Formatted balance sheet with assets, liabilities, equity, and balance verification",
            "examples": [
                'generate_balance_sheet()  # Current cumulative with period analysis',
                'generate_balance_sheet(as_of_date="2025-08-31")  # As of specific date',
                'generate_balance_sheet(start_date="2025-08-01", as_of_date="2025-08-31", period_only=True)  # August changes only'
            ],
            "use_cases": [
                "Month-end financial position",
                "Period change analysis",
                "Audit documentation",
                "Bank reporting"
            ],
            "performance": "Processes all balance sheet accounts in 100-200ms",
            "best_practices": [
                "Use period_only for monthly closing",
                "Verify assets = liabilities + equity",
                "Review account 2894 (owner transactions)",
                "Keep for audit documentation"
            ],
            "pitfalls": [
                "period_only requires both dates",
                "Date format must be YYYY-MM-DD",
                "Check account type consistency"
            ],
            "related_tools": ["generate_income_statement", "generate_trial_balance"],
            "accounting_impact": "No direct impact - reporting tool only",
            "audit_trail": "Complete with account codes and period movements"
        }
    },
    
    "generate_income_statement": {
        "name": "generate_income_statement",
        "category": "reporting",
        "essentials": {
            "description": "Generate income statement with account codes and condensed view",
            "key_parameters": ["start_date", "end_date", "detailed"],
            "example": 'generate_income_statement("2025-08-01", "2025-08-31", detailed=True)',
            "performance": "Fast - processes revenue and expense accounts",
            "tips": [
                "Shows BAS 2022 account codes",
                "Condensed view: only non-zero accounts",
                "Swedish P&L format",
                "Period-specific reporting"
            ],
            "swedish_compliance": [
                "Swedish income statement format",
                "BAS 2022 account codes",
                "Tax-compliant reporting"
            ]
        },
        "full": {
            "description": "Generates professional income statement with account codes and condensed view showing only accounts with activity.",
            "parameters": {
                "start_date": {
                    "type": "string",
                    "description": "Period start date (YYYY-MM-DD)",
                    "required": True
                },
                "end_date": {
                    "type": "string",
                    "description": "Period end date (YYYY-MM-DD)",
                    "required": True
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Show account codes and only non-zero accounts",
                    "required": False,
                    "default": True
                }
            },
            "returns": "Formatted income statement with account codes, revenue, expenses, and net income",
            "examples": [
                'generate_income_statement("2025-08-01", "2025-08-31")  # August with account codes',
                'generate_income_statement("2025-01-01", "2025-12-31", detailed=False)  # Full year, all accounts'
            ],
            "use_cases": [
                "Monthly P&L review",
                "Quarterly tax preparation",
                "Annual statements",
                "Performance analysis"
            ],
            "performance": "Processes revenue/expense accounts in 50-150ms",
            "best_practices": [
                "Use detailed=True for cleaner reports",
                "Review account codes match transactions",
                "Compare period-over-period",
                "Archive for tax records"
            ],
            "pitfalls": [
                "Date ranges must be valid",
                "Only posted vouchers included",
                "Zero accounts hidden in detailed mode"
            ],
            "related_tools": ["generate_balance_sheet", "generate_trial_balance"],
            "accounting_impact": "No direct impact - reporting tool only",
            "audit_trail": "Income statement with full account code visibility"
        }
    },
    
    "check_overdue_invoices": {
        "name": "check_overdue_invoices",
        "category": "invoicing",
        "essentials": {
            "description": "Find invoices requiring payment reminders",
            "key_parameters": ["grace_days"],
            "example": 'check_overdue_invoices(5)',
            "performance": "Fast - scans invoice due dates",
            "tips": [
                "Grace period before reminder",
                "Lists invoices needing follow-up",
                "Basis for payment reminder process",
                "Customer relationship management"
            ],
            "swedish_compliance": [
                "30-day payment terms standard",
                "Interest calculation after due date",
                "Professional reminder process"
            ]
        },
        "full": {
            "description": "Scans all sent invoices to identify those requiring payment reminders based on due dates and grace periods.",
            "parameters": {
                "grace_days": {
                    "type": "number",
                    "description": "Days after due date before reminder (default: 5)",
                    "required": False,
                    "swedish_rule": "Swedish law allows interest after due date, but grace period is business courtesy"
                }
            },
            "returns": "List of overdue invoices with customer details and amounts",
            "examples": [
                'check_overdue_invoices()',
                'check_overdue_invoices(7)'
            ],
            "use_cases": [
                "Daily/weekly payment follow-up",
                "Customer relationship management",
                "Cash flow management",
                "Automated reminder processing"
            ],
            "performance": "Scans invoice table in 10-50ms",
            "best_practices": [
                "Check daily for overdue invoices",
                "Use appropriate grace period",
                "Contact customers before formal reminders",
                "Track payment patterns"
            ],
            "pitfalls": [
                "Grace period may be too short/long",
                "Customer disputes not considered",
                "Partial payments not tracked"
            ],
            "related_tools": ["create_payment_reminder", "update_invoice_status"],
            "accounting_impact": "No direct impact - reporting tool only",
            "audit_trail": "Overdue invoice check logged with timestamp"
        }
    },
    
    # TOTP-Protected Voucher Operations
    "supersede_voucher": {
        "name": "supersede_voucher",
        "category": "voucher_security",
        "essentials": {
            "description": "🔐 TOTP-PROTECTED: Mark voucher as superseded with security verification",
            "key_parameters": ["original_voucher_id", "replacement_voucher_id", "reason", "user_id", "totp_code"],
            "example": 'supersede_voucher(21, 22, "Balance error corrected", "tkaxberg@gmail.com", "123456")',
            "performance": "Fast - includes TOTP verification and database updates",
            "tips": [
                "🔐 Requires 6-digit TOTP from Google Authenticator",
                "Or use 8-digit backup code in emergencies",
                "Creates full audit trail with annotations",
                "Original voucher excluded from trial balance",
                "Rate limited: Max 3 attempts per 30 seconds"
            ],
            "swedish_compliance": [
                "Maintains complete transaction history",
                "Explains sequential numbering gaps",
                "Professional audit documentation",
                "Bank-level security for corrections"
            ]
        },
        "full": {
            "description": "Marks a voucher as superseded with TOTP two-factor authentication. Creates annotations for both original and replacement vouchers, maintaining complete audit trail required by Swedish accounting law.",
            "parameters": {
                "original_voucher_id": {
                    "type": "number",
                    "description": "Voucher being replaced",
                    "required": True
                },
                "replacement_voucher_id": {
                    "type": "number",
                    "description": "Correct replacement voucher",
                    "required": True
                },
                "reason": {
                    "type": "string",
                    "description": "Business justification (max 200 chars)",
                    "required": True
                },
                "user_id": {
                    "type": "string",
                    "description": "User performing operation (e.g., 'tkaxberg@gmail.com')",
                    "required": True
                },
                "totp_code": {
                    "type": "string",
                    "description": "6-digit TOTP from authenticator app or 8-digit backup code",
                    "required": True
                }
            },
            "returns": "Success message with security verification details or error with retry information",
            "examples": [
                'supersede_voucher(21, 22, "Balance error", "tkaxberg@gmail.com", "123456")',
                'supersede_voucher(21, 22, "Emergency fix", "tkaxberg@gmail.com", "12345678")  # Backup code'
            ],
            "security_features": [
                "⏱️ Rate Limited: Max 3 attempts per 30 seconds",
                "🔒 Account Lockout: 15 minutes after 5 failed attempts",
                "🛡️ Replay Protection: Each code can only be used once",
                "📱 Backup Codes: 8 emergency access codes",
                "📋 Full Audit: All attempts logged with timestamp"
            ],
            "use_cases": [
                "Correcting posting errors",
                "Fixing unbalanced entries",
                "Reversing incorrect vouchers",
                "Audit-compliant corrections"
            ],
            "performance": "TOTP verification: 50-100ms, Database updates: 10-20ms",
            "best_practices": [
                "Document reason clearly",
                "Create replacement voucher first",
                "Verify TOTP code is current",
                "Keep backup codes secure"
            ],
            "pitfalls": [
                "TOTP codes expire every 30 seconds",
                "Account lockout after 5 failures",
                "Clock synchronization issues",
                "Backup codes are single-use only"
            ],
            "error_handling": {
                "INVALID_TOTP": "Wrong code - check Google Authenticator",
                "RATE_LIMITED": "Too many attempts - wait and retry",
                "ACCOUNT_LOCKED": "Account locked - wait 15 minutes or use backup code"
            },
            "related_tools": ["add_secure_voucher_annotation", "get_voucher_history", "generate_trial_balance"],
            "accounting_impact": "Original voucher excluded from financial reports, replacement voucher becomes active",
            "audit_trail": "Complete security log with TOTP verification, timestamps, and user identification"
        }
    },
    
    "add_secure_voucher_annotation": {
        "name": "add_secure_voucher_annotation",
        "category": "voucher_security",
        "essentials": {
            "description": "🔐 TOTP-PROTECTED: Add annotation to voucher with security verification",
            "key_parameters": ["voucher_id", "annotation_type", "message", "user_id", "totp_code"],
            "example": 'add_secure_voucher_annotation(21, "NOTE", "Pending approval", "tkaxberg@gmail.com", "123456")',
            "performance": "Fast - includes TOTP verification and database insert",
            "tips": [
                "🔐 Requires 6-digit TOTP from Google Authenticator",
                "Or use 8-digit backup code in emergencies",
                "ALL annotations now require TOTP protection",
                "Allowed types: CORRECTION, REVERSAL, NOTE only",
                "SUPERSEDED/VOID use dedicated supersede_voucher() method"
            ],
            "swedish_compliance": [
                "Complete audit trail with security verification",
                "Bank-level security for all annotation changes",
                "Professional audit documentation"
            ]
        },
        "full": {
            "description": "Adds annotations to vouchers with TOTP two-factor authentication. ALL voucher annotations affect audit trail and require security verification per user directive.",
            "parameters": {
                "voucher_id": {
                    "type": "number",
                    "description": "Target voucher ID",
                    "required": True
                },
                "annotation_type": {
                    "type": "string",
                    "description": "CORRECTION | REVERSAL | NOTE (SUPERSEDED/VOID use supersede_voucher())",
                    "required": True
                },
                "message": {
                    "type": "string",
                    "description": "Annotation message (max 500 chars)",
                    "required": True
                },
                "user_id": {
                    "type": "string",
                    "description": "User performing operation (e.g., 'tkaxberg@gmail.com')",
                    "required": True
                },
                "totp_code": {
                    "type": "string",
                    "description": "6-digit TOTP from authenticator app or 8-digit backup code",
                    "required": True
                },
                "related_voucher_id": {
                    "type": "number",
                    "description": "Optional link to related voucher",
                    "required": False
                }
            },
            "returns": "Success message with TOTP verification details or error",
            "examples": [
                'add_secure_voucher_annotation(21, "NOTE", "Review needed", "tkaxberg@gmail.com", "123456")',
                'add_secure_voucher_annotation(21, "CORRECTION", "VAT fixed", "tkaxberg@gmail.com", "12345678")  # Backup code'
            ],
            "security_features": [
                "⏱️ Rate Limited: Max 3 attempts per 30 seconds",
                "🔒 Account Lockout: 15 minutes after 5 failed attempts",
                "🛡️ Replay Protection: Each code can only be used once",
                "📱 Backup Codes: 8 emergency access codes",
                "📋 Full Audit: All attempts logged with timestamp"
            ],
            "allowed_annotation_types": {
                "CORRECTION": "Error correction with TOTP protection",
                "REVERSAL": "Transaction reversal with TOTP protection", 
                "NOTE": "General note with TOTP protection"
            },
            "blocked_operations": {
                "SUPERSEDED": "🔒 Use supersede_voucher() method instead",
                "VOID": "🔒 Use void_voucher() method instead",
                "CREATED": "🔒 Internal system use only"
            },
            "performance": "TOTP verification: 50-100ms, Database insert: 10-20ms",
            "use_cases": [
                "Add secure review notes",
                "Document corrections with audit",
                "Link related transactions securely",
                "Professional audit trail maintenance"
            ],
            "best_practices": [
                "Use current TOTP code from authenticator",
                "Keep backup codes secure and private",
                "Document reasons clearly",
                "Use supersede_voucher() for voucher replacements"
            ],
            "pitfalls": [
                "TOTP codes expire every 30 seconds",
                "Account lockout after 5 failures", 
                "Clock synchronization issues",
                "Backup codes are single-use only"
            ],
            "error_handling": {
                "INVALID_TOTP": "Wrong code - check Google Authenticator",
                "RATE_LIMITED": "Too many attempts - wait and retry",
                "ACCOUNT_LOCKED": "Account locked - wait 15 minutes or use backup code"
            },
            "related_tools": ["supersede_voucher", "get_voucher_history", "generate_trial_balance"],
            "accounting_impact": "No direct impact - secure documentation only",
            "audit_trail": "Complete security log with TOTP verification, timestamps, and user identification"
        }
    },
    
    "list_vouchers_by_period": {
        "name": "list_vouchers_by_period",
        "category": "voucher_reporting",
        "essentials": {
            "description": "List all vouchers for a period with summary information for efficient review",
            "key_parameters": ["start_date", "end_date", "include_superseded", "voucher_type"],
            "example": 'list_vouchers_by_period("2025-07-01", "2025-07-31")',
            "performance": "Optimized - single query with aggregated summaries",
            "tips": [
                "Perfect for monthly closing reviews",
                "Replaces multiple individual voucher queries",
                "Shows balance status for each voucher",
                "Provides period summary statistics"
            ],
            "swedish_compliance": [
                "Period-based reporting for tax compliance",
                "Complete audit trail visibility",
                "VAT period reconciliation support"
            ]
        },
        "full": {
            "description": "Efficiently retrieves all vouchers within a date range with summary information. Eliminates need for multiple individual get_voucher_history calls during period analysis. Essential for monthly closing and audit reviews.",
            "parameters": {
                "start_date": {
                    "type": "string",
                    "description": "Start of period in YYYY-MM-DD format",
                    "required": True
                },
                "end_date": {
                    "type": "string", 
                    "description": "End of period in YYYY-MM-DD format",
                    "required": True
                },
                "include_superseded": {
                    "type": "boolean",
                    "description": "Include superseded vouchers (default: False)",
                    "required": False
                },
                "voucher_type": {
                    "type": "string",
                    "description": "Filter by type: INVOICE, EXPENSE, MANUAL, etc.",
                    "required": False
                }
            },
            "returns": "List of vouchers with ID, number, date, description, amount, status, posting status, balance check, plus period summary",
            "examples": [
                'list_vouchers_by_period("2025-07-01", "2025-07-31")',
                'list_vouchers_by_period("2025-07-01", "2025-07-31", include_superseded=True)',
                'list_vouchers_by_period("2025-01-01", "2025-03-31", voucher_type="INVOICE")'
            ],
            "response_structure": {
                "vouchers": "List with key info for each voucher",
                "summary": "Period statistics (totals, counts by status/type)",
                "period": "Date range confirmation",
                "filters": "Applied filter settings"
            },
            "performance": "Fast - single optimized query with LEFT JOINs for ~100ms for 100+ vouchers",
            "use_cases": [
                "Monthly closing procedures",
                "Period audit reviews",
                "VAT period preparation",
                "Unbalanced voucher detection",
                "Posting status verification"
            ],
            "best_practices": [
                "Use for period analysis instead of multiple get_voucher_history calls",
                "Review unbalanced vouchers before closing",
                "Include superseded for complete audit trail",
                "Filter by type for focused analysis"
            ],
            "pitfalls": [
                "Date format must be YYYY-MM-DD",
                "Large date ranges may return many results",
                "Superseded vouchers excluded by default"
            ],
            "related_tools": ["get_voucher_history", "generate_trial_balance", "supersede_voucher"],
            "accounting_impact": "No direct impact - reporting tool only",
            "audit_trail": "Shows complete voucher list with status indicators for period review"
        }
    },
    
    "get_voucher_history": {
        "name": "get_voucher_history",
        "category": "voucher_reporting",
        "essentials": {
            "description": "Get complete history, relationships, and security audit for a single voucher",
            "key_parameters": ["voucher_id"],
            "example": 'get_voucher_history(21)',
            "performance": "Fast - multiple table joins",
            "tips": [
                "Shows all annotations",
                "Displays relationships",
                "Includes security audit",
                "Complete voucher lifecycle",
                "For period analysis, use list_vouchers_by_period instead"
            ],
            "swedish_compliance": [
                "Full audit documentation",
                "Relationship tracking",
                "Security verification history"
            ]
        },
        "full": {
            "description": "Retrieves complete voucher history including annotations, relationships, and security audit trail. Essential for deep analysis of a single voucher. For period analysis, use list_vouchers_by_period instead.",
            "parameters": {
                "voucher_id": {
                    "type": "number",
                    "description": "Voucher to analyze",
                    "required": True
                }
            },
            "returns": "Complete history with voucher details, relationships, annotations, and security audit",
            "examples": [
                'get_voucher_history(21)',
                'get_voucher_history(100)'
            ],
            "response_structure": {
                "voucher": "Basic voucher information",
                "relationships": "Superseded by/supersedes links",
                "annotations": "All annotations with timestamps",
                "security_audit": "TOTP verification history"
            },
            "performance": "Fast - multiple table joins with indexed lookups",
            "use_cases": [
                "Investigate specific voucher issues",
                "Deep audit trail review",
                "Security verification",
                "Relationship analysis",
                "Single voucher corrections"
            ],
            "best_practices": [
                "Use for single voucher analysis",
                "For multiple vouchers, use list_vouchers_by_period",
                "Review before corrections",
                "Check security history",
                "Verify relationships",
                "Document findings"
            ],
            "pitfalls": [
                "Large result sets for busy vouchers",
                "Security history privacy concerns",
                "Relationship complexity",
                "Information overload"
            ],
            "related_tools": ["add_secure_voucher_annotation", "supersede_voucher"],
            "accounting_impact": "No impact - reporting tool only",
            "audit_trail": "Read-only access logged"
        }
    },
    
    "generate_trial_balance": {
        "name": "generate_trial_balance",
        "category": "financial_reporting",
        "essentials": {
            "description": "Generate professional trial balance with period analysis and account codes",
            "key_parameters": ["as_of_date", "start_date", "period_analysis", "include_superseded"],
            "example": 'generate_trial_balance(start_date="2025-08-01", as_of_date="2025-08-31")',
            "performance": "Fast - optimized SQL queries",
            "tips": [
                "Shows BAS 2022 account codes",
                "Period analysis: opening/debit/credit/closing",
                "Excludes superseded vouchers by default",
                "Verifies balanced accounts"
            ],
            "swedish_compliance": [
                "BAS 2022 account codes displayed",
                "Professional audit format",
                "Complete documentation option"
            ]
        },
        "full": {
            "description": "Generates professional trial balance with account codes, period analysis, and advanced filtering. Shows opening balances, period movements, and closing balances.",
            "parameters": {
                "as_of_date": {
                    "type": "string",
                    "description": "Closing balance date (YYYY-MM-DD)",
                    "required": False,
                    "default": "today"
                },
                "start_date": {
                    "type": "string",
                    "description": "Opening balance date for period comparison (YYYY-MM-DD)",
                    "required": False,
                    "default": "beginning of year"
                },
                "period_analysis": {
                    "type": "boolean",
                    "description": "Show opening/debit/credit/closing columns",
                    "required": False,
                    "default": True
                },
                "include_superseded": {
                    "type": "boolean",
                    "description": "Include SUPERSEDED/VOID vouchers",
                    "required": False,
                    "default": False
                },
                "security_audit": {
                    "type": "boolean",
                    "description": "Include security verification details",
                    "required": False,
                    "default": False
                }
            },
            "returns": "Professional trial balance with account codes, period analysis, and balance verification",
            "examples": [
                'generate_trial_balance()  # Current with full period analysis',
                'generate_trial_balance(as_of_date="2025-08-31", period_analysis=False)  # Simple format',
                'generate_trial_balance(start_date="2025-08-01", as_of_date="2025-08-31")  # August period analysis'
            ],
            "metadata_includes": {
                "total_vouchers": "All vouchers in system",
                "active_vouchers": "Non-superseded vouchers",
                "superseded_vouchers": "Excluded vouchers",
                "security_protected_operations": "TOTP-verified operations (if security_audit=True)"
            },
            "performance": "Fast - optimized SQL queries with conditional filtering",
            "use_cases": [
                "Monthly financial review",
                "Audit preparation",
                "Balance verification",
                "Security audit review"
            ],
            "best_practices": [
                "Use clean view for reports",
                "Include all for audits",
                "Review metadata",
                "Verify balance status"
            ],
            "pitfalls": [
                "Mixing superseded and clean views",
                "Ignoring balance warnings",
                "Large account lists in output",
                "Metadata interpretation errors"
            ],
            "related_tools": ["get_voucher_history", "supersede_voucher"],
            "accounting_impact": "No impact - reporting tool only",
            "audit_trail": "Report generation logged with parameters"
        }
    }
}