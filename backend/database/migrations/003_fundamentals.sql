-- Add instrument_fundamentals table for FMP data caching
-- Separate from instruments table to avoid breaking existing queries

CREATE TABLE IF NOT EXISTS instrument_fundamentals (
    symbol VARCHAR(20) PRIMARY KEY REFERENCES instruments(symbol),
    -- Company profile
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    description TEXT,
    -- Key metrics (TTM)
    pe_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    dividend_yield DECIMAL(8,4),
    roe DECIMAL(8,4),
    debt_to_equity DECIMAL(10,2),
    revenue_per_share DECIMAL(10,2),
    eps DECIMAL(10,2),
    -- Pricing extras
    price_change_pct DECIMAL(8,4),
    fifty_two_week_high DECIMAL(12,4),
    fifty_two_week_low DECIMAL(12,4),
    avg_volume BIGINT,
    beta DECIMAL(6,3),
    -- Freshness
    fetched_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Auto-update timestamp trigger
CREATE TRIGGER update_instrument_fundamentals_updated_at
    BEFORE UPDATE ON instrument_fundamentals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
