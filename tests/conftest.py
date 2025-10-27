"""
Pytest configuration and fixtures for MCP accounting server tests.

Uses in-memory SQLite database - no data written to production database.
"""

import pytest
import sqlite3
from decimal import Decimal
from datetime import date
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager
from src.modules.accounting import AccountingService
from src.models.accounting_models import VoucherType


@pytest.fixture
def test_db():
    """
    Create an in-memory test database with schema.
    Fresh database for each test - no pollution.

    DatabaseManager automatically creates all tables via init_database().
    """
    # Create in-memory database - DatabaseManager will initialize schema
    db = DatabaseManager(db_path=":memory:")

    # Just add test-specific data (accounts are already created by DatabaseManager)
    # No need to create tables manually - DatabaseManager does that

    yield db

    # Cleanup happens automatically when in-memory DB goes out of scope


@pytest.fixture
def accounting_service(test_db):
    """AccountingService instance with test database."""
    return AccountingService(test_db)


@pytest.fixture
def sample_voucher(accounting_service):
    """Create a sample voucher for testing."""
    voucher_id = accounting_service.create_voucher(
        description="Test voucher",
        voucher_type=VoucherType.PURCHASE,
        total_amount=Decimal("1000.00"),
        voucher_date=date.today()
    )
    return voucher_id
