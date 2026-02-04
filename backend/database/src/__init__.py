"""
Database package for Alex Financial Planner
Provides database models, schemas, and Data API client
"""

from .client import DataAPIClient
from .models import Database
from .market_data_models import InstrumentFundamentals
from .schemas import (
    # Types
    RegionType,
    AssetClassType,
    SectorType,
    InstrumentType,
    JobType,
    JobStatus,
    AccountType,

    # Create schemas (for inputs)
    InstrumentCreate,
    UserCreate,
    AccountCreate,
    PositionCreate,
    JobCreate,
    JobUpdate,

    # Response schemas (for outputs)
    InstrumentResponse,
    FundamentalsResponse,
    PortfolioAnalysis,
    RebalanceRecommendation,
)

__all__ = [
    'Database',
    'DataAPIClient',
    'InstrumentFundamentals',
    'InstrumentCreate',
    'UserCreate',
    'AccountCreate',
    'PositionCreate',
    'JobCreate',
    'JobUpdate',
    'InstrumentResponse',
    'FundamentalsResponse',
    'PortfolioAnalysis',
    'RebalanceRecommendation',
    'RegionType',
    'AssetClassType',
    'SectorType',
    'InstrumentType',
    'JobType',
    'JobStatus',
    'AccountType',
]