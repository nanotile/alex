"""
Tagger Agent FastAPI Server for Cloud Run
Classifies financial instruments and updates the GCP database.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import GCP database library
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database_gcp'))
from src.client import CloudSQLClient

from agent import tag_instruments, classification_to_db_format
from schemas import InstrumentCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Tagger Agent", description="Financial Instrument Classification Service")

# Initialize database client (will use environment variables)
db_client = None


def get_db_client():
    """Get or create database client"""
    global db_client
    if db_client is None:
        db_client = CloudSQLClient()
    return db_client


class InstrumentRequest(BaseModel):
    """Request model for instrument classification"""
    symbol: str
    name: str
    instrument_type: str = "etf"


class TagRequest(BaseModel):
    """Request model for tagging multiple instruments"""
    instruments: List[InstrumentRequest]


class TagResponse(BaseModel):
    """Response model for tagging results"""
    tagged: int
    updated: List[str]
    errors: List[Dict[str, str]]
    classifications: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Tagger Agent",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        # Test database connection
        client = get_db_client()
        result = client.query("SELECT 1 as health_check")

        return {
            "status": "healthy",
            "database": "connected",
            "checks": {
                "db_query": "passed"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/tag", response_model=TagResponse)
async def tag_instruments_endpoint(request: TagRequest):
    """
    Classify financial instruments and update database.

    Args:
        request: List of instruments to classify

    Returns:
        Classification results and database update status
    """
    try:
        logger.info(f"Received request to tag {len(request.instruments)} instruments")

        # Convert request to dict format expected by agent
        instruments_dict = [
            {
                "symbol": inst.symbol,
                "name": inst.name,
                "instrument_type": inst.instrument_type
            }
            for inst in request.instruments
        ]

        # Run classification
        classifications = await tag_instruments(instruments_dict)
        logger.info(f"Successfully classified {len(classifications)} instruments")

        # Update database with classifications
        client = get_db_client()
        updated = []
        errors = []

        for classification in classifications:
            try:
                # Convert to database format
                db_instrument = classification_to_db_format(classification)

                # Check if instrument exists
                existing = client.query(
                    "SELECT symbol FROM instruments WHERE symbol = :symbol",
                    {"symbol": classification.symbol}
                )

                if existing:
                    # Update existing instrument
                    client.execute("""
                        UPDATE instruments SET
                            name = :name,
                            instrument_type = :instrument_type,
                            current_price = :current_price,
                            allocation_regions = CAST(:allocation_regions AS jsonb),
                            allocation_sectors = CAST(:allocation_sectors AS jsonb),
                            allocation_asset_class = CAST(:allocation_asset_class AS jsonb),
                            updated_at = NOW()
                        WHERE symbol = :symbol
                    """, {
                        "symbol": db_instrument.symbol,
                        "name": db_instrument.name,
                        "instrument_type": db_instrument.instrument_type,
                        "current_price": float(db_instrument.current_price),
                        "allocation_regions": json.dumps(db_instrument.allocation_regions),
                        "allocation_sectors": json.dumps(db_instrument.allocation_sectors),
                        "allocation_asset_class": json.dumps(db_instrument.allocation_asset_class),
                    })
                    logger.info(f"Updated {classification.symbol} in database")
                else:
                    # Insert new instrument
                    client.execute("""
                        INSERT INTO instruments (
                            symbol, name, instrument_type, current_price,
                            allocation_regions, allocation_sectors, allocation_asset_class
                        )
                        VALUES (
                            :symbol, :name, :instrument_type, :current_price,
                            CAST(:allocation_regions AS jsonb),
                            CAST(:allocation_sectors AS jsonb),
                            CAST(:allocation_asset_class AS jsonb)
                        )
                    """, {
                        "symbol": db_instrument.symbol,
                        "name": db_instrument.name,
                        "instrument_type": db_instrument.instrument_type,
                        "current_price": float(db_instrument.current_price),
                        "allocation_regions": json.dumps(db_instrument.allocation_regions),
                        "allocation_sectors": json.dumps(db_instrument.allocation_sectors),
                        "allocation_asset_class": json.dumps(db_instrument.allocation_asset_class),
                    })
                    logger.info(f"Created {classification.symbol} in database")

                updated.append(classification.symbol)

            except Exception as e:
                logger.error(f"Error updating {classification.symbol}: {e}")
                errors.append({
                    'symbol': classification.symbol,
                    'error': str(e)
                })

        # Prepare response (convert Pydantic models to dicts)
        return TagResponse(
            tagged=len(classifications),
            updated=updated,
            errors=errors,
            classifications=[
                {
                    'symbol': c.symbol,
                    'name': c.name,
                    'type': c.instrument_type,
                    'current_price': c.current_price,
                    'asset_class': c.allocation_asset_class.model_dump(),
                    'regions': c.allocation_regions.model_dump(),
                    'sectors': c.allocation_sectors.model_dump()
                }
                for c in classifications
            ]
        )

    except Exception as e:
        logger.error(f"Tagging failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Tagger Agent service...")
    logger.info(f"Vertex AI Project: {os.getenv('VERTEX_PROJECT', 'not set')}")
    logger.info(f"Vertex AI Location: {os.getenv('VERTEX_LOCATION', 'not set')}")
    logger.info(f"Model ID: {os.getenv('VERTEX_MODEL_ID', 'gemini-2.0-flash-exp')}")
    logger.info(f"Cloud SQL Instance: {os.getenv('CLOUD_SQL_INSTANCE', 'not set')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_client
    if db_client:
        db_client.close()
    logger.info("Tagger Agent service stopped")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
