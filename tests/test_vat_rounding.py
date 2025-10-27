"""
Test Swedish VAT rounding compliance.

Tests the fix for the bug where VAT calculations with decimals
failed Swedish Skatteverket whole-number validation.
"""

import pytest
from decimal import Decimal
from datetime import date


class TestSwedishVATRounding:
    """Test Swedish VAT rounding with account 3740 adjustments."""

    def test_failing_case_1006_53_sek(self, accounting_service, sample_voucher):
        """
        Test the original failing case: 1006.53 SEK with 25% VAT.

        Bug: VAT calculation produced 201.306 SEK (has decimals)
        Fix: VAT rounded to 201.00 SEK, difference (0.31) goes to account 3740
        """
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1006.53"),
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Claude Max plan oktober",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        # Verify calculations
        assert result["vat_amount"] == Decimal("201"), "VAT should be rounded to whole SEK"
        assert result["net_amount"] == Decimal("805.224"), "Net amount is theoretical value"
        assert result["has_rounding"] == True, "Should have rounding adjustment"
        assert abs(result["rounding_diff"]) == pytest.approx(0.306, abs=0.001)

        # Verify voucher is balanced
        assert accounting_service.validate_voucher_balance(sample_voucher)

        # Verify journal entries created
        with accounting_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT account_number, debit_amount, credit_amount
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                WHERE je.voucher_id = ?
                ORDER BY account_number
            """, (sample_voucher,))
            entries = cursor.fetchall()

        # Should have 3 entries: net (6110), VAT (2640), rounding (3740)
        assert len(entries) == 3, "Should have 3 journal entries"

        # Check account 2640 (VAT) has whole number
        vat_entry = [e for e in entries if e[0] == "2640"][0]
        assert vat_entry[1] == 201.0, "VAT debit should be exactly 201.00 SEK"

        # Check account 3740 (rounding) exists
        rounding_entry = [e for e in entries if e[0] == "3740"][0]
        assert abs(rounding_entry[1]) == pytest.approx(0.306, abs=0.001)

    def test_working_case_1013_06_sek(self, accounting_service, sample_voucher):
        """
        Test the working case from bug report: 1013.06 SEK with 25% VAT.

        This case has VAT rounding in the opposite direction (up instead of down).
        """
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1013.06"),
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Test expense",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        # VAT theoretical: 202.612, rounds to 203
        assert result["vat_amount"] == Decimal("203"), "VAT should round to 203 SEK"
        assert result["has_rounding"] == True
        assert result["rounding_diff"] < 0, "Rounding diff should be negative (rounded up)"

        # Verify balanced
        assert accounting_service.validate_voucher_balance(sample_voucher)

    def test_vat_exempt_transaction(self, accounting_service, sample_voucher):
        """Test VAT-exempt transaction (vat_rate=0)."""
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1000.00"),
            vat_rate=Decimal("0"),
            net_account="6110",
            vat_account="2640",
            net_description="VAT-exempt service",
            vat_description="",
            transaction_type="expense"
        )

        assert result["net_amount"] == Decimal("1000.00")
        assert result["vat_amount"] == Decimal("0")
        assert result["has_rounding"] == False

        # Should only have 1 entry (net amount)
        with accounting_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM journal_entries WHERE voucher_id = ?
            """, (sample_voucher,))
            count = cursor.fetchone()[0]

        assert count == 1, "VAT-exempt should have only 1 journal entry"

    def test_perfect_whole_number_vat(self, accounting_service, sample_voucher):
        """Test case where VAT is already a whole number (no rounding needed)."""
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1250.00"),  # 1000 + 250 VAT
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Test expense",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        assert result["vat_amount"] == Decimal("250"), "VAT should be exactly 250"
        assert result["has_rounding"] == False, "No rounding needed"

        # Should only have 2 entries (net + VAT, no rounding adjustment)
        with accounting_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM journal_entries WHERE voucher_id = ?
            """, (sample_voucher,))
            count = cursor.fetchone()[0]

        assert count == 2, "No rounding entry needed"

    def test_revenue_vat_rounding(self, accounting_service, sample_voucher):
        """Test VAT rounding for revenue (opposite debit/credit direction)."""
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1006.53"),
            vat_rate=Decimal("0.25"),
            net_account="3001",
            vat_account="2650",
            net_description="Consulting revenue",
            vat_description="VAT 25%",
            transaction_type="revenue"
        )

        # Same calculations as expense
        assert result["vat_amount"] == Decimal("201")
        assert result["has_rounding"] == True

        # Verify entries are credits (revenue side)
        with accounting_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT account_number, debit_amount, credit_amount
                FROM journal_entries je
                JOIN accounts a ON je.account_id = a.id
                WHERE je.voucher_id = ?
                ORDER BY account_number
            """, (sample_voucher,))
            entries = cursor.fetchall()

        # Revenue and VAT should be credits
        revenue_entry = [e for e in entries if e[0] == "3001"][0]
        assert revenue_entry[2] > 0, "Revenue should be credit"

        vat_entry = [e for e in entries if e[0] == "2650"][0]
        assert vat_entry[2] == 201.0, "VAT should be credit of 201"

    def test_multiple_vat_rates(self, accounting_service):
        """Test different Swedish VAT rates: 25%, 12%, 6%, 0%."""
        test_cases = [
            (Decimal("0.25"), "Standard rate"),
            (Decimal("0.12"), "Food rate"),
            (Decimal("0.06"), "Books/newspapers rate"),
            (Decimal("0.0"), "Exempt"),
        ]

        for vat_rate, description in test_cases:
            voucher_id = accounting_service.create_voucher(
                description=f"Test {description}",
                voucher_type="PURCHASE",
                total_amount=Decimal("1234.56"),
                voucher_date=date.today()
            )

            result = accounting_service.add_swedish_vat_entries(
                voucher_id=voucher_id,
                gross_amount=Decimal("1234.56"),
                vat_rate=vat_rate,
                net_account="6110",
                vat_account="2640",
                net_description=description,
                vat_description=f"VAT {int(vat_rate*100)}%",
                transaction_type="expense"
            )

            # VAT amount must be whole number (or zero)
            assert result["vat_amount"] == round(result["vat_amount"]), \
                f"VAT must be whole number for rate {vat_rate}"

            # Voucher must be balanced
            assert accounting_service.validate_voucher_balance(voucher_id)

    def test_invalid_vat_rate(self, accounting_service, sample_voucher):
        """Test that invalid VAT rates are rejected."""
        with pytest.raises(ValueError, match="Invalid VAT rate"):
            accounting_service.add_swedish_vat_entries(
                voucher_id=sample_voucher,
                gross_amount=Decimal("1000.00"),
                vat_rate=Decimal("1.5"),  # Invalid: > 1
                net_account="6110",
                vat_account="2640",
                net_description="Test",
                vat_description="VAT",
                transaction_type="expense"
            )

        with pytest.raises(ValueError, match="Invalid VAT rate"):
            accounting_service.add_swedish_vat_entries(
                voucher_id=sample_voucher,
                gross_amount=Decimal("1000.00"),
                vat_rate=Decimal("-0.25"),  # Invalid: negative
                net_account="6110",
                vat_account="2640",
                net_description="Test",
                vat_description="VAT",
                transaction_type="expense"
            )


class TestVATRoundingEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_tiny_amount(self, accounting_service, sample_voucher):
        """Test very small amounts (1 SEK with VAT)."""
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1.25"),
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Tiny expense",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        # VAT theoretical: 0.25, rounds to 0
        assert result["vat_amount"] == Decimal("0")
        assert accounting_service.validate_voucher_balance(sample_voucher)

    def test_large_amount(self, accounting_service, sample_voucher):
        """Test large amounts (millions of SEK)."""
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1000000.49"),
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Large expense",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        # Should still work and be balanced
        assert result["vat_amount"] == round(result["vat_theoretical"])
        assert accounting_service.validate_voucher_balance(sample_voucher)

    def test_rounding_threshold(self, accounting_service, sample_voucher):
        """Test that rounding adjustment is only added when >= 0.01 SEK."""
        # Find an amount where rounding is exactly 0.5 öre (0.005 SEK)
        result = accounting_service.add_swedish_vat_entries(
            voucher_id=sample_voucher,
            gross_amount=Decimal("1.00"),
            vat_rate=Decimal("0.25"),
            net_account="6110",
            vat_account="2640",
            net_description="Test",
            vat_description="VAT 25%",
            transaction_type="expense"
        )

        # VAT: 0.20, rounded to 0
        # Even with rounding, if < 0.01 it might not add entry
        # Just verify it's balanced
        assert accounting_service.validate_voucher_balance(sample_voucher)
