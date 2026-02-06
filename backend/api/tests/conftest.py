"""
Pytest configuration and fixtures for API tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment before importing app
os.environ['CLERK_JWKS_URL'] = 'https://test.clerk.dev/.well-known/jwks.json'
os.environ['CORS_ORIGINS'] = 'http://localhost:3000,http://test.example.com'
os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'
os.environ['DEFAULT_AWS_REGION'] = 'us-east-1'


def _make_mock_db():
    """Create a comprehensive mock Database."""
    mock_db = MagicMock()

    # Users
    mock_db.users.find_by_clerk_id.return_value = {
        'clerk_user_id': 'test_user_001',
        'display_name': 'Test User',
        'years_until_retirement': 20,
        'target_retirement_income': 80000,
        'asset_class_targets': {'equity': 70, 'fixed_income': 30},
        'region_targets': {'north_america': 60, 'international': 40}
    }

    # Accounts
    mock_db.accounts.find_by_user.return_value = [
        {
            'id': 'acc_001',
            'clerk_user_id': 'test_user_001',
            'account_name': 'Test 401k',
            'account_purpose': 'Retirement',
            'cash_balance': Decimal('5000.00')
        }
    ]
    mock_db.accounts.find_by_id.return_value = {
        'id': 'acc_001',
        'clerk_user_id': 'test_user_001',
        'account_name': 'Test 401k',
        'account_purpose': 'Retirement',
        'cash_balance': Decimal('5000.00')
    }
    mock_db.accounts.create_account.return_value = 'acc_002'

    # Positions
    mock_db.positions.find_by_account.return_value = [
        {
            'id': 'pos_001',
            'account_id': 'acc_001',
            'symbol': 'SPY',
            'quantity': Decimal('100')
        }
    ]
    mock_db.positions.find_by_id.return_value = {
        'id': 'pos_001',
        'account_id': 'acc_001',
        'symbol': 'SPY',
        'quantity': Decimal('100')
    }
    mock_db.positions.add_position.return_value = 'pos_002'

    # Instruments
    mock_db.instruments.find_by_symbol.return_value = {
        'symbol': 'SPY',
        'name': 'SPDR S&P 500 ETF',
        'instrument_type': 'etf',
        'current_price': Decimal('450.00')
    }
    mock_db.instruments.find_all.return_value = [
        {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF', 'instrument_type': 'etf', 'current_price': Decimal('450.00')},
        {'symbol': 'VTI', 'name': 'Vanguard Total Stock', 'instrument_type': 'etf', 'current_price': Decimal('250.00')}
    ]

    # Jobs
    mock_db.jobs.find_by_id.return_value = {
        'id': 'job_001',
        'clerk_user_id': 'test_user_001',
        'job_type': 'portfolio_analysis',
        'status': 'completed',
        'created_at': '2026-02-06T12:00:00Z'
    }
    mock_db.jobs.find_by_user.return_value = [
        {'id': 'job_001', 'clerk_user_id': 'test_user_001', 'job_type': 'portfolio_analysis', 'status': 'completed', 'created_at': '2026-02-06T12:00:00Z'}
    ]
    mock_db.jobs.create_job.return_value = 'job_002'

    return mock_db


@pytest.fixture
def mock_db():
    """Provide a mock database for testing."""
    return _make_mock_db()


@pytest.fixture
def mock_sqs():
    """Provide a mock SQS client."""
    mock = MagicMock()
    mock.send_message.return_value = {'MessageId': 'test-msg-001'}
    return mock


@pytest.fixture
def mock_clerk_token():
    """Decoded Clerk JWT token payload."""
    return {
        'sub': 'test_user_001',
        'name': 'Test User',
        'email': 'test@example.com'
    }


@pytest.fixture
def auth_headers():
    """Authorization headers for authenticated requests."""
    return {'Authorization': 'Bearer test_token_123'}


@pytest.fixture
def client(mock_db, mock_sqs, mock_clerk_token):
    """Create a test client with mocked dependencies."""
    from fastapi.testclient import TestClient

    # Patch dependencies before importing app
    with patch('main.Database', return_value=mock_db), \
         patch('main.sqs_client', mock_sqs), \
         patch('main.clerk_guard') as mock_guard:

        # Mock clerk_guard to return decoded token
        mock_creds = MagicMock()
        mock_creds.decoded = mock_clerk_token
        mock_guard.return_value = mock_creds

        # Now import the app
        from main import app, get_current_user_id

        # Override the auth dependency
        async def override_get_current_user_id():
            return 'test_user_001'

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        yield TestClient(app)

        # Clean up
        app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(mock_db, mock_sqs):
    """Create a test client without auth override (for testing auth failures)."""
    from fastapi.testclient import TestClient

    with patch('main.Database', return_value=mock_db), \
         patch('main.sqs_client', mock_sqs):

        from main import app
        yield TestClient(app)
