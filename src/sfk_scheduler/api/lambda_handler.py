"""
Lambda handler for routing API requests.
"""
import json

def lambda_handler(event, context):
    """
    Entry point for the Lambda function triggered by API Gateway.

    Routes requests to appropriate handlers based on HTTP paths and methods.

    Args:
        event (dict): The API Gateway event payload containing request details.
        context: AWS Lambda execution context.

    Returns:
        dict: Response object containing statusCode, headers, and body.
    """
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET').upper()

    routes = {
        ('GET', '/health'): health_handler,
    }

    handler = routes.get((method, path), not_found_handler)
    return handler(event)

def health_handler(event):
    """
    Health-check endpoint.
    
    Returns:
        dict: Response object stating API health.
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok", "message": "API is functional."}),
    }

def not_found_handler(event):
    """
    Not Found handler for unmatched routes.

    Returns:
        dict: Response indicating resource not found.
    """
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "error", "message": "Resource not found."}),
    }
