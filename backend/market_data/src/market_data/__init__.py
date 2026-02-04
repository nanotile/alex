"""
Market data service for Alex Financial Planner.
Wraps external data APIs (Polygon, FMP) into a unified interface.
"""

from .fmp import FMPClient
from .polygon_prices import (
    get_share_price,
    get_share_price_polygon,
    is_market_open,
)
from .prices import get_price

__all__ = [
    "FMPClient",
    "get_share_price",
    "get_share_price_polygon",
    "get_price",
    "is_market_open",
]
