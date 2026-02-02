"""
Lambda function for searching S3 Vectors.
Uses AWS Bedrock Titan Embeddings for query vector generation.
"""

import json
import os
import boto3

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
    Search handler.
    Expects JSON body with:
    {
        "query": "Search query text",
        "k": 5  # Optional, defaults to 5
    }
    """
    # Parse the request body
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    else:
        body = event.get('body', {})
    
    query_text = body.get('query')
    k = body.get('k', 5)
    
    if not query_text:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required field: query'})
        }
    
    # Get embedding for query
    print(f"Getting embedding for query: {query_text}")
    query_embedding = get_embedding(query_text)
    
    # Search S3 Vectors
    print(f"Searching in bucket: {VECTOR_BUCKET}, index: {INDEX_NAME}")
    response = s3_vectors.query_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=INDEX_NAME,
        queryVector={"float32": query_embedding},
        topK=k,
        returnDistance=True,
        returnMetadata=True
    )
    
    # Format results
    results = []
    for vector in response.get('vectors', []):
        results.append({
            'id': vector['key'],
            'score': vector.get('distance', 0),
            'text': vector.get('metadata', {}).get('text', ''),
            'metadata': vector.get('metadata', {})
        })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'results': results,
            'count': len(results)
        })
    }