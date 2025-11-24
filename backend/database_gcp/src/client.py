"""
Cloud SQL Client for GCP
Simplified connector for Cloud Run services
"""

import os
from typing import List, Dict, Any, Optional
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class CloudSQLClient:
    """Simple Cloud SQL client wrapper"""

    def __init__(
        self,
        instance_connection_name: str = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        """
        Initialize Cloud SQL client

        Args:
            instance_connection_name: Format "project:region:instance"
            database: Database name
            user: Database user
            password: Database password
        """
        self.instance_connection_name = instance_connection_name or os.environ.get(
            "CLOUD_SQL_INSTANCE"
        )
        self.database = database or os.environ.get("CLOUD_SQL_DATABASE", "alex")
        self.user = user or os.environ.get("CLOUD_SQL_USER")
        self.password = password or os.environ.get("CLOUD_SQL_PASSWORD")

        if not all([self.instance_connection_name, self.user, self.password]):
            raise ValueError(
                "Missing required Cloud SQL configuration. "
                "Set CLOUD_SQL_INSTANCE, CLOUD_SQL_USER, and CLOUD_SQL_PASSWORD."
            )

        self.connector = Connector()
        self.engine = None

    def get_engine(self):
        """Get or create SQLAlchemy engine"""
        if self.engine is None:
            def getconn():
                return self.connector.connect(
                    self.instance_connection_name,
                    "pg8000",
                    user=self.user,
                    password=self.password,
                    db=self.database
                )

            self.engine = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )

        return self.engine

    def query(self, sql: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute SELECT query and return results as list of dicts

        Args:
            sql: SELECT statement
            parameters: Optional parameters

        Returns:
            List of dictionaries with column names as keys
        """
        engine = self.get_engine()

        with engine.connect() as conn:
            if parameters:
                result = conn.execute(text(sql), parameters)
            else:
                result = conn.execute(text(sql))

            # Convert to list of dicts
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]

    def execute(self, sql: str, parameters: Dict = None) -> Any:
        """
        Execute INSERT/UPDATE/DELETE statement

        Args:
            sql: SQL statement
            parameters: Optional parameters

        Returns:
            Result of execution
        """
        engine = self.get_engine()

        with engine.begin() as conn:
            if parameters:
                result = conn.execute(text(sql), parameters)
            else:
                result = conn.execute(text(sql))

            return result

    def close(self):
        """Close connections"""
        if self.engine:
            self.engine.dispose()
        self.connector.close()
