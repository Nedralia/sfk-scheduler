"""
Unit tests for Lambda handler in API routing.
"""
import json
from src.sfk_scheduler.api.lambda_handler import lambda_handler

def test_health_check():
    """
    Test the health endpoint of the API Lambda handler.
    """
    event = {
        "path": "/health",
        "httpMethod": "GET",
    }
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assert the response
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "status": "ok",
        "message": "API is functional."
    }

def test_not_found():
    """
    Test a non-existent route.
    """
    event = {
        "path": "/non-existent",
        "httpMethod": "GET",
    }
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assert the response
    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {
        "status": "error",
        "message": "Resource not found."
    }