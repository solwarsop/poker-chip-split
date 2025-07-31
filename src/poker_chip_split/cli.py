"""Command-line interface for poker chip split calculator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .calculator import ChipSplitCalculator
from .config import PokerConfig, create_example_config
from .models import ChipDistribution


def print_distribution(distribution: ChipDistribution, config: PokerConfig) -> None:
    """Print the chip distribution results in a readable format."""
    print("\n" + "="*60)
    print("POKER CHIP DISTRIBUTION RESULTS")
    print("="*60)
    
    print(f"\nGame Configuration:")
    print(f"  Buy-in per player: ${config.buy_in_per_person:.2f}")
    print(f"  Number of players: {config.num_players}")
    print(f"  Total pot: ${config.buy_in_per_person * config.num_players:.2f}")
    
    print(f"\nChip Values:")
    for color, value in distribution.chip_values.items():
        print(f"  {color.capitalize()}: ${value:.2f}")
    
    print(f"\nPer Player Distribution:")
    total_value = 0
    for color, count in distribution.chips_per_player.items():
        value = distribution.chip_values[color]
        color_total = count * value
        total_value += color_total
        print(f"  {color.capitalize()}: {count} chips (${color_total:.2f})")
    
    print(f"\nTotal value per player: ${total_value:.2f}")
    print(f"Target buy-in: ${config.buy_in_per_person:.2f}")
    error = abs(total_value - config.buy_in_per_person)
    print(f"Error: ${error:.2f} ({error/config.buy_in_per_person*100:.1f}%)")
    
    print(f"\nUnused Chips:")
    total_unused = 0
    for color, count in distribution.unused_chips.items():
        total_unused += count
        if count > 0:
            print(f"  {color.capitalize()}: {count} chips")
    
    if total_unused == 0:
        print("  None - Perfect efficiency!")
    else:
        efficiency = distribution.get_efficiency()
        print(f"\nEfficiency: {efficiency:.1f}% ({total_unused} chips unused)")


def create_example_command(args: argparse.Namespace) -> int:
    """Handle the create-example command."""
    output_file = Path(args.output or "poker_config_example.yaml")
    
    if output_file.exists() and not args.force:
        print(f"Error: File {output_file} already exists. Use --force to overwrite.")
        return 1
    
    try:
        create_example_config(output_file)
        print(f"Example configuration created at: {output_file}")
        print("\nYou can now edit this file and run:")
        print(f"  poker-chip-split calculate {output_file}")
        return 0
    except Exception as e:
        print(f"Error creating example file: {e}")
        return 1


def calculate_command(args: argparse.Namespace) -> int:
    """Handle the calculate command."""
    config_file = Path(args.config_file)
    
    try:
        # Load configuration
        config = PokerConfig.from_yaml_file(config_file)
        
        # Initialize calculator
        calculator = ChipSplitCalculator(custom_values=args.custom_values)
        
        # Calculate optimal distribution
        distribution = calculator.calculate_optimal_split(
            config.chip_set,
            config.buy_in_per_person,
            config.num_players,
        )
        
        # Print results
        print_distribution(distribution, config)
        
        return 0
        
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        print("Create an example file with: poker-chip-split create-example")
        return 1
    except ValueError as e:
        print(f"Error in configuration: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate optimal poker chip distributions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poker-chip-split create-example
  poker-chip-split create-example -o my_game.yaml
  poker-chip-split calculate poker_config.yaml
  poker-chip-split calculate game.yaml --custom-values 0.5 1 5 25
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create example command
    create_parser = subparsers.add_parser(
        "create-example", 
        help="Create an example configuration file",
    )
    create_parser.add_argument(
        "-o", "--output",
        help="Output file name (default: poker_config_example.yaml)",
    )
    create_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing file",
    )
    
    # Calculate command
    calc_parser = subparsers.add_parser(
        "calculate",
        help="Calculate chip distribution from config file",
    )
    calc_parser.add_argument(
        "config_file",
        help="Path to YAML configuration file",
    )
    calc_parser.add_argument(
        "--custom-values",
        type=float,
        nargs="+",
        help="Custom chip values to use (e.g., --custom-values 0.25 0.5 1 5 10)",
    )
    
    args = parser.parse_args()
    
    if args.command == "create-example":
        return create_example_command(args)
    elif args.command == "calculate":
        return calculate_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
