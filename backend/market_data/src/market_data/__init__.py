"""
Market data service for Alex Financial Planner.
Wraps external data APIs (Polygon, FMP, FRED) and SageMaker sentiment into a unified interface.
"""

from .fmp import FMPClient
from .fred import FREDClient
from .polygon_prices import (
    get_share_price,
    get_share_price_polygon,
    is_market_open,
)
from .prices import get_price
from .sentiment import SentimentClient

__all__ = [
    "FMPClient",
    "FREDClient",
    "SentimentClient",
    "get_share_price",
    "get_share_price_polygon",
    "get_price",
    "is_market_open",
]
