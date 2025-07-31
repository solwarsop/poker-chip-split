"""YAML configuration file handling for poker chip split calculator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .models import ChipSet


# Default poker chip values in dollars
DEFAULT_CHIP_VALUES = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0]


@dataclass
class PokerConfig:
    """Configuration for a poker game chip split."""
    
    buy_in_per_person: float
    num_players: int
    chip_set: ChipSet
    chip_values: list[float] | None = None
    
    def get_chip_values(self) -> list[float]:
        """Get the chip values to use, either custom or default.
        
        Returns:
            List of chip values in dollars (always returns a copy)
        """
        if self.chip_values is not None:
            return self.chip_values.copy()
        return DEFAULT_CHIP_VALUES.copy()
    
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
        """
        try:
            buy_in_per_person = float(data["buy_in_per_person"])
            num_players = int(data["num_players"])
            
            # Parse chip colors and quantities
            chip_colors = data["chip_colors"]
            if not isinstance(chip_colors, dict):
                raise ValueError("chip_colors must be a dictionary")
            
            # Convert all values to integers and validate
            chip_set_data = {}
            for color, count in chip_colors.items():
                try:
                    chip_count = int(count)
                    if chip_count < 0:
                        raise ValueError(f"Chip count for {color} must be non-negative")
                    chip_set_data[str(color)] = chip_count
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid chip count for {color}: {count}") from e
            
            chip_set = ChipSet(colors=chip_set_data)
            
            # Parse optional chip values
            chip_values = None
            if "chip_values" in data:
                try:
                    chip_values = [float(value) for value in data["chip_values"]]
                    if not chip_values:
                        raise ValueError("chip_values cannot be empty")
                    if any(value <= 0 for value in chip_values):
                        raise ValueError("All chip values must be positive")
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid chip_values: {e}") from e
            
            return cls(
                buy_in_per_person=buy_in_per_person,
                num_players=num_players,
                chip_set=chip_set,
                chip_values=chip_values,
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
        
        data: dict[str, Any] = {
            "buy_in_per_person": self.buy_in_per_person,
            "num_players": self.num_players,
            "chip_colors": self.chip_set.colors,
        }
        
        # Include chip values if they are specified
        if self.chip_values is not None:
            data["chip_values"] = self.chip_values
        
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)


def create_example_config(file_path: str | Path) -> None:
    """Create an example configuration file.
    
    Args:
        file_path: Path where to create the example file
    """
    example_config = PokerConfig(
        buy_in_per_person=20.0,
        num_players=6,
        chip_set=ChipSet(colors={
            "white": 100,
            "red": 80,
            "green": 60,
            "black": 40,
            "blue": 20,
        }),
    )
    
    example_config.to_yaml_file(file_path)
