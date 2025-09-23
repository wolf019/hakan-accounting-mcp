# MCP Accounting Server - Documentation System Implementation

## Overview

Implement a comprehensive documentation system for the MCP Accounting Server that provides contextual guidance and best practices for both AI assistants and human users. This system will ensure proper tool usage, prevent common mistakes, and provide a clear understanding of accounting workflows.

## Inspiration

Following best practices MCP approach where users **ALWAYS start with** `tools_documentation()` to understand available tools and best practices before taking any actions. Implement this as python code to be consistent with the MCP Accounting Server. The TS code is example code.

## Requirements

### Core Documentation Tool

```typescript
@mcp.tool()
def tools_documentation(
    topic: Optional[str] = None,
    depth: str = "essentials",
    category: Optional[str] = None
) -> str:
    """
    Get comprehensive documentation for accounting tools and workflows.

    Args:
        topic: Specific tool name or "overview" for general guidance
        depth: "essentials" (quick reference) or "full" (complete details)
        category: Filter by category (invoicing, expenses, accounting, reporting)

    Returns:
        Formatted documentation with examples and best practices
    """
```

### Documentation Data Structure

```typescript
interface ToolDocumentation {
  name: string;
  category: string; // "invoicing", "expenses", "accounting", "reporting", "reconciliation"
  essentials: {
    description: string;
    keyParameters: string[];
    example: string;
    performance: string;
    tips: string[];
    swedishCompliance?: string[];
  };
  full: {
    description: string;
    parameters: Record<string, {
      type: string;
      description: string;
      required?: boolean;
      swedishRule?: string; // Link to Swedish regulation
    }>;
    returns: string;
    examples: string[];
    useCases: string[];
    performance: string;
    bestPractices: string[];
    pitfalls: string[];
    relatedTools: string[];
    accountingImpact: string; // How this affects books
    vatConsiderations?: string[];
    auditTrail: string; // What records are created
  };
}
```

## Key Documentation Categories

### 1. Invoicing Tools
- `create_invoice`
- `generate_pdf`
- `send_reminder`
- `check_overdue_invoices`

### 2. Expense Management
- `add_expense`
- `scan_receipt`
- `categorize_expense`
- `list_expenses`

### 3. Core Accounting
- `create_voucher`
- `post_journal_entries`
- `get_account_balance`
- `generate_trial_balance`

### 4. Financial Reporting
- `generate_income_statement`
- `generate_balance_sheet`
- `generate_vat_report`
- `close_accounting_period`

### 5. Bank Reconciliation
- `import_bank_csv`
- `reconcile_payment`
- `match_transactions`

## Essential Guidance Content

### Swedish Compliance Integration
Each tool should include:
- **VAT implications** (25%, 12%, 6%, 0% rates)
- **BAS 2022 account mapping** (which accounts are affected)
- **Skatteverket requirements** (audit trail, documentation)
- **Legal deadlines** (payment terms, VAT reporting)

### Workflow Patterns
Document common accounting workflows:

```typescript
const COMMON_WORKFLOWS = {
  "invoice_to_payment": {
    description: "Complete invoice lifecycle from creation to payment",
    steps: [
      "create_invoice",
      "generate_pdf",
      "auto_create_voucher",
      "send_to_customer",
      "import_bank_csv",
      "reconcile_payment",
      "mark_paid"
    ],
    accountingImpact: "Debits A/R, Credits Revenue & VAT, then reverses on payment"
  },

  "expense_recording": {
    description: "Record business expense with proper VAT handling",
    steps: [
      "add_expense",
      "scan_receipt",
      "categorize_expense",
      "auto_create_voucher",
      "post_journal_entries"
    ],
    accountingImpact: "Debits expense account & VAT, Credits A/P or Cash"
  },

  "monthly_closing": {
    description: "Month-end procedures for clean books",
    steps: [
      "reconcile_all_accounts",
      "review_unmatched_transactions",
      "generate_trial_balance",
      "create_adjusting_entries",
      "close_accounting_period"
    ],
    accountingImpact: "Ensures all transactions recorded, accounts balanced"
  }
};
```

## Example Tool Documentation

```typescript
const toolsDocumentation = {
  create_invoice: {
    name: 'create_invoice',
    category: 'invoicing',
    essentials: {
      description: 'Create customer invoice with automatic VAT calculation and voucher generation',
      keyParameters: ['customer_email', 'line_items', 'due_days'],
      example: 'create_invoice("pal.brattberg@intersolia.com", [{"description": "Programming", "quantity": 20, "unit_price": 1250}], 30)',
      performance: 'Fast - creates invoice, voucher, and journal entries in single transaction',
      tips: [
        'Customer must exist in database first',
        'VAT automatically calculated at 25% for Swedish B2B',
        'Due date calculated from invoice date + due_days',
        'Voucher auto-generated: DR A/R, CR Revenue & VAT'
      ],
      swedishCompliance: [
        'Invoice number sequential per Swedish law',
        'VAT registration number included',
        'Payment terms clearly stated'
      ]
    },
    full: {
      description: 'Creates a sales invoice with complete accounting integration. Automatically generates voucher with journal entries for Accounts Receivable (1910), Revenue (3001), and Output VAT (2611). Follows Swedish invoicing regulations.',
      parameters: {
        customer_email: {
          type: 'string',
          description: 'Customer email (must exist in customers table)',
          required: true
        },
        line_items: {
          type: 'array',
          description: 'Invoice line items with description, quantity, unit_price',
          required: true
        },
        due_days: {
          type: 'number',
          description: 'Payment due in X days from invoice date (default: 30)',
          required: false,
          swedishRule: 'Swedish law allows interest charges after 30 days for B2B'
        }
      },
      returns: 'Invoice object with invoice_number, total amount, voucher_id, and PDF path',
      examples: [
        'create_invoice("client@company.se", [{"description": "Consulting", "quantity": 10, "unit_price": 1500}])',
        'create_invoice("customer@business.com", [{"description": "Software license", "quantity": 1, "unit_price": 12000}], 14)'
      ],
      useCases: [
        'Billing customers for services rendered',
        'Product sales with proper VAT handling',
        'Recurring billing automation',
        'International B2B invoicing'
      ],
      performance: 'Creates invoice + voucher + 3 journal entries in ~50ms',
      bestPractices: [
        'Verify customer exists before invoicing',
        'Use descriptive line item descriptions for audit trail',
        'Set appropriate due_days based on customer agreement',
        'Check PDF generation completes successfully'
      ],
      pitfalls: [
        'Customer email must match exactly with database',
        'Line items must have positive quantities and prices',
        'VAT rate changes require system update',
        'Invoice numbers cannot be modified once created'
      ],
      relatedTools: ['generate_pdf', 'create_voucher', 'check_overdue_invoices'],
      accountingImpact: 'DR 1910 (A/R) total, CR 2611 (VAT) tax_amount, CR 3001 (Revenue) subtotal',
      vatConsiderations: [
        '25% VAT rate applied automatically for Swedish B2B',
        'VAT recorded in account 2611 (Utgående moms)',
        'Net amount recorded in appropriate revenue account'
      ],
      auditTrail: 'Creates invoice record, voucher, and 3 journal entries with full timestamp trail'
    }
  }
};
```

## User Experience Guidelines

### AI Assistant Workflow
1. **Always start with context**: `tools_documentation()` on first accounting interaction
2. **Understand before acting**: Review essentials for unfamiliar tools
3. **Follow Swedish compliance**: Check swedishCompliance notes
4. **Verify accounting impact**: Understand which accounts are affected
5. **Use workflows**: Follow documented patterns for common tasks

### Progressive Disclosure
- **Essentials view**: Quick reference for experienced users
- **Full view**: Complete details including compliance and examples
- **Category filtering**: Focus on relevant tool groups
- **Workflow guidance**: Step-by-step processes for complex tasks

## Implementation Structure

```typescript
// Core documentation service
class AccountingDocumentationService {
  getToolDocumentation(toolName: string, depth: 'essentials' | 'full'): string
  getToolsOverview(category?: string): string
  searchDocumentation(query: string): string[]
  getWorkflowGuide(workflow: string): string
  getSwedishComplianceInfo(topic: string): string
  getChartOfAccountsReference(): string
}

// MCP tool wrapper
@mcp.tool()
def tools_documentation(topic=None, depth="essentials", category=None):
    """Main documentation access point"""
    return documentation_service.get_documentation(topic, depth, category)

@mcp.tool()
def workflow_guide(workflow_name: str):
    """Get step-by-step workflow documentation"""
    return documentation_service.get_workflow_guide(workflow_name)

@mcp.tool()
def swedish_compliance_guide(topic: str):
    """Get Swedish-specific compliance information"""
    return documentation_service.get_compliance_info(topic)
```

## Content Requirements

### Essential Information for Every Tool
1. **Clear description** with accounting context
2. **Key parameters** with Swedish compliance notes
3. **Working example** with realistic Swedish business data
4. **Performance expectations**
5. **Common tips** and Swedish-specific guidance

### Full Documentation Elements
1. **Complete parameter reference** with validation rules
2. **Multiple examples** covering edge cases
3. **Accounting impact explanation** (which accounts affected)
4. **VAT considerations** for Swedish rates
5. **Audit trail information** for compliance
6. **Best practices** from accounting perspective
7. **Common pitfalls** and how to avoid them
8. **Related tools** for workflow completion

## Swedish Compliance Integration

### Account Reference Integration
```typescript
const ACCOUNT_MAPPINGS = {
  "1910": {name: "Kundfordringar", usage: "Customer invoices", vat: false},
  "2611": {name: "Utgående moms", usage: "VAT on sales", vat: true},
  "3001": {name: "Konsultintäkter", usage: "Service revenue", vat: false},
  // ... complete BAS 2022 mapping
};
```

### VAT Rate Reference
```typescript
const VAT_RATES = {
  "25%": {description: "Standard rate for most services", account: "2611"},
  "12%": {description: "Reduced rate for food, hotels", account: "2612"},
  "6%": {description: "Low rate for books, newspapers", account: "2613"},
  "0%": {description: "Exports and exempt services", account: null}
};
```

## Success Criteria

1. **Contextual Guidance**: Users understand system before using tools
2. **Compliance Awareness**: Swedish rules clearly communicated
3. **Workflow Clarity**: Common patterns documented and accessible
4. **Error Prevention**: Best practices prevent common mistakes
5. **Audit Readiness**: Clear explanation of what records are created

## Usage Examples

```typescript
// Always start with overview
tools_documentation()
// Returns: "Welcome! Here's how to use the accounting system..."

// Get specific tool help
tools_documentation({topic: "create_invoice", depth: "essentials"})
// Returns: Quick reference for invoice creation

// Understand workflows
workflow_guide("invoice_to_payment")
// Returns: Step-by-step invoice lifecycle process

// Check compliance
swedish_compliance_guide("vat_reporting")
// Returns: VAT reporting requirements and deadlines
```

This documentation system will ensure both AI assistants and human users understand the accounting implications of their actions and follow Swedish compliance requirements properly.

make sure that no typescript code is written. Only python.
