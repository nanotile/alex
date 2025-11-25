"""
Tests for Reporter Lambda handler
"""

import pytest
import json
import os
from unittest.mock import patch, Mock, AsyncMock
from assertions import assert_lambda_response_valid


# Set mock mode before importing handler
os.environ['MOCK_LAMBDAS'] = 'true'


class TestLambdaHandler:
    """Test Reporter Lambda handler entry point"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_successful_invocation(self, mock_runner, mock_db_class):
        """Test successful report generation"""
        from lambda_handler import lambda_handler

        # Setup mocks
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending'
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'clerk_user_id': 'test_user',
            'preferences': {}
        }

        # Mock agent run result
        mock_result = Mock()
        mock_result.final_output = "Comprehensive portfolio report..."
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_preferences": {}
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 200

        body = json.loads(result['body'])
        assert body['success'] is True
        assert 'report' in body

    def test_missing_job_id(self):
        """Test error handling for missing job_id"""
        from lambda_handler import lambda_handler

        event = {}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 400
        assert 'job_id' in result['body']

    def test_missing_portfolio_data(self):
        """Test error handling for missing portfolio_data"""
        from lambda_handler import lambda_handler

        event = {"job_id": "test_job"}
        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 400
        assert 'portfolio_data' in result['body']

    @patch('lambda_handler.Database')
    def test_job_not_found(self, mock_db_class):
        """Test handling of non-existent job"""
        from lambda_handler import lambda_handler

        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.jobs.find_by_id.return_value = None

        event = {
            "job_id": "nonexistent",
            "portfolio_data": {"accounts": []},
            "user_preferences": {}
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 404

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_agent_execution_error(self, mock_runner, mock_db_class):
        """Test error handling when agent execution fails"""
        from lambda_handler import lambda_handler

        mock_db = Mock()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending'
        }

        # Mock agent failure
        mock_runner.run = AsyncMock(side_effect=Exception("Agent error"))

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_preferences": {}
        }

        result = lambda_handler(event, None)

        assert_lambda_response_valid(result)
        assert result['statusCode'] == 500

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_response_structure(self, mock_runner, mock_db_class):
        """Test that response has correct structure"""
        from lambda_handler import lambda_handler

        mock_db = Mock()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user'
        }

        mock_result = Mock()
        mock_result.final_output = "Test report"
        mock_runner.run = AsyncMock(return_value=mock_result)

        event = {
            "job_id": "test_job",
            "portfolio_data": {"accounts": []},
            "user_preferences": {}
        }

        result = lambda_handler(event, None)

        assert 'statusCode' in result
        assert 'body' in result
        assert isinstance(result['body'], str)

        body = json.loads(result['body'])
        assert 'success' in body
        assert 'report' in body


class TestLambdaIntegration:
    """Test Lambda integration scenarios"""

    @patch('lambda_handler.Database')
    @patch('lambda_handler.Runner')
    def test_complete_workflow(self, mock_runner, mock_db_class):
        """Test complete report generation workflow"""
        from lambda_handler import lambda_handler

        # Setup complete mock environment
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        mock_db.jobs.find_by_id.return_value = {
            'id': 'test_job',
            'clerk_user_id': 'test_user',
            'status': 'pending'
        }

        mock_db.users.find_by_clerk_id.return_value = {
            'id': 'user_001',
            'preferences': {'risk_tolerance': 'moderate'}
        }

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
            "user_preferences": {"risk_tolerance": "moderate"}
        }

        result = lambda_handler(event, None)

        # Verify success
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] is True
        assert len(body['report']) > 0

        # Verify database was called
        mock_db.jobs.find_by_id.assert_called_with('test_job')
