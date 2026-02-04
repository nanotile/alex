"""
Unified price fetcher — tries Polygon first, falls back to FMP quote.
"""

import logging
from typing import Optional

from .polygon_prices import get_share_price as polygon_get_price
from .fmp import FMPClient

logger = logging.getLogger(__name__)


def get_price(symbol: str, fmp_client: Optional[FMPClient] = None) -> float:
    """
    Get the current price for a symbol.

    Tries Polygon first (existing behavior), then falls back to FMP quote
    if Polygon returns 0 or fails. Returns 0.0 only if both sources fail.
    """
    # Try Polygon first (handles its own fallback to random internally)
    price = polygon_get_price(symbol)
    if price and price > 0:
        return price

    # Fall back to FMP quote
    if fmp_client is None:
        fmp_client = FMPClient()

    if fmp_client.api_key:
        try:
            quote = fmp_client.get_quote(symbol)
            if quote and quote.get("price"):
                fmp_price = float(quote["price"])
                if fmp_price > 0:
                    logger.info(f"Got price for {symbol} from FMP fallback: ${fmp_price:.2f}")
                    return fmp_price
        except Exception as e:
            logger.warning(f"FMP price fallback failed for {symbol}: {e}")

    return 0.0
