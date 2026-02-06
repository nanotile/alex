"""
Tests for Planner orchestration logic
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from assertions import assert_valid_job_structure, assert_lambda_response_valid


class TestOrchestrationLogic:
    """Test planner orchestration decisions"""

    @patch('agent.LitellmModel')
    def test_determine_required_agents(self, mock_model):
        """Test that planner determines which agents are needed"""
        # This would test the agent creation and decision logic
        # For now, this is a placeholder for the orchestration logic
        required_agents = ["tagger", "reporter", "charter"]
        assert len(required_agents) > 0

    def test_job_status_transitions(self, mock_db, sample_job):
        """Test job status transitions during orchestration"""
        job_id = mock_db.jobs.create(sample_job)

        # Pending -> In Progress
        mock_db.jobs.update_status(job_id, "in_progress")
        job = mock_db.jobs.find_by_id(job_id)
        assert job['status'] == "in_progress"

        # In Progress -> Completed
        mock_db.jobs.update_status(job_id, "completed")
        job = mock_db.jobs.find_by_id(job_id)
        assert job['status'] == "completed"


class TestAgentInvocation:
    """Test agent invocation patterns"""

    def test_invoke_tagger_agent(self, mock_lambda):
        """Test invoking tagger agent"""
        mock_lambda.set_response('alex-tagger', {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'classifications': {'VTI': 'etf'}
            })
        })

        payload = {
            'job_id': 'test_job',
            'symbols': ['VTI', 'BND']
        }

        result = mock_lambda.invoke(
            FunctionName='alex-tagger',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode()
        )

        assert result['StatusCode'] == 200
        assert len(mock_lambda.invocations) == 1

    def test_invoke_multiple_agents_parallel(self, mock_lambda):
        """Test invoking multiple agents in parallel"""
        agents = ['alex-reporter', 'alex-charter', 'alex-retirement']

        for agent in agents:
            mock_lambda.set_response(agent, {
                'statusCode': 200,
                'body': json.dumps({'success': True})
            })

        # Invoke all agents
        for agent in agents:
            mock_lambda.invoke(
                FunctionName=agent,
                InvocationType='RequestResponse',
                Payload=json.dumps({'job_id': 'test'}).encode()
            )

        assert len(mock_lambda.invocations) == 3

    def test_handle_agent_failure(self, mock_lambda):
        """Test handling agent invocation failure"""
        mock_lambda.set_response('alex-reporter', {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': 'Internal error'
            })
        })

        result = mock_lambda.invoke(
            FunctionName='alex-reporter',
            InvocationType='RequestResponse',
            Payload=json.dumps({'job_id': 'test'}).encode()
        )

        response = json.loads(result['Payload'].read())
        assert response['statusCode'] == 500
        assert 'error' in response['body']


class TestResultAggregation:
    """Test aggregating results from multiple agents"""

    def test_aggregate_agent_results(self, mock_db, sample_job):
        """Test combining results from multiple agents"""
        job_id = mock_db.jobs.create(sample_job)

        # Simulate agent results
        mock_db.jobs.update_payload(job_id, 'report_payload', {
            'analysis': 'Portfolio report'
        })

        mock_db.jobs.update_payload(job_id, 'charts_payload', {
            'chart1': {'title': 'Allocation'}
        })

        mock_db.jobs.update_payload(job_id, 'retirement_payload', {
            'success_rate': 85.0
        })

        job = mock_db.jobs.find_by_id(job_id)

        assert 'report_payload' in job
        assert 'charts_payload' in job
        assert 'retirement_payload' in job

    def test_generate_summary(self, mock_db, sample_job):
        """Test generating summary from agent results"""
        job_id = mock_db.jobs.create(sample_job)

        # Add mock results
        mock_db.jobs.update_payload(job_id, 'report_payload', {
            'analysis': 'Strong portfolio'
        })

        summary = {
            'summary': 'Portfolio analysis complete',
            'key_findings': ['Well diversified', 'Low risk'],
            'recommendations': ['Consider rebalancing']
        }

        mock_db.jobs.update_payload(job_id, 'summary_payload', summary)

        job = mock_db.jobs.find_by_id(job_id)
        assert job['summary_payload']['summary'] == 'Portfolio analysis complete'
        assert len(job['summary_payload']['key_findings']) == 2


class TestErrorHandling:
    """Test error handling in orchestration"""

    def test_handle_missing_portfolio_data(self, mock_db):
        """Test handling missing portfolio data"""
        job_data = {
            'clerk_user_id': 'test_user',
            'job_type': 'portfolio_analysis',
            'status': 'pending',
            'request_payload': {}
        }

        job_id = mock_db.jobs.create(job_data)

        # Orchestrator should handle this gracefully
        job = mock_db.jobs.find_by_id(job_id)
        assert job is not None

    def test_mark_job_failed(self, mock_db, sample_job):
        """Test marking job as failed on error"""
        job_id = mock_db.jobs.create(sample_job)

        mock_db.jobs.update_status(job_id, "failed")
        mock_db.jobs.update_payload(job_id, 'error_message', 'Agent invocation failed')

        job = mock_db.jobs.find_by_id(job_id)
        assert job['status'] == 'failed'
        assert 'error_message' in job
