# KryptoRozliczator

Zestaw narzędzi do rozliczania podatków od kryptowalut w Polsce.

## Prerequisites

- Python 3.12
- Poetry (Python package manager)

## Setup

1. Install Poetry if you haven't already:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/kryptorozliczator.git
cd kryptorozliczator
poetry install
```

3. Install pre-commit hooks:

```bash
poetry run pre-commit install
```

## Development

The project uses:

- `black` for code formatting
- `isort` for import sorting
- `ruff` for linting
- `pytest` for testing

All these tools are automatically run on commit thanks to pre-commit hooks.

### Running Tests

```bash
poetry run pytest
```

### Running Linters

```bash
poetry run black .
poetry run isort .
poetry run ruff check .
```

## Project Structure

```
kryptorozliczator/
├── kryptorozliczator/     # Main package directory
│   └── __init__.py
├── tests/                 # Test directory
├── pyproject.toml         # Project configuration (Poetry)
├── .pre-commit-config.yaml # Pre-commit hooks configuration
└── README.md             # This file
```
