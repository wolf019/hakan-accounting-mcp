# Payment Reminder System - Implementation Brief

## Overview

Extend the existing MCP Invoice Server to handle overdue payments and payment reminders according to Swedish commercial law. This feature will automate the reminder process and ensure legal compliance for late payment handling.

## Current System

The existing MCP server successfully handles:
- Invoice creation and PDF generation
- Customer management
- SQLite database with invoices, customers, and line items
- Natural language interface via Claude Desktop

## Requirements

### Core Functionality
1. **Automatic overdue detection** - identify invoices past due date
2. **Payment reminder creation** - generate reminders with calculated fees and interest
3. **PDF reminder generation** - professional reminder documents
4. **Interest calculation** - according to Swedish law (reference rate + 8%)
5. **Legal fee handling** - reminder fees and delay compensation

### Swedish Legal Compliance

#### For Business Customers (B2B):
- **Interest rate**: Swedish Central Bank reference rate + 8% annually
- **Interest start date**: 30 days after invoice date (not due date)
- **Delay compensation**: 450 SEK automatic right for business customers
- **Reminder fee**: 60 SEK (if contractually agreed)
- **Interest calculation base**: Full amount including VAT

#### For Consumers (B2C):
- Same interest rate but requires 30-day advance notice
- No delay compensation allowed
- Reminder fee only if agreed in advance

## Implementation Tasks

### 1. Database Schema Extension

Add payment reminders tracking table with fields for:
- Reminder sequence (1st, 2nd, 3rd reminder)
- Amount calculations (original, interest, fees, total)
- Legal compliance data (reference rate, customer type)
- Audit trail (dates, PDF generation status)

Update existing invoices table with reminder counters and status fields.

### 2. MCP Tools Implementation

Create three primary tools:
- `check_overdue_invoices()` - scan for invoices needing reminders
- `create_payment_reminder(invoice_id, customer_type)` - generate reminder with calculations
- `generate_reminder_pdf(reminder_id)` - create PDF document

### 3. Interest Calculation Engine

Implement Swedish legal interest calculation:
- Fetch current reference rate (manual input or API integration)
- Calculate daily interest: `(amount × (ref_rate + 8%)) / 365 × days_overdue`
- Handle business vs consumer rules
- Apply appropriate fees (60 SEK reminder, 450 SEK delay compensation)

### 4. PDF Template System

Create reminder PDF template following Swedish standards:
- Clear overdue notice
- Breakdown of original amount, interest, and fees
- New total amount due
- Legal text about consequences of continued non-payment
- Payment instructions with updated amount

### 5. Business Logic

Implement reminder workflow:
- Grace period handling (few days after due date before first reminder)
- Progressive reminder system (1st, 2nd, final notice)
- Automatic calculation updates for subsequent reminders
- Integration with existing invoice status system

## Technical Notes

- **Reference rate source**: Manual input initially, can be enhanced with Riksbank API later
- **Customer type detection**: Default to 'business' for B2B invoicing, allow override
- **Interest accrual**: Calculate from invoice date + 30 days, not due date
- **Template integration**: Use existing embedded template system for consistency
- **Database efficiency**: Minimal schema changes, leverage existing patterns

## Success Criteria

1. **Legal compliance**: All calculations follow Swedish commercial law
2. **Automation**: Single command creates complete reminder with all fees
3. **Professional output**: PDF reminders match quality of existing invoices
4. **User experience**: Natural language interface ("create reminder for invoice 2025-004")
5. **Audit trail**: Complete history of all reminder actions

## Usage Examples

```
"Check which invoices are overdue"
"Create payment reminder for invoice 2025-004" 
"Generate reminder PDF for Intersolia's overdue payment"
"What's the total amount Pål owes including interest?"
```

## References

- [Swedish Payment Reminder Regulations](https://verksamt.se/avtal-fakturering/betalningspaminnelse-och-drojsmalsranta)
- [Riksbank Reference Rate](https://www.riksbank.se/sv/statistik/sok-rantor--valutakurser/referensranta/)

This implementation will provide complete automation of the Swedish payment reminder process while maintaining legal compliance and professional standards.
