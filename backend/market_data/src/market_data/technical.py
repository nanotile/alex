"""
Module: Technical Indicators via Polygon.io + pandas-ta
Version: 0.1.0
Development Iteration: v1

Project: Alex (Agentic Learning Equities eXplainer)
Developer: Kent Benson
Created: 2026-02-05

Enhancement: Initial implementation of technical indicator computation

Features:
- Fetches 200-day historical OHLCV from Polygon.io
- Computes RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(50), SMA(200), EMA(20)
- Returns structured dict per symbol with signal summary

UV ENVIRONMENT: Run with `uv run python technical.py`

INSTALLATION:
uv add pandas pandas-ta
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import pandas as pd
import pandas_ta as ta
from polygon import RESTClient
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

polygon_api_key = os.getenv("POLYGON_API_KEY")


def get_historical_bars(symbol: str, days: int = 200) -> Optional[pd.DataFrame]:
    """
    Fetch historical daily OHLCV bars from Polygon.io.

    Args:
        symbol: Ticker symbol (e.g. "SPY")
        days: Number of calendar days of history to fetch (default 200)

    Returns:
        DataFrame with columns: open, high, low, close, volume, timestamp
        or None if the fetch fails.
    """
    if not polygon_api_key:
        logger.warning("Technical: POLYGON_API_KEY not set — skipping historical bars")
        return None

    try:
        client = RESTClient(polygon_api_key)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        aggs = client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="day",
            from_=start_date.isoformat(),
            to=end_date.isoformat(),
            adjusted=True,
            sort="asc",
            limit=50000,
        )

        if not aggs:
            logger.warning(f"Technical: No historical data returned for {symbol}")
            return None

        rows = []
        for agg in aggs:
            rows.append({
                "open": agg.open,
                "high": agg.high,
                "low": agg.low,
                "close": agg.close,
                "volume": agg.volume,
                "timestamp": datetime.fromtimestamp(agg.timestamp / 1000),
            })

        df = pd.DataFrame(rows)
        df.set_index("timestamp", inplace=True)
        logger.info(f"Technical: Fetched {len(df)} bars for {symbol}")
        return df

    except Exception as e:
        logger.warning(f"Technical: Failed to fetch historical bars for {symbol}: {e}")
        return None


def compute_indicators(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Compute technical indicators from OHLCV DataFrame using pandas-ta.

    Args:
        df: DataFrame with open, high, low, close, volume columns

    Returns:
        Dict with computed indicator values, or None if insufficient data.
    """
    if df is None or len(df) < 50:
        logger.warning("Technical: Insufficient data for indicator computation (need >= 50 bars)")
        return None

    try:
        close = df["close"]
        current_price = float(close.iloc[-1])

        result = {
            "current_price": current_price,
        }

        # RSI(14)
        rsi = ta.rsi(close, length=14)
        if rsi is not None and len(rsi.dropna()) > 0:
            result["rsi_14"] = round(float(rsi.iloc[-1]), 2)

        # MACD(12, 26, 9)
        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        if macd_df is not None and len(macd_df.dropna()) > 0:
            last_row = macd_df.iloc[-1]
            result["macd"] = round(float(last_row.iloc[0]), 4)
            result["macd_signal"] = round(float(last_row.iloc[2]), 4)
            result["macd_histogram"] = round(float(last_row.iloc[1]), 4)

        # Bollinger Bands(20, 2)
        bbands = ta.bbands(close, length=20, std=2)
        if bbands is not None and len(bbands.dropna()) > 0:
            last_bb = bbands.iloc[-1]
            bb_lower = float(last_bb.iloc[0])
            bb_mid = float(last_bb.iloc[1])
            bb_upper = float(last_bb.iloc[2])
            bb_range = bb_upper - bb_lower
            bb_pctb = (current_price - bb_lower) / bb_range if bb_range > 0 else 0.5

            result["bb_upper"] = round(bb_upper, 2)
            result["bb_middle"] = round(bb_mid, 2)
            result["bb_lower"] = round(bb_lower, 2)
            result["bb_pctb"] = round(bb_pctb, 4)

        # SMA(50)
        sma50 = ta.sma(close, length=50)
        if sma50 is not None and len(sma50.dropna()) > 0:
            result["sma_50"] = round(float(sma50.iloc[-1]), 2)

        # SMA(200) — only if we have enough data
        if len(df) >= 200:
            sma200 = ta.sma(close, length=200)
            if sma200 is not None and len(sma200.dropna()) > 0:
                result["sma_200"] = round(float(sma200.iloc[-1]), 2)

        # EMA(20)
        ema20 = ta.ema(close, length=20)
        if ema20 is not None and len(ema20.dropna()) > 0:
            result["ema_20"] = round(float(ema20.iloc[-1]), 2)

        # Derived signals
        if "sma_50" in result:
            result["price_vs_sma50"] = "above" if current_price > result["sma_50"] else "below"
        if "sma_200" in result:
            result["price_vs_sma200"] = "above" if current_price > result["sma_200"] else "below"

        # Signal summary
        result["signal_summary"] = _generate_signal_summary(result)

        return result

    except Exception as e:
        logger.warning(f"Technical: Error computing indicators: {e}")
        return None


def _generate_signal_summary(indicators: Dict[str, Any]) -> str:
    """Generate a human-readable signal summary from computed indicators."""
    signals = []

    # RSI interpretation
    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi > 70:
            signals.append("RSI overbought")
        elif rsi < 30:
            signals.append("RSI oversold")
        else:
            signals.append("RSI neutral")

    # MACD interpretation
    macd_hist = indicators.get("macd_histogram")
    if macd_hist is not None:
        if macd_hist > 0:
            signals.append("MACD positive")
        else:
            signals.append("MACD negative")

    # SMA trend
    sma50_signal = indicators.get("price_vs_sma50")
    sma200_signal = indicators.get("price_vs_sma200")
    if sma50_signal and sma200_signal:
        if sma50_signal == "above" and sma200_signal == "above":
            signals.append("above both SMAs")
        elif sma50_signal == "below" and sma200_signal == "below":
            signals.append("below both SMAs")
        else:
            signals.append(f"SMA50 {sma50_signal}, SMA200 {sma200_signal}")

    # Bollinger Band position
    bb_pctb = indicators.get("bb_pctb")
    if bb_pctb is not None:
        if bb_pctb > 0.8:
            signals.append("near upper Bollinger Band")
        elif bb_pctb < 0.2:
            signals.append("near lower Bollinger Band")

    # Overall sentiment
    bullish = 0
    bearish = 0
    if rsi is not None:
        if rsi > 50:
            bullish += 1
        else:
            bearish += 1
    if macd_hist is not None:
        if macd_hist > 0:
            bullish += 1
        else:
            bearish += 1
    if sma50_signal == "above":
        bullish += 1
    elif sma50_signal == "below":
        bearish += 1

    if bullish > bearish:
        sentiment = "Moderately bullish"
    elif bearish > bullish:
        sentiment = "Moderately bearish"
    else:
        sentiment = "Mixed/neutral"

    detail = ", ".join(signals) if signals else "insufficient data"
    return f"{sentiment} — {detail}"


def get_technical_indicators(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch historical data and compute technical indicators for multiple symbols.

    Args:
        symbols: List of ticker symbols

    Returns:
        Dict of {symbol: indicators_dict} for each symbol that succeeded.
    """
    results = {}

    for symbol in symbols:
        try:
            df = get_historical_bars(symbol, days=300)  # 300 days for SMA(200) headroom
            if df is not None:
                indicators = compute_indicators(df)
                if indicators:
                    results[symbol] = indicators
                    logger.info(f"Technical: Computed indicators for {symbol}")
                else:
                    logger.warning(f"Technical: Could not compute indicators for {symbol}")
            else:
                logger.warning(f"Technical: No historical data for {symbol}")
        except Exception as e:
            logger.warning(f"Technical: Error processing {symbol}: {e}")

    logger.info(f"Technical: Computed indicators for {len(results)}/{len(symbols)} symbols")
    return results
