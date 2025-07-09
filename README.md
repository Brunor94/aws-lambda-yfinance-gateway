![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-up--to--date-brightgreen)
![AWS Service](https://img.shields.io/badge/service-AWS%20Lambda-orange)

# AWS Lambda Yfinance Gateway (Python 3.9)

A simple AWS Lambda function written in Python 3.9 that returns a "Hello World" message.

> **IMPORTANT**: This project is specifically designed for Python 3.9 runtime. Using other Python versions may cause compatibility issues with AWS Lambda.

## Project Structure

```
aws-lambda-yfinance-gateway/
├── lambda_function.py    # Main Lambda handler function
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── tests/                # Test files (optional)
    └── test_lambda.py    # Unit tests for the Lambda function
```

## Setup Instructions

### Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Deployment

#### Manual Deployment

1. Create a deployment package:
   ```
   zip -r deployment.zip lambda_function.py
   ```
   
   If you have dependencies:
   ```
   pip install -t package/ -r requirements.txt
   cd package
   zip -r ../deployment.zip .
   cd ..
   zip -g deployment.zip lambda_function.py
   ```

2. Upload the deployment.zip file to AWS Lambda via the AWS Management Console or AWS CLI.

#### Using AWS CLI

```
aws lambda create-function \
  --function-name hello-world-lambda \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::<ACCOUNT_ID>:role/lambda-execution-role
```

Replace `<ACCOUNT_ID>` with your AWS account ID.

## Testing

### Local Testing

Create a test event file `test_event.json`:

```json
{
  "key1": "value1",
  "key2": "value2"
}
```

Run the test:

```python
import json
from lambda_function import lambda_handler

with open('test_event.json', 'r') as f:
    event = json.load(f)

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

### AWS Console Testing

1. Navigate to your Lambda function in the AWS Console
2. Click on the "Test" tab
3. Create a new test event or use the default
4. Click "Test" to execute the function

## Runtime

This Lambda function uses Python 3.9 runtime.
