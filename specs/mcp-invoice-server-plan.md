# MCP Invoice Generation Server - Technical Specification

## Overview

This project implements a Model Context Protocol (MCP) server that provides AI-powered invoice generation capabilities using WeasyPrint and Jinja2. The server enables seamless invoice creation through email integration, database management, and PDF generation.

## Tech Stack

- **uvx** - Modern Python application runner with automatic dependency management
- **FastAPI** - MCP server framework with async support
- **SQLite** - Database for invoices, customers, and line items
- **WeasyPrint** - HTML/CSS to PDF conversion
- **Jinja2** - Dynamic HTML template rendering
- **Pydantic** - Data validation and serialization
- **Python MCP SDK** - Official Model Context Protocol implementation

## Project Structure

```
mcp-invoice-server/
├── pyproject.toml             # uvx/uv project configuration
├── src/
│   ├── __init__.py            # Python package initialization
│   ├── server.py              # Main MCP server implementation
│   ├── models.py              # Pydantic data models
│   ├── database.py            # SQLite database operations
│   ├── pdf_generator.py       # WeasyPrint PDF generation
├── templates/
│   ├── invoice.html.j2        # Main invoice template
│   ├── _header.html.j2        # Invoice header partial
│   ├── _line_items.html.j2    # Line items table partial
│   └── _footer.html.j2        # Invoice footer partial
├── static/
│   └── invoice.css            # Invoice styling
├── tests/
└── README.md
```

## Data Models

### Invoice
```python
@dataclass
class Invoice:
    id: Optional[int] = None
    invoice_number: str
    customer_id: int
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.DRAFT
    subtotal: Decimal
    tax_rate: Decimal = Decimal("0.25")  # 25% Swedish VAT
    tax_amount: Decimal
    total: Decimal
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Customer
```python
@dataclass
class Customer:
    id: Optional[int] = None
    name: str
    email: str
    address: Optional[str] = None
    company: Optional[str] = None
    org_number: Optional[str] = None
    vat_number: Optional[str] = None
```

### LineItem
```python
@dataclass
class LineItem:
    id: Optional[int] = None
    invoice_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
```

## MCP Server Implementation

### Core MCP Functions

Based on the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), the server will expose these key functions:

#### Tools (Model-controlled actions)
```python
@mcp.tool()
def create_invoice(
    customer_email: str,
    line_items: List[Dict[str, Any]],
    due_days: int = 30
) -> str:
    """Create a new invoice with line items"""

@mcp.tool()
def generate_pdf(invoice_id: int) -> str:
    """Generate PDF for an existing invoice"""

@mcp.tool()
def update_invoice_status(invoice_id: int, status: str) -> str:
    """Update invoice status (draft, sent, paid, overdue)"""

@mcp.tool()
def send_invoice_email(invoice_id: int, recipient_email: str) -> str:
    """Send invoice PDF via email"""
```

#### Resources (Application-controlled data)
```python
@mcp.resource("invoices://list/{status?}")
def list_invoices(status: Optional[str] = None) -> str:
    """List invoices, optionally filtered by status"""

@mcp.resource("invoice://{invoice_id}")
def get_invoice_details(invoice_id: int) -> str:
    """Get detailed invoice information"""

@mcp.resource("customers://list")
def list_customers() -> str:
    """List all customers"""

@mcp.resource("customer://{email}")
def get_customer_by_email(email: str) -> str:
    """Get customer information by email"""
```

## PDF Generation with WeasyPrint

### Invoice Template Structure

Following the [WeasyPrint + Jinja2 guide](https://joshkaramuth.com/blog/generate-good-looking-pdfs-weasyprint-jinja2/), we'll implement:

#### Main Template (`invoice.html.j2`)
```html
<!doctype html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Invoice {{ invoice.invoice_number }}</title>
</head>
<body>
    {% include "_header.html.j2" %}
    {% include "_line_items.html.j2" %}
    {% include "_footer.html.j2" %}
</body>
</html>
```

#### Header Partial (`_header.html.j2`)
```html
<header>
    <div class="company-info">
        <h1>{{ company.name }}</h1>
        <p>{{ company.address }}</p>
        <p>Org.nr: {{ company.org_number }}</p>
        <p>VAT: {{ company.vat_number }}</p>
    </div>
    <div class="invoice-info">
        <h2>Invoice {{ invoice.invoice_number }}</h2>
        <p><b>Date:</b> {{ invoice.issue_date|format_date("%Y-%m-%d") }}</p>
        <p><b>Due:</b> {{ invoice.due_date|format_date("%Y-%m-%d") }}</p>
    </div>
    <div class="customer-info">
        <h3>Bill To:</h3>
        <p>{{ customer.name }}</p>
        <p>{{ customer.company or "" }}</p>
        <p>{{ customer.address or "" }}</p>
    </div>
</header>
```

#### Line Items Table (`_line_items.html.j2`)
```html
<section class="line-items">
    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in line_items %}
            <tr>
                <td>{{ item.description }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ item.unit_price|format_currency }}</td>
                <td>{{ item.total|format_currency }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals">
        <p>Subtotal: {{ invoice.subtotal|format_currency }}</p>
        <p>VAT ({{ (invoice.tax_rate * 100)|int }}%): {{ invoice.tax_amount|format_currency }}</p>
        <p><strong>Total: {{ invoice.total|format_currency }}</strong></p>
    </div>
</section>
```

### PDF Generation Implementation

```python
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from decimal import Decimal

class PDFGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("templates"))
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_currency'] = self._format_currency
    
    def _format_date(self, date_obj, format_str="%Y-%m-%d"):
        """Format date for display"""
        return date_obj.strftime(format_str)
    
    def _format_currency(self, amount):
        """Format currency for Swedish krona"""
        return f"{amount:,.2f} kr"
    
    def generate_invoice_pdf(self, invoice, customer, line_items, company_info):
        """Generate PDF invoice using WeasyPrint"""
        template = self.env.get_template("invoice.html.j2")
        
        html_content = template.render(
            invoice=invoice,
            customer=customer,
            line_items=line_items,
            company=company_info
        )
        
        # Load CSS
        css = CSS('static/invoice.css')
        
        # Generate PDF
        html_doc = HTML(string=html_content, base_url="")
        pdf_bytes = html_doc.write_pdf(stylesheets=[css])
        
        return pdf_bytes
```

### Server Entry Point

```python
# src/server.py
from mcp.server.fastmcp import FastMCP
import asyncio

# ... all your MCP functions ...

def main():
    """Entry point for uvx"""
    mcp = FastMCP("Invoice Generator")
    
    # Add all your tools and resources here
    # ...
    
    # Run the server
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
```

### CSS Styling (`invoice.css`)

Using CSS Flexbox and print-specific styling:

```css
@page {
    size: A4;
    margin: 2.5cm;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #2c3e50;
}

.company-info h1 {
    color: #2c3e50;
    margin-bottom: 10px;
}

.invoice-info {
    text-align: right;
}

.line-items table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

.line-items th,
.line-items td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.line-items th {
    background-color: #f8f9fa;
    font-weight: bold;
}

.totals {
    margin-left: auto;
    width: 300px;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 5px;
}

.totals p:last-child {
    font-size: 1.2em;
    font-weight: bold;
    border-top: 2px solid #2c3e50;
    padding-top: 10px;
}
```

## Database Schema

```sql
-- Customers table
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    address TEXT,
    company TEXT,
    org_number TEXT,
    vat_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices table
CREATE TABLE invoices (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- Line items table
CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
);
```


## Installation & Usage

### Prerequisites

Install uvx (if not already installed):

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# uvx comes with uv
uvx --help
```

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd mcp-invoice-server

# Install dependencies and run with uvx
uvx --from . mcp-invoice-server

# Or for development with live reload
uvx --from . --with-editable . mcp-invoice-server
```

### MCP Integration with Claude Desktop

Add to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "invoice-generator": {
      "command": "uvx",
      "args": [
        "--from",
        "/Users/tomaxberg/MCPToolbox/mcp-invoice-server",
        "mcp-invoice-server"
      ]
    }
  }
}
```

**For production deployment from git:**

```json
{
  "mcpServers": {
    "invoice-generator": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/yourusername/mcp-invoice-server.git",
        "mcp-invoice-server"
      ]
    }
  }
}
```

Restart Claude Desktop after updating the configuration.

### Usage Examples

Once installed, you can interact with the invoice server through Claude:

**Creating an invoice:**
```
Create an invoice for pal.brattberg@intersolia.com:
- 10 hours programming at 1250 SEK per hour
- Due in 30 days
```

**Email-based invoice creation:**
```
Parse this email and create an invoice:
"Hi Tom, please bill us for 5 hours consulting work at our agreed rate. Thanks, Pål"
```

**Managing invoices:**
```
Show me all pending invoices
Generate PDF for invoice #2025-001
Mark invoice #2025-001 as paid
```

## Testing & Validation

### Test Coverage
- Unit tests for all MCP tools and resources
- Integration tests for PDF generation
- Email parsing validation tests
- Database operation tests

### MCP Inspector
Use the built-in MCP Inspector for development:

```bash
mcp dev src/server.py
```

This provides a web interface for testing all MCP functions interactively.

## Documentation References

- [WeasyPrint Official Documentation](https://doc.courtbouillon.org/weasyprint/stable/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [WeasyPrint + Jinja2 Tutorial](https://joshkaramuth.com/blog/generate-good-looking-pdfs-weasyprint-jinja2/)

## Future Enhancements

- Email sending integration via SMTP
- Multiple template designs
- Multi-currency support  
- Recurring invoice automation
- Integration with accounting systems
- Advanced reporting features
- Mobile-responsive invoice viewing

## Security Considerations

- SQL injection prevention
- File system access restrictions
- PDF generation memory limits
- Secure customer data handling

This specification provides a comprehensive foundation for building a professional MCP invoice generation server that integrates seamlessly with AI assistants while maintaining high code quality and security standards.
