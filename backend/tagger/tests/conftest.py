"""
Pytest configuration and fixtures for Tagger agent tests
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
from fixtures import SAMPLE_INSTRUMENTS


@pytest.fixture
def mock_db():
    """Provide a mock database for testing"""
    db = MockDatabase()
    db.setup_test_data()
    return db


@pytest.fixture
def sample_symbols():
    """Sample symbols for testing"""
    return list(SAMPLE_INSTRUMENTS.keys())


@pytest.fixture
def sample_instruments():
    """Sample instruments data"""
    return SAMPLE_INSTRUMENTS.copy()


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set up environment variables for testing"""
    os.environ['BEDROCK_REGION'] = 'us-west-2'
    os.environ['BEDROCK_MODEL_ID'] = 'us.amazon.nova-pro-v1:0'
    os.environ['AWS_REGION_NAME'] = 'us-west-2'
    yield
