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
    num_players: int = 1  # number of players (added for efficiency calculation)
    
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
        # Calculate total chips available across all colors
        total_available_chips = 0
        total_used_chips = 0
        
        for color in self.chips_per_player:
            chips_per_player_this_color = self.chips_per_player[color]
            unused_this_color = self.unused_chips.get(color, 0)
            
            # Total available for this color = used by all players + unused
            total_used_this_color = chips_per_player_this_color * self.num_players
            total_available_this_color = total_used_this_color + unused_this_color
            
            total_available_chips += total_available_this_color
            total_used_chips += total_used_this_color
        
        if total_available_chips == 0:
            return 0.0
            
        return (total_used_chips / total_available_chips) * 100
