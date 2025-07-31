"""Command-line interface for poker chip split calculator."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .calculator import ChipSplitCalculator
from .config import PokerConfig, create_example_config, create_example_config_with_values
from .models import ChipDistribution


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        verbose: If True    if args.command == "create-example":
        return create_example_command(args)
    
    if args.command == "calculate":
        return calculate_command(args)
    
    if args.command == "distribute":
        return distribute_command(args)
    
    parser.print_help()
    return 1gging level to DEBUG, otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=format_str)


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
    mode = getattr(args, 'mode', 'calculate')
    
    if mode == 'distribute':
        default_filename = "distribute_example.yaml"
        create_func = create_example_config_with_values
        command_example = "distribute"
    else:  # calculate mode (default)
        default_filename = "calculate_example.yaml" 
        create_func = create_example_config
        command_example = "calculate"
    
    output_file = Path(args.output or default_filename)
    
    if output_file.exists() and not args.force:
        print(f"Error: File {output_file} already exists. Use --force to overwrite.")
        return 1
    
    try:
        create_func(output_file)
        print(f"Example configuration created at: {output_file}")
        print(f"\nYou can now edit this file and run:")
        print(f"  poker-chip-split {command_example} {output_file}")
        return 0
    except Exception as e:
        print(f"Error creating example file: {e}")
        return 1


def calculate_command(args: argparse.Namespace) -> int:
    """Handle the calculate command (optimize values for given buy-in)."""
    # Set up logging first
    setup_logging(verbose=args.verbose)
    
    logger = logging.getLogger(__name__)
    config_file = Path(args.config_file)
    
    try:
        # Load configuration
        config = PokerConfig.from_yaml_file(config_file)
        logger.info(f"Loaded configuration from: {config_file}")
        logger.info(f"Game setup: {config.num_players} players, ${config.buy_in_per_person:.2f} buy-in per player")
        logger.info(f"Total pot: ${config.buy_in_per_person * config.num_players:.2f}")
        
        # Log chip set details
        total_chips = sum(config.chip_set.colors.values())
        logger.info(f"Available chips: {total_chips} total across {len(config.chip_set.colors)} colors")
        for color, count in config.chip_set.colors.items():
            logger.debug(f"  {color}: {count} chips")
        
        # Initialize calculator with chip values from config or CLI args
        chip_values = args.custom_values or config.get_chip_values()
        logger.info(f"Using {len(chip_values)} possible chip values: {chip_values}")
        
        # Calculate total combinations to check
        colors = list(config.chip_set.colors.keys())
        num_colors = len(colors)
        
        # Calculate value permutations
        total_permutations = 1
        for i in range(num_colors):
            total_permutations *= (len(chip_values) - i)
        
        # Calculate average chip combinations per permutation
        avg_combinations_per_permutation = 1
        for color in colors:
            available_chips = config.chip_set.get_color_count(color)
            max_per_player = available_chips // config.num_players
            if max_per_player > 0:
                avg_combinations_per_permutation *= max_per_player
        
        total_combinations = total_permutations * avg_combinations_per_permutation
        
        logger.info(
            f"Search space: {total_permutations:,} value permutations x "
            f"~{avg_combinations_per_permutation:,} chip combinations = "
            f"~{total_combinations:,} total combinations"
        )
        logger.info("Starting exhaustive search...")
        
        calculator = ChipSplitCalculator(custom_values=chip_values)
        
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


def distribute_command(args: argparse.Namespace) -> int:
    """Handle the distribute command (distribute with fixed values)."""
    # Set up logging first
    setup_logging(verbose=args.verbose)
    
    logger = logging.getLogger(__name__)
    config_file = Path(args.config_file)
    
    try:
        # Load configuration
        config = PokerConfig.from_yaml_file(config_file)
        logger.info(f"Loaded configuration from: {config_file}")
        logger.info(f"Game setup: {config.num_players} players")
        
        # Verify that chip values are defined
        if not config.has_fixed_values():
            missing_colors = [
                color for color, chip_color in config.chip_colors.items()
                if chip_color.value is None
            ]
            raise ValueError(
                f"Fixed chip values must be defined for all colors in 'distribute' mode. "
                f"Missing values for: {sorted(missing_colors)}. "
                f"Use format: chip_colors: {{color: {{count: N, value: V}}}}",
            )
        
        # Get fixed chip values
        fixed_values = config.get_fixed_chip_values()
        
        # Log chip set details
        total_chips = sum(config.chip_set.colors.values())
        logger.info(f"Available chips: {total_chips} total across {len(fixed_values)} colors")
        for color, count in config.chip_set.colors.items():
            logger.debug(f"  {color}: {count} chips (${fixed_values[color]:.2f} each)")
        
        # Calculate total value if all chips distributed
        total_available_value = sum(
            fixed_values[color] * config.chip_set.colors[color]
            for color in fixed_values
        )
        logger.info(f"Total available value: ${total_available_value:.2f}")
        
        calculator = ChipSplitCalculator()
        
        # Calculate optimal distribution with fixed values
        distribution = calculator.calculate_distribution_with_values(
            config.chip_set,
            fixed_values,
            config.num_players,
            config.buy_in_per_person,  # Pass the buy-in target
        )
        
        if distribution is None:
            logger.error("No valid chip distribution found with the given fixed values")
            print("ERROR: Could not find a valid distribution with the specified chip values.")
            print("Try adjusting the chip values or quantities.")
            return 1
        
        # Print results (create a mock config with per-player value for formatting)
        mock_config = PokerConfig(
            buy_in_per_person=config.buy_in_per_person,  # Use actual buy-in from config
            num_players=config.num_players,
            chip_colors=config.chip_colors,
        )
        print_distribution_fixed_values(distribution, mock_config)
        
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


def print_distribution_fixed_values(distribution: ChipDistribution, config: PokerConfig) -> None:
    """Print the chip distribution results for fixed values mode."""
    print("\n" + "="*60)
    print("POKER CHIP DISTRIBUTION RESULTS (Fixed Values Mode)")
    print("="*60)
    
    print(f"\nGame Configuration:")
    print(f"  Buy-in per player: ${config.buy_in_per_person:.2f}")
    print(f"  Number of players: {config.num_players}")
    total_pot = config.buy_in_per_person * config.num_players
    print(f"  Total pot: ${total_pot:.2f}")
    
    print(f"\nChip Values (Fixed):")
    for color, value in distribution.chip_values.items():
        print(f"  {color.capitalize()}: ${value:.2f}")
    
    print(f"\nPer Player Distribution:")
    total_value = 0
    total_chips = 0
    for color, count in distribution.chips_per_player.items():
        if count > 0:  # Only show colors with chips distributed
            value = distribution.chip_values[color]
            color_total = count * value
            total_value += color_total
            total_chips += count
            print(f"  {color.capitalize()}: {count} chips (${color_total:.2f})")
    
    print(f"\nTotal per player: {total_chips} chips worth ${total_value:.2f}")
    print(f"Target buy-in: ${config.buy_in_per_person:.2f}")
    error = abs(total_value - config.buy_in_per_person)
    if error < 0.01:  # Practically perfect
        print(f"✓ Perfect match!")
    else:
        print(f"Error: ${error:.2f} ({error/config.buy_in_per_person*100:.1f}%)")
    
    print(f"\nUnused Chips:")
    total_unused = 0
    total_unused_value = 0
    for color, count in distribution.unused_chips.items():
        total_unused += count
        if count > 0:
            unused_value = count * distribution.chip_values[color]
            total_unused_value += unused_value
            print(f"  {color.capitalize()}: {count} chips (${unused_value:.2f})")
    
    if total_unused == 0:
        print("  None - Perfect efficiency!")
    else:
        efficiency = distribution.get_efficiency()
        print(f"\nEfficiency: {efficiency:.1f}% ({total_unused} chips unused)")
        print(f"Unused value: ${total_unused_value:.2f}")


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate optimal poker chip distributions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poker-chip-split create-example calculate
  poker-chip-split create-example distribute -o my_game.yaml
  poker-chip-split calculate calculate_example.yaml
  poker-chip-split calculate game.yaml --custom-values 0.5 1 5 25
  poker-chip-split distribute distribute_example.yaml
        """,
    )
    
    # Global arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create example command
    create_parser = subparsers.add_parser(
        "create-example",
        help="Create an example configuration file",
    )
    create_parser.add_argument(
        "mode",
        choices=["calculate", "distribute"],
        help="Mode to create example for: 'calculate' (optimize values) or 'distribute' (fixed values)",
    )
    create_parser.add_argument(
        "-o", "--output",
        help="Output file name (default: calculate_example.yaml or distribute_example.yaml)",
    )
    create_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing file",
    )
    
    # Calculate command
    calc_parser = subparsers.add_parser(
        "calculate",
        help="Calculate chip distribution from config file (optimize values for target buy-in)",
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
    
    # Distribute command (new mode)
    dist_parser = subparsers.add_parser(
        "distribute",
        help="Distribute chips with fixed values (optimize quantities for given values)",
    )
    dist_parser.add_argument(
        "config_file",
        help="Path to YAML configuration file with 'chip_values' defined",
    )
    
    args = parser.parse_args()
    
    # Set up logging based on verbose flag
    setup_logging(verbose=getattr(args, "verbose", False))
    
    if args.command == "create-example":
        return create_example_command(args)
    
    if args.command == "calculate":
        return calculate_command(args)
    
    if args.command == "distribute":
        return distribute_command(args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
