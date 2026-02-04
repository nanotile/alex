"""
Backward-compatible wrapper — delegates to market_data.polygon_prices.

All Polygon logic now lives in backend/market_data/src/market_data/polygon_prices.py.
This file remains so existing imports in market.py continue to work.
"""

from market_data.polygon_prices import (
    is_market_open,
    get_all_share_prices_polygon_eod,
    get_share_price_polygon,
    get_share_price,
)

__all__ = [
    "is_market_open",
    "get_all_share_prices_polygon_eod",
    "get_share_price_polygon",
    "get_share_price",
]
