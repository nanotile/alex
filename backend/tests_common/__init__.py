"""
Common testing utilities for Alex backend agents
"""

from .mocks import MockLiteLLM, MockDatabase, MockSQS, MockLambda
from .fixtures import (
    SAMPLE_PORTFOLIO,
    SAMPLE_USER_PREFS,
    SAMPLE_JOB,
    SAMPLE_INSTRUMENTS,
    create_test_user,
    create_test_portfolio,
)
from .assertions import (
    assert_valid_portfolio_structure,
    assert_valid_job_structure,
    assert_agent_response_valid,
)

__all__ = [
    'MockLiteLLM',
    'MockDatabase',
    'MockSQS',
    'MockLambda',
    'SAMPLE_PORTFOLIO',
    'SAMPLE_USER_PREFS',
    'SAMPLE_JOB',
    'SAMPLE_INSTRUMENTS',
    'create_test_user',
    'create_test_portfolio',
    'assert_valid_portfolio_structure',
    'assert_valid_job_structure',
    'assert_agent_response_valid',
]
