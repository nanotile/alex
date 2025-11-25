"""
Database models for GCP
Simplified for demo purposes
"""

from typing import Dict, Optional
from decimal import Decimal


class Instrument:
    """Instrument model"""

    def __init__(
        self,
        symbol: str,
        name: str,
        instrument_type: str,
        current_price: Decimal,
        allocation_regions: Dict = None,
        allocation_sectors: Dict = None,
        allocation_asset_class: Dict = None,
    ):
        self.symbol = symbol
        self.name = name
        self.instrument_type = instrument_type
        self.current_price = current_price
        self.allocation_regions = allocation_regions or {}
        self.allocation_sectors = allocation_sectors or {}
        self.allocation_asset_class = allocation_asset_class or {}

    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        return cls(
            symbol=data['symbol'],
            name=data['name'],
            instrument_type=data['instrument_type'],
            current_price=Decimal(str(data['current_price'])),
            allocation_regions=data.get('allocation_regions', {}),
            allocation_sectors=data.get('allocation_sectors', {}),
            allocation_asset_class=data.get('allocation_asset_class', {}),
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'instrument_type': self.instrument_type,
            'current_price': float(self.current_price),
            'allocation_regions': self.allocation_regions,
            'allocation_sectors': self.allocation_sectors,
            'allocation_asset_class': self.allocation_asset_class,
        }
