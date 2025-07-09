import json
import logging
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from curl_cffi import requests

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@dataclass
class PricingInfo:
    """Data class to store stock pricing information.
    
    Attributes:
        current_price: Current stock price
        target_low_price: Analysts' low price target
        target_mean_price: Analysts' mean price target
        target_median_price: Analysts' median price target
        fifty_two_week_low: 52-week low price
        fifty_two_week_high: 52-week high price
        dividend_yield: Annual dividend yield percentage
    """
    current_price: Optional[float]
    target_low_price: Optional[float]
    target_mean_price: Optional[float]
    target_median_price: Optional[float]
    fifty_two_week_low: Optional[float]
    fifty_two_week_high: Optional[float]
    dividend_yield: Optional[float]
    
    def to_dict(self) -> Dict[str, Optional[float]]:
        """Convert the dataclass to a dictionary.
        
        Returns:
            Dictionary representation of the pricing information
        """
        return asdict(self)


class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy and pandas data types.
    
    Extends the standard JSON encoder to properly serialize NumPy integers,
    floats, and handle NaN values from both NumPy and pandas.
    """
    def default(self, obj: Any) -> Any:
        """Convert objects to JSON serializable types.
        
        Args:
            obj: The object to serialize
            
        Returns:
            JSON serializable version of the object
            
        Raises:
            TypeError: If the object cannot be serialized
        """
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            if np.isnan(obj):
                return None
            return float(obj)
        if pd.isna(obj):
            return None
        return super(CustomEncoder, self).default(obj)


def get_price_by_currency(price: Optional[float], currency: Optional[str]) -> Optional[float]:
    """Convert price to the appropriate currency format.
    
    Handles special cases like GBp (British pence) which needs conversion to pounds.
    
    Args:
        price: The price value to convert
        currency: The currency code
        
    Returns:
        Converted price or None if input price is None
    """
    if price is None:
        return None
        
    # Convert British pence to pounds
    if currency == "GBp":
        return price / 100
        
    return price


def get_dividend_yield(
    currency: Optional[str], current_price: Optional[float], dividends: pd.DataFrame
) -> Optional[float]:
    """Calculate the annual dividend yield percentage.
    
    Uses the last year of dividend payments to calculate an annual yield.
    
    Args:
        currency: The currency code for the stock
        current_price: Current stock price
        dividends: DataFrame containing dividend history
        
    Returns:
        Annual dividend yield as a percentage, or None if it cannot be calculated
    """
    # Early returns for invalid inputs
    if current_price is None or current_price == 0 or dividends.empty:
        return None

    if not isinstance(dividends.index, pd.DatetimeIndex):
        logger.warning("Dividend data does not have a DatetimeIndex")
        return None

    try:
        # Ensure timezone-aware datetime index
        if dividends.index.tz is None:
            dividends.index = dividends.index.tz_localize("America/New_York")
        else:
            dividends.index = dividends.index.tz_convert("America/New_York")

        # Get dividends from the last year
        now = pd.Timestamp.now(tz="America/New_York")
        one_year_ago = now - pd.DateOffset(years=1)
        recent_dividends = dividends[dividends.index > one_year_ago]

        if recent_dividends.empty:
            logger.info("No dividends in the last year")
            return 0.0

        # Sum up the dividends and convert to the right currency
        annual_dividends = get_price_by_currency(recent_dividends.sum(), currency)

        if annual_dividends is None:
            return None

        # Calculate yield percentage
        dividend_yield = (annual_dividends / current_price) * 100
        return dividend_yield
        
    except Exception as e:
        logger.error(f"Error calculating dividend yield: {str(e)}")
        return None


def safe_round(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """Safely round a value that might be None.
    
    Args:
        value: The value to round
        decimals: Number of decimal places
        
    Returns:
        Rounded value or None if input is None
    """
    return round(value, decimals) if value is not None else None


def get_pricing_information_from_tickers(stock: yf.Ticker, ticker: str) -> Optional[PricingInfo]:
    """Extract pricing information from a yfinance Ticker object.
    
    Args:
        stock: yfinance Ticker object
        ticker: Stock ticker symbol
        
    Returns:
        PricingInfo object with stock data or None if data cannot be retrieved
        
    Raises:
        ValueError: If no valid data is found for the ticker
    """
    try:
        # Get stock information
        info = stock.info

        # Validate that we have meaningful data
        if not info or not any(key in info for key in ["trailingPegRatio", "currentPrice", "marketCap"]):
            raise ValueError(f"No valid data found for ticker '{ticker}'.")

        # Extract currency and price data
        currency = info.get("currency", None)
        
        # Extract and convert all price data
        current_price = get_price_by_currency(info.get("currentPrice", None), currency)
        fifty_two_week_low = get_price_by_currency(info.get("fiftyTwoWeekLow", None), currency)
        fifty_two_week_high = get_price_by_currency(info.get("fiftyTwoWeekHigh", None), currency)
        target_low_price = get_price_by_currency(info.get("targetLowPrice", None), currency)
        target_mean_price = get_price_by_currency(info.get("targetMeanPrice", None), currency)
        target_median_price = get_price_by_currency(info.get("targetMedianPrice", None), currency)

        # Get dividend information
        dividends = stock.dividends
        dividend_yield = get_dividend_yield(currency, current_price, dividends)

        # Create and return the pricing info object with rounded values
        return PricingInfo(
            safe_round(current_price),
            safe_round(target_low_price),
            safe_round(target_mean_price),
            safe_round(target_median_price),
            safe_round(fifty_two_week_low),
            safe_round(fifty_two_week_high),
            safe_round(dividend_yield),
        )

    except Exception as e:
        logger.error(f"Error getting pricing information for {ticker}: {str(e)}")
        raise


def check_python_version() -> bool:
    """Check if the current Python version is 3.9.
    
    Returns:
        True if running on Python 3.9, False otherwise
    """
    version_info = sys.version_info
    if version_info.major != 3 or version_info.minor != 9:
        logger.warning(
            f"This Lambda function is designed for Python 3.9. Current version: {sys.version}"
        )
        return False
    logger.info(f"Python version check passed: {sys.version}")
    return True


def parse_event(event: Dict[str, Any]) -> Tuple[List[str], bool]:
    """Parse and validate the Lambda event.
    
    Args:
        event: AWS Lambda event object
        
    Returns:
        Tuple containing list of tickers and a boolean indicating success
        
    Raises:
        ValueError: If the event format is invalid or tickers are missing
    """
    try:
        # Handle both direct invocation and API Gateway event formats
        if isinstance(event.get("body"), str):
            body = json.loads(event.get("body", "{}"))
        elif isinstance(event.get("body"), dict):
            body = event.get("body")
        else:
            body = event
            
        tickers = body.get("tickers")

        if not tickers or not isinstance(tickers, list):
            raise ValueError('Please provide a JSON object with a "tickers" key containing a list of ticker strings.')
            
        # Filter out invalid tickers
        valid_tickers = [t for t in tickers if t and isinstance(t, str)]
        
        if not valid_tickers:
            raise ValueError("No valid ticker symbols provided")
            
        return valid_tickers, True
        
    except Exception as e:
        logger.error(f"Error parsing event: {str(e)}")
        raise ValueError(f"Invalid request format: {str(e)}")


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        Formatted error response for API Gateway
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda function handler for the YFinance Gateway.
    
    Retrieves stock pricing information for the requested ticker symbols.
    
    Args:
        event: The event dict from the Lambda invocation
        context: The context object from the Lambda invocation
        
    Returns:
        API Gateway response object with the pricing data or error information
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Check Python version
    check_python_version()

    # Parse and validate the event
    try:
        tickers, is_valid = parse_event(event)
        if not is_valid:
            return create_error_response(400, "Invalid request format")
    except ValueError as e:
        return create_error_response(400, str(e))

    results = {}
    errors = {}

    try:
        # Create a session that impersonates Chrome to avoid blocking
        session = requests.Session(impersonate="chrome")
        
        # Get data for all tickers in one batch request
        logger.info(f"Fetching data for tickers: {', '.join(tickers)}")
        tickers_obj = yf.Tickers(tickers, session=session)

        # Process each ticker
        for ticker_symbol in tickers:
            try:
                logger.info(f"Processing {ticker_symbol}...")
                stock = tickers_obj.tickers.get(ticker_symbol)

                if not stock:
                    raise ValueError(f"Ticker {ticker_symbol} not found in yf.Tickers.")

                pricing_info = get_pricing_information_from_tickers(stock, ticker_symbol)
                if pricing_info:
                    results[ticker_symbol] = pricing_info.to_dict()
                    logger.info(f"Successfully processed data for {ticker_symbol}")
            except Exception as e:
                error_message = f"Error processing {ticker_symbol}: {str(e)}"
                logger.error(error_message)
                errors[ticker_symbol] = error_message

    except Exception as outer_exception:
        logger.error(f"Unexpected failure: {str(outer_exception)}")
        return create_error_response(500, f"Unexpected failure: {str(outer_exception)}")

    # Prepare the response
    response_body = {"data": results, "errors": errors}

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response_body, indent=4, cls=CustomEncoder),
    }
