# MCP Accounting Server Test Suite

## Overview

This test suite uses **pytest** with **in-memory SQLite databases**. No data is written to your production database.

## Setup

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Or with standard pip
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_vat_rounding.py

# Run specific test
pytest tests/test_vat_rounding.py::TestSwedishVATRounding::test_failing_case_1006_53_sek

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures (in-memory DB setup)
├── test_vat_rounding.py     # Swedish VAT rounding compliance tests
└── README.md                # This file
```

## Key Fixtures

### `test_db`
- Creates a fresh in-memory SQLite database for each test
- Includes full schema with all necessary tables
- Pre-populated with test accounts (BAS 2022)
- Automatically cleaned up after each test

### `accounting_service`
- AccountingService instance connected to test database
- Ready to use for all accounting operations

### `sample_voucher`
- Pre-created voucher for quick testing
- Clean starting point for journal entry tests

## What Gets Tested

### VAT Rounding Tests (`test_vat_rounding.py`)

**Core Bug Fix:**
- ✅ Failing case: 1006.53 SEK with 25% VAT
- ✅ Working case: 1013.06 SEK with 25% VAT
- ✅ VAT-exempt transactions (0% VAT)
- ✅ Perfect whole-number VAT (no rounding needed)
- ✅ Revenue VAT rounding (credit side)
- ✅ Multiple VAT rates (25%, 12%, 6%, 0%)
- ✅ Invalid VAT rate rejection

**Edge Cases:**
- ✅ Tiny amounts (1 SEK)
- ✅ Large amounts (millions of SEK)
- ✅ Rounding threshold (0.01 SEK minimum)

## Example Test Output

```bash
$ pytest tests/test_vat_rounding.py -v

tests/test_vat_rounding.py::TestSwedishVATRounding::test_failing_case_1006_53_sek PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_working_case_1013_06_sek PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_vat_exempt_transaction PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_perfect_whole_number_vat PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_revenue_vat_rounding PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_multiple_vat_rates PASSED
tests/test_vat_rounding.py::TestSwedishVATRounding::test_invalid_vat_rate PASSED
tests/test_vat_rounding.py::TestVATRoundingEdgeCases::test_tiny_amount PASSED
tests/test_vat_rounding.py::TestVATRoundingEdgeCases::test_large_amount PASSED
tests/test_vat_rounding.py::TestVATRoundingEdgeCases::test_rounding_threshold PASSED

======================== 10 passed in 0.15s ========================
```

## Adding New Tests

1. Create a new test file: `tests/test_your_feature.py`
2. Import fixtures from `conftest.py`
3. Use in-memory database fixtures
4. Write test functions starting with `test_`

Example:

```python
def test_my_feature(accounting_service, sample_voucher):
    # Use accounting_service with in-memory DB
    result = accounting_service.some_method(sample_voucher)

    # Assert expected behavior
    assert result == expected_value

    # No cleanup needed - happens automatically
```

## Benefits of This Approach

✅ **Zero Database Pollution** - In-memory SQLite, destroyed after tests
✅ **Fast** - No disk I/O, runs in milliseconds
✅ **Isolated** - Each test gets fresh database
✅ **Safe** - Can't accidentally modify production data
✅ **Repeatable** - Same starting state every time
✅ **CI/CD Ready** - No external dependencies

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    uv pip install -e ".[dev]"
    pytest --cov=src --cov-report=xml
```

## Troubleshooting

**Import errors?**
```bash
# Make sure you're in the project root
cd /path/to/mcp-accounting-server

# Install in development mode
uv pip install -e ".[dev]"
```

**Fixture not found?**
- Check that `conftest.py` is in the `tests/` directory
- Make sure `tests/__init__.py` exists

**Database errors?**
- Tests use in-memory DB (`:memory:`)
- No configuration needed
- Should work on any system with SQLite support
