"""
Tests for Charter chart validation logic
"""

import pytest
import json
import sys
from pathlib import Path

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from lambda_handler import validate_charts, VALID_CHART_TYPES


class TestValidateCharts:
    """Test chart JSON validation"""

    def test_valid_pie_chart(self, valid_charts_json):
        """Test validation of valid pie chart"""
        charts, error = validate_charts(valid_charts_json)
        assert error == ""
        assert len(charts) == 2
        assert charts[0]["type"] == "pie"

    def test_valid_bar_chart(self):
        """Test validation of valid bar chart"""
        data = {
            "charts": [
                {
                    "key": "test",
                    "title": "Test Bar",
                    "type": "bar",
                    "data": [{"name": "A", "value": 10}]
                }
            ]
        }
        charts, error = validate_charts(data)
        assert error == ""
        assert len(charts) == 1

    def test_valid_donut_chart(self):
        """Test validation of valid donut chart"""
        data = {
            "charts": [
                {
                    "key": "test",
                    "title": "Test Donut",
                    "type": "donut",
                    "data": [{"name": "A", "value": 50}, {"name": "B", "value": 50}]
                }
            ]
        }
        charts, error = validate_charts(data)
        assert error == ""
        assert charts[0]["type"] == "donut"

    def test_valid_horizontal_bar_chart(self):
        """Test validation of valid horizontal bar chart"""
        data = {
            "charts": [
                {
                    "key": "test",
                    "title": "Test HBar",
                    "type": "horizontalBar",
                    "data": [{"name": "A", "value": 10}]
                }
            ]
        }
        charts, error = validate_charts(data)
        assert error == ""
        assert charts[0]["type"] == "horizontalBar"

    def test_invalid_not_dict(self):
        """Test validation fails for non-dict input"""
        charts, error = validate_charts("not a dict")
        assert charts == []
        assert "not a JSON object" in error

    def test_invalid_missing_charts_array(self):
        """Test validation fails when charts array is missing"""
        charts, error = validate_charts({"other": "data"})
        assert charts == []
        assert "Missing or empty 'charts' array" in error

    def test_invalid_empty_charts_array(self):
        """Test validation fails when charts array is empty"""
        charts, error = validate_charts({"charts": []})
        assert charts == []
        assert "Missing or empty 'charts' array" in error

    def test_invalid_chart_not_object(self):
        """Test validation fails when chart is not an object"""
        charts, error = validate_charts({"charts": ["not an object"]})
        assert charts == []
        assert "not an object" in error

    def test_invalid_missing_required_fields(self, invalid_charts_missing_fields):
        """Test validation fails when required fields are missing"""
        charts, error = validate_charts(invalid_charts_missing_fields)
        assert charts == []
        assert "missing fields" in error

    def test_invalid_chart_type(self, invalid_charts_wrong_type):
        """Test validation fails for invalid chart type"""
        charts, error = validate_charts(invalid_charts_wrong_type)
        assert charts == []
        assert "invalid type" in error

    def test_invalid_empty_data_array(self):
        """Test validation fails when data array is empty"""
        data = {
            "charts": [
                {
                    "key": "test",
                    "title": "Test",
                    "type": "pie",
                    "data": []
                }
            ]
        }
        charts, error = validate_charts(data)
        assert charts == []
        assert "empty or invalid data" in error

    def test_multiple_charts(self):
        """Test validation of multiple valid charts"""
        data = {
            "charts": [
                {"key": "c1", "title": "Chart 1", "type": "pie", "data": [{"name": "A", "value": 100}]},
                {"key": "c2", "title": "Chart 2", "type": "bar", "data": [{"name": "B", "value": 50}]},
                {"key": "c3", "title": "Chart 3", "type": "donut", "data": [{"name": "C", "value": 25}]}
            ]
        }
        charts, error = validate_charts(data)
        assert error == ""
        assert len(charts) == 3


class TestValidChartTypes:
    """Test valid chart types constant"""

    def test_valid_chart_types_set(self):
        """Test that VALID_CHART_TYPES contains expected types"""
        assert "pie" in VALID_CHART_TYPES
        assert "bar" in VALID_CHART_TYPES
        assert "donut" in VALID_CHART_TYPES
        assert "horizontalBar" in VALID_CHART_TYPES
        assert len(VALID_CHART_TYPES) == 4
