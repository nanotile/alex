"""
Pytest configuration and fixtures for Reporter agent tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests_common"))

from mocks import MockDatabase, MockLiteLLM
from fixtures import (
    SAMPLE_PORTFOLIO,
    SAMPLE_USER_PREFS,
    SAMPLE_JOB,
    create_test_user,
    SAMPLE_REPORT_OUTPUT
)


@pytest.fixture
def mock_db():
    """Provide a mock database for testing"""
    db = MockDatabase()
    db.setup_test_data()
    return db


@pytest.fixture
def mock_llm():
    """Provide a mock LiteLLM model"""
    return MockLiteLLM(response_text=SAMPLE_REPORT_OUTPUT)


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data"""
    return SAMPLE_PORTFOLIO.copy()


@pytest.fixture
def sample_user_data():
    """Sample user data"""
    return create_test_user()


@pytest.fixture
def sample_job():
    """Sample job data"""
    return SAMPLE_JOB.copy()


@pytest.fixture
def reporter_context():
    """Sample ReporterContext for testing"""
    from agent import ReporterContext

    return ReporterContext(
        job_id="test_job_001",
        portfolio_data=SAMPLE_PORTFOLIO.copy(),
        user_data=create_test_user(),
        db=None
    )


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ['BEDROCK_REGION'] = 'us-west-2'
    os.environ['BEDROCK_MODEL_ID'] = 'us.amazon.nova-pro-v1:0'
    os.environ['AWS_REGION_NAME'] = 'us-west-2'
    yield
    # Cleanup not strictly necessary but good practice
