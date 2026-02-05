-- Migration 005: Technical indicators cache table
-- Stores pandas-ta computed indicators per symbol with JSONB storage

CREATE TABLE IF NOT EXISTS technical_indicators (
    symbol VARCHAR(20) PRIMARY KEY,
    indicators JSONB NOT NULL,
    computed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TRIGGER update_technical_indicators_updated_at BEFORE UPDATE ON technical_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
