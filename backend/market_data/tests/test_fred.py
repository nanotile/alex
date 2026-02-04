"""
Mock tests for FRED client — no real API calls needed.
"""

import pytest
import httpx
from unittest.mock import patch, MagicMock
from market_data.fred import FREDClient, FRED_SERIES


@pytest.fixture
def fred():
    return FREDClient(api_key="test-key")


@pytest.fixture
def mock_observations_dgs10():
    return {
        "observations": [
            {"date": "2026-02-03", "value": "4.21"},
            {"date": "2026-01-31", "value": "4.18"},
        ]
    }


@pytest.fixture
def mock_observations_fedfunds():
    return {
        "observations": [
            {"date": "2026-01-01", "value": "5.33"},
            {"date": "2025-12-01", "value": "5.33"},
        ]
    }


@pytest.fixture
def mock_series_info():
    return {
        "seriess": [
            {
                "id": "DGS10",
                "title": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
                "frequency": "Daily",
                "units": "Percent",
            }
        ]
    }


class TestFREDClient:
    def test_init_with_api_key(self):
        client = FREDClient(api_key="my-key")
        assert client.api_key == "my-key"

    @patch.dict("os.environ", {"FRED_API_KEY": "env-key"})
    def test_init_from_env(self):
        client = FREDClient()
        assert client.api_key == "env-key"

    @patch("market_data.fred.httpx.Client")
    def test_get_series_info(self, mock_httpx_class, fred, mock_series_info):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_series_info
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_series_info("DGS10")
        assert result["id"] == "DGS10"
        assert result["frequency"] == "Daily"

    @patch("market_data.fred.httpx.Client")
    def test_get_latest_observation(self, mock_httpx_class, fred, mock_observations_dgs10):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_observations_dgs10
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_latest_observation("DGS10")
        assert result["value"] == 4.21
        assert result["date"] == "2026-02-03"
        assert result["previous_value"] == 4.18
        assert result["previous_date"] == "2026-01-31"

    @patch("market_data.fred.httpx.Client")
    def test_get_latest_observation_single(self, mock_httpx_class, fred):
        """Only one observation available — no previous value."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [{"date": "2026-02-03", "value": "4.21"}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_latest_observation("DGS10")
        assert result["value"] == 4.21
        assert "previous_value" not in result

    @patch("market_data.fred.httpx.Client")
    def test_get_latest_observation_missing_value(self, mock_httpx_class, fred):
        """FRED uses '.' for missing data — should be filtered."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [
                {"date": "2026-02-03", "value": "."},
                {"date": "2026-01-31", "value": "4.18"},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_latest_observation("DGS10")
        assert result["value"] == 4.18
        assert "previous_value" not in result

    @patch("market_data.fred.httpx.Client")
    def test_get_latest_observation_all_missing(self, mock_httpx_class, fred):
        """All observations are '.' — should return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [
                {"date": "2026-02-03", "value": "."},
                {"date": "2026-01-31", "value": "."},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_latest_observation("DGS10")
        assert result is None

    @patch("market_data.fred.httpx.Client")
    def test_get_economic_snapshot(self, mock_httpx_class, fred):
        """Snapshot fetches all series — mock returns data for each call."""
        mock_values = {
            "DGS10": ("4.21", "4.18"),
            "DGS2": ("4.45", "4.42"),
            "T10Y2Y": ("-0.24", "-0.20"),
            "FEDFUNDS": ("5.33", "5.33"),
            "CPIAUCSL": ("314.2", "313.5"),
            "UNRATE": ("3.7", "3.8"),
            "VIXCLS": ("14.2", "15.1"),
            "GDP": ("28269.1", "27956.3"),
        }

        call_count = 0
        series_order = list(FRED_SERIES.keys())

        def side_effect(*args, **kwargs):
            nonlocal call_count
            idx = call_count
            call_count += 1
            series_id = series_order[idx] if idx < len(series_order) else "DGS10"

            mock_response = MagicMock()
            vals = mock_values.get(series_id, ("0", "0"))
            mock_response.json.return_value = {
                "observations": [
                    {"date": "2026-02-03", "value": vals[0]},
                    {"date": "2026-01-31", "value": vals[1]},
                ]
            }
            mock_response.raise_for_status.return_value = None
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = side_effect
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        snapshot = fred.get_economic_snapshot()

        assert len(snapshot) == 8
        assert snapshot["DGS10"]["value"] == 4.21
        assert snapshot["DGS10"]["series_name"] == "10-Year Treasury Yield"
        assert snapshot["DGS10"]["units"] == "Percent"
        assert snapshot["FEDFUNDS"]["value"] == 5.33
        assert snapshot["GDP"]["value"] == 28269.1
        assert snapshot["VIXCLS"]["previous_value"] == 15.1

    @patch("market_data.fred.httpx.Client")
    def test_get_economic_snapshot_partial_failure(self, mock_httpx_class, fred):
        """Snapshot should skip series that fail."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = MagicMock()

            if call_count == 1:
                # First series succeeds
                mock_response.json.return_value = {
                    "observations": [
                        {"date": "2026-02-03", "value": "4.21"},
                        {"date": "2026-01-31", "value": "4.18"},
                    ]
                }
                mock_response.raise_for_status.return_value = None
            else:
                # All others fail
                mock_response.json.return_value = {
                    "error_code": 429,
                    "error_message": "Rate limit exceeded",
                }
                mock_response.raise_for_status.return_value = None

            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = side_effect
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        snapshot = fred.get_economic_snapshot()

        # Only the first series should succeed
        assert len(snapshot) == 1
        first_series = list(FRED_SERIES.keys())[0]
        assert first_series in snapshot

    @patch("market_data.fred.httpx.Client")
    def test_http_error_returns_none(self, mock_httpx_class, fred):
        """HTTP errors should return None gracefully."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock(status_code=403)
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_latest_observation("DGS10")
        assert result is None

    @patch("market_data.fred.httpx.Client")
    def test_fred_api_error_response(self, mock_httpx_class, fred):
        """FRED error_code in response should return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error_code": 400,
            "error_message": "Bad Request. Variable series_id is not set.",
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx_class.return_value = mock_client

        result = fred.get_series_info("INVALID")
        assert result is None
