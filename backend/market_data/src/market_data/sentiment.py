"""
Module: SentimentClient — FinBERT financial sentiment analysis via SageMaker
Version: 0.1.0
Development Iteration: v1

Project: Alex (Agentic Learning Equities eXplainer)
Developer: Kent Benson
Created: 2026-02-04

Enhancement: Initial implementation — FinBERT sentiment scoring for financial text

Features:
- Analyze financial text sentiment (positive/negative/neutral) via SageMaker FinBERT endpoint
- Graceful degradation when endpoint is unavailable
- Text truncation to BERT's 512-token limit
- Batch analysis support

UV ENVIRONMENT: Run with `uv run python -c "from market_data.sentiment import SentimentClient"`

INSTALLATION:
uv add boto3
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

import boto3

logger = logging.getLogger(__name__)

# Approximate max characters for 512 BERT tokens (~4 chars per token)
MAX_CHARS = 2000


class SentimentClient:
    """Financial sentiment analysis via SageMaker FinBERT endpoint."""

    def __init__(self, endpoint_name: str = None, region: str = None):
        self.endpoint_name = endpoint_name or os.getenv(
            "SAGEMAKER_SENTIMENT_ENDPOINT", "alex-sentiment-endpoint"
        )
        self.region = region or os.getenv(
            "SAGEMAKER_REGION", os.getenv("AWS_REGION", "us-east-1")
        )
        self.client = boto3.client("sagemaker-runtime", region_name=self.region)

    def analyze(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze financial text sentiment using FinBERT on SageMaker.

        Args:
            text: Financial text to analyze.

        Returns:
            Dict with keys:
                label: "positive", "negative", or "neutral"
                score: float confidence of the top label (0.0-1.0)
                scores: {positive: float, negative: float, neutral: float}
            Returns None if the endpoint call fails.
        """
        if not text or not text.strip():
            return None

        # Truncate to approximate BERT token limit
        truncated = text[:MAX_CHARS]

        try:
            response = self.client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=json.dumps({"inputs": truncated}),
            )

            result = json.loads(response["Body"].read())

            # HF text-classification returns [[{"label": "positive", "score": 0.87}, ...]]
            # or [{"label": "positive", "score": 0.87}, ...] depending on version
            predictions = result
            if isinstance(predictions, list) and len(predictions) > 0:
                if isinstance(predictions[0], list):
                    predictions = predictions[0]

            # Build scores dict from all labels
            scores = {}
            top_label = None
            top_score = 0.0
            for pred in predictions:
                label = pred["label"].lower()
                score = float(pred["score"])
                scores[label] = score
                if score > top_score:
                    top_score = score
                    top_label = label

            return {
                "label": top_label,
                "score": top_score,
                "scores": scores,
            }

        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return None

    def analyze_batch(self, texts: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Analyze multiple texts sequentially.

        Args:
            texts: List of financial texts to analyze.

        Returns:
            List of sentiment results (None for any that fail).
        """
        return [self.analyze(text) for text in texts]
