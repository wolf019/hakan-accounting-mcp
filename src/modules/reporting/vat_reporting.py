"""
VAT Reporting - Swedish VAT compliance and reporting functionality
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any

from src.database import DatabaseManager


class VATReportingService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def generate_vat_report_data(self, year: int, quarter: int) -> Dict[str, Any]:
        """Generate VAT report data for Swedish quarterly filing"""
        # Calculate quarter dates
        quarter_months = {
            1: (1, 3),
            2: (4, 6), 
            3: (7, 9),
            4: (10, 12)
        }
        
        start_month, end_month = quarter_months[quarter]
        start_date = date(year, start_month, 1)
        
        # Calculate end date
        if end_month == 12:
            end_date = date(year, 12, 31)
        elif end_month in [3, 9]:
            end_date = date(year, end_month, 31)
        else:
            end_date = date(year, end_month, 30)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get invoices for the period (output VAT)
            cursor.execute("""
                SELECT COUNT(*), SUM(subtotal), SUM(tax_amount), SUM(total)
                FROM invoices 
                WHERE issue_date >= ? AND issue_date <= ? 
                AND status != 'draft'
            """, (start_date, end_date))
            
            invoice_data = cursor.fetchone()
            invoice_count = invoice_data[0] or 0
            total_sales = Decimal(str(invoice_data[1] or 0))
            output_vat = Decimal(str(invoice_data[2] or 0))
            
            # Get expenses for the period (input VAT)
            cursor.execute("""
                SELECT COUNT(*), SUM(amount - vat_amount), SUM(vat_amount)
                FROM expenses 
                WHERE expense_date >= ? AND expense_date <= ?
                AND is_deductible = TRUE
            """, (start_date, end_date))
            
            expense_data = cursor.fetchone()
            expense_count = expense_data[0] or 0
            total_purchases = Decimal(str(expense_data[1] or 0))
            input_vat = Decimal(str(expense_data[2] or 0))
            
            # Calculate net VAT
            net_vat = output_vat - input_vat
            
            return {
                'year': year,
                'quarter': quarter,
                'start_date': start_date,
                'end_date': end_date,
                'invoice_count': invoice_count,
                'expense_count': expense_count,
                'total_sales': total_sales,
                'total_purchases': total_purchases,
                'output_vat': output_vat,
                'input_vat': input_vat,
                'net_vat': net_vat
            }
    
    def format_vat_report(self, report_data: Dict[str, Any]) -> str:
        """Format VAT report for display"""
        result = [
            f"VAT Report - Q{report_data['quarter']} {report_data['year']}",
            f"Period: {report_data['start_date']} to {report_data['end_date']}",
            "",
            "SALES (Försäljning):",
            f"  Invoices: {report_data['invoice_count']}",
            f"  Total sales (excl. VAT): {report_data['total_sales']:.2f} SEK",
            f"  Output VAT (utgående moms): {report_data['output_vat']:.2f} SEK",
            "",
            "PURCHASES (Inköp):",
            f"  Expenses: {report_data['expense_count']}",
            f"  Total purchases (excl. VAT): {report_data['total_purchases']:.2f} SEK",
            f"  Input VAT (ingående moms): {report_data['input_vat']:.2f} SEK",
            "",
            "SUMMARY:",
            f"  Output VAT: {report_data['output_vat']:.2f} SEK",
            f"  Input VAT: {report_data['input_vat']:.2f} SEK",
        ]
        
        if report_data['net_vat'] >= 0:
            result.append(f"  Net VAT to pay: {report_data['net_vat']:.2f} SEK")
        else:
            result.append(f"  Net VAT to receive: {abs(report_data['net_vat']):.2f} SEK")
        
        return "\n".join(result)