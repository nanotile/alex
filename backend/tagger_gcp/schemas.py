"""
Pydantic schemas for Tagger agent
"""

from typing import Dict, Literal
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

# Define allowed values as Literals
RegionType = Literal[
    "north_america",
    "europe",
    "asia",
    "latin_america",
    "africa",
    "middle_east",
    "oceania",
    "global",
    "international",
]

AssetClassType = Literal[
    "equity", "fixed_income", "real_estate", "commodities", "cash", "alternatives"
]

SectorType = Literal[
    "technology",
    "healthcare",
    "financials",
    "consumer_discretionary",
    "consumer_staples",
    "industrials",
    "energy",
    "materials",
    "utilities",
    "real_estate",
    "communication",
    "treasury",
    "corporate",
    "mortgage",
    "government_related",
    "commodities",
    "diversified",
    "other",
]

InstrumentType = Literal["etf", "mutual_fund", "stock", "bond", "bond_fund", "commodity", "reit"]


class InstrumentCreate(BaseModel):
    """Schema for creating a new instrument"""

    symbol: str = Field(
        description="The ticker symbol of the instrument (e.g., 'SPY', 'BND')",
        min_length=1,
        max_length=20,
    )
    name: str = Field(description="Full name of the instrument", min_length=1, max_length=255)
    instrument_type: InstrumentType = Field(description="The type of financial instrument")
    current_price: Decimal = Field(
        description="Current price of the instrument for portfolio calculations",
        ge=0,
        le=999999,
    )
    allocation_regions: Dict[RegionType, float] = Field(
        description="Geographic allocation percentages. Must sum to 100.",
        example={"north_america": 100},
    )
    allocation_sectors: Dict[SectorType, float] = Field(
        description="Sector allocation percentages. Must sum to 100.",
        example={"technology": 40, "healthcare": 30, "financials": 30},
    )
    allocation_asset_class: Dict[AssetClassType, float] = Field(
        description="Asset class allocation percentages. Must sum to 100.", example={"equity": 100}
    )

    @field_validator("allocation_regions", "allocation_sectors", "allocation_asset_class")
    def validate_allocations(cls, v):
        """Ensure all allocations sum to 100"""
        if not v:
            raise ValueError("Allocation cannot be empty")
        total = sum(v.values())
        if abs(total - 100) > 3:
            raise ValueError(f"Allocations must sum to 100, got {total}")
        return v
