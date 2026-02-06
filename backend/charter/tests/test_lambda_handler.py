"""
Tests for Charter Lambda handler
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
    """Test Charter Lambda handler entry point"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_successful_invocation(self, mock_runner, mock_db_class, sample_portfolio):
        """Test successful chart generation"""
        from lambda_handler import lambda_handler

        # Setup mocks
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.update_charts.return_value = True
        mock_db.technical_indicators.find_by_symbols.return_value = []

        # Mock agent output with valid JSON
        valid_output = json.dumps({
            "charts": [
                {"key": "test", "title": "Test", "type": "pie", "data": [{"name": "A", "value": 100}]}
            ]
        })
        mock_result = Mock()
        mock_result.final_output = valid_output
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
        assert body['charts_generated'] == 1

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
        assert result['statusCode'] == 404

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_invalid_json_output(self, mock_runner, mock_db_class, sample_portfolio):
        """Test handling of invalid JSON from agent"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.update_charts.return_value = True
        mock_db.technical_indicators.find_by_symbols.return_value = []

        # Mock agent output with invalid JSON
        mock_result = Mock()
        mock_result.final_output = "This is not valid JSON"
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 200  # Still 200 but success=False
        body = json.loads(result['body'])
        assert body['success'] is False

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_retry_on_invalid_output(self, mock_runner, mock_db_class, sample_portfolio):
        """Test that agent retries on invalid output"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.update_charts.return_value = True
        mock_db.technical_indicators.find_by_symbols.return_value = []

        # First call returns invalid, second returns valid
        first_result = Mock()
        first_result.final_output = "invalid json"

        second_result = Mock()
        second_result.final_output = json.dumps({
            "charts": [
                {"key": "test", "title": "Test", "type": "bar", "data": [{"name": "A", "value": 50}]}
            ]
        })

        mock_runner.run = AsyncMock(side_effect=[first_result, second_result])

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        body = json.loads(result['body'])
        assert body['success'] is True
        # Verify retry was called
        assert mock_runner.run.call_count == 2

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_response_structure(self, mock_runner, mock_db_class, sample_portfolio):
        """Test response has correct structure"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.update_charts.return_value = True
        mock_db.technical_indicators.find_by_symbols.return_value = []

        mock_result = Mock()
        mock_result.final_output = json.dumps({
            "charts": [
                {"key": "c1", "title": "Chart 1", "type": "pie", "data": [{"name": "A", "value": 100}]},
                {"key": "c2", "title": "Chart 2", "type": "bar", "data": [{"name": "B", "value": 50}]}
            ]
        })
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
        assert 'charts_generated' in body
        assert 'chart_keys' in body
        assert body['charts_generated'] == 2
        assert 'c1' in body['chart_keys']
        assert 'c2' in body['chart_keys']

    @patch('lambda_handler.Database')
    def test_loads_portfolio_from_db(self, mock_db_class, mock_db):
        """Test that handler loads portfolio from DB when not provided"""
        from lambda_handler import lambda_handler

        mock_db_class.return_value = mock_db

        # Don't include portfolio_data - should load from DB
        event = {"job_id": "test_job"}

        with patch('lambda_handler.Runner') as mock_runner:
            mock_result = Mock()
            mock_result.final_output = json.dumps({
                "charts": [{"key": "t", "title": "T", "type": "pie", "data": [{"name": "A", "value": 1}]}]
            })
            mock_runner.run = AsyncMock(return_value=mock_result)

            result = lambda_handler(event, None)

        # Should have tried to load from DB
        mock_db.jobs.find_by_id.assert_called_with("test_job")
        mock_db.accounts.find_by_user.assert_called()


class TestErrorHandling:
    """Test error handling"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_exception_returns_500(self, mock_runner, mock_db_class, sample_portfolio):
        """Test that exceptions are caught and return 500"""
        from lambda_handler import lambda_handler

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.technical_indicators.find_by_symbols.side_effect = Exception("DB error")

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
        mock_db.technical_indicators.find_by_symbols.side_effect = Exception("password=secret123")

        event = {
            "job_id": "test_job",
            "portfolio_data": sample_portfolio
        }

        result = lambda_handler(event, None)

        body = json.loads(result['body'])
        # Should not expose raw error
        assert 'secret123' not in json.dumps(body)
        assert 'password' not in json.dumps(body).lower()
