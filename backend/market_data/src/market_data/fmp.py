"""
FMP (Financial Modeling Prep) API client.
Provides company profiles, key metrics, quotes, and financial statements.

API docs: https://site.financialmodelingprep.com/developer/docs
"""

import os
import logging
from typing import Dict, Any, Optional, List

import httpx

logger = logging.getLogger(__name__)

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


class FMPClient:
    """Client for Financial Modeling Prep API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY", "")
        if not self.api_key:
            logger.warning("FMP_API_KEY not set — FMP calls will fail")

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make a GET request to the FMP API."""
        url = f"{FMP_BASE_URL}/{endpoint}"
        request_params = {"apikey": self.api_key}
        if params:
            request_params.update(params)

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=request_params)
                response.raise_for_status()
                data = response.json()

                # FMP returns error messages as dicts sometimes
                if isinstance(data, dict) and "Error Message" in data:
                    logger.error(f"FMP API error: {data['Error Message']}")
                    return None

                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"FMP HTTP error for {endpoint}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"FMP request failed for {endpoint}: {e}")
            return None

    def get_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company profile: sector, industry, market cap, description, etc.

        GET /api/v3/profile/{symbol}
        """
        data = self._get(f"profile/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def get_key_metrics_ttm(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get trailing twelve month key metrics: PE, PB, dividend yield, ROE, debt/equity.

        GET /api/v3/key-metrics-ttm/{symbol}
        """
        data = self._get(f"key-metrics-ttm/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current quote: price, change, volume.

        GET /api/v3/quote/{symbol}
        """
        data = self._get(f"quote/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def get_income_statement(self, symbol: str, limit: int = 4) -> Optional[List[Dict[str, Any]]]:
        """
        Get income statements (last N quarters).

        GET /api/v3/income-statement/{symbol}?period=quarter&limit=N
        """
        data = self._get(f"income-statement/{symbol}", params={"period": "quarter", "limit": limit})
        if data and isinstance(data, list):
            return data
        return None

    def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch all fundamental data for a symbol and return a unified dict
        suitable for database storage.

        Combines profile, key metrics, and quote data. Returns None if
        all three sources fail.
        """
        profile = self.get_profile(symbol)
        metrics = self.get_key_metrics_ttm(symbol)
        quote = self.get_quote(symbol)

        if not profile and not metrics and not quote:
            logger.warning(f"FMP: No data available for {symbol}")
            return None

        result = {"symbol": symbol}

        # From profile
        if profile:
            result.update({
                "company_name": profile.get("companyName"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "market_cap": profile.get("mktCap"),
                "description": profile.get("description", "")[:2000],
                "beta": profile.get("beta"),
            })

        # From key metrics TTM
        if metrics:
            result.update({
                "pe_ratio": metrics.get("peRatioTTM"),
                "pb_ratio": metrics.get("pbRatioTTM"),
                "dividend_yield": metrics.get("dividendYieldTTM"),
                "roe": metrics.get("roeTTM"),
                "debt_to_equity": metrics.get("debtToEquityTTM"),
                "revenue_per_share": metrics.get("revenuePerShareTTM"),
                "eps": metrics.get("netIncomePerShareTTM"),
            })

        # From quote
        if quote:
            result.update({
                "price_change_pct": quote.get("changesPercentage"),
                "fifty_two_week_high": quote.get("yearHigh"),
                "fifty_two_week_low": quote.get("yearLow"),
                "avg_volume": quote.get("avgVolume"),
            })
            # Override beta from quote if profile didn't have it
            if not result.get("beta"):
                result.update({"beta": quote.get("beta")})

        return result

    def get_bulk_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols at once.
        FMP supports comma-separated symbols in the quote endpoint.
        """
        if not symbols:
            return {}

        # FMP allows comma-separated symbols
        symbol_str = ",".join(symbols[:50])  # FMP has a limit
        data = self._get(f"quote/{symbol_str}")

        if not data or not isinstance(data, list):
            return {}

        return {item["symbol"]: item for item in data if "symbol" in item}
