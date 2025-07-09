![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-up--to--date-brightgreen)
![AWS Service](https://img.shields.io/badge/service-AWS%20Lambda-orange)
![YFinance](https://img.shields.io/badge/YFinance-0.2.65-green)

# AWS Lambda YFinance Gateway (Python 3.9)

A serverless API gateway built on AWS Lambda that provides stock pricing information using the YFinance library. This service retrieves current prices, analyst targets, 52-week ranges, and dividend yields for requested stock tickers.

> **IMPORTANT**: This project is specifically designed for Python 3.9 runtime. Using other Python versions may cause compatibility issues with AWS Lambda.

## Project Structure

```
aws-lambda-yfinance-gateway/
├── lambda_function.py         # Main Lambda handler function
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python runtime version
├── README.md                 # This documentation
├── create_deployment_package.py # Script to create Lambda deployment package
├── run_local.py              # Script to test the Lambda function locally
├── test_event.json           # Sample test event for local testing
└── tests/                    # Test files
    └── test_lambda.py        # Unit tests for the Lambda function
```

## Features

- **Stock Price Data**: Retrieves current stock prices and historical ranges
- **Analyst Targets**: Provides low, mean, and median price targets
- **Dividend Information**: Calculates annual dividend yield based on recent dividend history
- **Batch Processing**: Handles multiple stock tickers in a single request
- **Error Handling**: Provides detailed error messages for failed requests
- **Browser Fingerprinting**: Uses Chrome browser impersonation to avoid API blocks

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
   
4. Run the local test script:
   ```
   python run_local.py
   ```

### Deployment

#### Automated Deployment Package Creation

1. Use the included script to create a deployment package:
   ```
   python create_deployment_package.py
   ```
   
   This script will:
   - Verify you're using Python 3.9
   - Install dependencies to a package directory
   - Create a properly structured deployment.zip file

2. Upload the deployment.zip file to AWS Lambda via the AWS Management Console or AWS CLI.

#### Using AWS CLI

```
aws lambda create-function \
  --function-name yfinance-gateway \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::<ACCOUNT_ID>:role/lambda-execution-role \
  --timeout 30 \
  --memory-size 256
```

Replace `<ACCOUNT_ID>` with your AWS account ID.

#### Updating an Existing Function

```
aws lambda update-function-code \
  --function-name yfinance-gateway \
  --zip-file fileb://deployment.zip
```

## Testing

### Local Testing

A test script is included for local testing:

```
python run_local.py
```

This script uses a mock event with sample tickers (OXY, MSFT, AAPL, GOOGL) and prints the response.

To test with different tickers, modify the `mock_event` in `run_local.py`.

### Creating Custom Test Events

You can create custom test events by modifying `test_event.json` or creating new JSON files with the following format:

```json
{
  "body": "{\"tickers\": [\"AAPL\", \"MSFT\", \"GOOGL\"]}"
}
```

### AWS Console Testing

1. Navigate to your Lambda function in the AWS Console
2. Click on the "Test" tab
3. Create a new test event with the following template:
   ```json
   {
     "body": "{\"tickers\": [\"AAPL\", \"MSFT\", \"GOOGL\"]}"
   }
   ```
4. Click "Test" to execute the function

## API Usage

### Request Format

```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

### Response Format

```json
{
  "data": {
    "AAPL": {
      "current_price": 189.97,
      "target_low_price": 150.0,
      "target_mean_price": 205.76,
      "target_median_price": 210.0,
      "fifty_two_week_low": 124.17,
      "fifty_two_week_high": 198.23,
      "dividend_yield": 0.52
    },
    "MSFT": {
      "current_price": 414.47,
      "target_low_price": 370.0,
      "target_mean_price": 473.67,
      "target_median_price": 475.0,
      "fifty_two_week_low": 309.45,
      "fifty_two_week_high": 430.82,
      "dividend_yield": 0.71
    }
  },
  "errors": {
    "INVALID": "Error processing INVALID: No valid data found for ticker 'INVALID'."
  }
}
```

## Runtime

This Lambda function uses Python 3.9 runtime.

## Dependencies

- curl_cffi==0.11.4
- numpy==1.26.4
- pandas==2.3.1
- requests==2.32.4
- yfinance==0.2.65
