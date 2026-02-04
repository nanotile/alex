"""
FRED (Federal Reserve Economic Data) API client.
Provides macro-economic indicators: interest rates, inflation, unemployment, GDP, VIX.

API docs: https://fred.stlouisfed.org/docs/api/fred/
"""

import os
import logging
from typing import Dict, Any, Optional, List

import httpx

logger = logging.getLogger(__name__)

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Series to fetch for economic snapshot
FRED_SERIES = {
    "DGS10": {"name": "10-Year Treasury Yield", "units": "Percent", "frequency": "Daily"},
    "DGS2": {"name": "2-Year Treasury Yield", "units": "Percent", "frequency": "Daily"},
    "T10Y2Y": {"name": "10Y-2Y Treasury Spread", "units": "Percent", "frequency": "Daily"},
    "FEDFUNDS": {"name": "Federal Funds Rate", "units": "Percent", "frequency": "Monthly"},
    "CPIAUCSL": {"name": "CPI (All Urban Consumers)", "units": "Index 1982-84=100", "frequency": "Monthly"},
    "UNRATE": {"name": "Unemployment Rate", "units": "Percent", "frequency": "Monthly"},
    "VIXCLS": {"name": "CBOE Volatility Index (VIX)", "units": "Index", "frequency": "Daily"},
    "GDP": {"name": "Gross Domestic Product", "units": "Billions of Dollars", "frequency": "Quarterly"},
}


class FREDClient:
    """Client for Federal Reserve Economic Data (FRED) API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        if not self.api_key:
            logger.warning("FRED_API_KEY not set — FRED calls will fail")

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make a GET request to the FRED API."""
        url = f"{FRED_BASE_URL}/{endpoint}"
        request_params = {"api_key": self.api_key, "file_type": "json"}
        if params:
            request_params.update(params)

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=request_params)
                response.raise_for_status()
                data = response.json()

                # FRED returns error messages in an "error_code" field
                if isinstance(data, dict) and "error_code" in data:
                    logger.error(f"FRED API error: {data.get('error_message', 'Unknown error')}")
                    return None

                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"FRED HTTP error for {endpoint}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"FRED request failed for {endpoint}: {e}")
            return None

    def get_series_info(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a FRED series.

        GET /fred/series?series_id=DGS10
        """
        data = self._get("series", params={"series_id": series_id})
        if data and "seriess" in data and len(data["seriess"]) > 0:
            return data["seriess"][0]
        return None

    def get_latest_observation(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest two observations for a series (current + previous).

        GET /fred/series/observations?series_id=DGS10&sort_order=desc&limit=2

        Returns dict with: value, date, previous_value, previous_date
        or None if the request fails.
        """
        data = self._get(
            "series/observations",
            params={
                "series_id": series_id,
                "sort_order": "desc",
                "limit": 2,
            },
        )

        if not data or "observations" not in data:
            return None

        observations = data["observations"]
        if not observations:
            return None

        # Filter out observations with "." value (FRED uses "." for missing data)
        valid_obs = [o for o in observations if o.get("value", ".") != "."]

        if not valid_obs:
            return None

        result = {
            "value": float(valid_obs[0]["value"]),
            "date": valid_obs[0]["date"],
        }

        if len(valid_obs) > 1:
            result["previous_value"] = float(valid_obs[1]["value"])
            result["previous_date"] = valid_obs[1]["date"]

        return result

    def get_economic_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch latest observations for all tracked FRED series.

        Returns {series_id: {name, value, date, previous_value, previous_date, units, frequency}}
        Skips series that fail to fetch.
        """
        snapshot = {}

        for series_id, metadata in FRED_SERIES.items():
            obs = self.get_latest_observation(series_id)
            if obs is None:
                logger.warning(f"FRED: Could not fetch {series_id} ({metadata['name']})")
                continue

            snapshot[series_id] = {
                "series_id": series_id,
                "series_name": metadata["name"],
                "value": obs["value"],
                "date": obs["date"],
                "previous_value": obs.get("previous_value"),
                "previous_date": obs.get("previous_date"),
                "units": metadata["units"],
                "frequency": metadata["frequency"],
            }

        return snapshot
