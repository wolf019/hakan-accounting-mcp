from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any

from jinja2 import Environment, BaseLoader, select_autoescape
from weasyprint import HTML  # type: ignore[import-untyped]

from ...models.invoice_models import Invoice, Customer, LineItem, CompanyInfo, PaymentReminder
# Import all templates from single source
from ...templates.all_templates import (
    INVOICE_TEMPLATE, HEADER_TEMPLATE, LINE_ITEMS_TEMPLATE, FOOTER_TEMPLATE, CSS_CONTENT,
    REMINDER_TEMPLATE as PAYMENT_REMINDER_TEMPLATE,
    REMINDER_HEADER_TEMPLATE, REMINDER_CONTENT_TEMPLATE, REMINDER_FOOTER_TEMPLATE,
    VAT_REPORT_TEMPLATE, VAT_REPORT_HEADER_TEMPLATE, VAT_SUMMARY_TEMPLATE,
    VAT_SALES_DETAIL_TEMPLATE, VAT_EXPENSE_DETAIL_TEMPLATE, VAT_REPORT_FOOTER_TEMPLATE
)


class EmbeddedTemplateLoader(BaseLoader):
    """Custom Jinja2 loader for embedded templates"""
    
    def __init__(self):
        self.templates = {
            'invoice.html.j2': INVOICE_TEMPLATE,
            '_header.html.j2': HEADER_TEMPLATE,
            '_line_items.html.j2': LINE_ITEMS_TEMPLATE,
            '_footer.html.j2': FOOTER_TEMPLATE,
            'reminder.html.j2': PAYMENT_REMINDER_TEMPLATE,
            '_reminder_header.html.j2': REMINDER_HEADER_TEMPLATE,
            '_reminder_content.html.j2': REMINDER_CONTENT_TEMPLATE,
            '_reminder_footer.html.j2': REMINDER_FOOTER_TEMPLATE,
            'vat_report.html.j2': VAT_REPORT_TEMPLATE,
            '_vat_report_header.html.j2': VAT_REPORT_HEADER_TEMPLATE,
            '_vat_summary.html.j2': VAT_SUMMARY_TEMPLATE,
            '_vat_sales_detail.html.j2': VAT_SALES_DETAIL_TEMPLATE,
            '_vat_expense_detail.html.j2': VAT_EXPENSE_DETAIL_TEMPLATE,
            '_vat_report_footer.html.j2': VAT_REPORT_FOOTER_TEMPLATE,
        }
    
    def get_source(self, environment, template):
        if template not in self.templates:
            raise Exception(f"Template {template} not found")
        source = self.templates[template]
        return source, None, lambda: True


class PDFGenerator:
    def __init__(self):
        import sys
        
        print("Using embedded templates for PDF generation", file=sys.stderr)
        
        # Use embedded templates
        self.env = Environment(
            loader=EmbeddedTemplateLoader(),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_currency'] = self._format_currency

    def _format_date(self, date_obj, format_str: str = "%Y-%m-%d") -> str:
        """Format date for display"""
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime(format_str)

    def _format_currency(self, amount) -> str:
        """Format currency for Swedish krona"""
        if isinstance(amount, str):
            amount = Decimal(amount)
        return f"{amount:,.2f} SEK"

    def generate_invoice_pdf(
        self, 
        invoice: Invoice, 
        customer: Customer, 
        line_items: List[LineItem], 
        company_info: CompanyInfo
    ) -> bytes:
        """Generate PDF invoice using WeasyPrint with embedded templates"""
        # Render individual template sections
        header_template = self.env.get_template("_header.html.j2")
        line_items_template = self.env.get_template("_line_items.html.j2")
        footer_template = self.env.get_template("_footer.html.j2")
        
        # Render each section
        header_content = header_template.render(
            invoice=invoice,
            customer=customer,
            company=company_info
        )
        
        line_items_content = line_items_template.render(
            invoice=invoice,
            line_items=line_items
        )
        
        footer_content = footer_template.render(
            invoice=invoice,
            company=company_info
        )
        
        # Render main template with all sections
        main_template = self.env.get_template("invoice.html.j2")
        html_content = main_template.render(
            invoice=invoice,
            customer=customer,
            line_items=line_items,
            company=company_info,
            header_content=header_content,
            line_items_content=line_items_content,
            footer_content=footer_content,
            css_content=CSS_CONTENT
        )
        
        # Generate PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Ensure we return bytes, not None
        if pdf_bytes is None:
            raise Exception("Failed to generate PDF - write_pdf() returned None")
        
        return pdf_bytes

    def save_pdf(self, pdf_bytes: bytes, filename: str) -> str:
        """Save PDF bytes to file and return path"""
        import os
        
        # Save PDFs directly to Desktop for easy access
        home_dir = os.path.expanduser("~")
        pdf_dir = os.path.join(home_dir, "Desktop")
        
        output_path = Path(pdf_dir) / filename
        output_path.write_bytes(pdf_bytes)
        return str(output_path)
    
    def generate_reminder_pdf(
        self,
        reminder: PaymentReminder,
        original_invoice: Invoice,
        customer: Customer,
        company_info: CompanyInfo
    ) -> bytes:
        """Generate PDF payment reminder using WeasyPrint with embedded templates"""
        # Render individual template sections
        header_template = self.env.get_template("_reminder_header.html.j2")
        content_template = self.env.get_template("_reminder_content.html.j2")
        footer_template = self.env.get_template("_reminder_footer.html.j2")
        
        # Render each section
        header_content = header_template.render(
            reminder=reminder,
            original_invoice=original_invoice,
            customer=customer,
            company=company_info
        )
        
        reminder_content = content_template.render(
            reminder=reminder,
            original_invoice=original_invoice,
            customer=customer
        )
        
        footer_content = footer_template.render(
            reminder=reminder,
            original_invoice=original_invoice,
            company=company_info
        )
        
        # Render main template with all sections
        main_template = self.env.get_template("reminder.html.j2")
        html_content = main_template.render(
            reminder=reminder,
            original_invoice=original_invoice,
            customer=customer,
            company=company_info,
            header_content=header_content,
            reminder_content=reminder_content,
            footer_content=footer_content,
            css_content=CSS_CONTENT
        )
        
        # Generate PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Ensure we return bytes, not None
        if pdf_bytes is None:
            raise Exception("Failed to generate reminder PDF - write_pdf() returned None")
        
        return pdf_bytes

    def generate_vat_report_pdf(
        self,
        report_data: Dict[str, Any],
        company_info: CompanyInfo,
        invoices: Optional[List[Dict[str, Any]]] = None,
        expenses: Optional[List[Dict[str, Any]]] = None,
        expenses_by_category: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate PDF VAT report using WeasyPrint with embedded templates"""
        from .models import EXPENSE_CATEGORIES
        
        # Prepare data for templates
        quarter = report_data['quarter']
        year = report_data['year']
        start_date = report_data['start_date']
        end_date = report_data['end_date']
        report_date = datetime.now()
        
        # Add Swedish category names to expenses if provided
        if expenses:
            for expense in expenses:
                expense['category_name'] = EXPENSE_CATEGORIES.get(
                    expense.get('category', ''), 
                    expense.get('category', '')
                )
        
        # Render individual template sections
        header_template = self.env.get_template("_vat_report_header.html.j2")
        summary_template = self.env.get_template("_vat_summary.html.j2")
        sales_template = self.env.get_template("_vat_sales_detail.html.j2")
        expense_template = self.env.get_template("_vat_expense_detail.html.j2")
        footer_template = self.env.get_template("_vat_report_footer.html.j2")
        
        # Render each section
        header_content = header_template.render(
            company=company_info,
            quarter=quarter,
            year=year,
            start_date=start_date,
            end_date=end_date,
            report_date=report_date
        )
        
        vat_summary_content = summary_template.render(
            total_sales=report_data['total_sales'],
            total_purchases=report_data['total_purchases'],
            output_vat=report_data['output_vat'],
            input_vat=report_data['input_vat'],
            net_vat=report_data['net_vat']
        )
        
        sales_detail_content = sales_template.render(
            invoice_count=report_data['invoice_count'],
            invoices=invoices or []
        )
        
        expense_detail_content = expense_template.render(
            expense_count=report_data['expense_count'],
            expenses=expenses or [],
            expenses_by_category=expenses_by_category or {}
        )
        
        footer_content = footer_template.render(
            net_vat=report_data['net_vat'],
            report_date=report_date
        )
        
        # Render main template with all sections
        main_template = self.env.get_template("vat_report.html.j2")
        html_content = main_template.render(
            company=company_info,
            quarter=quarter,
            year=year,
            start_date=start_date,
            end_date=end_date,
            report_date=report_date,
            header_content=header_content,
            vat_summary_content=vat_summary_content,
            sales_detail_content=sales_detail_content,
            expense_detail_content=expense_detail_content,
            footer_content=footer_content,
            css_content=CSS_CONTENT,
            **report_data
        )
        
        # Generate PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Ensure we return bytes, not None
        if pdf_bytes is None:
            raise Exception("Failed to generate VAT report PDF - write_pdf() returned None")
        
        return pdf_bytes