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
        best_score = None
        
        # Ensure we have enough possible values for all colors
        if len(self.possible_values) < len(colors):
            raise ValueError(
                f"Not enough chip values ({len(self.possible_values)}) for all colors ({len(colors)}). "
                f"Need at least {len(colors)} different values."
            )
        
        # Try all possible permutations of values for the available colors
        # Use permutations to ensure each color gets a unique value
        for value_combination in itertools.permutations(self.possible_values, len(colors)):
            distribution = self._evaluate_distribution(
                chip_set, colors, value_combination, buy_in_per_person, num_players,
            )
            
            if distribution is None:
                continue
                
            # Calculate total chips per player (what we want to maximize)
            total_chips_per_player = sum(distribution.chips_per_player.values())
            
            # Calculate error from target buy-in (what we want to minimize)
            error = abs(distribution.total_value_per_player - buy_in_per_person)
            
            # Prefer distributions with more chips per player and less error
            # Heavily favor total chips per player for better poker gameplay
            # Only penalize error if it's significant (>5%)
            error_penalty = max(0, error - 0.25) * 100  # Only penalize errors above $0.25
            score = (total_chips_per_player * 10, -error_penalty)  # Heavily weight chip count
            
            if best_score is None or score > best_score:
                best_score = score
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
        
        # STEP 1: Ensure all colors are used (give at least 1 chip of each color)
        for color in colors:
            available_chips = chip_set.get_color_count(color)
            max_chips_per_player = available_chips // num_players
            
            if max_chips_per_player == 0:
                return None  # Not enough chips of this color for all players
            
            # Give at least 1 chip of each color to each player
            chips_per_player[color] = 1
            total_value_per_player += chip_values[color]
        
        # STEP 2: Allocate remaining value using greedy approach
        # Sort colors by value (highest first) for efficient allocation
        sorted_colors = sorted(colors, key=lambda c: chip_values[c], reverse=True)
        
        remaining_value = buy_in_per_person - total_value_per_player
        
        for color in sorted_colors:
            if remaining_value <= 0:
                break
                
            value = chip_values[color]
            available_chips = chip_set.get_color_count(color)
            max_chips_per_player = available_chips // num_players
            current_chips = chips_per_player[color]
            
            # Calculate how many additional chips of this color each player should get
            additional_chips_needed = int(remaining_value // value)
            additional_chips_possible = max_chips_per_player - current_chips
            additional_chips = min(additional_chips_needed, additional_chips_possible)
            
            if additional_chips > 0:
                chips_per_player[color] += additional_chips
                total_value_per_player += additional_chips * value
                remaining_value -= additional_chips * value
        
        # Calculate unused chips
        unused_chips = {}
        for color in colors:
            used_chips = chips_per_player.get(color, 0) * num_players
            unused_chips[color] = chip_set.get_color_count(color) - used_chips
        
        # Check if this distribution is reasonable (gets close to buy-in amount)
        value_error = abs(total_value_per_player - buy_in_per_person)
        max_acceptable_error = buy_in_per_person * 0.2  # 20% tolerance (increased for constraint)
        
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
        # Assign unique values to colors (first N values for N colors)
        chip_values = {}
        for i, color in enumerate(colors):
            if i < len(self.possible_values):
                chip_values[color] = self.possible_values[i]
            else:
                # If we run out of values, use the highest available value
                # This shouldn't happen due to the check in calculate_optimal_split
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
