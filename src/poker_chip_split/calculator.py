"""Core calculator for optimal poker chip splits."""

from __future__ import annotations

import itertools
import logging
import multiprocessing as mp
from functools import partial
from typing import Optional

import numpy as np
from tqdm import tqdm

from .models import ChipDistribution, ChipSet

# Set up logging
logger = logging.getLogger(__name__)

# Default poker chip values in dollars - moved here for consistency
DEFAULT_CHIP_VALUES = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0]


def _evaluate_combinations_batch(
    combinations_batch: list[tuple[int, ...]],
    colors: list[str],
    chip_values: dict[str, float],
    buy_in_per_person: float,
) -> tuple[Optional[dict[str, int]], Optional[tuple[float, float]]]:
    """Evaluate a batch of chip combinations in parallel.
    
    Args:
        combinations_batch: List of combinations to evaluate
        colors: List of chip colors
        chip_values: Mapping of colors to values
        buy_in_per_person: Target buy-in per person
        
    Returns:
        Tuple of (best_combination, best_score) for this batch
    """
    best_combination = None
    best_score = None
    
    # Convert to numpy arrays for vectorized operations
    combinations_array = np.array(combinations_batch)
    values_array = np.array([chip_values[color] for color in colors])
    
    # Vectorized calculations
    total_values_per_player = np.sum(combinations_array * values_array, axis=1)
    errors = np.abs(total_values_per_player - buy_in_per_person)
    max_acceptable_error = buy_in_per_person * 0.2
    
    # Filter combinations within acceptable error
    valid_mask = errors <= max_acceptable_error
    if not np.any(valid_mask):
        return None, None
    
    valid_combinations = combinations_array[valid_mask]
    valid_errors = errors[valid_mask]
    
    # Calculate scores for valid combinations
    total_chips_per_player = np.sum(valid_combinations, axis=1)
    error_penalties = np.maximum(0, valid_errors - 0.25) * 100
    scores = total_chips_per_player * 10 - error_penalties
    
    # Find best combination in this batch
    best_idx = np.argmax(scores)
    best_combination = dict(zip(colors, valid_combinations[best_idx]))
    best_score = (total_chips_per_player[best_idx] * 10, -error_penalties[best_idx])
    
    return best_combination, best_score


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
        colors = list(chip_set.colors.keys())
        
        best_distribution = None
        best_score = None
        
        # Ensure we have enough possible values for all colors
        if len(self.possible_values) < len(colors):
            raise ValueError(
                f"Not enough chip values ({len(self.possible_values)}) for all colors ({len(colors)}). "
                f"Need at least {len(colors)} different values.",
            )
        
        # Calculate total number of permutations for progress bar
        total_permutations = 1
        for i in range(len(colors)):
            total_permutations *= (len(self.possible_values) - i)
        
        logger.info(f"Starting evaluation of {total_permutations:,} value permutations...")
        
        # Try all possible permutations of values for the available colors
        # Use permutations to ensure each color gets a unique value
        permutations = itertools.permutations(self.possible_values, len(colors))
        
        # Show progress bar for value combinations
        progress_bar = tqdm(
            permutations,
            total=total_permutations,
            desc="Testing value combinations",
            unit="permutation",
        )
        
        for value_combination in progress_bar:
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
    ) -> ChipDistribution | None:
        """Evaluate a specific value assignment for colors using parallel exhaustive search."""
        # Create value mapping
        chip_values = dict(zip(colors, values))
        
        # Calculate max chips per player for each color (constraint: all colors used)
        max_chips_per_color = {}
        for color in colors:
            available_chips = chip_set.get_color_count(color)
            max_per_player = available_chips // num_players
            
            if max_per_player == 0:
                return None  # Not enough chips of this color for all players
            
            max_chips_per_color[color] = max_per_player
        
        # Create ranges for each color (1 to max_chips_per_player)
        ranges = [range(1, max_chips_per_color[color] + 1) for color in colors]
        
        # Calculate total combinations
        total_combinations = 1
        for r in ranges:
            total_combinations *= len(r)
        
        logger.debug(f"  Evaluating {total_combinations:,} chip combinations for values {values}")
        
        # Generate all combinations
        all_combinations = list(itertools.product(*ranges))
        
        # Determine optimal batch size and number of processes
        num_cores = mp.cpu_count()
        batch_size = max(1000, total_combinations // (num_cores * 4))  # At least 1000, but split across cores
        
        # Split combinations into batches
        batches = [
            all_combinations[i:i + batch_size]
            for i in range(0, len(all_combinations), batch_size)
        ]
        
        logger.debug(f"  Using {num_cores} cores with {len(batches)} batches of ~{batch_size} combinations each")
        
        # Create partial function for parallel processing
        evaluate_func = partial(
            _evaluate_combinations_batch,
            colors=colors,
            chip_values=chip_values,
            buy_in_per_person=buy_in_per_person,
        )
        
        # Process batches in parallel
        best_combination = None
        best_score = None
        
        logger.debug(f"  Starting parallel processing with {len(batches)} batches")
        
        with mp.Pool(processes=num_cores) as pool:
            # Use map instead of imap for better reliability with tqdm
            if logger.isEnabledFor(logging.DEBUG):
                # Only show progress bar in debug mode to avoid interference
                results = list(tqdm(
                    pool.map(evaluate_func, batches),
                    total=len(batches),
                    desc="  Processing batches",
                    leave=False,
                ))
            else:
                results = pool.map(evaluate_func, batches)
        
        logger.debug(f"  Completed parallel processing, analyzing {len(results)} batch results")
        
        # Find the best result across all batches
        for combination, score in results:
            if combination is not None and score is not None and (best_score is None or score > best_score):
                best_score = score
                best_combination = combination
        
        if best_combination is None:
            return None
        
        # Calculate unused chips for the best combination
        unused_chips = {}
        for color in colors:
            used_chips = best_combination[color] * num_players
            unused_chips[color] = chip_set.get_color_count(color) - used_chips
        
        # Calculate final total value per player
        total_value_per_player = sum(
            best_combination[color] * chip_values[color]
            for color in colors
        )
        
        return ChipDistribution(
            chip_values=chip_values,
            chips_per_player=best_combination,
            total_value_per_player=total_value_per_player,
            unused_chips=unused_chips,
        )

    def _create_fallback_distribution(
        self,
        chip_set: ChipSet,
        colors: list[str],
        buy_in_per_person: float,  # noqa: ARG002
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
