"""Configuration management for poker chip splits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .models import ChipSet


# Default poker chip values in dollars
DEFAULT_CHIP_VALUES = [0.05, 0.10, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]


@dataclass
class ChipColor:
    """Represents a chip color with its quantity and optional value.
    
    Attributes:
        count: Number of chips of this color available
        value: Value of each chip in dollars (None for calculate mode)
    
    """
    
    count: int
    value: float | None = None
    
    def __post_init__(self) -> None:
        """Validate chip color data.
        
        Raises:
            ValueError: If count is negative or value is non-positive
        
        """
        if self.count < 0:
            raise ValueError(f"Chip count must be non-negative, got {self.count}")
        if self.value is not None and self.value <= 0:
            raise ValueError(f"Chip value must be positive, got {self.value}")


@dataclass
class PokerConfig:
    """Configuration for a poker game chip split.
    
    Attributes:
        buy_in_per_person: Amount each player pays to buy in
        num_players: Number of players in the game
        chip_colors: Dictionary mapping color names to ChipColor objects
    
    """
    
    buy_in_per_person: float
    num_players: int
    chip_colors: dict[str, ChipColor]
    
    @property
    def chip_set(self) -> ChipSet:
        """Get the chip set from the color configuration.
        
        Returns:
            ChipSet: A ChipSet containing just the colors and counts
        
        """
        colors = {color: chip_color.count for color, chip_color in self.chip_colors.items()}
        return ChipSet(colors=colors)
    
    def get_chip_values(self) -> list[float]:
        """Get the chip values to use for calculate mode.
        
        Returns:
            List of default chip values in dollars
        
        """
        return DEFAULT_CHIP_VALUES.copy()
    
    def get_fixed_chip_values(self) -> dict[str, float]:
        """Get fixed chip values for distribute mode.
        
        Returns:
            Dictionary mapping color names to their fixed values
            
        Raises:
            ValueError: If any color doesn't have a value specified
        
        """
        result: dict[str, float] = {}
        missing_values: list[str] = []
        
        for color, chip_color in self.chip_colors.items():
            if chip_color.value is None:
                missing_values.append(color)
            else:
                result[color] = chip_color.value
        
        if missing_values:
            raise ValueError(
                f"Missing values for colors: {sorted(missing_values)}. "
                f"For 'distribute' mode, all colors must have values specified.",
            )
        
        return result
    
    def has_fixed_values(self) -> bool:
        """Check if all colors have fixed values defined.
        
        Returns:
            True if all colors have values, False otherwise
        
        """
        return all(chip_color.value is not None for chip_color in self.chip_colors.values())
    
    @classmethod
    def from_yaml_file(cls, file_path: str | Path) -> PokerConfig:
        """Load configuration from a YAML file.
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            PokerConfig instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the YAML format is invalid
        
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {file_path}: {e}") from e
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PokerConfig:
        """Create PokerConfig from a dictionary.
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            PokerConfig instance
            
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If data types are incorrect
        
        """
        try:
            buy_in_per_person = float(data["buy_in_per_person"])
            num_players = int(data["num_players"])
            
            # Parse chip colors and quantities
            chip_colors_data = data["chip_colors"]
            if not isinstance(chip_colors_data, dict):
                raise TypeError("chip_colors must be a dictionary")
            
            # Parse chip colors with optional values
            chip_colors: dict[str, ChipColor] = {}
            for color, color_data in chip_colors_data.items():
                color_str = str(color)
                
                if isinstance(color_data, (int, float)):
                    # Legacy format: just a count
                    chip_colors[color_str] = ChipColor(count=int(color_data))
                elif isinstance(color_data, dict):
                    # New format: dictionary with count and optional value
                    count = int(color_data["count"])  # type: ignore  # dict access validated above
                    value = None
                    if "value" in color_data:
                        value = float(color_data["value"])  # type: ignore  # dict access validated above
                    chip_colors[color_str] = ChipColor(count=count, value=value)
                else:
                    raise TypeError(
                        f"Invalid chip color data for {color}. "
                        f"Expected number (legacy) or dict with 'count' and optional 'value'",
                    )
            
            return cls(
                buy_in_per_person=buy_in_per_person,
                num_players=num_players,
                chip_colors=chip_colors,
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}") from e
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid configuration data: {e}") from e
    
    def to_yaml_file(self, file_path: str | Path) -> None:
        """Save configuration to a YAML file.
        
        Args:
            file_path: Path where to save the YAML file
        
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert chip colors to YAML format
        chip_colors_data: dict[str, Any] = {}
        for color, chip_color in self.chip_colors.items():
            if chip_color.value is not None:
                # New format with explicit count and value
                chip_colors_data[color] = {
                    "count": chip_color.count,
                    "value": chip_color.value,
                }
            else:
                # Legacy format: just count (for calculate mode)
                chip_colors_data[color] = chip_color.count
        
        data: dict[str, Any] = {
            "buy_in_per_person": self.buy_in_per_person,
            "num_players": self.num_players,
            "chip_colors": chip_colors_data,
        }
        
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)


def create_example_config(file_path: str | Path) -> None:
    """Create an example configuration file for calculate mode.
    
    Args:
        file_path: Path where to create the example file
    
    """
    chip_colors = {
        "white": ChipColor(count=100),
        "red": ChipColor(count=100),
        "green": ChipColor(count=100),
        "black": ChipColor(count=100),
        "blue": ChipColor(count=100),
    }
    
    example_config = PokerConfig(
        buy_in_per_person=5.0,
        num_players=9,
        chip_colors=chip_colors,
    )
    
    example_config.to_yaml_file(file_path)


def create_example_config_with_values(file_path: str | Path) -> None:
    """Create an example configuration file with fixed chip values for distribute mode.
    
    Args:
        file_path: Path where to create the example file
    
    """
    chip_colors = {
        "white": ChipColor(count=100, value=0.25),
        "red": ChipColor(count=100, value=0.10),
        "green": ChipColor(count=100, value=0.50),
        "black": ChipColor(count=100, value=0.05),
        "blue": ChipColor(count=100, value=1.00),
    }
    
    example_config = PokerConfig(
        buy_in_per_person=5.0,
        num_players=9,
        chip_colors=chip_colors,
    )
    
    example_config.to_yaml_file(file_path)
