"""
Lambda function for ingesting text into S3 Vectors with embeddings.
Uses AWS Bedrock Titan Embeddings for vector generation.
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
        
        # Generate unique ID for the vector
        vector_id = str(uuid.uuid4())
        
        # Store in S3 Vectors
        print(f"Storing vector in bucket: {VECTOR_BUCKET}, index: {INDEX_NAME}")
        s3_vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            vectors=[{
                "key": vector_id,
                "data": {"float32": embedding},
                "metadata": {
                    "text": text,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    **metadata  # Include any additional metadata
                }
            }]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document indexed successfully',
                'document_id': vector_id
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }