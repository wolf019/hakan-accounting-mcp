"""
Core documentation service for the MCP Accounting Server.
Provides contextual guidance and best practices for accounting tools.
"""

from typing import Optional, Dict, List, Any
from .tool_documentation import TOOL_DOCUMENTATION, WORKFLOWS, ACCOUNT_MAPPINGS, VAT_RATES


class AccountingDocumentationService:
    """
    Service class for providing comprehensive accounting tool documentation.
    Handles tool documentation, workflow guidance, and Swedish compliance information.
    """
    
    def __init__(self):
        self.tool_docs = TOOL_DOCUMENTATION
        self.workflows = WORKFLOWS
        self.accounts = ACCOUNT_MAPPINGS
        self.vat_rates = VAT_RATES
    
    def get_documentation(self, topic: Optional[str] = None, 
                         depth: str = "essentials", 
                         category: Optional[str] = None) -> str:
        """
        Get comprehensive documentation for accounting tools and workflows.
        
        Args:
            topic: Specific tool name or "overview" for general guidance
            depth: "essentials" (quick reference) or "full" (complete details)
            category: Filter by category (invoicing, expenses, accounting, reporting)
        
        Returns:
            Formatted documentation with examples and best practices
        """
        if topic is None or topic == "overview":
            return self._get_overview(category)
        
        if topic in self.tool_docs:
            return self._format_tool_documentation(topic, depth)
        
        # Search for partial matches
        matches = [tool for tool in self.tool_docs.keys() if topic.lower() in tool.lower()]
        if matches:
            if len(matches) == 1:
                return self._format_tool_documentation(matches[0], depth)
            else:
                return f"Multiple tools found: {', '.join(matches)}. Please specify one."
        
        return f"Tool '{topic}' not found. Use tools_documentation() for overview."
    
    def _get_overview(self, category: Optional[str] = None) -> str:
        """Generate overview documentation with tool listings."""
        output = []
        
        # Welcome message
        output.append("# 🏢 MCP Accounting Server - Tool Documentation")
        output.append("")
        output.append("Welcome to Sweden's AI-powered accounting system! This system provides")
        output.append("complete double-entry bookkeeping with Swedish compliance (BAS 2022).")
        output.append("")
        
        # Key principles
        output.append("## 🎯 Key Principles")
        output.append("- **Swedish Compliance**: All tools follow BAS 2022 and Swedish tax law")
        output.append("- **Double-Entry**: Every transaction creates balanced journal entries")
        output.append("- **Audit Trail**: Complete history of all financial transactions")
        output.append("- **VAT Integration**: Automatic 25% VAT calculation and posting")
        output.append("")
        
        # Tool categories
        categories = {}
        for tool_name, tool_doc in self.tool_docs.items():
            cat = tool_doc['category']
            if category is None or cat == category:
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(tool_name)
        
        output.append("## 📋 Available Tools")
        output.append("")
        
        category_names = {
            'invoicing': '📄 Invoicing Tools',
            'expenses': '💰 Expense Management',
            'accounting': '📊 Core Accounting',
            'reporting': '📈 Financial Reporting',
            'reconciliation': '🔄 Bank Reconciliation',
            'voucher_security': '🔐 Security-Protected Operations',
            'voucher_management': '📝 Voucher Management',
            'voucher_reporting': '📋 Voucher Reporting',
            'financial_reporting': '📈 Financial Reporting'
        }
        
        for cat, tools in categories.items():
            output.append(f"### {category_names.get(cat, cat.title())}")
            for tool in tools:
                doc = self.tool_docs[tool]['essentials']
                output.append(f"- **{tool}**: {doc['description']}")
            output.append("")
        
        # Common workflows
        output.append("## 🔄 Common Workflows")
        output.append("")
        for workflow_name, workflow in self.workflows.items():
            output.append(f"### {workflow_name.replace('_', ' ').title()}")
            output.append(f"{workflow['description']}")
            output.append(f"**Steps**: {' → '.join(workflow['steps'])}")
            output.append("")
        
        # Swedish compliance highlights
        output.append("## 🇸🇪 Swedish Compliance Highlights")
        output.append("- **BAS 2022**: Standard Swedish chart of accounts")
        output.append("- **VAT Rates**: 25% standard, 12% reduced, 6% low, 0% export")
        output.append("- **Invoice Numbers**: Sequential numbering required")
        output.append("- **Payment Terms**: 30 days standard, interest after due date")
        output.append("- **Audit Trail**: Complete transaction history maintained")
        output.append("")
        
        # Quick start
        output.append("## 🚀 Quick Start")
        output.append("1. **Get tool help**: `tools_documentation('create_invoice')`")
        output.append("2. **Create invoice**: `create_invoice('customer@company.se', [...])`")
        output.append("3. **Check books**: `generate_trial_balance()`")
        output.append("4. **Get workflows**: `workflow_guide('invoice_to_payment')`")
        output.append("")
        
        output.append("Use `tools_documentation('tool_name', 'full')` for detailed documentation.")
        
        return "\n".join(output)
    
    def _format_tool_documentation(self, tool_name: str, depth: str) -> str:
        """Format documentation for a specific tool."""
        tool_doc = self.tool_docs[tool_name]
        
        if depth == "essentials":
            return self._format_essentials(tool_name, tool_doc)
        else:
            return self._format_full_documentation(tool_name, tool_doc)
    
    def _format_essentials(self, tool_name: str, tool_doc: Dict) -> str:
        """Format essential (quick reference) documentation."""
        essentials = tool_doc['essentials']
        output = []
        
        output.append(f"# 📋 {tool_name} - Quick Reference")
        output.append("")
        output.append(f"**Category**: {tool_doc['category'].title()}")
        output.append(f"**Description**: {essentials['description']}")
        output.append("")
        
        output.append("## 🔧 Key Parameters")
        for param in essentials['key_parameters']:
            output.append(f"- `{param}`")
        output.append("")
        
        output.append("## 💡 Example")
        output.append(f"```python")
        output.append(f"{essentials['example']}")
        output.append(f"```")
        output.append("")
        
        output.append("## ⚡ Performance")
        output.append(f"{essentials['performance']}")
        output.append("")
        
        output.append("## 💭 Tips")
        for tip in essentials['tips']:
            output.append(f"- {tip}")
        output.append("")
        
        if 'swedish_compliance' in essentials:
            output.append("## 🇸🇪 Swedish Compliance")
            for item in essentials['swedish_compliance']:
                output.append(f"- {item}")
            output.append("")
        
        output.append(f"Use `tools_documentation('{tool_name}', 'full')` for complete documentation.")
        
        return "\n".join(output)
    
    def _format_full_documentation(self, tool_name: str, tool_doc: Dict) -> str:
        """Format complete documentation for a tool."""
        full_doc = tool_doc['full']
        output = []
        
        output.append(f"# 📚 {tool_name} - Complete Documentation")
        output.append("")
        output.append(f"**Category**: {tool_doc['category'].title()}")
        output.append("")
        
        output.append("## 📝 Description")
        output.append(full_doc['description'])
        output.append("")
        
        output.append("## 🔧 Parameters")
        for param_name, param_info in full_doc['parameters'].items():
            required = " (required)" if param_info.get('required', False) else " (optional)"
            output.append(f"### `{param_name}`{required}")
            output.append(f"- **Type**: {param_info['type']}")
            output.append(f"- **Description**: {param_info['description']}")
            if 'swedish_rule' in param_info:
                output.append(f"- **Swedish Rule**: {param_info['swedish_rule']}")
            output.append("")
        
        output.append("## 📤 Returns")
        output.append(full_doc['returns'])
        output.append("")
        
        output.append("## 💡 Examples")
        for example in full_doc['examples']:
            output.append(f"```python")
            output.append(f"{example}")
            output.append(f"```")
        output.append("")
        
        output.append("## 🎯 Use Cases")
        for use_case in full_doc['use_cases']:
            output.append(f"- {use_case}")
        output.append("")
        
        output.append("## ⚡ Performance")
        output.append(full_doc['performance'])
        output.append("")
        
        output.append("## ✅ Best Practices")
        for practice in full_doc['best_practices']:
            output.append(f"- {practice}")
        output.append("")
        
        output.append("## ⚠️ Common Pitfalls")
        for pitfall in full_doc['pitfalls']:
            output.append(f"- {pitfall}")
        output.append("")
        
        output.append("## 🔗 Related Tools")
        output.append(", ".join(full_doc['related_tools']))
        output.append("")
        
        output.append("## 📊 Accounting Impact")
        output.append(full_doc['accounting_impact'])
        output.append("")
        
        if 'vat_considerations' in full_doc:
            output.append("## 🇸🇪 VAT Considerations")
            for consideration in full_doc['vat_considerations']:
                output.append(f"- {consideration}")
            output.append("")
        
        output.append("## 📋 Audit Trail")
        output.append(full_doc['audit_trail'])
        
        return "\n".join(output)
    
    def get_workflow_guide(self, workflow_name: str) -> str:
        """Get step-by-step workflow documentation."""
        if workflow_name not in self.workflows:
            available = ", ".join(self.workflows.keys())
            return f"Workflow '{workflow_name}' not found. Available: {available}"
        
        workflow = self.workflows[workflow_name]
        output = []
        
        output.append(f"# 🔄 {workflow_name.replace('_', ' ').title()} Workflow")
        output.append("")
        output.append(f"**Description**: {workflow['description']}")
        output.append("")
        output.append(f"**Accounting Impact**: {workflow['accounting_impact']}")
        output.append("")
        
        output.append("## 📋 Steps")
        for i, step in enumerate(workflow['steps'], 1):
            output.append(f"{i}. **{step}**")
            if step in self.tool_docs:
                desc = self.tool_docs[step]['essentials']['description']
                output.append(f"   - {desc}")
            output.append("")
        
        output.append("## 💡 Tips")
        output.append("- Follow steps in order for proper accounting")
        output.append("- Each step creates audit trail entries")
        output.append("- Check account balances after completion")
        output.append("- Keep documentation for compliance")
        
        return "\n".join(output)
    
    def get_compliance_info(self, topic: str) -> str:
        """Get Swedish-specific compliance information."""
        compliance_topics = {
            "vat_reporting": self._get_vat_compliance(),
            "invoice_requirements": self._get_invoice_compliance(),
            "audit_trail": self._get_audit_compliance(),
            "chart_of_accounts": self._get_chart_compliance()
        }
        
        if topic in compliance_topics:
            return compliance_topics[topic]
        
        available = ", ".join(compliance_topics.keys())
        return f"Compliance topic '{topic}' not found. Available: {available}"
    
    def _get_vat_compliance(self) -> str:
        """VAT compliance information."""
        output = []
        
        output.append("# 🇸🇪 Swedish VAT Compliance")
        output.append("")
        output.append("## VAT Rates")
        for rate, info in self.vat_rates.items():
            output.append(f"- **{rate}**: {info['description']}")
            if info['account']:
                output.append(f"  - Account: {info['account']}")
        output.append("")
        
        output.append("## Reporting Requirements")
        output.append("- Monthly VAT returns for large businesses")
        output.append("- Quarterly VAT returns for small businesses")
        output.append("- Annual VAT declaration")
        output.append("- Electronic filing required")
        output.append("")
        
        output.append("## Key Deadlines")
        output.append("- Monthly returns: 12th of following month")
        output.append("- Quarterly returns: 12th of month after quarter")
        output.append("- Annual declaration: January 31st")
        
        return "\n".join(output)
    
    def _get_invoice_compliance(self) -> str:
        """Invoice compliance requirements."""
        output = []
        
        output.append("# 🇸🇪 Swedish Invoice Requirements")
        output.append("")
        output.append("## Mandatory Information")
        output.append("- Sequential invoice number")
        output.append("- Invoice date")
        output.append("- Supplier name and address")
        output.append("- Customer name and address")
        output.append("- VAT registration number")
        output.append("- Description of goods/services")
        output.append("- Unit price and quantity")
        output.append("- VAT rate and amount")
        output.append("- Total amount")
        output.append("- Payment terms")
        output.append("")
        
        output.append("## Payment Terms")
        output.append("- 30 days standard payment term")
        output.append("- Interest allowed after due date")
        output.append("- Late payment fee: 450 SEK + 60 SEK reminder fee")
        output.append("- Different rules for B2B vs B2C")
        
        return "\n".join(output)
    
    def _get_audit_compliance(self) -> str:
        """Audit trail compliance."""
        output = []
        
        output.append("# 🇸🇪 Swedish Audit Trail Requirements")
        output.append("")
        output.append("## Record Keeping")
        output.append("- 7 years retention period")
        output.append("- Complete transaction history")
        output.append("- All supporting documents")
        output.append("- Chronological order")
        output.append("")
        
        output.append("## Digital Records")
        output.append("- Electronic records acceptable")
        output.append("- Must be readable and searchable")
        output.append("- Backup copies required")
        output.append("- System documentation needed")
        
        return "\n".join(output)
    
    def _get_chart_compliance(self) -> str:
        """Chart of accounts compliance."""
        output = []
        
        output.append("# 🇸🇪 Swedish Chart of Accounts (BAS 2022)")
        output.append("")
        output.append("## Account Structure")
        output.append("- 1xxx: Assets (Tillgångar)")
        output.append("- 2xxx: Liabilities (Skulder)")
        output.append("- 3xxx: Revenue (Intäkter)")
        output.append("- 4xxx: Costs of Goods Sold")
        output.append("- 5xxx-8xxx: Operating Expenses")
        output.append("")
        
        output.append("## Key Accounts")
        for account_num, account_info in self.accounts.items():
            output.append(f"- **{account_num}**: {account_info['name']} - {account_info['usage']}")
        
        return "\n".join(output)
    
    def search_documentation(self, query: str) -> List[str]:
        """Search documentation for specific terms."""
        results = []
        query_lower = query.lower()
        
        for tool_name, tool_doc in self.tool_docs.items():
            # Search in tool name
            if query_lower in tool_name.lower():
                results.append(tool_name)
                continue
            
            # Search in description
            if query_lower in tool_doc['essentials']['description'].lower():
                results.append(tool_name)
                continue
            
            # Search in tips
            for tip in tool_doc['essentials']['tips']:
                if query_lower in tip.lower():
                    results.append(tool_name)
                    break
        
        return list(set(results))  # Remove duplicates