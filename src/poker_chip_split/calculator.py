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
    
    # Calculate scores for valid combinations - prioritize accuracy over chip count
    total_chips_per_player = np.sum(valid_combinations, axis=1)
    
    # Primary score: minimize error (accuracy is most important)
    # Secondary score: maximize chips (for tie-breaking)
    accuracy_scores = 1000.0 / (1.0 + valid_errors * 100)  # Higher for lower errors
    chip_count_scores = total_chips_per_player  # Linear bonus for more chips
    
    # Combine scores: accuracy is 100x more important than chip count
    scores = accuracy_scores * 100 + chip_count_scores
    
    # Find best combination in this batch
    best_idx = np.argmax(scores)
    best_combination = dict(zip(colors, valid_combinations[best_idx]))
    best_score = (accuracy_scores[best_idx], chip_count_scores[best_idx])

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
        
        # OPTIMIZATION 1: Sort colors by chip availability (least first for better pruning)
        colors_by_availability = sorted(
            colors, 
            key=lambda c: chip_set.get_color_count(c) // num_players
        )
        
        # OPTIMIZATION 2: Calculate theoretical bounds for early termination
        max_possible_chips = sum(
            chip_set.get_color_count(color) // num_players 
            for color in colors_by_availability
        )
        
        # OPTIMIZATION 3: Sort possible values by proximity to ideal target
        target_value_per_chip = buy_in_per_person / max_possible_chips
        sorted_values = sorted(
            self.possible_values,
            key=lambda v: abs(v - target_value_per_chip)
        )
        
        # Calculate total number of permutations for progress bar
        total_permutations = 1
        for i in range(len(colors)):
            total_permutations *= (len(self.possible_values) - i)
        
        logger.info(f"Evaluating up to {total_permutations:,} value permutations...")
        logger.info(f"Target value per chip: ${target_value_per_chip:.4f}")
        logger.info(f"Max possible chips per player: {max_possible_chips}")
        
        # OPTIMIZATION 4: Early termination criteria
        acceptable_error = buy_in_per_person * 0.01  # 1% error is excellent
        excellent_chip_threshold = max_possible_chips * 0.95  # 95% of max chips
        
        permutations_checked = 0
        pruned_count = 0
        
        # OPTIMIZATION 5: Try permutations starting with values closest to target
        for value_combination in tqdm(
            itertools.permutations(sorted_values, len(colors)), 
            total=total_permutations, 
            desc="Testing value combinations"
        ):
            permutations_checked += 1
            
            # Less aggressive pruning - only skip if completely unreasonable
            avg_value = sum(value_combination) / len(value_combination)
            if avg_value > buy_in_per_person or avg_value < 0.01:
                pruned_count += 1
                continue
            
            distribution = self._evaluate_distribution(
                chip_set, colors_by_availability, value_combination, buy_in_per_person, num_players,
            )
            
            if distribution is None:
                continue
                
            # Calculate total chips per player (secondary priority)
            total_chips_per_player = sum(distribution.chips_per_player.values())
            
            # Calculate error from target buy-in (primary priority)
            error = abs(distribution.total_value_per_player - buy_in_per_person)
            
            # Prioritize accuracy over chip count - same as batch evaluation
            accuracy_score = 1000.0 / (1.0 + error * 100)  # Higher for lower errors
            chip_count_score = total_chips_per_player  # Linear bonus for more chips
            
            # Combine scores: accuracy is 100x more important than chip count
            combined_score = accuracy_score * 100 + chip_count_score
            score = (accuracy_score, chip_count_score)
            
            if best_score is None or combined_score > (best_score[0] * 100 + best_score[1]):
                best_score = score
                best_distribution = distribution
                
                # OPTIMIZATION 7: Early termination for excellent solutions
                if (error <= acceptable_error and
                    total_chips_per_player >= excellent_chip_threshold):
                    logger.info(f"Excellent solution found after {permutations_checked:,} permutations!")
                    break
            
            # OPTIMIZATION 8: Stop if we've found a perfect solution
            if error == 0.0 and total_chips_per_player == max_possible_chips:
                logger.info(f"Perfect solution found after {permutations_checked:,} permutations!")
                break
        
        if best_distribution is None:
            logger.warning(f"No valid distribution found after {permutations_checked:,} permutations!")
            # Fallback: create a basic distribution if no optimal one found
            return self._create_fallback_distribution(chip_set, colors, buy_in_per_person)
        
        if pruned_count > 0:
            logger.info(f"Pruned {pruned_count:,} unpromising value combinations")
        logger.info(f"Checked {permutations_checked:,}/{total_permutations:,} permutations")
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
        
        # OPTIMIZATION 9: Limit search space for very large combinations
        total_combinations = 1
        for r in ranges:
            total_combinations *= len(r)
        
        # If combinations are too large, use smart sampling instead of exhaustive search
        max_combinations_threshold = 200_000  # Increased threshold for better solutions
        
        if total_combinations > max_combinations_threshold:
            logger.info(f"Large search space ({total_combinations:,} combinations), using smart sampling")
            return self._evaluate_distribution_sampled(
                colors, chip_values, max_chips_per_color, buy_in_per_person, num_players, chip_set
            )
        
        # Generate all combinations for smaller search spaces
        all_combinations = list(itertools.product(*ranges))
        
        # Determine optimal batch size and number of processes
        num_cores = mp.cpu_count()
        batch_size = max(1000, total_combinations // (num_cores * 4))  # At least 1000, but split across cores
        
        # Split combinations into batches
        batches = [
            all_combinations[i:i + batch_size]
            for i in range(0, len(all_combinations), batch_size)
        ]
        
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
        
        with mp.Pool(processes=num_cores) as pool:
            results = pool.map(evaluate_func, batches)
        
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

    def _evaluate_distribution_sampled(
        self,
        colors: list[str],
        chip_values: dict[str, float],
        max_chips_per_color: dict[str, int],
        buy_in_per_person: float,
        num_players: int,
        chip_set: ChipSet,
    ) -> ChipDistribution | None:
        """Evaluate distribution using smart sampling for large search spaces."""
        logger.info("  Using smart sampling strategy for large search space")
        
        best_combination = None
        best_score = None
        
        # Strategy 1: Start with balanced distribution (equal chips per color)
        base_chips_per_color = max(1, buy_in_per_person // sum(chip_values.values()) * len(colors))
        
        # Strategy 2: Target-based distribution (aim for specific buy-in)
        target_combinations = []
        
        # Generate some smart starting points
        for strategy in ["balanced", "high_value_focus", "low_value_focus"]:
            if strategy == "balanced":
                # Equal chips for each color
                combo = {color: min(base_chips_per_color, max_chips_per_color[color]) for color in colors}
            elif strategy == "high_value_focus":
                # More chips for higher value colors
                sorted_colors = sorted(colors, key=lambda c: chip_values[c], reverse=True)
                combo = {}
                remaining_value = buy_in_per_person
                for color in sorted_colors:
                    max_chips = max_chips_per_color[color]
                    value = chip_values[color]
                    target_chips = min(max_chips, max(1, int(remaining_value / (value * 2))))
                    combo[color] = target_chips
                    remaining_value -= target_chips * value
            else:  # low_value_focus
                # More chips for lower value colors
                sorted_colors = sorted(colors, key=lambda c: chip_values[c])
                combo = {}
                remaining_value = buy_in_per_person
                for color in sorted_colors:
                    max_chips = max_chips_per_color[color]
                    value = chip_values[color]
                    target_chips = min(max_chips, max(1, int(remaining_value / (value * 1.5))))
                    combo[color] = target_chips
                    remaining_value -= target_chips * value
            
            target_combinations.append(combo)
        
        # Strategy 3: Local search around promising points
        search_combinations = []
        for base_combo in target_combinations:
            # Add variations around each base combination
            for _ in range(100):  # Try 100 variations per base
                variant = base_combo.copy()
                # Randomly adjust 1-2 colors
                colors_to_adjust = np.random.choice(colors, size=min(2, len(colors)), replace=False)
                for color in colors_to_adjust:
                    current = variant[color]
                    max_val = max_chips_per_color[color]
                    # Random adjustment within bounds
                    adjustment = np.random.randint(-min(2, current - 1), min(3, max_val - current + 1))
                    variant[color] = max(1, min(max_val, current + adjustment))
                search_combinations.append(variant)
        
        # Evaluate all candidate combinations
        logger.info(f"  Evaluating {len(search_combinations)} candidate combinations")
        all_candidates = target_combinations + search_combinations
        
        for chips_per_player in tqdm(all_candidates, desc="  Smart sampling", leave=False):
            # Calculate total value per player
            total_value_per_player = sum(
                chips_per_player[color] * chip_values[color]
                for color in colors
            )
            
            # Check if this gets us close to the target buy-in
            error = abs(total_value_per_player - buy_in_per_person)
            max_acceptable_error = buy_in_per_person * 0.2  # 20% tolerance
            
            if error > max_acceptable_error:
                continue
            
            # Calculate total chips per player (what we want to maximize)
            total_chips_per_player = sum(chips_per_player.values())
            
            # Calculate score
            error_penalty = max(0, error - 0.25) * 100
            score = (total_chips_per_player * 10, -error_penalty)
            
            if best_score is None or score > best_score:
                best_score = score
                best_combination = chips_per_player.copy()
        
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
