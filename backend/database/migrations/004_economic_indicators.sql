-- Migration 004: Economic indicators table (FRED data cache)
-- Stores macro-economic data: interest rates, inflation, unemployment, GDP, VIX
-- Keyed by series_id (not symbol) since this is economy-wide data shared across all portfolios

CREATE TABLE IF NOT EXISTS economic_indicators (
    series_id VARCHAR(50) PRIMARY KEY,
    series_name VARCHAR(255),
    latest_value DECIMAL(20,4),
    latest_date DATE,
    previous_value DECIMAL(20,4),
    previous_date DATE,
    units VARCHAR(100),
    frequency VARCHAR(20),
    fetched_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TRIGGER update_economic_indicators_updated_at BEFORE UPDATE ON economic_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
