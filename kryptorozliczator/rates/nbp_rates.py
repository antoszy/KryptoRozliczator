from datetime import datetime, timedelta

import requests

# Define constants for HTTP status codes
HTTP_OK = 200
HTTP_NOT_FOUND = 404


def get_nbp_exchange_rate(currency_code: str, date: datetime) -> float:
    """
    Get exchange rate from NBP API for a given currency and date.

    Args:
        currency_code (str): Currency code (e.g., 'USD', 'EUR')
        date (datetime): Date for which to get the exchange rate

    Returns:
        float: Exchange rate or 1.0 for PLN

    Raises:
        Exception: If failed to get exchange rate
    """
    if currency_code == "PLN":
        return 1.0

    # NBP API requires uppercase currency codes
    currency_code = currency_code.upper()

    # Format date as YYYY-MM-DD
    date_str = date.strftime("%Y-%m-%d")

    # NBP API endpoint
    url = f"http://api.nbp.pl/api/exchangerates/rates/A/{currency_code}/{date_str}/?format=json"

    try:
        response = requests.get(url)
        if response.status_code == HTTP_OK:
            data = response.json()
            return data["rates"][0]["mid"]
        elif response.status_code == HTTP_NOT_FOUND:
            # If rate not found for given date, try previous day
            yesterday = date - timedelta(days=1)
            return get_nbp_exchange_rate(currency_code, yesterday)
    except Exception as e:
        raise Exception(f"Failed to get exchange rate for {currency_code}: {e!s}") from e
