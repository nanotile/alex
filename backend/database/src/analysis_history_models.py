"""
Database model for analysis history snapshots (portfolio metrics over time).
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .client import DataAPIClient

logger = logging.getLogger(__name__)


class AnalysisHistory:
    """Analysis history table operations — stores portfolio metric snapshots over time."""

    table_name = "analysis_history"

    def __init__(self, db: DataAPIClient):
        self.db = db

    def save_snapshot(
        self,
        clerk_user_id: str,
        total_value: float,
        num_positions: int,
        asset_allocation: Dict[str, Any],
        top_holdings: List[Dict[str, Any]],
        technical_summary: Dict[str, Any] = None,
    ) -> Optional[str]:
        """Save a portfolio analysis snapshot.

        Returns the snapshot id on success, None on failure.
        """
        sql = f"""
            INSERT INTO {self.table_name}
                (clerk_user_id, snapshot_date, total_value, num_positions,
                 asset_allocation, top_holdings, technical_summary)
            VALUES
                (:clerk_user_id, NOW(), :total_value::numeric,
                 :num_positions::integer, :asset_allocation::jsonb,
                 :top_holdings::jsonb, :technical_summary::jsonb)
            RETURNING id
        """

        params = [
            {"name": "clerk_user_id", "value": {"stringValue": clerk_user_id}},
            {"name": "total_value", "value": {"stringValue": str(total_value)}},
            {"name": "num_positions", "value": {"longValue": num_positions}},
            {"name": "asset_allocation", "value": {"stringValue": json.dumps(asset_allocation)}},
            {"name": "top_holdings", "value": {"stringValue": json.dumps(top_holdings)}},
            {"name": "technical_summary", "value": {"stringValue": json.dumps(technical_summary or {})}},
        ]

        try:
            response = self.db.execute(sql, params)
            if response.get("records"):
                return response["records"][0][0].get("stringValue")
            return None
        except Exception as e:
            logger.error(f"Failed to save analysis snapshot: {e}")
            return None

    def find_recent(self, clerk_user_id: str, limit: int = 5) -> List[Dict]:
        """Find the most recent snapshots for a user, ordered newest first."""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE clerk_user_id = :clerk_user_id
            ORDER BY snapshot_date DESC
            LIMIT :limit
        """
        params = [
            {"name": "clerk_user_id", "value": {"stringValue": clerk_user_id}},
            {"name": "limit", "value": {"longValue": limit}},
        ]
        return self.db.query(sql, params)
