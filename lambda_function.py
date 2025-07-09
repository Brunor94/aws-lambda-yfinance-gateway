import json
import logging
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import yfinance as yf
from curl_cffi import requests

import os
import tempfile

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

# --- START: SECURITY CONFIGURATION ---
SECRET_KEY = os.environ.get("SECRET_KEY")
# --- END: SECURITY CONFIGURATION ---


# Get the system's temp directory and create our cache folder inside it
CACHE_DIR = os.path.join(tempfile.gettempdir(), "yfinance_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

logger.info("Setting cache to: %s", CACHE_DIR)
yf.set_tz_cache_location(CACHE_DIR)


@dataclass
class PricingInfo:
    """Data class to store stock pricing information."""

    current_price: Optional[float]
    target_low_price: Optional[float]
    target_mean_price: Optional[float]
    target_median_price: Optional[float]
    fifty_two_week_low: Optional[float]
    fifty_two_week_high: Optional[float]
    dividend_yield: Optional[float]

    def to_dict(self) -> Dict[str, Optional[float]]:
        """Convert the dataclass to a dictionary."""
        return asdict(self)


class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy and pandas data types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            if np.isnan(obj):
                return None
            return float(obj)
        if pd.isna(obj):
            return None
        return super(CustomEncoder, self).default(obj)


def get_price_by_currency(
    price: Optional[float], currency: Optional[str]
) -> Optional[float]:
    """Convert price to the appropriate currency format."""
    if price is None:
        return None
    if currency == "GBp":
        return price / 100
    return price


def get_dividend_yield(
    currency: Optional[str], current_price: Optional[float], dividends: pd.DataFrame
) -> Optional[float]:
    """Calculate the annual dividend yield percentage."""
    if current_price is None or current_price == 0 or dividends.empty:
        return None

    if not isinstance(dividends.index, pd.DatetimeIndex):
        logger.warning("Dividend data does not have a DatetimeIndex")
        return None

    try:
        if dividends.index.tz is None:
            dividends.index = dividends.index.tz_localize("America/New_York")
        else:
            dividends.index = dividends.index.tz_convert("America/New_York")

        now = pd.Timestamp.now(tz="America/New_York")
        one_year_ago = now - pd.DateOffset(years=1)
        recent_dividends = dividends[dividends.index > one_year_ago]

        if recent_dividends.empty:
            logger.info("No dividends in the last year")
            return 0.0

        annual_dividends = get_price_by_currency(recent_dividends.sum(), currency)

        if annual_dividends is None:
            return None

        dividend_yield = (annual_dividends / current_price) * 100
        return dividend_yield

    except Exception as e:
        logger.error(f"Error calculating dividend yield: {str(e)}")
        return None


def safe_round(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """Safely round a value that might be None."""
    return round(value, decimals) if value is not None else None


def get_pricing_information_from_tickers(
    stock: yf.Ticker, ticker: str
) -> Optional[PricingInfo]:
    """Extract pricing information from a yfinance Ticker object."""
    try:
        info = stock.info
        if info.get("currentPrice") is None:
            raise ValueError(f"No valid data found for ticker '{ticker}'.")

        currency = info.get("currency")
        current_price = get_price_by_currency(info.get("currentPrice"), currency)
        fifty_two_week_low = get_price_by_currency(
            info.get("fiftyTwoWeekLow"), currency
        )
        fifty_two_week_high = get_price_by_currency(
            info.get("fiftyTwoWeekHigh"), currency
        )
        target_low_price = get_price_by_currency(info.get("targetLowPrice"), currency)
        target_mean_price = get_price_by_currency(info.get("targetMeanPrice"), currency)
        target_median_price = get_price_by_currency(
            info.get("targetMedianPrice"), currency
        )

        dividends = stock.dividends
        dividend_yield = get_dividend_yield(currency, current_price, dividends)

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
    """Check if the current Python version is 3.9."""
    version_info = sys.version_info
    if version_info.major != 3 or version_info.minor != 9:
        logger.warning(
            f"This Lambda function is designed for Python 3.9. Current version: {sys.version}"
        )
        return False
    logger.info(f"Python version check passed: {sys.version}")
    return True


def parse_event(event: Dict[str, Any]) -> Tuple[List[str], bool]:
    """Parse and validate the Lambda event."""
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event.get("body", "{}"))
        elif isinstance(event.get("body"), dict):
            body = event.get("body")
        else:
            body = event

        tickers = body.get("tickers")
        if not tickers or not isinstance(tickers, list):
            raise ValueError(
                'Please provide a JSON object with a "tickers" key containing a list of ticker strings.'
            )

        valid_tickers = [t for t in tickers if t and isinstance(t, str)]
        if not valid_tickers:
            raise ValueError("No valid ticker symbols provided")

        return valid_tickers, True

    except Exception as e:
        logger.error(f"Error parsing event: {str(e)}")
        raise ValueError(f"Invalid request format: {str(e)}")


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda function handler for the YFinance Gateway."""
    
    # --- ADDED: SECURITY CHECK ---
    # This check runs first. If the key is wrong, the function stops.
    if not SECRET_KEY:
        logger.error("Security key is not configured in environment variables.")
        return create_error_response(500, "Internal server error: misconfigured security")

    headers = event.get("headers", {})
    # Note: API Gateway may convert header names to lowercase.
    client_secret = headers.get("x-api-key") 

    if client_secret != SECRET_KEY:
        logger.warning("Forbidden: Invalid or missing API key.")
        return create_error_response(403, "Forbidden")
    # --- END OF SECURITY CHECK ---

    logger.info("Security check passed. Processing event.")
    check_python_version()

    try:
        tickers, is_valid = parse_event(event)
        if not is_valid:
            return create_error_response(400, "Invalid request format")
    except ValueError as e:
        return create_error_response(400, str(e))

    results = {}
    errors = {}
    try:
        session = requests.Session(impersonate="chrome")
        logger.info(f"Fetching data for tickers: {', '.join(tickers)}")
        tickers_obj = yf.Tickers(tickers, session=session)

        for ticker_symbol in tickers:
            try:
                logger.info(f"Processing {ticker_symbol}...")
                stock = tickers_obj.tickers.get(ticker_symbol)
                if not stock:
                    raise ValueError(f"Ticker {ticker_symbol} not found in yf.Tickers.")

                pricing_info = get_pricing_information_from_tickers(
                    stock, ticker_symbol
                )
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

    response_body = {"data": results, "errors": errors}
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(response_body, indent=4, cls=CustomEncoder),
    }