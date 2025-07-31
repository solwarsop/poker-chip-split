"""Tests for the poker chip split calculator."""

import pytest

from poker_chip_split.calculator import ChipSplitCalculator
from poker_chip_split.models import ChipSet


class TestChipSplitCalculator:
    """Test ChipSplitCalculator functionality."""

    def test_calculator_initialization(self) -> None:
        """Test calculator initialization with default values."""
        calculator = ChipSplitCalculator()
        
        expected_values = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0]
        assert calculator.possible_values == expected_values

    def test_calculator_with_custom_values(self) -> None:
        """Test calculator initialization with custom values."""
        custom_values = [0.5, 1.0, 5.0, 10.0]
        calculator = ChipSplitCalculator(custom_values=custom_values)
        
        assert calculator.possible_values == custom_values

    def test_simple_chip_split(self) -> None:
        """Test a simple chip split calculation."""
        # Simple case: 2 colors, even split
        chip_set = ChipSet(colors={"white": 40, "red": 20})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=10.0,
            num_players=2,
        )
        
        # Should have valid chip values
        assert len(distribution.chip_values) == 2
        assert "white" in distribution.chip_values
        assert "red" in distribution.chip_values
        
        # Should be reasonably close to target
        target_value = 10.0
        actual_value = distribution.get_player_value()
        error_percent = abs(actual_value - target_value) / target_value * 100
        assert error_percent <= 30.0  # Within 30% tolerance (more realistic for optimization)

    def test_efficiency_optimization(self) -> None:
        """Test that calculator optimizes for efficiency."""
        # Case with many chips available
        chip_set = ChipSet(colors={"white": 100, "red": 100, "green": 100})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=20.0,
            num_players=4,
        )
        
        # Should use a reasonable number of chips (not waste too many)
        efficiency = distribution.get_efficiency()
        assert efficiency > 10.0  # Should use at least 10% of available chips

    def test_fallback_distribution(self) -> None:
        """Test fallback when no optimal distribution is found."""
        # Impossible case: very few chips, high buy-in
        chip_set = ChipSet(colors={"white": 1, "red": 1})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=1000.0,
            num_players=10,
        )
        
        # Should still return a valid distribution (fallback)
        assert distribution is not None
        assert len(distribution.chip_values) == 2
        assert distribution.total_value_per_player > 0

    def test_single_color_chips(self):
        """Test calculation with only one color of chips."""
        chip_set = ChipSet(colors={"red": 50})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=10.0,
            num_players=2,
        )
        
        # Should use one of the available values for the single color
        assert distribution.chip_values["red"] in calculator.possible_values
        assert distribution.chips_per_player["red"] > 0
        assert distribution.get_total_unused_chips() >= 0

    def test_unique_chip_values(self):
        """Test that each chip color gets a unique value."""
        chip_set = ChipSet(colors={"white": 100, "red": 80, "green": 60, "black": 40})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=25.0,
            num_players=4,
        )
        
        # Check that all chip values are unique
        chip_values = list(distribution.chip_values.values())
        assert len(chip_values) == len(set(chip_values)), "All chip colors should have unique values"
        
        # Verify we have the expected number of different values
        assert len(chip_values) == 4

    def test_insufficient_chip_values_error(self):
        """Test that an error is raised when there aren't enough possible values for all colors."""
        chip_set = ChipSet(colors={"white": 100, "red": 80, "green": 60, "black": 40, "blue": 20})
        
        # Create calculator with fewer values than colors
        calculator = ChipSplitCalculator(custom_values=[1.0, 5.0])  # Only 2 values for 5 colors
        
        with pytest.raises(ValueError, match="Not enough chip values"):
            calculator.calculate_optimal_split(
                chip_set=chip_set,
                buy_in_per_person=20.0,
                num_players=4,
            )
