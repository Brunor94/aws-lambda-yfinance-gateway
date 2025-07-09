import json
import unittest
import sys
import os

# Add parent directory to path to import lambda_function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):
    def test_lambda_handler(self):
        # Test event
        test_event = {
            "key1": "value1",
            "key2": "value2"
        }
        
        # Call the lambda handler
        response = lambda_handler(test_event, None)
        
        # Check the response
        self.assertEqual(response['statusCode'], 200)
        
        # Parse the body
        body = json.loads(response['body'])
        
        # Check the message
        self.assertEqual(body['message'], 'Hello World from AWS Lambda!')
        
        # Check that the event was returned
        self.assertEqual(body['event'], test_event)

if __name__ == '__main__':
    unittest.main()
