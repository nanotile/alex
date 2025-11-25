"""
Custom assertion helpers for Alex backend tests
"""

from typing import Dict, Any, List


def assert_valid_portfolio_structure(portfolio: Dict[str, Any]) -> None:
    """Assert that a portfolio has the expected structure"""
    assert isinstance(portfolio, dict), "Portfolio must be a dictionary"
    assert "accounts" in portfolio, "Portfolio must have 'accounts' key"
    assert isinstance(portfolio["accounts"], list), "Accounts must be a list"

    for account in portfolio["accounts"]:
        assert "id" in account, "Account must have 'id'"
        assert "name" in account, "Account must have 'name'"
        assert "account_type" in account, "Account must have 'account_type'"
        assert "cash_balance" in account, "Account must have 'cash_balance'"
        assert "positions" in account, "Account must have 'positions'"

        for position in account["positions"]:
            assert "symbol" in position, "Position must have 'symbol'"
            assert "quantity" in position, "Position must have 'quantity'"
            assert "instrument" in position, "Position must have 'instrument'"


def assert_valid_job_structure(job: Dict[str, Any]) -> None:
    """Assert that a job has the expected structure"""
    assert isinstance(job, dict), "Job must be a dictionary"

    required_fields = ["id", "clerk_user_id", "job_type", "status"]
    for field in required_fields:
        assert field in job, f"Job must have '{field}' field"

    valid_statuses = ["pending", "in_progress", "completed", "failed"]
    assert job["status"] in valid_statuses, f"Job status must be one of {valid_statuses}"


def assert_agent_response_valid(response: str, min_length: int = 10) -> None:
    """Assert that an agent response is valid"""
    assert isinstance(response, str), "Agent response must be a string"
    assert len(response) >= min_length, f"Agent response must be at least {min_length} characters"
    assert response.strip(), "Agent response must not be empty or whitespace only"


def assert_valid_chart_data(chart: Dict[str, Any]) -> None:
    """Assert that chart data has the expected structure"""
    assert isinstance(chart, dict), "Chart must be a dictionary"
    assert "title" in chart, "Chart must have 'title'"
    assert "type" in chart, "Chart must have 'type'"
    assert "data" in chart, "Chart must have 'data'"
    assert isinstance(chart["data"], list), "Chart data must be a list"
    assert len(chart["data"]) > 0, "Chart data must not be empty"


def assert_valid_retirement_projection(projection: Dict[str, Any]) -> None:
    """Assert that retirement projection has expected structure"""
    assert isinstance(projection, dict), "Projection must be a dictionary"

    required_fields = ["success_rate", "projected_value", "years_to_retirement"]
    for field in required_fields:
        assert field in projection, f"Projection must have '{field}' field"

    assert 0 <= projection["success_rate"] <= 100, "Success rate must be between 0 and 100"
    assert projection["projected_value"] >= 0, "Projected value must be non-negative"
    assert projection["years_to_retirement"] >= 0, "Years to retirement must be non-negative"


def assert_portfolio_metrics_valid(metrics: Dict[str, Any]) -> None:
    """Assert that calculated portfolio metrics are valid"""
    assert isinstance(metrics, dict), "Metrics must be a dictionary"

    required_fields = ["total_value", "num_accounts", "num_positions"]
    for field in required_fields:
        assert field in metrics, f"Metrics must have '{field}' field"

    assert metrics["total_value"] >= 0, "Total value must be non-negative"
    assert metrics["num_accounts"] >= 0, "Number of accounts must be non-negative"
    assert metrics["num_positions"] >= 0, "Number of positions must be non-negative"


def assert_lambda_response_valid(response: Dict[str, Any]) -> None:
    """Assert that a Lambda response has the expected structure"""
    assert isinstance(response, dict), "Lambda response must be a dictionary"
    assert "statusCode" in response, "Lambda response must have 'statusCode'"
    assert "body" in response, "Lambda response must have 'body'"

    assert isinstance(response["statusCode"], int), "Status code must be an integer"
    assert 200 <= response["statusCode"] < 600, "Status code must be valid HTTP status"
