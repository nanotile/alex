"""
Database model for instrument fundamentals (FMP data cache).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .client import DataAPIClient


class InstrumentFundamentals:
    """Instrument fundamentals table operations (FMP data cache)."""

    table_name = "instrument_fundamentals"

    def __init__(self, db: DataAPIClient):
        self.db = db

    def find_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Find fundamentals by symbol."""
        sql = f"SELECT * FROM {self.table_name} WHERE symbol = :symbol"
        params = [{"name": "symbol", "value": {"stringValue": symbol}}]
        return self.db.query_one(sql, params)

    def find_by_symbols(self, symbols: List[str]) -> List[Dict]:
        """Find fundamentals for multiple symbols."""
        if not symbols:
            return []

        # Build IN clause with positional params
        placeholders = []
        params = []
        for i, symbol in enumerate(symbols):
            param_name = f"sym_{i}"
            placeholders.append(f":{param_name}")
            params.append({"name": param_name, "value": {"stringValue": symbol}})

        sql = f"SELECT * FROM {self.table_name} WHERE symbol IN ({', '.join(placeholders)})"
        return self.db.query(sql, params)

    def upsert_fundamentals(self, data: Dict[str, Any]) -> bool:
        """
        Insert or update fundamentals for a symbol.
        Uses PostgreSQL ON CONFLICT ... DO UPDATE for upsert.
        """
        symbol = data.get("symbol")
        if not symbol:
            return False

        # Build column lists dynamically from the data
        columns = []
        param_refs = []
        update_parts = []
        params = []

        field_types = {
            "symbol": "stringValue",
            "company_name": "stringValue",
            "sector": "stringValue",
            "industry": "stringValue",
            "market_cap": "longValue",
            "description": "stringValue",
            "pe_ratio": "stringValue",      # Decimal via string
            "pb_ratio": "stringValue",
            "dividend_yield": "stringValue",
            "roe": "stringValue",
            "debt_to_equity": "stringValue",
            "revenue_per_share": "stringValue",
            "eps": "stringValue",
            "price_change_pct": "stringValue",
            "fifty_two_week_high": "stringValue",
            "fifty_two_week_low": "stringValue",
            "avg_volume": "longValue",
            "beta": "stringValue",
        }

        # Decimal columns need ::numeric cast
        decimal_columns = {
            "pe_ratio", "pb_ratio", "dividend_yield", "roe",
            "debt_to_equity", "revenue_per_share", "eps",
            "price_change_pct", "fifty_two_week_high", "fifty_two_week_low",
            "beta",
        }

        for col, value_type in field_types.items():
            value = data.get(col)
            if value is None:
                continue

            columns.append(col)

            # Convert numeric values to strings for Decimal columns
            if col in decimal_columns:
                cast = f":{col}::numeric"
                param_refs.append(cast)
                params.append({"name": col, "value": {"stringValue": str(value)}})
            elif value_type == "longValue":
                param_refs.append(f":{col}")
                params.append({"name": col, "value": {"longValue": int(value)}})
            else:
                param_refs.append(f":{col}")
                params.append({"name": col, "value": {"stringValue": str(value)}})

            if col != "symbol":
                if col in decimal_columns:
                    update_parts.append(f"{col} = EXCLUDED.{col}")
                else:
                    update_parts.append(f"{col} = EXCLUDED.{col}")

        # Always update fetched_at
        update_parts.append("fetched_at = NOW()")
        update_parts.append("updated_at = NOW()")

        sql = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(param_refs)})
            ON CONFLICT (symbol) DO UPDATE SET
                {', '.join(update_parts)}
        """

        try:
            self.db.execute(sql, params)
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Failed to upsert fundamentals for {symbol}: {e}"
            )
            return False

    def is_stale(self, symbol: str, max_age_hours: int = 24) -> bool:
        """
        Check if fundamentals data is stale (older than max_age_hours).
        Returns True if data doesn't exist or is older than the threshold.
        """
        record = self.find_by_symbol(symbol)
        if not record:
            return True

        fetched_at = record.get("fetched_at")
        if not fetched_at:
            return True

        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)

        age = datetime.utcnow() - fetched_at
        return age > timedelta(hours=max_age_hours)

    def get_stale_symbols(self, symbols: List[str], max_age_hours: int = 24) -> List[str]:
        """
        From a list of symbols, return those that need a fresh FMP fetch.
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

            fetched_at = record.get("fetched_at")
            if not fetched_at:
                stale.append(symbol)
                continue

            if isinstance(fetched_at, str):
                fetched_at = datetime.fromisoformat(fetched_at)

            if fetched_at < cutoff:
                stale.append(symbol)

        return stale
