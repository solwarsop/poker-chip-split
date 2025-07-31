# Poker Chip Split Calculator

A Python package for calculating optimal poker chip distributions based on buy-in amounts and available chip colors. The calculator minimizes unused chips while sticking to standard poker chip values.

## Features

- **YAML Configuration**: Define game parameters in easy-to-read YAML files
- **Optimal Distribution**: Calculates chip values that minimize waste
- **Standard Values**: Uses common poker chip values ($0.25, $0.50, $1, $2, $5, $10, etc.)
- **Flexible Input**: Support for any number of chip colors and quantities
- **Command Line Interface**: Easy-to-use CLI for quick calculations
- **Efficiency Reporting**: Shows how many chips go unused

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/solwarsop/poker-chip-split.git
cd poker-chip-split

# Create and activate conda environment
conda env create -f dev-environment.yml
conda activate poker-chip-split

# Install the package
pip install -e .
```

## Quick Start

### 1. Create an Example Configuration

```bash
poker-chip-split create-example
```

This creates `poker_config_example.yaml` with the following structure:

```yaml
buy_in_per_person: 20.0
num_players: 6
chip_colors:
  white: 100
  red: 80
  green: 60
  black: 40
  blue: 20
```

### 2. Calculate Optimal Distribution

```bash
poker-chip-split calculate poker_config_example.yaml
```

This will output something like:

```
============================================================
POKER CHIP DISTRIBUTION RESULTS
============================================================

Game Configuration:
  Buy-in per player: $20.00
  Number of players: 6
  Total pot: $120.00

Chip Values:
  White: $0.25
  Red: $1.00
  Green: $5.00
  Black: $10.00
  Blue: $25.00

Per Player Distribution:
  White: 16 chips ($4.00)
  Red: 16 chips ($16.00)
  Green: 0 chips ($0.00)
  Black: 0 chips ($0.00)
  Blue: 0 chips ($0.00)

Total value per player: $20.00
Target buy-in: $20.00
Error: $0.00 (0.0%)

Unused Chips:
  White: 4 chips
  Red: 0 chips
  Green: 60 chips
  Black: 40 chips
  Blue: 20 chips

Efficiency: 19.4% (124 chips unused)
```

## Usage

### YAML Configuration Format

Your configuration file should contain:

```yaml
# Required fields
buy_in_per_person: 25.0    # Dollar amount each player pays
num_players: 8             # Number of players
chip_colors:               # Available chips
  white: 200              # Color name: quantity
  red: 100
  green: 50
  black: 25
```

### Command Line Options

#### Create Example Configuration

```bash
# Create with default name
poker-chip-split create-example

# Create with custom name
poker-chip-split create-example -o my_game.yaml

# Overwrite existing file
poker-chip-split create-example -f
```

#### Calculate Distribution

```bash
# Basic calculation
poker-chip-split calculate config.yaml

# Use custom chip values
poker-chip-split calculate config.yaml --custom-values 0.5 1 5 25
```

### Python API

You can also use the package programmatically:

```python
from poker_chip_split import ChipSplitCalculator, ChipSet
from poker_chip_split.config import PokerConfig

# Load configuration from file
config = PokerConfig.from_yaml_file("my_config.yaml")

# Or create manually
chip_set = ChipSet(colors={"white": 100, "red": 50, "green": 25})

# Calculate optimal distribution
calculator = ChipSplitCalculator()
distribution = calculator.calculate_optimal_split(
    chip_set=chip_set,
    buy_in_per_person=20.0,
    num_players=4
)

# Access results
print(f"Efficiency: {distribution.get_efficiency():.1f}%")
print(f"Unused chips: {distribution.get_total_unused_chips()}")
```

## How It Works

The calculator:

1. **Tries all combinations** of standard poker chip values for your available colors
2. **Optimizes for minimal waste** by finding the combination that uses the most chips
3. **Uses greedy allocation** starting with highest-value chips
4. **Validates results** ensuring each player gets close to the target buy-in amount

### Standard Chip Values

The calculator uses these standard poker chip values by default:
- $0.25, $0.50, $1.00, $2.00, $5.00, $10.00, $25.00, $50.00, $100.00

You can override these with the `--custom-values` option.

## Development

### Setup Development Environment

```bash
# Create conda environment
conda env create -f dev-environment.yml
conda activate poker-chip-split

# Install in development mode
pip install -e .

# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=poker_chip_split

# Run specific test file
pytest tests/test_models.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests and linting (`pytest && black src/ tests/ && mypy src/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
