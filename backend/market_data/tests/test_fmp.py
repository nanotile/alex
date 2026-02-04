"""
Mock tests for FMP client — no real API calls needed.
"""

import pytest
import httpx
from unittest.mock import patch, MagicMock
from market_data.fmp import FMPClient


@pytest.fixture
def fmp():
    return FMPClient(api_key="test-key")


@pytest.fixture
def mock_profile():
    return [
        {
            "symbol": "AAPL",
            "companyName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "mktCap": 3400000000000,
            "description": "Apple designs and sells consumer electronics.",
            "beta": 1.25,
        }
    ]


@pytest.fixture
def mock_metrics():
    return [
        {
            "peRatioTTM": 28.5,
            "pbRatioTTM": 45.2,
            "dividendYieldTTM": 0.005,
            "roeTTM": 1.47,
            "debtToEquityTTM": 1.87,
            "revenuePerShareTTM": 25.12,
            "netIncomePerShareTTM": 6.42,
        }
    ]


@pytest.fixture
def mock_quote():
    return [
        {
            "symbol": "AAPL",
            "price": 195.50,
            "changesPercentage": 1.25,
            "yearHigh": 199.62,
            "yearLow": 164.08,
            "avgVolume": 54321000,
            "beta": 1.25,
        }
    ]


class TestFMPClient:
    def test_init_with_api_key(self):
        client = FMPClient(api_key="my-key")
        assert client.api_key == "my-key"

    @patch.dict("os.environ", {"FMP_API_KEY": "env-key"})
    def test_init_from_env(self):
        client = FMPClient()
        assert client.api_key == "env-key"

    @patch("market_data.fmp.httpx.Client")
    def test_get_profile(self, mock_httpx_class, fmp, mock_profile):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_profile
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_profile("AAPL")
        assert result["companyName"] == "Apple Inc."
        assert result["sector"] == "Technology"
        assert result["mktCap"] == 3400000000000

    @patch("market_data.fmp.httpx.Client")
    def test_get_key_metrics_ttm(self, mock_httpx_class, fmp, mock_metrics):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_metrics
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_key_metrics_ttm("AAPL")
        assert result["peRatioTTM"] == 28.5
        assert result["dividendYieldTTM"] == 0.005

    @patch("market_data.fmp.httpx.Client")
    def test_get_quote(self, mock_httpx_class, fmp, mock_quote):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_quote
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_quote("AAPL")
        assert result["price"] == 195.50
        assert result["symbol"] == "AAPL"

    @patch("market_data.fmp.httpx.Client")
    def test_get_fundamentals_combined(self, mock_httpx_class, fmp, mock_profile, mock_metrics, mock_quote):
        """Test that get_fundamentals combines all three sources."""
        responses = [mock_profile, mock_metrics, mock_quote]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            mock_response = MagicMock()
            mock_response.json.return_value = responses[call_count]
            mock_response.raise_for_status.return_value = None
            call_count += 1
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = side_effect
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_fundamentals("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["company_name"] == "Apple Inc."
        assert result["sector"] == "Technology"
        assert result["pe_ratio"] == 28.5
        assert result["fifty_two_week_high"] == 199.62

    @patch("market_data.fmp.httpx.Client")
    def test_get_fundamentals_partial_data(self, mock_httpx_class, fmp, mock_profile):
        """Test that get_fundamentals works with partial data (only profile)."""
        responses = [mock_profile, None, None]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            mock_response = MagicMock()
            resp_data = responses[call_count]
            if resp_data is None:
                mock_response.json.return_value = {"Error Message": "Not found"}
            else:
                mock_response.json.return_value = resp_data
            mock_response.raise_for_status.return_value = None
            call_count += 1
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = side_effect
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_fundamentals("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["company_name"] == "Apple Inc."
        # Metrics fields should not be present
        assert result.get("pe_ratio") is None

    @patch("market_data.fmp.httpx.Client")
    def test_get_profile_http_error(self, mock_httpx_class, fmp):
        """Test graceful handling when HTTP request fails."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock(status_code=403)
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_profile("AAPL")
        assert result is None

    @patch("market_data.fmp.httpx.Client")
    def test_get_bulk_quotes(self, mock_httpx_class, fmp):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"symbol": "AAPL", "price": 195.50},
            {"symbol": "MSFT", "price": 420.00},
        ]
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fmp.get_bulk_quotes(["AAPL", "MSFT"])
        assert "AAPL" in result
        assert "MSFT" in result
        assert result["AAPL"]["price"] == 195.50
