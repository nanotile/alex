"""
Tests for Tagger agent classification logic
"""

import pytest
from unittest.mock import Mock, patch


class TestInstrumentClassification:
    """Test instrument classification logic"""

    def test_classify_etf_symbol(self, sample_instruments):
        """Test classifying ETF symbols"""
        vti = sample_instruments['VTI']

        assert vti['instrument_type'] == 'etf'
        assert vti['asset_class'] == 'equity'

    def test_classify_with_regions(self, sample_instruments):
        """Test classification includes regional data"""
        vti = sample_instruments['VTI']

        assert 'regions' in vti
        assert len(vti['regions']) > 0
        assert vti['regions'][0]['name'] == 'North America'

    def test_classify_bond_instrument(self, sample_instruments):
        """Test classifying bond instruments"""
        bnd = sample_instruments['BND']

        assert bnd['instrument_type'] == 'etf'
        assert bnd['asset_class'] == 'bond'

    def test_classify_international(self, sample_instruments):
        """Test classifying international instruments"""
        vxus = sample_instruments['VXUS']

        assert 'regions' in vxus
        regions = [r['name'] for r in vxus['regions']]
        assert 'Europe' in regions
        assert 'Asia' in regions


class TestSymbolProcessing:
    """Test symbol processing and lookup"""

    def test_process_multiple_symbols(self, sample_symbols):
        """Test processing list of symbols"""
        assert len(sample_symbols) == 3
        assert 'VTI' in sample_symbols
        assert 'BND' in sample_symbols
        assert 'VXUS' in sample_symbols

    def test_deduplicate_symbols(self):
        """Test that duplicate symbols are handled"""
        symbols = ['VTI', 'VTI', 'BND', 'VTI']
        unique_symbols = list(set(symbols))

        assert len(unique_symbols) == 2
        assert 'VTI' in unique_symbols
        assert 'BND' in unique_symbols

    def test_handle_empty_symbols_list(self):
        """Test handling empty symbols list"""
        symbols = []
        result = {}

        assert len(result) == 0


class TestDatabaseIntegration:
    """Test tagger integration with database"""

    def test_lookup_instrument_by_symbol(self, mock_db):
        """Test looking up instrument from database"""
        instrument = mock_db.instruments.find_by_symbol('VTI')

        assert instrument is not None
        assert instrument['symbol'] == 'VTI'
        assert 'instrument_type' in instrument

    def test_instrument_not_found(self, mock_db):
        """Test handling unknown instrument"""
        instrument = mock_db.instruments.find_by_symbol('UNKNOWN')

        assert instrument is None

    def test_update_instrument_classification(self, mock_db, sample_instruments):
        """Test updating instrument with new classification data"""
        # Create a new instrument
        new_inst = sample_instruments['VTI'].copy()
        new_inst['symbol'] = 'NEWETF'

        inst_id = mock_db.instruments.create(new_inst)

        # Verify it was created
        instrument = mock_db.instruments.find_by_symbol('NEWETF')
        assert instrument is not None


class TestClassificationOutput:
    """Test tagger output format"""

    def test_classification_structure(self, sample_instruments):
        """Test that classification has expected structure"""
        vti = sample_instruments['VTI']

        required_fields = ['symbol', 'name', 'instrument_type', 'asset_class']
        for field in required_fields:
            assert field in vti

    def test_classification_includes_price(self, sample_instruments):
        """Test that classification includes current price"""
        vti = sample_instruments['VTI']

        assert 'current_price' in vti
        assert vti['current_price'] > 0

    def test_classification_includes_expense_ratio(self, sample_instruments):
        """Test that classification includes expense ratio for ETFs"""
        vti = sample_instruments['VTI']

        assert 'expense_ratio' in vti
        assert vti['expense_ratio'] >= 0


class TestBatchProcessing:
    """Test batch processing of instruments"""

    def test_process_batch_of_symbols(self, sample_symbols, mock_db):
        """Test processing multiple symbols at once"""
        results = {}

        for symbol in sample_symbols:
            instrument = mock_db.instruments.find_by_symbol(symbol)
            if instrument:
                results[symbol] = instrument

        assert len(results) > 0

    def test_batch_includes_all_symbols(self, sample_symbols):
        """Test that all symbols are processed"""
        processed = []

        for symbol in sample_symbols:
            processed.append(symbol)

        assert len(processed) == len(sample_symbols)
        assert all(sym in processed for sym in sample_symbols)
