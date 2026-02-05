"""
Database model for technical indicators (pandas-ta computed data cache).
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .client import DataAPIClient

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Technical indicators table operations (pandas-ta data cache)."""

    table_name = "technical_indicators"

    def __init__(self, db: DataAPIClient):
        self.db = db

    def find_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Find technical indicators by symbol."""
        sql = f"SELECT * FROM {self.table_name} WHERE symbol = :symbol"
        params = [{"name": "symbol", "value": {"stringValue": symbol}}]
        return self.db.query_one(sql, params)

    def find_by_symbols(self, symbols: List[str]) -> List[Dict]:
        """Find technical indicators for multiple symbols."""
        if not symbols:
            return []

        placeholders = []
        params = []
        for i, symbol in enumerate(symbols):
            param_name = f"sym_{i}"
            placeholders.append(f":{param_name}")
            params.append({"name": param_name, "value": {"stringValue": symbol}})

        sql = f"SELECT * FROM {self.table_name} WHERE symbol IN ({', '.join(placeholders)})"
        return self.db.query(sql, params)

    def upsert_indicators(self, symbol: str, indicators: Dict[str, Any]) -> bool:
        """
        Insert or update technical indicators for a symbol.
        Stores the full indicators dict as JSONB.
        Uses PostgreSQL ON CONFLICT ... DO UPDATE for upsert.
        """
        if not symbol or not indicators:
            return False

        indicators_json = json.dumps(indicators)

        sql = f"""
            INSERT INTO {self.table_name} (symbol, indicators, computed_at)
            VALUES (:symbol, :indicators::jsonb, NOW())
            ON CONFLICT (symbol) DO UPDATE SET
                indicators = EXCLUDED.indicators,
                computed_at = NOW(),
                updated_at = NOW()
        """

        params = [
            {"name": "symbol", "value": {"stringValue": symbol}},
            {"name": "indicators", "value": {"stringValue": indicators_json}},
        ]

        try:
            self.db.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert technical indicators for {symbol}: {e}")
            return False

    def is_stale(self, symbol: str, max_age_hours: int = 1) -> bool:
        """
        Check if technical indicator data is stale (older than max_age_hours).
        Returns True if data doesn't exist or is older than the threshold.
        Default 1 hour — indicators change intraday.
        """
        record = self.find_by_symbol(symbol)
        if not record:
            return True

        computed_at = record.get("computed_at")
        if not computed_at:
            return True

        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        age = datetime.utcnow() - computed_at
        return age > timedelta(hours=max_age_hours)

    def get_stale_symbols(self, symbols: List[str], max_age_hours: int = 1) -> List[str]:
        """
        From a list of symbols, return those that need fresh technical indicator computation.
        Default 1 hour staleness window.
        """
        if not symbols:
            return []

        existing = self.find_by_symbols(symbols)
        existing_map = {r["symbol"]: r for r in existing}

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale = []

        for symbol in symbols:
            record = existing_map.get(symbol)
            if not record:
                stale.append(symbol)
                continue

            computed_at = record.get("computed_at")
            if not computed_at:
                stale.append(symbol)
                continue

            if isinstance(computed_at, str):
                computed_at = datetime.fromisoformat(computed_at)

            if computed_at < cutoff:
                stale.append(symbol)

        return stale
