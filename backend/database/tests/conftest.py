"""
Pytest configuration and fixtures for database tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests_common"))

from mocks import MockDatabase


@pytest.fixture
def mock_db():
    """Provide a mock database for testing"""
    db = MockDatabase()
    db.setup_test_data()
    return db


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "clerk_user_id": "test_clerk_123",
        "email": "newuser@example.com",
        "display_name": "New Test User",
        "preferences": {
            "risk_tolerance": "aggressive",
            "retirement_age": 70
        }
    }


@pytest.fixture
def sample_account_data():
    """Sample account data for testing"""
    return {
        "user_id": "user_001",
        "name": "New Account",
        "account_type": "taxable",
        "cash_balance": 10000.0
    }


@pytest.fixture
def sample_instrument_data():
    """Sample instrument data for testing"""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "instrument_type": "stock",
        "asset_class": "equity",
        "current_price": 150.0
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing"""
    return {
        "clerk_user_id": "test_user_001",
        "job_type": "portfolio_analysis",
        "status": "pending",
        "request_payload": {
            "analysis_type": "full",
            "test": True
        }
    }
