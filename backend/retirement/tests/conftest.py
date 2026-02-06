"""
Pytest configuration and fixtures for Retirement agent tests
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
        'status': 'pending',
        'request_payload': {'portfolio_data': {}}
    }

    mock_db.users.find_by_clerk_id.return_value = {
        'clerk_user_id': 'test_user',
        'years_until_retirement': 25,
        'target_retirement_income': 75000
    }

    mock_db.jobs.update_retirement.return_value = True

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
                "name": "401k",
                "type": "retirement",
                "cash_balance": 10000,
                "positions": [
                    {
                        "symbol": "SPY",
                        "quantity": 100,
                        "instrument": {
                            "name": "SPDR S&P 500 ETF",
                            "current_price": 450,
                            "allocation_asset_class": {"equity": 100}
                        }
                    },
                    {
                        "symbol": "BND",
                        "quantity": 100,
                        "instrument": {
                            "name": "Vanguard Total Bond Market ETF",
                            "current_price": 75,
                            "allocation_asset_class": {"fixed_income": 100}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing."""
    return {
        'years_until_retirement': 25,
        'target_retirement_income': 75000.0,
        'current_age': 40
    }


@pytest.fixture
def sample_retirement_output():
    """Sample retirement analysis output."""
    return """
# Retirement Analysis Summary

## Current Portfolio Value
Your current portfolio is valued at $55,000 with 81% in equities and 19% in fixed income.

## Monte Carlo Simulation Results

### Conservative Scenario
- Success Rate: 72%
- Projected Portfolio at Retirement: $350,000
- Safe Withdrawal Rate: 3.5%

### Base Scenario
- Success Rate: 85%
- Projected Portfolio at Retirement: $520,000
- Safe Withdrawal Rate: 4.0%

### Optimistic Scenario
- Success Rate: 95%
- Projected Portfolio at Retirement: $750,000
- Safe Withdrawal Rate: 4.5%

## Recommendations
1. Consider increasing bond allocation as you approach retirement
2. Maintain consistent contributions to maximize compound growth
3. Review and rebalance portfolio annually
"""
