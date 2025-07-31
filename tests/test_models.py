"""Tests for poker chip split models."""

import pytest

from poker_chip_split.models import ChipDistribution, ChipSet


class TestChipSet:
    """Test ChipSet functionality."""

    def test_chip_set_creation(self) -> None:
        """Test creating a chip set."""
        colors = {"white": 100, "red": 50, "green": 25}
        chip_set = ChipSet(colors=colors)
        
        assert chip_set.colors == colors
        assert chip_set.total_chips() == 175
    
    def test_get_color_count(self) -> None:
        """Test getting chip count for specific colors."""
        chip_set = ChipSet(colors={"white": 100, "red": 50})
        
        assert chip_set.get_color_count("white") == 100
        assert chip_set.get_color_count("red") == 50
        assert chip_set.get_color_count("blue") == 0  # Non-existent color


class TestChipDistribution:
    """Test ChipDistribution functionality."""

    def test_chip_distribution_creation(self) -> None:
        """Test creating a chip distribution."""
        distribution = ChipDistribution(
            chip_values={"white": 0.25, "red": 1.0},
            chips_per_player={"white": 20, "red": 5},
            total_value_per_player=10.0,
            unused_chips={"white": 10, "red": 0},
        )
        
        assert distribution.chip_values == {"white": 0.25, "red": 1.0}
        assert distribution.chips_per_player == {"white": 20, "red": 5}
        assert distribution.total_value_per_player == 10.0
    
    def test_get_player_value(self) -> None:
        """Test calculating player value."""
        distribution = ChipDistribution(
            chip_values={"white": 0.25, "red": 1.0},
            chips_per_player={"white": 20, "red": 5},
            total_value_per_player=10.0,
            unused_chips={"white": 10, "red": 0},
        )
        
        # 20 * 0.25 + 5 * 1.0 = 5 + 5 = 10
        assert distribution.get_player_value() == 10.0
    
    def test_get_total_unused_chips(self) -> None:
        """Test calculating total unused chips."""
        distribution = ChipDistribution(
            chip_values={"white": 0.25, "red": 1.0},
            chips_per_player={"white": 20, "red": 5},
            total_value_per_player=10.0,
            unused_chips={"white": 10, "red": 5},
        )
        
        assert distribution.get_total_unused_chips() == 15
    
    def test_get_efficiency(self) -> None:
        """Test calculating efficiency."""
        distribution = ChipDistribution(
            chip_values={"white": 0.25, "red": 1.0},
            chips_per_player={"white": 20, "red": 5},  # 25 used
            total_value_per_player=10.0,
            unused_chips={"white": 10, "red": 5},  # 15 unused
        )
        
        # 25 used out of 40 total = 62.5%
        assert distribution.get_efficiency() == 62.5
    
    def test_efficiency_with_no_chips(self) -> None:
        """Test efficiency calculation with zero chips."""
        distribution = ChipDistribution(
            chip_values={},
            chips_per_player={},
            total_value_per_player=0.0,
            unused_chips={},
        )
        
        assert distribution.get_efficiency() == 0.0
