"""Tests for the poker chip split calculator."""

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

    def test_single_color_chips(self) -> None:
        """Test with only one color of chips."""
        chip_set = ChipSet(colors={"blue": 50})
        calculator = ChipSplitCalculator()
        
        distribution = calculator.calculate_optimal_split(
            chip_set=chip_set,
            buy_in_per_person=25.0,
            num_players=2,
        )
        
        assert len(distribution.chip_values) == 1
        assert "blue" in distribution.chip_values
        assert distribution.chip_values["blue"] > 0
