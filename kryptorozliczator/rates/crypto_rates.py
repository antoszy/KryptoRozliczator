from datetime import datetime

import requests

# Define a constant for HTTP success status code
HTTP_OK = 200


def get_crypto_exchange_rate(crypto_id: str, vs_currency: str, date: str) -> float:
    """
    Fetch historical price for a given crypto in a given fiat currency on a specific date.

    Args:
        crypto_id (str): CoinGecko coin ID, e.g., 'bitcoin', 'ethereum'
        vs_currency (str): Fiat currency code, e.g., 'usd', 'eur'
        date (str): Date in format 'YYYY-MM-DD'

    Returns:
        float: Price of 1 unit of crypto in vs_currency at given date
    """

    # Convert date from YYYY-MM-DD to timestamp format
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    timestamp = int(date_obj.timestamp() * 1000)  # Binance uses milliseconds

    # Map crypto_id to Binance symbol format
    symbol = f"{crypto_id.upper()}{vs_currency.upper()}"

    # Binance klines API endpoint
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "startTime": timestamp, "limit": 1}
    response = requests.get(url, params=params)

    if response.status_code != HTTP_OK:
        raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

    try:
        price = response.json()[0][4]
    except IndexError as err:
        raise Exception(f"No data found for {crypto_id} in {vs_currency} on {date}") from err

    return float(price)


if __name__ == "__main__":
    # Example usage
    crypto = "btc"
    fiat = "usdt"
    date = "28-04-2025"  # dd-mm-yyyy
    price = get_crypto_exchange_rate(crypto, fiat, date)
    print(f"On {date}, 1 {crypto} was worth {price} {fiat.upper()}")

    # BTC in PLN
    crypto = "btc"
    fiat = "pln"
    date = "28-01-2024"  # dd-mm-yyyy
    price = get_crypto_exchange_rate(crypto, fiat, date)
    print(f"On {date}, 1 {crypto} was worth {price} {fiat.upper()}")

    # ETH in PLN
    crypto = "eth"
    fiat = "pln"
    date = "28-01-2025"  # dd-mm-yyyy
    price = get_crypto_exchange_rate(crypto, fiat, date)
    print(f"On {date}, 1 {crypto} was worth {price} {fiat.upper()}")
