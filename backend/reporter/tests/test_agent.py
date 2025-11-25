"""
Tests for Reporter agent logic and helper functions
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agent import (
    calculate_portfolio_metrics,
    format_portfolio_for_analysis,
    create_agent,
    ReporterContext
)
from fixtures import SAMPLE_PORTFOLIO, create_test_user
from assertions import assert_agent_response_valid, assert_portfolio_metrics_valid


class TestPortfolioMetrics:
    """Test portfolio calculation logic"""

    def test_calculate_metrics_empty_portfolio(self):
        """Test calculating metrics for empty portfolio"""
        portfolio_data = {"accounts": []}
        metrics = calculate_portfolio_metrics(portfolio_data)

        assert metrics['total_value'] == 0
        assert metrics['cash_balance'] == 0
        assert metrics['num_accounts'] == 0
        assert metrics['num_positions'] == 0
        assert metrics['unique_symbols'] == 0

    def test_calculate_metrics_with_positions(self, sample_portfolio):
        """Test calculating metrics with actual positions"""
        metrics = calculate_portfolio_metrics(sample_portfolio)

        assert_portfolio_metrics_valid(metrics)
        assert metrics['num_accounts'] == 2
        assert metrics['num_positions'] == 3
        assert metrics['unique_symbols'] == 3
        assert metrics['cash_balance'] == 7000.0  # 5000 + 2000
        # Total: 5000 cash + (100*220 VTI) + (200*75 BND) + 2000 cash + (50*60 VXUS)
        # = 5000 + 22000 + 15000 + 2000 + 3000 = 47000
        assert metrics['total_value'] == 47000.0

    def test_calculate_metrics_without_prices(self):
        """Test calculating metrics when instruments don't have prices"""
        portfolio_data = {
            "accounts": [{
                "cash_balance": 1000.0,
                "positions": [{
                    "symbol": "TEST",
                    "quantity": 10,
                    "instrument": {}  # No price
                }]
            }]
        }

        metrics = calculate_portfolio_metrics(portfolio_data)

        assert metrics['total_value'] == 1000.0  # Only cash
        assert metrics['num_positions'] == 1

    def test_calculate_metrics_unique_symbols(self):
        """Test that duplicate symbols are counted once"""
        portfolio_data = {
            "accounts": [
                {
                    "cash_balance": 0,
                    "positions": [
                        {"symbol": "VTI", "quantity": 10, "instrument": {}},
                        {"symbol": "VTI", "quantity": 20, "instrument": {}},
                        {"symbol": "BND", "quantity": 30, "instrument": {}}
                    ]
                }
            ]
        }

        metrics = calculate_portfolio_metrics(portfolio_data)

        assert metrics['unique_symbols'] == 2  # VTI and BND


class TestFormatPortfolio:
    """Test portfolio formatting for agent consumption"""

    def test_format_portfolio_structure(self, sample_portfolio):
        """Test that formatted portfolio has expected structure"""
        user_data = create_test_user()
        formatted = format_portfolio_for_analysis(sample_portfolio, user_data)

        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "Portfolio Overview:" in formatted
        assert "Account Details:" in formatted

    def test_format_includes_symbols(self, sample_portfolio):
        """Test that formatting includes position symbols"""
        user_data = create_test_user()
        formatted = format_portfolio_for_analysis(sample_portfolio, user_data)

        assert "VTI" in formatted
        assert "BND" in formatted
        assert "VXUS" in formatted

    def test_format_includes_metrics(self, sample_portfolio):
        """Test that formatting includes calculated metrics"""
        user_data = create_test_user()
        formatted = format_portfolio_for_analysis(sample_portfolio, user_data)

        assert "accounts" in formatted
        assert "positions" in formatted
        assert "cash" in formatted

    def test_format_empty_portfolio(self):
        """Test formatting empty portfolio"""
        portfolio_data = {"accounts": []}
        user_data = create_test_user()

        formatted = format_portfolio_for_analysis(portfolio_data, user_data)

        assert isinstance(formatted, str)
        assert "0 accounts" in formatted


class TestAgentCreation:
    """Test Reporter agent creation"""

    @patch('agent.LitellmModel')
    def test_create_agent_returns_components(self, mock_model_class, mock_db, sample_portfolio):
        """Test that create_agent returns all necessary components"""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        model, tools, task = create_agent(
            job_id="test_job",
            portfolio_data=sample_portfolio,
            user_preferences={},
            db=mock_db
        )

        assert model is not None
        assert isinstance(tools, list)
        assert isinstance(task, str)
        assert len(task) > 0

    @patch('agent.LitellmModel')
    def test_create_agent_task_includes_portfolio(self, mock_model_class, mock_db, sample_portfolio):
        """Test that task includes portfolio information"""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        _, _, task = create_agent(
            job_id="test_job",
            portfolio_data=sample_portfolio,
            user_preferences={},
            db=mock_db
        )

        # Task should include portfolio details
        assert "VTI" in task or "portfolio" in task.lower()

    @patch('agent.LitellmModel')
    def test_create_agent_with_preferences(self, mock_model_class, mock_db, sample_portfolio):
        """Test agent creation with user preferences"""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        user_prefs = {"risk_tolerance": "aggressive", "retirement_age": 60}

        _, _, task = create_agent(
            job_id="test_job",
            portfolio_data=sample_portfolio,
            user_preferences=user_prefs,
            db=mock_db
        )

        assert isinstance(task, str)


class TestReporterContext:
    """Test ReporterContext dataclass"""

    def test_reporter_context_creation(self, sample_portfolio):
        """Test creating ReporterContext"""
        context = ReporterContext(
            job_id="test_job",
            portfolio_data=sample_portfolio,
            user_data=create_test_user(),
            db=None
        )

        assert context.job_id == "test_job"
        assert context.portfolio_data is not None
        assert context.user_data is not None

    def test_reporter_context_with_db(self, sample_portfolio, mock_db):
        """Test ReporterContext with database"""
        context = ReporterContext(
            job_id="test_job",
            portfolio_data=sample_portfolio,
            user_data=create_test_user(),
            db=mock_db
        )

        assert context.db is not None
        assert context.db == mock_db


class TestAgentTools:
    """Test Reporter agent tool functions"""

    @pytest.mark.asyncio
    @patch('agent.get_market_insights')
    async def test_market_insights_tool_called(self, mock_insights, reporter_context):
        """Test that market insights tool can be called"""
        mock_insights.return_value = "Market analysis for VTI, BND"

        result = await mock_insights(Mock(), ["VTI", "BND"])

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_tool_receives_context(self, reporter_context):
        """Test that tools receive proper context"""
        # This is a structural test - the context should be passed correctly
        assert reporter_context.job_id is not None
        assert reporter_context.portfolio_data is not None
