"""
Tests for Retirement Lambda handler
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock, MagicMock

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add tests_common
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests_common"))

from assertions import assert_lambda_response_valid


class TestLambdaHandler:
    """Test Retirement Lambda handler entry point"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_successful_invocation(self, mock_runner, mock_db_class, sample_portfolio, sample_retirement_output):
        """Test successful retirement analysis"""
        from lambda_handler import lambda_handler

        # Setup mocks
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user'
        }
        mock_db.users.find_by_clerk_id.return_value = {
            'clerk_user_id': 'test_user',
            'years_until_retirement': 25,
            'target_retirement_income': 75000
        }
        mock_db.jobs.update_retirement.return_value = True

        mock_result = Mock()
        mock_result.final_output = sample_retirement_output
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 200

        body = json.loads(result['body'])
        assert body['success'] is True
        assert 'Retirement analysis completed' in body['message']

    def test_missing_job_id(self):
        """Test error handling for missing job_id"""
        from lambda_handler import lambda_handler

        event = {}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 400
        assert 'job_id' in result['body']

    @patch('lambda_handler.Database')
    def test_job_not_found(self, mock_db_class):
        """Test error when job not found in database"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = None

        event = {"job_id": "nonexistent"}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        # Returns 400 or 404 depending on code path
        assert result['statusCode'] in [400, 404]
        assert 'error' in result['body'].lower() or 'not found' in result['body'].lower()

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_response_structure(self, mock_runner, mock_db_class, sample_portfolio, sample_retirement_output):
        """Test response has correct structure"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = {'id': 'test', 'clerk_user_id': 'user'}
        mock_db.users.find_by_clerk_id.return_value = {
            'years_until_retirement': 20,
            'target_retirement_income': 80000
        }
        mock_db.jobs.update_retirement.return_value = True

        mock_result = Mock()
        mock_result.final_output = sample_retirement_output
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        assert 'statusCode' in result
        assert 'body' in result

        body = json.loads(result['body'])
        assert 'success' in body
        assert 'message' in body
        assert 'final_output' in body

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_db_save_failure(self, mock_runner, mock_db_class, sample_portfolio, sample_retirement_output):
        """Test handling when database save fails"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = {'id': 'test', 'clerk_user_id': 'user'}
        mock_db.users.find_by_clerk_id.return_value = {
            'years_until_retirement': 20,
            'target_retirement_income': 80000
        }
        mock_db.jobs.update_retirement.return_value = False  # Save fails

        mock_result = Mock()
        mock_result.final_output = sample_retirement_output
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        body = json.loads(result['body'])
        assert body['success'] is False
        assert 'failed to save' in body['message'].lower()


class TestGetUserPreferences:
    """Test user preferences loading"""

    @patch('lambda_handler.Database')
    def test_loads_user_preferences(self, mock_db_class, mock_db):
        """Test that user preferences are loaded from database"""
        from lambda_handler import get_user_preferences

        mock_db_class.return_value = mock_db

        prefs = get_user_preferences("test_job_001")

        assert prefs['years_until_retirement'] == 25
        assert prefs['target_retirement_income'] == 75000.0

    @patch('lambda_handler.Database')
    def test_defaults_when_user_not_found(self, mock_db_class):
        """Test default preferences when user not found"""
        from lambda_handler import get_user_preferences

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = None

        prefs = get_user_preferences("nonexistent")

        # Should return defaults
        assert prefs['years_until_retirement'] == 30
        assert prefs['target_retirement_income'] == 80000.0

    @patch('lambda_handler.Database')
    def test_defaults_on_db_error(self, mock_db_class):
        """Test default preferences on database error"""
        from lambda_handler import get_user_preferences

        mock_db_class.side_effect = Exception("DB connection failed")

        prefs = get_user_preferences("test_job")

        # Should return defaults without crashing
        assert prefs['years_until_retirement'] == 30
        assert prefs['target_retirement_income'] == 80000.0


class TestErrorHandling:
    """Test error handling"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_exception_returns_500(self, mock_runner, mock_db_class, sample_portfolio):
        """Test that exceptions are caught and return 500"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = {'id': 'test', 'clerk_user_id': 'user'}
        mock_db.users.find_by_clerk_id.side_effect = Exception("DB error")

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert body['success'] is False

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_error_sanitized(self, mock_runner, mock_db_class, sample_portfolio):
        """Test that error messages are sanitized"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.side_effect = Exception("password=secret123")

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        body = json.loads(result['body'])
        # Should not expose raw error
        assert 'secret123' not in json.dumps(body)
        assert 'password' not in json.dumps(body).lower()

    def test_string_event_parsed(self):
        """Test that string event is parsed as JSON"""
        from lambda_handler import lambda_handler

        event = json.dumps({})  # String, no job_id
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 400
        assert 'job_id' in result['body']
