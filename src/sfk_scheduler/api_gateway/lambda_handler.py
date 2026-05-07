"""
Lambda handler for API Gateway routing.
"""
import json

def lambda_handler(event, context):
    """
    Entry point for the Lambda function triggered by API Gateway.
    Routes the requests to appropriate handlers based on HTTP path and method.
    
    Args:
        event (dict): The API Gateway event payload containing request details.
        context (LambdaContext): AWS Lambda uses this parameter to provide runtime information to your handler.
    
    Returns:
        dict: A response object with statusCode, headers, and body.
    """
    # Extract HTTP path and method from the event
    http_path = event.get('path', '/')
    http_method = event.get('httpMethod', 'GET').upper()

    # Dispatcher for paths
    route_map = {
        ('GET', '/health'): health_check,
    }

    # Route to appropriate handler or respond with 404
    handler = route_map.get((http_method, http_path), not_found_handler)
    return handler(event)

def health_check(event):
    """
    Handles the /health endpoint for checking API status.
    
    Args:
        event (dict): The event payload from AWS API Gateway.
    
    Returns:
        dict: A HTTP response indicating API is healthy.
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok", "message": "API is healthy."}),
    }

def not_found_handler(event):
    """
    Handles unknown routes and responds with 404.

    Args:
        event (dict): The event payload from AWS API Gateway.

    Returns:
        dict: A HTTP response indicating the endpoint is not found.
    """
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "error", "message": "Not Found"}),
    }