import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import requests
from bip32utils import BIP32Key
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

# Load wallet configuration
with open("config/wallet_config.json") as f:
    wallet_config = json.load(f)


def get_wallet_addresses(wallet_name: str) -> dict[str, list[str]]:
    """
    Get addresses for a specific wallet by name
    """
    for wallet in wallet_config["wallets"]:
        if wallet["name"].lower() == wallet_name.lower():
            return wallet["addresses"]
    return {}


# Get API key from environment variable
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "your_api_key_here")


class TransferType(Enum):
    SENT = "sent"
    RECEIVED = "received"


@dataclass
class Transfer:
    timestamp: datetime
    transfer_type: TransferType
    amount: float
    currency: str
    tx_hash: str
    from_address: str
    to_address: str
    fee: float | None = None


class TransfersInterface:
    def __init__(self):
        self.bitcoin_api_url = "https://blockchain.info"
        self.ethereum_api_url = "https://api.etherscan.io/api"
        self.etherscan_api_key = ETHERSCAN_API_KEY

    def get_wallet_transfers(self, wallet_name: str, year: int) -> dict[str, list[Transfer]]:
        """
        Get all transfers for a wallet by name
        Returns a dictionary with currency as key and list of transfers as value
        """
        addresses = get_wallet_addresses(wallet_name)
        if not addresses:
            print(f"Wallet '{wallet_name}' not found in configuration")
            return {}

        transfers = {}

        # Get Bitcoin transfers from regular addresses
        if "bitcoin" in addresses:
            btc_transfers = []
            for address in addresses["bitcoin"]:
                btc_transfers.extend(self.get_bitcoin_transfers(address, year))
            transfers["BTC"] = btc_transfers

        # Get Bitcoin transfers from xpub addresses
        if "bitcoint_xpub" in addresses:
            btc_transfers = transfers.get("BTC", [])
            for xpub in addresses["bitcoint_xpub"]:
                # Get derived addresses from xpub (first 20 addresses)
                derived_addresses = self.get_addresses_from_xpub(xpub)
                for address in derived_addresses:
                    btc_transfers.extend(self.get_bitcoin_transfers(address, year))
            transfers["BTC"] = btc_transfers

        # Get Ethereum transfers from regular addresses
        if "ethereum" in addresses:
            eth_transfers = []
            for address in addresses["ethereum"]:
                eth_transfers.extend(self.get_ethereum_transfers(address, year))
            transfers["ETH"] = eth_transfers

        # Get Ethereum transfers from public keys
        if "ethereum_pub" in addresses:
            eth_transfers = transfers.get("ETH", [])
            for pub_key in addresses["ethereum_pub"]:
                # Convert public key to address
                print(pub_key)
                address = self.get_address_from_pubkey(pub_key)
                print(address)
                if address:
                    eth_transfers.extend(self.get_ethereum_transfers(address, year))
            transfers["ETH"] = eth_transfers

        return transfers

    def get_addresses_from_xpub(self, xpub: str, limit: int = 20) -> list[str]:
        """
        Get derived addresses from an xpub key using BIP32 derivation with path M/84H/0H/0H
        Returns a list of derived addresses up to the specified limit
        """
        try:
            # Create BIP32Key from xpub
            key = BIP32Key.fromExtendedKey(xpub)

            # Derive addresses using path: M/84H/0H/0H/0/i
            # where i is the address index
            addresses = []
            for i in range(limit):
                # Derive child key for this index
                # M/84H/0H/0H/0/i
                child_key = key.ChildKey(84 + 0x80000000)  # 84H
                child_key = child_key.ChildKey(0 + 0x80000000)  # 0H
                child_key = child_key.ChildKey(0 + 0x80000000)  # 0H
                child_key = child_key.ChildKey(0)  # 0
                child_key = child_key.ChildKey(i)  # i
                # Get the address (native segwit)
                address = child_key.Address()
                addresses.append(address)

            return addresses
        except Exception as e:
            print(f"Error deriving addresses from xpub: {e}")
            return []

    def get_address_from_pubkey(self, pub_key: str) -> str | None:
        """
        Convert an Ethereum public key to an address using BIP32 derivation with path M/44H/60H/0H
        """
        try:
            # Remove the '0x' prefix if present
            if pub_key.startswith("0x"):
                pub_key = pub_key[2:]

            # Convert public key to address
            pub_key_bytes = bytes.fromhex(pub_key)
            keccak_hash = Web3.keccak(pub_key_bytes)
            address = "0x" + keccak_hash[-20:].hex()
            return Web3.to_checksum_address(address)
        except Exception as e:
            print(f"Error converting public key to address: {e}")
            return None

    def get_bitcoin_transfers(self, address: str, year: int) -> list[Transfer]:
        """
        Get Bitcoin transfers for a given address and year using blockchain.info API
        """
        transfers = []
        try:
            # Get all transfers for the address
            response = requests.get(f"{self.bitcoin_api_url}/rawaddr/{address}")
            response.raise_for_status()
            data = response.json()

            for tx in data.get("txs", []):
                tx_time = datetime.fromtimestamp(tx["time"])
                if tx_time.year != year:
                    continue

                # Determine if this is a sent or received transfer
                is_sent = any(addr["addr"] == address for addr in tx["inputs"])
                transfer_type = TransferType.SENT if is_sent else TransferType.RECEIVED

                # Calculate the amount
                amount = 0
                for output in tx["out"]:
                    if output["addr"] == address:
                        amount += output["value"] / 100000000  # Convert satoshis to BTC

                transfers.append(
                    Transfer(
                        timestamp=tx_time,
                        transfer_type=transfer_type,
                        amount=amount,
                        currency="BTC",
                        tx_hash=tx["hash"],
                        from_address=tx["inputs"][0]["prev_out"]["addr"] if is_sent else address,
                        to_address=address if is_sent else tx["out"][0]["addr"],
                        fee=tx.get("fee", 0) / 100000000,  # Convert satoshis to BTC
                    )
                )

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Bitcoin transfers: {e}")
            return []

        return transfers

    def get_ethereum_transfers(self, address: str, year: int) -> list[Transfer]:
        """
        Get Ethereum transfers for a given address and year using Etherscan API
        """
        transfers = []
        try:
            # Get normal transfers
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "sort": "desc",
                "apikey": self.etherscan_api_key,
            }

            response = requests.get(self.ethereum_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "1":
                print(f"Error from Etherscan API: {data['message']}")
                return []

            for tx in data["result"]:
                tx_time = datetime.fromtimestamp(int(tx["timeStamp"]))
                if tx_time.year != year:
                    continue

                # Determine transfer type
                is_sent = tx["from"].lower() == address.lower()
                transfer_type = TransferType.SENT if is_sent else TransferType.RECEIVED

                # Convert wei to ETH
                amount = float(tx["value"]) / 1e18
                fee = (float(tx["gasPrice"]) * float(tx["gasUsed"])) / 1e18

                transfers.append(
                    Transfer(
                        timestamp=tx_time,
                        transfer_type=transfer_type,
                        amount=amount,
                        currency="ETH",
                        tx_hash=tx["hash"],
                        from_address=tx["from"],
                        to_address=tx["to"],
                        fee=fee,
                    )
                )

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Ethereum transfers: {e}")
            return []

        return transfers

    def get_transfers(self, address: str, year: int, currency: str) -> list[Transfer]:
        """
        Get transfers for a given address, year, and currency
        """
        if currency.upper() == "BTC":
            return self.get_bitcoin_transfers(address, year)
        elif currency.upper() == "ETH":
            return self.get_ethereum_transfers(address, year)
        else:
            print(f"Unsupported currency: {currency}")
            return []
