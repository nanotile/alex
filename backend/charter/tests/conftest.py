"""
Pytest configuration and fixtures for Charter agent tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add tests_common for shared fixtures
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests_common"))

# Set mock mode before importing handler
os.environ['MOCK_LAMBDAS'] = 'true'
os.environ['BEDROCK_REGION'] = 'us-west-2'
os.environ['BEDROCK_MODEL_ID'] = 'us.amazon.nova-pro-v1:0'
os.environ['AWS_REGION_NAME'] = 'us-west-2'


def _make_mock_db():
    """Create a mock Database with required attributes."""
    mock_db = MagicMock()

    mock_db.jobs.find_by_id.return_value = {
        'id': 'test_job_001',
        'clerk_user_id': 'test_user',
        'status': 'pending'
    }

    mock_db.users.find_by_clerk_id.return_value = {
        'clerk_user_id': 'test_user',
        'years_until_retirement': 20
    }

    mock_db.accounts.find_by_user.return_value = [
        {
            'id': 'acc_001',
            'account_name': 'Test 401k',
            'cash_balance': Decimal('5000.00')
        }
    ]

    mock_db.positions.find_by_account.return_value = [
        {
            'id': 'pos_001',
            'symbol': 'SPY',
            'quantity': Decimal('100')
        }
    ]

    mock_db.instruments.find_by_symbol.return_value = {
        'symbol': 'SPY',
        'name': 'SPDR S&P 500 ETF',
        'current_price': Decimal('450.00'),
        'allocation_asset_class': {'equity': 100},
        'allocation_regions': {'north_america': 100}
    }

    mock_db.technical_indicators.find_by_symbols.return_value = []
    mock_db.jobs.update_charts.return_value = True

    return mock_db


@pytest.fixture
def mock_db():
    """Provide a mock database for testing."""
    return _make_mock_db()


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing."""
    return {
        "accounts": [
            {
                "id": "acc_001",
                "name": "Test 401k",
                "type": "401k",
                "cash_balance": 5000,
                "positions": [
                    {
                        "symbol": "SPY",
                        "quantity": 100,
                        "instrument": {
                            "name": "SPDR S&P 500 ETF",
                            "current_price": 450,
                            "allocation_asset_class": {"equity": 100},
                            "allocation_regions": {"north_america": 100},
                            "allocation_sectors": {"technology": 30, "financials": 20}
                        }
                    },
                    {
                        "symbol": "BND",
                        "quantity": 50,
                        "instrument": {
                            "name": "Vanguard Bond ETF",
                            "current_price": 80,
                            "allocation_asset_class": {"fixed_income": 100},
                            "allocation_regions": {"north_america": 100}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def valid_charts_json():
    """Valid charts JSON output from agent."""
    return {
        "charts": [
            {
                "key": "asset_allocation",
                "title": "Asset Allocation",
                "type": "pie",
                "data": [
                    {"name": "Equity", "value": 70},
                    {"name": "Fixed Income", "value": 30}
                ]
            },
            {
                "key": "sector_breakdown",
                "title": "Sector Breakdown",
                "type": "bar",
                "data": [
                    {"name": "Technology", "value": 30},
                    {"name": "Financials", "value": 20}
                ]
            }
        ]
    }


@pytest.fixture
def invalid_charts_missing_fields():
    """Invalid charts JSON - missing required fields."""
    return {
        "charts": [
            {
                "key": "incomplete",
                "title": "Incomplete Chart"
                # Missing 'type' and 'data'
            }
        ]
    }


@pytest.fixture
def invalid_charts_wrong_type():
    """Invalid charts JSON - invalid chart type."""
    return {
        "charts": [
            {
                "key": "test",
                "title": "Test",
                "type": "invalid_type",
                "data": [{"name": "A", "value": 1}]
            }
        ]
    }
