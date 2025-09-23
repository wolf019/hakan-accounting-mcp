"""
Documentation module for the MCP Accounting Server.
Provides comprehensive guidance and best practices for accounting tools.
"""

from .documentation_service import AccountingDocumentationService
from .tool_documentation import TOOL_DOCUMENTATION, WORKFLOWS, ACCOUNT_MAPPINGS, VAT_RATES

__all__ = [
    'AccountingDocumentationService',
    'TOOL_DOCUMENTATION',
    'WORKFLOWS',
    'ACCOUNT_MAPPINGS',
    'VAT_RATES'
]