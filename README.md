# Poker Chip Split Calculator

A Python package for calculating optimal poker chip distributions based on buy-in amounts and available chip colors. The calculator offers two modes: optimizing chip values for maximum usage, or distributing chips with fixed predetermined values.

## Features

- **Two Distribution Modes**:
  - **Calculate Mode**: Optimizes chip values to maximize chip usage for target buy-in
  - **Distribute Mode**: Distributes chips with fixed predetermined values targeting specific buy-in
- **YAML Configuration**: Define game parameters in easy-to-read YAML files
- **Exhaustive Search**: Uses comprehensive algorithms to find optimal distributions
- **All Colors Used**: Ensures every chip color is used when possible, giving players diverse denominations
- **Unique Chip Values**: Each chip color gets a different value (no duplicates)
- **Standard Values**: Uses common poker chip values (£0.05, £0.10, £0.25, £0.50, £1, £2, £5, etc.)
- **Custom Values**: Optional custom chip denominations in YAML configuration
- **Flexible Input**: Support for any number of chip colors and quantities
- **Command Line Interface**: Easy-to-use CLI for quick calculations
- **Efficiency Reporting**: Shows how many chips go unused with accurate percentage calculation
- **Parallel Processing**: Uses multiprocessing for faster calculation of large search spaces

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

### 1. Create Example Configurations

```bash
# Create calculate mode example (optimizes chip values)
poker-chip-split create-example calculate

# Create distribute mode example (fixed values)
poker-chip-split create-example distribute

# Create with custom filename
poker-chip-split create-example calculate -o my_game.yaml
```

This creates configuration files with the following structures:

**Calculate Mode** (`calculate_example.yaml`):

```yaml
buy_in_per_person: 5.0
chip_colors:
  black: 100
  blue: 100
  green: 100
  red: 100
  white: 100
num_players: 9
chip_values: [0.05, 0.10, 0.25, 0.5, 1]  # Optional custom values
```

**Distribute Mode** (`distribute_example.yaml`):

```yaml
buy_in_per_person: 5.0
chip_colors:
  white:
    count: 100
    value: 0.05
  red:
    count: 100
    value: 0.1
  green:
    count: 100
    value: 0.25
  blue:
    count: 100
    value: 0.5
  black:
    count: 100
    value: 1
num_players: 9
```

### 2. Calculate Optimal Distribution

**Calculate Mode** (optimizes chip values):

```bash
poker-chip-split calculate calculate_example.yaml
```

**Distribute Mode** (uses fixed values):

```bash
poker-chip-split distribute distribute_example.yaml
```

This will output something like:

```
============================================================
POKER CHIP DISTRIBUTION RESULTS (Fixed Values Mode)
============================================================

Game Configuration:
  Buy-in per player: £5.00
  Number of players: 9
  Total pot: £45.00

Chip Values (Fixed):
  White: £0.05
  Red: £0.10
  Green: £0.25
  Blue: £0.50
  Black: £1.00

Per Player Distribution:
  White: 10 chips (£0.50)
  Red: 10 chips (£1.00)
  Green: 8 chips (£2.00)
  Blue: 1 chips (£0.50)
  Black: 1 chips (£1.00)

Total per player: 30 chips worth £5.00
Target buy-in: £5.00
✓ Perfect match!

Unused Chips:
  White: 10 chips (£0.50)
  Red: 10 chips (£1.00)
  Green: 28 chips (£7.00)
  Blue: 91 chips (£45.50)
  Black: 91 chips (£91.00)

Efficiency: 54.0% (230 chips unused)
Unused value: £145.00
```

## Usage

### YAML Configuration Format

**For Calculate Mode**, your configuration file should contain:

```yaml
# Required fields
buy_in_per_person: 5.0     # Dollar amount each player pays
chip_colors:               # Available chips (color: count format)
  white: 100              # Color name: quantity
  red: 100
  green: 100
  blue: 100
  black: 100
num_players: 9             # Number of players

# Optional: Custom chip values (must have at least as many values as colors)
chip_values: [0.05, 0.10, 0.25, 0.5, 1]  # Each color gets a unique value
```

**For Distribute Mode**, your configuration file should contain:

```yaml
# Required fields
buy_in_per_person: 5.0     # Dollar amount each player pays
chip_colors:               # Available chips with fixed values
  white:
    count: 100
    value: 0.05
  red:
    count: 100
    value: 0.10
  green:
    count: 100
    value: 0.25
  blue:
    count: 100
    value: 0.50
  black:
    count: 100
    value: 1.00
num_players: 9             # Number of players
```

### Command Line Options

#### Create Example Configuration

```bash
# Create calculate mode example (optimizes chip values)
poker-chip-split create-example calculate

# Create distribute mode example (fixed values)
poker-chip-split create-example distribute

# Create with custom filename
poker-chip-split create-example calculate -o my_game.yaml

# Overwrite existing file
poker-chip-split create-example distribute -f
```

#### Calculate Distribution

```bash
# Calculate mode (optimizes chip values for target buy-in)
poker-chip-split calculate calculate_example.yaml

# Calculate mode with custom chip values
poker-chip-split calculate calculate_example.yaml --custom-values 0.5 1 5 25

# Distribute mode (uses fixed values from config)
poker-chip-split distribute distribute_example.yaml
```

### Python API

You can also use the package programmatically:

```python
from poker_chip_split import ChipSplitCalculator, ChipSet
from poker_chip_split.config import PokerConfig

# Load configuration from file
config = PokerConfig.from_yaml_file("my_config.yaml")

# Or create manually for calculate mode
chip_set = ChipSet(colors={"white": 100, "red": 50, "green": 25})

# Calculate optimal distribution (optimizes chip values)
calculator = ChipSplitCalculator()
distribution = calculator.calculate_optimal_split(
    chip_set=chip_set,
    buy_in_per_person=5.0,
    num_players=4
)

# Or distribute with fixed values (distribute mode)
chip_values = {"white": 0.05, "red": 0.10, "green": 0.25}
distribution = calculator.calculate_distribution_with_values(
    chip_set=chip_set,
    chip_values=chip_values,
    num_players=4,
    buy_in_per_person=5.0  # Optional: target specific buy-in
)

# Access results
print(f"Efficiency: {distribution.get_efficiency():.1f}%")
print(f"Unused chips: {distribution.get_total_unused_chips()}")
```

## How It Works

The calculator offers two distinct modes:

### Calculate Mode

1. **Optimizes chip values** for the available chip colors to achieve target buy-in
2. **Tries all permutations** of standard poker chip values for your available colors
3. **Ensures all colors are used** by giving each player at least 1 chip of every color
4. **Maximizes total chips per player** while staying close to the target buy-in amount
5. **Ensures unique values** with each chip color getting a different denomination
6. **Uses parallel processing** for efficient calculation of large search spaces

### Distribute Mode

1. **Uses fixed chip values** defined in the configuration file
2. **Targets specific buy-in** per person when specified, or maximizes chip usage
3. **Employs exhaustive search** with diversity scoring to prefer solutions using all chip types
4. **Uses parallel processing** to evaluate all possible chip combinations efficiently
5. **Provides accurate efficiency reporting** showing percentage of chips actually used

Both modes ensure players get a diverse mix of chip denominations, maximizing the total number of chips for better poker gameplay with more flexibility for betting and making change.

### Standard Chip Values

The calculator uses these standard poker chip values by default:

- £0.05, £0.10, £0.25, £0.50, £1.00, £2.00, £5.00, £10.00, £25.00, £50.00, £100.00, £200.00, £250.00, £500.00, £1000.00, £2000.00, £5000.00

You can override these with the `--custom-values` option or by specifying `chip_values` in your YAML configuration.

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
