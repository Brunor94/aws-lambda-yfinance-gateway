# local_test.py
import json
from lambda_function import lambda_handler

# 1. Define a mock 'event' object.
# This simulates the input your Lambda would receive from API Gateway.
# You can change the tickers here to test different stocks.
mock_event = {"body": json.dumps({"tickers": ["OXY", "MSFT", "AAPL", "GOOGL"]})}

# 2. Define a mock 'context' object.
# Our function doesn't use this, but the handler signature requires it.
# An empty object is fine.
mock_context = {}

# 3. Call your handler function directly.
if __name__ == "__main__":
    print("--- Running local test ---")

    # Call the handler from your other file
    response = lambda_handler(mock_event, mock_context)

    # 4. Pretty-print the response to see the results clearly.
    print("\n--- Lambda Response ---")
    if response and response.get("body"):
        # The body is a JSON string, so we parse it to print it nicely
        response_body = json.loads(response["body"])
        print(json.dumps(response_body, indent=4))
    else:
        print("No response body found.")
