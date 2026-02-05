"""
Market data functions using polygon.io for fetching real-time prices,
FMP for fundamental data, FRED for macro-economic indicators,
and pandas-ta for technical indicators.
"""

import os
import logging
from typing import Set, Dict, List, Any
from prices import get_share_price
from market_data.fmp import FMPClient
from market_data.fred import FREDClient, FRED_SERIES
from market_data.technical import get_technical_indicators

logger = logging.getLogger()


def update_instrument_prices(job_id: str, db) -> bool:
    """
    Fetch current prices for all instruments in the user's portfolio using polygon.io.
    Updates the instruments table with current prices.

    Returns True if at least one price was successfully fetched.
    """
    try:
        logger.info(f"Market: Fetching current prices for job {job_id}")

        # Get the job to find the user
        job = db.jobs.find_by_id(job_id)
        if not job:
            logger.error(f"Market: Job {job_id} not found")
            return False

        user_id = job['clerk_user_id']

        # Get all unique symbols from user's positions
        accounts = db.accounts.find_by_user(user_id)
        symbols = set()

        for account in accounts:
            positions = db.positions.find_by_account(account['id'])
            for position in positions:
                symbols.add(position['symbol'])

        if not symbols:
            logger.info("Market: No symbols to update prices for")
            return False

        logger.info(f"Market: Fetching prices for {len(symbols)} symbols: {symbols}")

        # Update prices for each symbol
        updated_count = update_prices_for_symbols(symbols, db)

        logger.info("Market: Price update complete")
        return updated_count > 0

    except Exception as e:
        logger.error(f"Market: Error updating instrument prices: {e}")
        return False


def update_prices_for_symbols(symbols: Set[str], db) -> int:
    """
    Fetch and update prices for a set of symbols using polygon.io.

    Returns the number of symbols successfully updated.
    """
    if not symbols:
        logger.info("Market: No symbols to update")
        return 0

    symbols_list = list(symbols)
    price_map = {}

    # Fetch price for each symbol using polygon.io
    for symbol in symbols_list:
        try:
            price = get_share_price(symbol)
            if price > 0:
                price_map[symbol] = price
                logger.info(f"Market: Retrieved {symbol} price: ${price:.2f}")
            else:
                logger.warning(f"Market: No price available for {symbol}")
        except Exception as e:
            logger.warning(f"Market: Could not fetch price for {symbol}: {e}")

    logger.info(f"Market: Retrieved prices for {len(price_map)}/{len(symbols_list)} symbols")

    # Update database with fetched prices
    for symbol, price in price_map.items():
        try:
            instrument = db.instruments.find_by_symbol(symbol)
            if instrument:
                update_data = {'current_price': price}
                success = db.client.update(
                    'instruments',
                    update_data,
                    "symbol = :symbol",
                    {'symbol': symbol}
                )
                if success:
                    logger.info(f"Market: Updated {symbol} price to ${price:.2f}")
                else:
                    logger.warning(f"Market: Failed to update price for {symbol}")
            else:
                logger.warning(f"Market: Instrument {symbol} not found in database")
        except Exception as e:
            logger.error(f"Market: Error updating {symbol} in database: {e}")

    # Log symbols that didn't get prices
    missing = set(symbols_list) - set(price_map.keys())
    if missing:
        logger.warning(f"Market: No prices found for: {missing}")

    return len(price_map)


def get_all_portfolio_symbols(db) -> Set[str]:
    """
    Get all unique symbols across all users' portfolios.
    Useful for pre-fetching prices in batch operations.

    Args:
        db: Database instance

    Returns:
        Set of unique ticker symbols
    """
    symbols = set()

    try:
        # Get all positions (this might need pagination for large datasets)
        all_positions = db.db.execute(
            "SELECT DISTINCT symbol FROM positions"
        )

        for position in all_positions:
            if position['symbol']:
                symbols.add(position['symbol'])

    except Exception as e:
        logger.error(f"Market: Error fetching all symbols: {e}")

    return symbols


def update_instrument_fundamentals(job_id: str, db) -> tuple[Dict[str, Any], bool]:
    """
    Fetch FMP fundamentals for portfolio symbols and store in Aurora.
    Only re-fetches if data is older than 24 hours.

    Returns (dict of {symbol: fundamentals_dict}, success_bool).
    """
    fundamentals_map = {}

    try:
        fmp_api_key = os.getenv("FMP_API_KEY", "")
        if not fmp_api_key:
            logger.info("Market: FMP_API_KEY not set — skipping fundamentals fetch")
            return fundamentals_map, False

        fmp = FMPClient(api_key=fmp_api_key)

        # Get the job to find the user's symbols
        job = db.jobs.find_by_id(job_id)
        if not job:
            logger.error(f"Market: Job {job_id} not found for fundamentals update")
            return fundamentals_map

        user_id = job['clerk_user_id']
        accounts = db.accounts.find_by_user(user_id)
        symbols = set()

        for account in accounts:
            positions = db.positions.find_by_account(account['id'])
            for position in positions:
                symbols.add(position['symbol'])

        if not symbols:
            logger.info("Market: No symbols for fundamentals update")
            return fundamentals_map, False

        symbols_list = list(symbols)
        logger.info(f"Market: Checking fundamentals for {len(symbols_list)} symbols")

        # Only fetch stale data (older than 24 hours)
        stale_symbols = db.fundamentals.get_stale_symbols(symbols_list, max_age_hours=24)

        if stale_symbols:
            logger.info(f"Market: Fetching FMP fundamentals for {len(stale_symbols)} stale symbols: {stale_symbols}")

            for symbol in stale_symbols:
                try:
                    data = fmp.get_fundamentals(symbol)
                    if data:
                        db.fundamentals.upsert_fundamentals(data)
                        logger.info(f"Market: Updated fundamentals for {symbol}")
                except Exception as e:
                    logger.warning(f"Market: FMP fetch failed for {symbol}: {e}")
        else:
            logger.info("Market: All fundamentals are fresh (< 24 hours)")

        # Load all fundamentals (fresh + cached) for downstream agents
        all_fundamentals = db.fundamentals.find_by_symbols(symbols_list)
        for record in all_fundamentals:
            fundamentals_map[record['symbol']] = record

        logger.info(f"Market: Fundamentals available for {len(fundamentals_map)}/{len(symbols_list)} symbols")

    except Exception as e:
        logger.error(f"Market: Error updating fundamentals: {e}")
        # Non-critical — continue without fundamentals

    return fundamentals_map, bool(fundamentals_map)


def update_economic_indicators(db) -> tuple[Dict[str, Any], bool]:
    """
    Fetch FRED macro-economic data and cache in Aurora.
    No job_id needed — economic data is shared across all portfolios.
    Only re-fetches if data is older than 6 hours.

    Returns (dict of {series_id: indicator_dict}, success_bool).
    """
    indicators_map = {}

    try:
        fred_api_key = os.getenv("FRED_API_KEY", "")
        if not fred_api_key:
            logger.info("Market: FRED_API_KEY not set — skipping economic indicators")
            return indicators_map, False

        fred = FREDClient(api_key=fred_api_key)

        series_ids = list(FRED_SERIES.keys())
        stale_series = db.economic_indicators.get_stale_series(series_ids, max_age_hours=6)

        if stale_series:
            logger.info(f"Market: Fetching FRED data for {len(stale_series)} stale series: {stale_series}")

            for series_id in stale_series:
                try:
                    obs = fred.get_latest_observation(series_id)
                    if obs:
                        meta = FRED_SERIES[series_id]
                        data = {
                            "series_id": series_id,
                            "series_name": meta["name"],
                            "latest_value": obs["value"],
                            "latest_date": obs["date"],
                            "previous_value": obs.get("previous_value"),
                            "previous_date": obs.get("previous_date"),
                            "units": meta["units"],
                            "frequency": meta["frequency"],
                        }
                        db.economic_indicators.upsert_indicator(data)
                        logger.info(f"Market: Updated {series_id} ({meta['name']})")
                except Exception as e:
                    logger.warning(f"Market: FRED fetch failed for {series_id}: {e}")
        else:
            logger.info("Market: All economic indicators are fresh (< 6 hours)")

        # Load all indicators (fresh + cached) for downstream agents
        all_indicators = db.economic_indicators.find_all()
        for record in all_indicators:
            indicators_map[record["series_id"]] = record

        logger.info(f"Market: Economic indicators available for {len(indicators_map)} series")

    except Exception as e:
        logger.error(f"Market: Error updating economic indicators: {e}")
        # Non-critical — continue without economic data

    return indicators_map, bool(indicators_map)


def compute_technical_indicators(job_id: str, db) -> tuple[Dict[str, Any], bool]:
    """
    Compute technical indicators (RSI, MACD, Bollinger Bands, SMA/EMA) for portfolio symbols
    using Polygon.io historical data and pandas-ta.
    Caches results in Aurora with a 1-hour staleness window.

    Returns (dict of {symbol: indicators_dict}, success_bool).
    """
    technical_map = {}

    try:
        polygon_api_key = os.getenv("POLYGON_API_KEY", "")
        if not polygon_api_key:
            logger.info("Market: POLYGON_API_KEY not set — skipping technical indicators")
            return technical_map, False

        # Get the job to find the user's symbols
        job = db.jobs.find_by_id(job_id)
        if not job:
            logger.error(f"Market: Job {job_id} not found for technical indicators")
            return technical_map

        user_id = job['clerk_user_id']
        accounts = db.accounts.find_by_user(user_id)
        symbols = set()

        for account in accounts:
            positions = db.positions.find_by_account(account['id'])
            for position in positions:
                symbols.add(position['symbol'])

        if not symbols:
            logger.info("Market: No symbols for technical indicators")
            return technical_map, False

        # Always include benchmark symbols for comparison
        BENCHMARK_SYMBOLS = {"SPY", "AGG"}
        symbols = symbols | BENCHMARK_SYMBOLS

        symbols_list = list(symbols)
        logger.info(f"Market: Checking technical indicators for {len(symbols_list)} symbols (includes benchmarks SPY, AGG)")

        # Only compute for stale symbols (older than 1 hour)
        stale_symbols = db.technical_indicators.get_stale_symbols(symbols_list, max_age_hours=1)

        if stale_symbols:
            logger.info(f"Market: Computing technical indicators for {len(stale_symbols)} stale symbols: {stale_symbols}")

            computed = get_technical_indicators(stale_symbols)

            for symbol, indicators in computed.items():
                try:
                    db.technical_indicators.upsert_indicators(symbol, indicators)
                    logger.info(f"Market: Stored technical indicators for {symbol}")
                except Exception as e:
                    logger.warning(f"Market: Failed to store indicators for {symbol}: {e}")
        else:
            logger.info("Market: All technical indicators are fresh (< 1 hour)")

        # Load all indicators (fresh + cached) for downstream agents
        all_records = db.technical_indicators.find_by_symbols(symbols_list)
        for record in all_records:
            indicators = record.get("indicators")
            if isinstance(indicators, str):
                import json
                indicators = json.loads(indicators)
            technical_map[record["symbol"]] = indicators

        logger.info(f"Market: Technical indicators available for {len(technical_map)}/{len(symbols_list)} symbols")

    except Exception as e:
        logger.error(f"Market: Error computing technical indicators: {e}")
        # Non-critical — continue without technical data

    return technical_map, bool(technical_map)