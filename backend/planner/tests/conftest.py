"""
Pytest configuration and fixtures for Planner agent tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests_common"))

from mocks import MockDatabase, MockLambda, MockSQS
from fixtures import SAMPLE_JOB, SAMPLE_PORTFOLIO, create_test_user


@pytest.fixture
def mock_db():
    """Provide a mock database for testing"""
    db = MockDatabase()
    db.setup_test_data()
    return db


@pytest.fixture
def mock_lambda():
    """Provide a mock Lambda client"""
    return MockLambda()


@pytest.fixture
def mock_sqs():
    """Provide a mock SQS client"""
    return MockSQS()


@pytest.fixture
def sample_job():
    """Sample job data"""
    return SAMPLE_JOB.copy()


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data"""
    return SAMPLE_PORTFOLIO.copy()


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ['BEDROCK_REGION'] = 'us-west-2'
    os.environ['BEDROCK_MODEL_ID'] = 'us.amazon.nova-pro-v1:0'
    os.environ['AWS_REGION_NAME'] = 'us-west-2'
    os.environ['TAGGER_FUNCTION_NAME'] = 'alex-tagger'
    os.environ['REPORTER_FUNCTION_NAME'] = 'alex-reporter'
    os.environ['CHARTER_FUNCTION_NAME'] = 'alex-charter'
    os.environ['RETIREMENT_FUNCTION_NAME'] = 'alex-retirement'
    yield
