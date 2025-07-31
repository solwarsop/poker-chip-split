#!/usr/bin/env python3
"""
Example script demonstrating the poker chip split calculator API.

This script shows how to use the poker-chip-split package programmatically.
"""

from poker_chip_split import ChipSet, ChipSplitCalculator
from poker_chip_split.config import PokerConfig


def main():
    """Demonstrate the poker chip split calculator."""
    print("Poker Chip Split Calculator - Example Usage")
    print("=" * 50)
    
    # Example 1: Basic usage with ChipSet
    print("\n1. Basic Usage:")
    chip_set = ChipSet(colors={
        "white": 100,
        "red": 80,
        "green": 60,
        "black": 40,
        "blue": 20
    })
    
    calculator = ChipSplitCalculator()
    distribution = calculator.calculate_optimal_split(
        chip_set=chip_set,
        buy_in_per_person=25.0,
        num_players=4
    )
    
    print(f"Buy-in per player: $25.00")
    print(f"Players: 4")
    print(f"Chip values assigned: {distribution.chip_values}")
    print(f"Value per player: ${distribution.get_player_value():.2f}")
    print(f"Efficiency: {distribution.get_efficiency():.1f}%")
    
    # Example 2: Using custom chip values
    print("\n2. Custom Chip Values:")
    custom_calculator = ChipSplitCalculator(custom_values=[1.0, 5.0, 25.0])
    custom_distribution = custom_calculator.calculate_optimal_split(
        chip_set=chip_set,
        buy_in_per_person=30.0,
        num_players=3
    )
    
    print(f"Custom values used: [1.0, 5.0, 25.0]")
    print(f"Chip values assigned: {custom_distribution.chip_values}")
    print(f"Value per player: ${custom_distribution.get_player_value():.2f}")
    print(f"Efficiency: {custom_distribution.get_efficiency():.1f}%")
    
    # Example 3: Loading from YAML config
    print("\n3. Loading from YAML Configuration:")
    try:
        config = PokerConfig.from_yaml_file("test_config.yaml")
        yaml_distribution = calculator.calculate_optimal_split(
            config.chip_set,
            config.buy_in_per_person,
            config.num_players
        )
        
        print(f"Loaded from test_config.yaml")
        print(f"Buy-in: ${config.buy_in_per_person}")
        print(f"Players: {config.num_players}")
        print(f"Available chips: {config.chip_set.colors}")
        print(f"Efficiency: {yaml_distribution.get_efficiency():.1f}%")
        
    except FileNotFoundError:
        print("test_config.yaml not found - run 'poker-chip-split create-example' first")


if __name__ == "__main__":
    main()
