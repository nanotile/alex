"""
Tests for Reporter Lambda handler
"""

import pytest
import json
import os
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from assertions import assert_lambda_response_valid


# Set mock mode before importing handler
os.environ['MOCK_LAMBDAS'] = 'true'


def _make_mock_db():
    """Create a mock Database with all required attributes."""
    mock_db = MagicMock()
    # Ensure sub-models return proper iterables, not Mock objects
    mock_db.fundamentals.find_by_symbols.return_value = []
    mock_db.economic_indicators.find_all.return_value = []
    mock_db.technical_indicators.find_by_symbols.return_value = []
    mock_db.analysis_history.find_recent.return_value = []
    return mock_db


class TestLambdaHandler:
    """Test Reporter Lambda handler entry point"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_successful_invocation(self, mock_runner, mock_db_class):
        """Test successful report generation"""
        from lambda_handler import lambda_handler

        # Setup mocks
        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending',
            'summary_payload': None,
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'clerk_user_id': 'test_user',
            'years_until_retirement': 20,
            'target_retirement_income': 80000,
        }

        mock_db.jobs.update_report.return_value = True

        # Mock agent run result
        mock_result = Mock()
        mock_result.final_output = "Comprehensive portfolio report..."
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_data": {"years_until_retirement": 20, "target_retirement_income": 80000}
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 200

        body = json.loads(result['body'])
        assert body['success'] is True

    def test_missing_job_id(self):
        """Test error handling for missing job_id"""
        from lambda_handler import lambda_handler

        event = {}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 400
        assert 'job_id' in result['body']

    @patch('lambda_handler.Database')
    def test_missing_portfolio_data(self, mock_db_class):
        """Test error handling for missing portfolio_data"""
        from lambda_handler import lambda_handler

        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = None

        event = {"job_id": "test_job"}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        # When portfolio_data missing and job not found, returns 404
        assert result['statusCode'] == 404

    @patch('lambda_handler.Database')
    def test_job_not_found(self, mock_db_class):
        """Test handling of non-existent job"""
        from lambda_handler import lambda_handler

        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = None

        event = {
            "job_id": "nonexistent",
            "portfolio_data": None,
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 404

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_agent_execution_error(self, mock_runner, mock_db_class):
        """Test error handling when agent execution fails"""
        from lambda_handler import lambda_handler

        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending',
            'summary_payload': None,
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'years_until_retirement': 20,
            'target_retirement_income': 80000,
        }

        # Mock agent failure
        mock_runner.run = AsyncMock(side_effect=Exception("Agent error"))

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_data": {"years_until_retirement": 20}
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 500

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_response_structure(self, mock_runner, mock_db_class):
        """Test that response has correct structure"""
        from lambda_handler import lambda_handler

        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'summary_payload': None,
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'years_until_retirement': 20,
            'target_retirement_income': 80000,
        }

        mock_db.jobs.update_report.return_value = True

        mock_result = Mock()
        mock_result.final_output = "Test report"
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_data": {"years_until_retirement": 20}
        }

        result = lambda_handler(event, None)

        assert 'statusCode' in result
        assert 'body' in result
        assert isinstance(result['body'], str)

        body = json.loads(result['body'])
        assert 'success' in body


class TestLambdaIntegration:
    """Test Lambda integration scenarios"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_complete_workflow(self, mock_runner, mock_db_class):
        """Test complete report generation workflow"""
        from lambda_handler import lambda_handler

        # Setup complete mock environment
        mock_db = _make_mock_db()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending',
            'summary_payload': None,
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'years_until_retirement': 25,
            'target_retirement_income': 75000,
        }

        mock_db.jobs.update_report.return_value = True

        mock_result = Mock()
        mock_result.final_output = "Detailed portfolio analysis report"
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": {
                "accounts": [{
                    "name": "Test Account",
                    "cash_balance": 5000,
                    "positions": []
                }]
            },
            "user_data": {"years_until_retirement": 25, "target_retirement_income": 75000}
        }

        result = lambda_handler(event, None)

        # Verify success
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] is True

        # Verify database was called
        mock_db.jobs.find_by_id.assert_called()
