# Wallet Configuration

This directory contains a configuration file for storing cryptocurrency wallet addresses and extended public keys (xpubs).

## `wallet_config.json`

This configuration file stores wallet addresses and xpubs in a simple list format.

### Structure

1. **Version**
   - Tracks the configuration file version

2. **Wallets**
   - List of wallet configurations
   - Each wallet has:
     - `name`: Descriptive name for the wallet
     - Cryptocurrency sections with direct lists of addresses:
       - `bitcoin`: List of Bitcoin addresses
       - `bitcoin_xpub`: List of Bitcoin extended public keys
       - `ethereum`: List of Ethereum addresses

3. **Metadata**
   - Last update timestamp
   - Description

### Example Usage

```json
{
    "wallets": [
        {
            "name": "Main Wallet",
            "bitcoin": [
                "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "1A1zP1eP5QGefi2DMPTfTL5SLlv7DivfNa"
            ],
            "bitcoin_xpub": [
                "xpub661MyMwAqRbcFtXgS5sYJABqqG9KY3eFQCE1canF2UFqaruF95nyJvD45SgcghicwLvvKr5yYtN31bQf3gfk1ZHsvz9Wz86dQSFu2d41fR7yn"
            ],
            "ethereum": [
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            ]
        }
    ]
}
```

### Adding New Wallets

To add a new wallet, add a new object to the wallets array:

```json
{
    "name": "New Wallet",
    "bitcoin": ["address1", "address2"],
    "bitcoin_xpub": ["xpub1", "xpub2"],
    "ethereum": ["address1"]
}
```

### Security Notes

1. Never commit real addresses or xpubs to version control
2. Keep your configuration file secure
3. Regularly backup your configuration file

### Best Practices

1. Use descriptive names for your wallets
2. Keep the configuration file up to date
3. Use placeholder addresses in example configurations
4. Store xpubs only when necessary for address derivation
