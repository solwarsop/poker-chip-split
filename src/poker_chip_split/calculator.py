"""Core calculator for optimal poker chip splits."""

from __future__ import annotations

import itertools
from typing import Optional

from .models import ChipDistribution, ChipSet

# Default poker chip values in dollars - moved here for consistency
DEFAULT_CHIP_VALUES = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0]


class ChipSplitCalculator:
    """Calculate optimal poker chip distributions for poker games."""

    def __init__(self, custom_values: Optional[list[float]] = None) -> None:
        """Initialize calculator with optional custom chip values.
        
        Args:
            custom_values: Optional list of custom chip values to use instead of defaults
        """
        self.possible_values = custom_values or DEFAULT_CHIP_VALUES

    def calculate_optimal_split(
        self, 
        chip_set: ChipSet, 
        buy_in_per_person: float, 
        num_players: int,
    ) -> ChipDistribution:
        """Calculate the optimal chip distribution for given parameters.
        
        Args:
            chip_set: Available chips by color
            buy_in_per_person: Buy-in amount per player
            num_players: Number of players
            
        Returns:
            ChipDistribution with optimal value assignments
        """
        total_buy_in = buy_in_per_person * num_players
        colors = list(chip_set.colors.keys())
        
        best_distribution = None
        min_unused_chips = float("inf")
        
        # Try all possible combinations of values for the available colors
        for value_combination in itertools.product(self.possible_values, repeat=len(colors)):
            distribution = self._evaluate_distribution(
                chip_set, colors, value_combination, buy_in_per_person, num_players,
            )
            
            if distribution and distribution.get_total_unused_chips() < min_unused_chips:
                min_unused_chips = distribution.get_total_unused_chips()
                best_distribution = distribution
        
        if best_distribution is None:
            # Fallback: create a basic distribution if no optimal one found
            return self._create_fallback_distribution(chip_set, colors, buy_in_per_person)
        
        return best_distribution

    def _evaluate_distribution(
        self,
        chip_set: ChipSet,
        colors: list[str],
        values: tuple[float, ...],
        buy_in_per_person: float,
        num_players: int,
    ) -> Optional[ChipDistribution]:
        """Evaluate a specific value assignment for colors."""
        # Create value mapping
        chip_values = dict(zip(colors, values))
        
        # Calculate how many chips each player can get of each color
        chips_per_player = {}
        total_value_per_player = 0
        
        # Sort colors by value (highest first) for greedy allocation
        sorted_colors = sorted(colors, key=lambda c: chip_values[c], reverse=True)
        
        remaining_value = buy_in_per_person
        
        for color in sorted_colors:
            value = chip_values[color]
            available_chips = chip_set.get_color_count(color)
            max_chips_per_player = available_chips // num_players
            
            # Calculate how many chips of this color each player should get
            chips_needed = int(remaining_value // value)
            chips_to_give = min(chips_needed, max_chips_per_player)
            
            chips_per_player[color] = chips_to_give
            total_value_per_player += chips_to_give * value
            remaining_value -= chips_to_give * value
            
            # Stop if we've allocated enough value
            if remaining_value < min(self.possible_values):
                break
        
        # Calculate unused chips
        unused_chips = {}
        for color in colors:
            used_chips = chips_per_player.get(color, 0) * num_players
            unused_chips[color] = chip_set.get_color_count(color) - used_chips
        
        # Check if this distribution is reasonable (gets close to buy-in amount)
        value_error = abs(total_value_per_player - buy_in_per_person)
        max_acceptable_error = buy_in_per_person * 0.1  # 10% tolerance
        
        if value_error > max_acceptable_error:
            return None
        
        return ChipDistribution(
            chip_values=chip_values,
            chips_per_player=chips_per_player,
            total_value_per_player=total_value_per_player,
            unused_chips=unused_chips,
        )

    def _create_fallback_distribution(
        self, chip_set: ChipSet, colors: list[str], buy_in_per_person: float,
    ) -> ChipDistribution:
        """Create a basic fallback distribution when optimization fails."""
        # Assign lowest possible values to colors
        chip_values = {}
        for i, color in enumerate(colors):
            if i < len(self.possible_values):
                chip_values[color] = self.possible_values[i]
            else:
                chip_values[color] = self.possible_values[-1]
        
        # Give minimal chips
        chips_per_player = dict.fromkeys(colors, 1)
        total_value = sum(chip_values[color] for color in colors)
        
        unused_chips = {}
        for color in colors:
            unused_chips[color] = max(0, chip_set.get_color_count(color) - 1)
        
        return ChipDistribution(
            chip_values=chip_values,
            chips_per_player=chips_per_player,
            total_value_per_player=total_value,
            unused_chips=unused_chips,
        )
