"""
Database model for economic indicators (FRED data cache).
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .client import DataAPIClient

logger = logging.getLogger(__name__)


class EconomicIndicators:
    """Economic indicators table operations (FRED data cache)."""

    table_name = "economic_indicators"

    def __init__(self, db: DataAPIClient):
        self.db = db

    def find_by_series_id(self, series_id: str) -> Optional[Dict]:
        """Find an indicator by FRED series ID."""
        sql = f"SELECT * FROM {self.table_name} WHERE series_id = :series_id"
        params = [{"name": "series_id", "value": {"stringValue": series_id}}]
        return self.db.query_one(sql, params)

    def find_all(self) -> List[Dict]:
        """Find all cached economic indicators."""
        sql = f"SELECT * FROM {self.table_name} ORDER BY series_id"
        return self.db.query(sql, [])

    def upsert_indicator(self, data: Dict[str, Any]) -> bool:
        """
        Insert or update an economic indicator.
        Uses PostgreSQL ON CONFLICT ... DO UPDATE for upsert.
        """
        series_id = data.get("series_id")
        if not series_id:
            return False

        columns = []
        param_refs = []
        update_parts = []
        params = []

        field_types = {
            "series_id": "stringValue",
            "series_name": "stringValue",
            "latest_value": "stringValue",    # Decimal via string
            "latest_date": "stringValue",     # Date via string
            "previous_value": "stringValue",  # Decimal via string
            "previous_date": "stringValue",   # Date via string
            "units": "stringValue",
            "frequency": "stringValue",
        }

        decimal_columns = {"latest_value", "previous_value"}
        date_columns = {"latest_date", "previous_date"}

        for col, value_type in field_types.items():
            value = data.get(col)
            if value is None:
                continue

            columns.append(col)

            if col in decimal_columns:
                param_refs.append(f":{col}::numeric")
                params.append({"name": col, "value": {"stringValue": str(value)}})
            elif col in date_columns:
                param_refs.append(f":{col}::date")
                params.append({"name": col, "value": {"stringValue": str(value)}})
            else:
                param_refs.append(f":{col}")
                params.append({"name": col, "value": {"stringValue": str(value)}})

            if col != "series_id":
                update_parts.append(f"{col} = EXCLUDED.{col}")

        update_parts.append("fetched_at = NOW()")
        update_parts.append("updated_at = NOW()")

        sql = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(param_refs)})
            ON CONFLICT (series_id) DO UPDATE SET
                {', '.join(update_parts)}
        """

        try:
            self.db.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert economic indicator {series_id}: {e}")
            return False

    def is_stale(self, series_id: str, max_age_hours: int = 6) -> bool:
        """
        Check if indicator data is stale (older than max_age_hours).
        Returns True if data doesn't exist or is older than the threshold.
        """
        record = self.find_by_series_id(series_id)
        if not record:
            return True

        fetched_at = record.get("fetched_at")
        if not fetched_at:
            return True

        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)

        age = datetime.utcnow() - fetched_at
        return age > timedelta(hours=max_age_hours)

    def get_stale_series(self, series_ids: List[str], max_age_hours: int = 6) -> List[str]:
        """
        From a list of series IDs, return those that need a fresh FRED fetch.
        """
        if not series_ids:
            return []

        # Fetch all existing indicators in one query
        placeholders = []
        params = []
        for i, sid in enumerate(series_ids):
            param_name = f"sid_{i}"
            placeholders.append(f":{param_name}")
            params.append({"name": param_name, "value": {"stringValue": sid}})

        sql = f"SELECT * FROM {self.table_name} WHERE series_id IN ({', '.join(placeholders)})"
        existing = self.db.query(sql, params)
        existing_map = {r["series_id"]: r for r in existing}

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale = []

        for sid in series_ids:
            record = existing_map.get(sid)
            if not record:
                stale.append(sid)
                continue

            fetched_at = record.get("fetched_at")
            if not fetched_at:
                stale.append(sid)
                continue

            if isinstance(fetched_at, str):
                fetched_at = datetime.fromisoformat(fetched_at)

            if fetched_at < cutoff:
                stale.append(sid)

        return stale
