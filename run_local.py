#!/usr/bin/env python3
import json
from lambda_function import lambda_handler

def main():
    """
    Run the Lambda function locally with a test event
    """
    print("Running Lambda function locally...")
    
    # Load the test event
    try:
        with open('test_event.json', 'r') as f:
            event = json.load(f)
    except FileNotFoundError:
        print("test_event.json not found, using default event")
        event = {
            "key1": "value1",
            "key2": "value2"
        }
    
    # Call the Lambda handler
    response = lambda_handler(event, None)
    
    # Print the response
    print("\nLambda Response:")
    print(json.dumps(response, indent=2))
    
    # Parse and print the body for better readability
    if 'body' in response:
        try:
            body = json.loads(response['body'])
            print("\nParsed Response Body:")
            print(json.dumps(body, indent=2))
        except json.JSONDecodeError:
            print("\nBody is not valid JSON:", response['body'])

if __name__ == "__main__":
    main()
