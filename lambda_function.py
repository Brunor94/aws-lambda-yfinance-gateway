import json
import sys

# Check Python version
def check_python_version():
    """Verify that the correct Python version (3.9) is being used"""
    version_info = sys.version_info
    if version_info.major != 3 or version_info.minor != 9:
        print(f"Warning: This Lambda function is designed for Python 3.9. Current version: {sys.version}")
        return False
    return True

def lambda_handler(event, context):
    """
    Simple AWS Lambda function that returns a Hello World message
    
    Parameters:
    event (dict): Input event to the Lambda function
    context (LambdaContext): Lambda runtime information
    
    Returns:
    dict: Response containing statusCode and body
    """
    # Check Python version
    is_correct_version = check_python_version()
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello World from AWS Lambda!',
            'event': event
        })
    }
