import os
from datetime import datetime

import ccxt
from dotenv import load_dotenv


class ExchangeInterface:
    def __init__(self, exchange_id: str):
        """
        Initialize a universal exchange interface for any CCXT-supported exchange.

        Args:
            exchange_id: The CCXT exchange ID (e.g., 'binance', 'bitfinex', 'kraken')
        """
        self.exchange_name = exchange_id
        load_dotenv()

        # Construct environment variable names based on exchange ID
        api_key_var = f"{exchange_id.upper()}_API_KEY"
        api_secret_var = f"{exchange_id.upper()}_API_SECRET"

        api_key = os.getenv(api_key_var)
        api_secret = os.getenv(api_secret_var)

        if not api_key or not api_secret:
            raise ValueError(f"{api_key_var} and {api_secret_var} must be set in .env file")

        try:
            # Dynamically get the exchange class from ccxt
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                }
            )
        except AttributeError:
            raise ValueError(
                f"Exchange '{exchange_id}' is not supported by CCXT. "
                "Please check the CCXT documentation for supported exchanges."
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to initialize {exchange_id} exchange: {e!s}") from e

    def get_transaction_history(self, year: int) -> list[dict]:
        """
        Fetches transaction history for the specified year.

        Args:
            year: The year for which to fetch transactions.

        Returns:
            A list of transactions for that year.
        """
        if not self.exchange.has["fetchMyTrades"]:
            raise NotImplementedError(
                f"The {self.exchange_name} exchange does not support fetching user trades through"
                f"ccxt."
            )

        all_trades = []
        since = self.exchange.parse8601(f"{year}-01-01T00:00:00Z")
        end_timestamp = self.exchange.parse8601(f"{year+1}-01-01T00:00:00Z")
        limit = 100  # Adjust limit based on API capabilities/defaults

        try:
            while True:
                print(f"Fetching trades since {self.exchange.iso8601(since)}...")
                trades = self.exchange.fetch_my_trades(since=since, limit=limit)

                if not trades:
                    print("No more trades found.")
                    break

                # Filter trades that are within the target year
                new_trades_in_year = [
                    trade
                    for trade in trades
                    if trade["timestamp"] >= since and trade["timestamp"] < end_timestamp
                ]
                all_trades.extend(new_trades_in_year)

                # Check if the last fetched trade is outside the year or
                # if we received fewer trades than the limit
                if trades[-1]["timestamp"] >= end_timestamp or len(trades) < limit:
                    print("Reached end of relevant period or fetched less than limit.")
                    break

                # Update the 'since' timestamp to fetch the next batch
                since = trades[-1]["timestamp"] + 1  # +1 ms to avoid duplicates
                # Add a small delay to avoid hitting rate limits
                self.exchange.sleep(1000)  # sleep for 1 second

            # Ensure final list only contains trades from the specified year
            final_trades = [
                trade
                for trade in all_trades
                if datetime.fromtimestamp(trade["timestamp"] / 1000).year == year
            ]
            print(f"Fetched {len(final_trades)} total trades for the year {year}.")
            return final_trades

        except ccxt.AuthenticationError as e:
            print(f"Authentication Error: {e}. Check your API keys.")
            raise
        except ccxt.ExchangeError as e:
            print(f"Exchange Error: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

    def get_available_markets(self) -> list[str]:
        """
        Get a list of available trading pairs/markets on the exchange.

        Returns:
            List of trading pair symbols (e.g., ['BTC/USD', 'ETH/BTC'])
        """
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Error fetching markets: {e}")
            raise

    def get_ticker(self, symbol: str) -> dict:
        """
        Get the current ticker information for a trading pair.

        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USD')

        Returns:
            Dictionary containing ticker information
        """
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            raise

    def get_balance(self) -> dict[str, float]:
        """
        Get the current balance of all currencies.

        Returns:
            Dictionary mapping currency symbols to their balances
        """
        try:
            balance = self.exchange.fetch_balance()
            return {currency: amount for currency, amount in balance["total"].items() if amount > 0}
        except Exception as e:
            print(f"Error fetching balance: {e}")
            raise
