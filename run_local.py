# run_local.py
import json
import os
from dotenv import load_dotenv
from lambda_function import lambda_handler

# --- ADDED: Load .env file to get the secret key ---
load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")
# --- END ---


# 1. Define a mock 'event' object.
mock_event = {
    "headers": {"x-api-key": SECRET_KEY},
    "body": json.dumps({"tickers": ["OXY", "XPTO"]}),
}

# 2. Define a mock 'context' object (it's not used, but required).
mock_context = {}

# 3. Call your handler function directly.
if __name__ == "__main__":
    print("--- Running local test ---")

    if not SECRET_KEY:
        print("\nERROR: MY_APP_SECRET_KEY not found in .env file.")
        print("Please make sure your .env file is set up correctly.")
    else:
        # Call the handler from your other file
        response = lambda_handler(mock_event, mock_context)

        # 4. Pretty-print the response to see the results clearly.
        print("\n--- Lambda Response ---")
        print(f"Status Code: {response.get('statusCode')}")

        if response and response.get("body"):
            # The body is a JSON string, so we parse it to print it nicely
            response_body = json.loads(response["body"])
            print(json.dumps(response_body, indent=4))
        else:
            print("No response body found.")
