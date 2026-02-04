"""
Mock tests for SentimentClient — no real SageMaker calls needed.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from market_data.sentiment import SentimentClient, MAX_CHARS


# --- Fixtures ---


@pytest.fixture
def client():
    with patch("market_data.sentiment.boto3") as mock_boto3:
        mock_runtime = MagicMock()
        mock_boto3.client.return_value = mock_runtime
        sc = SentimentClient(endpoint_name="test-endpoint", region="us-east-1")
        sc._mock_runtime = mock_runtime  # attach for test access
        yield sc


def _make_response(predictions):
    """Build a mock SageMaker invoke_endpoint response."""
    body = MagicMock()
    body.read.return_value = json.dumps(predictions).encode()
    return {"Body": body}


# --- Tests ---


class TestSentimentClientInit:
    def test_init_default_endpoint(self):
        with patch("market_data.sentiment.boto3"):
            sc = SentimentClient()
            assert sc.endpoint_name == "alex-sentiment-endpoint"
            assert sc.region == "us-east-1"

    def test_init_custom_endpoint(self):
        with patch("market_data.sentiment.boto3"):
            sc = SentimentClient(endpoint_name="my-endpoint", region="eu-west-1")
            assert sc.endpoint_name == "my-endpoint"
            assert sc.region == "eu-west-1"

    @patch.dict("os.environ", {"SAGEMAKER_SENTIMENT_ENDPOINT": "env-endpoint", "SAGEMAKER_REGION": "us-west-2"})
    def test_init_from_env(self):
        with patch("market_data.sentiment.boto3"):
            sc = SentimentClient()
            assert sc.endpoint_name == "env-endpoint"
            assert sc.region == "us-west-2"


class TestSentimentAnalyze:
    def test_analyze_positive(self, client):
        predictions = [[
            {"label": "positive", "score": 0.87},
            {"label": "neutral", "score": 0.08},
            {"label": "negative", "score": 0.05},
        ]]
        client._mock_runtime.invoke_endpoint.return_value = _make_response(predictions)

        result = client.analyze("Apple reported strong Q4 earnings with revenue growth of 8%")

        assert result is not None
        assert result["label"] == "positive"
        assert result["score"] == pytest.approx(0.87)
        assert result["scores"]["positive"] == pytest.approx(0.87)
        assert result["scores"]["neutral"] == pytest.approx(0.08)
        assert result["scores"]["negative"] == pytest.approx(0.05)

    def test_analyze_negative(self, client):
        predictions = [[
            {"label": "negative", "score": 0.92},
            {"label": "neutral", "score": 0.05},
            {"label": "positive", "score": 0.03},
        ]]
        client._mock_runtime.invoke_endpoint.return_value = _make_response(predictions)

        result = client.analyze("Company filed for bankruptcy amid mounting debt")

        assert result is not None
        assert result["label"] == "negative"
        assert result["score"] == pytest.approx(0.92)

    def test_analyze_neutral(self, client):
        predictions = [[
            {"label": "neutral", "score": 0.75},
            {"label": "positive", "score": 0.15},
            {"label": "negative", "score": 0.10},
        ]]
        client._mock_runtime.invoke_endpoint.return_value = _make_response(predictions)

        result = client.analyze("The company held its annual shareholder meeting on Tuesday")

        assert result is not None
        assert result["label"] == "neutral"
        assert result["score"] == pytest.approx(0.75)

    def test_analyze_flat_response(self, client):
        """Some HF versions return flat list instead of nested."""
        predictions = [
            {"label": "positive", "score": 0.90},
            {"label": "neutral", "score": 0.07},
            {"label": "negative", "score": 0.03},
        ]
        client._mock_runtime.invoke_endpoint.return_value = _make_response(predictions)

        result = client.analyze("Revenue beat expectations")

        assert result is not None
        assert result["label"] == "positive"
        assert result["score"] == pytest.approx(0.90)

    def test_analyze_truncation(self, client):
        """Long text gets truncated to MAX_CHARS before sending to endpoint."""
        long_text = "x" * (MAX_CHARS + 500)
        predictions = [[
            {"label": "neutral", "score": 0.80},
            {"label": "positive", "score": 0.10},
            {"label": "negative", "score": 0.10},
        ]]
        client._mock_runtime.invoke_endpoint.return_value = _make_response(predictions)

        result = client.analyze(long_text)

        # Verify the text sent to endpoint was truncated
        call_args = client._mock_runtime.invoke_endpoint.call_args
        sent_body = json.loads(call_args[1]["Body"])
        assert len(sent_body["inputs"]) == MAX_CHARS
        assert result is not None

    def test_analyze_endpoint_error(self, client):
        """Returns None on endpoint failure."""
        client._mock_runtime.invoke_endpoint.side_effect = Exception("Endpoint not found")

        result = client.analyze("Some financial text")

        assert result is None

    def test_analyze_empty_text(self, client):
        """Returns None for empty text."""
        assert client.analyze("") is None
        assert client.analyze("   ") is None
        assert client.analyze(None) is None


class TestSentimentBatch:
    def test_analyze_batch(self, client):
        """Batch calls analyze for each text."""
        responses = [
            _make_response([[{"label": "positive", "score": 0.9}, {"label": "neutral", "score": 0.05}, {"label": "negative", "score": 0.05}]]),
            _make_response([[{"label": "negative", "score": 0.8}, {"label": "neutral", "score": 0.1}, {"label": "positive", "score": 0.1}]]),
        ]
        client._mock_runtime.invoke_endpoint.side_effect = responses

        results = client.analyze_batch(["Good earnings", "Bad outlook"])

        assert len(results) == 2
        assert results[0]["label"] == "positive"
        assert results[1]["label"] == "negative"

    def test_analyze_batch_partial_failure(self, client):
        """Batch returns None for failed items."""
        client._mock_runtime.invoke_endpoint.side_effect = [
            _make_response([[{"label": "positive", "score": 0.9}, {"label": "neutral", "score": 0.05}, {"label": "negative", "score": 0.05}]]),
            Exception("Endpoint cold start timeout"),
        ]

        results = client.analyze_batch(["Good earnings", "Another text"])

        assert len(results) == 2
        assert results[0]["label"] == "positive"
        assert results[1] is None
