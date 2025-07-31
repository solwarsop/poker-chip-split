"""Data models for poker chip split calculations."""

from dataclasses import dataclass


@dataclass
class ChipSet:
    """Represents a set of poker chips with their colors and quantities."""
    
    colors: dict[str, int]  # color name -> number of chips
    
    def total_chips(self) -> int:
        """Return the total number of chips across all colors."""
        return sum(self.colors.values())
    
    def get_color_count(self, color: str) -> int:
        """Get the number of chips for a specific color."""
        return self.colors.get(color, 0)


@dataclass
class ChipDistribution:
    """Represents the distribution of chip values and quantities per player."""
    
    chip_values: dict[str, float]  # color -> value
    chips_per_player: dict[str, int]  # color -> quantity per player
    total_value_per_player: float
    unused_chips: dict[str, int]  # color -> unused quantity
    
    def get_player_value(self) -> float:
        """Calculate the total value each player receives."""
        return sum(
            value * count
            for value, count in zip(
                self.chip_values.values(),
                self.chips_per_player.values(),
            )
        )
    
    def get_total_unused_chips(self) -> int:
        """Get the total number of unused chips."""
        return sum(self.unused_chips.values())
    
    def get_efficiency(self) -> float:
        """Calculate the efficiency as percentage of chips used."""
        total_chips = sum(self.chips_per_player.values()) + sum(self.unused_chips.values())
        if total_chips == 0:
            return 0.0
        used_chips = sum(self.chips_per_player.values())
        return (used_chips / total_chips) * 100
