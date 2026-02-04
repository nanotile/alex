"""
Lambda function for ingesting text into S3 Vectors with embeddings and sentiment.
Uses AWS Bedrock Titan Embeddings for vector generation and SageMaker FinBERT for sentiment.
"""

import json
import os
import boto3
import datetime
import uuid

# Environment variables
VECTOR_BUCKET = os.environ.get('VECTOR_BUCKET', 'alex-vectors')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
BEDROCK_REGION = os.environ.get('BEDROCK_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
INDEX_NAME = os.environ.get('INDEX_NAME', 'financial-research')
SAGEMAKER_SENTIMENT_ENDPOINT = os.environ.get('SAGEMAKER_SENTIMENT_ENDPOINT', 'alex-sentiment-endpoint')

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=BEDROCK_REGION)
s3_vectors = boto3.client('s3vectors')


def get_embedding(text):
    """Get embedding vector from AWS Bedrock Titan Embeddings."""
    response = bedrock_runtime.invoke_model(
        modelId=BEDROCK_EMBEDDING_MODEL,
        contentType='application/json',
        body=json.dumps({'inputText': text})
    )

    result = json.loads(response['body'].read())
    return result.get('embedding', [])


def get_sentiment(text):
    """
    Score financial text sentiment using SageMaker FinBERT endpoint.
    Returns {label, score} or None if scoring fails (graceful degradation).
    """
    try:
        sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=BEDROCK_REGION)
        # Truncate to ~512 BERT tokens (approx 2000 chars)
        truncated = text[:2000]
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_SENTIMENT_ENDPOINT,
            ContentType='application/json',
            Body=json.dumps({'inputs': truncated})
        )
        result = json.loads(response['Body'].read())

        # HF text-classification returns [[{label, score}, ...]] or [{label, score}, ...]
        predictions = result
        if isinstance(predictions, list) and len(predictions) > 0:
            if isinstance(predictions[0], list):
                predictions = predictions[0]

        top_label = None
        top_score = 0.0
        for pred in predictions:
            score = float(pred['score'])
            if score > top_score:
                top_score = score
                top_label = pred['label'].lower()

        return {'label': top_label, 'score': top_score}
    except Exception as e:
        print(f"Sentiment scoring skipped: {e}")
        return None


def lambda_handler(event, context):
    """
    Main Lambda handler.
    Expects JSON body with:
    {
        "text": "Text to ingest",
        "metadata": {
            "source": "optional source",
            "category": "optional category"
        }
    }
    """
    try:
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        text = body.get('text')
        metadata = body.get('metadata', {})

        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required field: text'})
            }

        # Get embedding from Bedrock
        print(f"Getting embedding for text: {text[:100]}...")
        embedding = get_embedding(text)

        # Score sentiment via FinBERT (graceful degradation)
        sentiment = get_sentiment(text)
        if sentiment:
            print(f"Sentiment: {sentiment['label']} ({sentiment['score']:.2f})")

        # Generate unique ID for the vector
        vector_id = str(uuid.uuid4())

        # Build metadata — include sentiment if available
        vector_metadata = {
            "text": text,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            **metadata,
        }
        if sentiment:
            vector_metadata["sentiment_label"] = sentiment["label"]
            vector_metadata["sentiment_score"] = str(sentiment["score"])

        # Store in S3 Vectors
        print(f"Storing vector in bucket: {VECTOR_BUCKET}, index: {INDEX_NAME}")
        s3_vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            vectors=[{
                "key": vector_id,
                "data": {"float32": embedding},
                "metadata": vector_metadata,
            }]
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document indexed successfully',
                'document_id': vector_id,
                'sentiment': sentiment,
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }