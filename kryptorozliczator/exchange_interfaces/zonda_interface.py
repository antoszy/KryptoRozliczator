import os
from datetime import datetime

import ccxt
from dotenv import load_dotenv


class ZondaInterface:
    def __init__(self):
        self.exchange_name = "zonda"
        load_dotenv()
        api_key = os.getenv("ZONDA_API_KEY")
        api_secret = os.getenv("ZONDA_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("ZONDA_API_KEY and ZONDA_API_SECRET must be set in .env file")

        # Attempt to initialize Zonda (formerly BitBay) via ccxt
        # Note: ccxt might use 'bitbay' as the id for Zonda.
        # If 'zonda' or 'bitbay' doesn't work, Zonda might not be supported by ccxt,
        # or requires a different identifier.
        try:
            # Try 'zonda' first
            self.exchange = ccxt.zonda(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                }
            )
        except AttributeError:
            try:
                # Fallback to 'bitbay'
                self.exchange = ccxt.bitbay(
                    {
                        "apiKey": api_key,
                        "secret": api_secret,
                    }
                )
                print("Initialized Zonda using 'bitbay' identifier.")
            except AttributeError:
                raise ValueError(
                    "Neither 'zonda' nor 'bitbay' exchange ID found in ccxt. "
                    "Zonda might not be supported."
                ) from None
            except Exception as e:
                raise RuntimeError("Failed to initialize ccxt exchange") from e
        except Exception as e:
            raise RuntimeError("Failed to initialize ccxt exchange") from e

    def get_transaction_history(self, year: int):
        """
        Fetches transaction history for the specified year.

        Args:
            year: The year for which to fetch transactions.

        Returns:
            A list of transactions for that year.
            (Format depends on ccxt's fetchMyTrades method)
        """
        if not self.exchange.has["fetchMyTrades"]:
            raise NotImplementedError(
                "The exchange does not support fetching user trades through ccxt."
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


# Example usage (optional, for testing)
if __name__ == "__main__":
    try:
        zonda = ZondaInterface()
        target_year = 2024  # Example year
        history = zonda.get_transaction_history(target_year)
        print(f"\nTransaction History for {target_year}:")
        if history:
            for trade in history:
                print(trade)
        else:
            print("No transactions found for this year.")
    except (
        ValueError,
        RuntimeError,
        NotImplementedError,
        ccxt.base.errors.AuthenticationError,
        ccxt.base.errors.ExchangeError,
    ) as e:
        print(f"Error: {e}")
