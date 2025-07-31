"""Tests for the poker chip split configuration module."""

import pytest
import tempfile
import yaml
from pathlib import Path

from poker_chip_split.config import PokerConfig, DEFAULT_CHIP_VALUES
from poker_chip_split.models import ChipSet


class TestPokerConfig:
    """Test suite for PokerConfig class."""

    def test_config_creation_with_defaults(self):
        """Test creating config with minimal required fields."""
        config = PokerConfig(
            buy_in_per_person=20.0,
            num_players=6,
            chip_set=ChipSet({"white": 100, "red": 80, "green": 60}),
        )
        
        assert config.buy_in_per_person == 20.0
        assert config.num_players == 6
        assert config.chip_values is None
        assert config.get_chip_values() == DEFAULT_CHIP_VALUES

    def test_config_creation_with_custom_chip_values(self):
        """Test creating config with custom chip values."""
        custom_values = [0.5, 1.0, 3.0, 15.0]
        config = PokerConfig(
            buy_in_per_person=25.0,
            num_players=4,
            chip_set=ChipSet({"white": 80, "red": 60}),
            chip_values=custom_values,
        )
        
        assert config.chip_values == custom_values
        assert config.get_chip_values() == custom_values

    def test_from_dict_minimal_config(self):
        """Test creating config from dictionary with minimal fields."""
        config_dict = {
            "buy_in_per_person": 15.0,
            "num_players": 8,
            "chip_colors": {"white": 120, "red": 100}
        }
        
        config = PokerConfig.from_dict(config_dict)
        
        assert config.buy_in_per_person == 15.0
        assert config.num_players == 8
        assert config.chip_values is None
        assert config.get_chip_values() == DEFAULT_CHIP_VALUES
        assert isinstance(config.chip_set, ChipSet)

    def test_from_dict_with_chip_values(self):
        """Test creating config from dictionary with custom chip values."""
        custom_values = [0.1, 0.5, 2.5, 10.0]
        config_dict = {
            "buy_in_per_person": 30.0,
            "num_players": 5,
            "chip_colors": {"white": 150, "red": 120, "green": 80},
            "chip_values": custom_values
        }
        
        config = PokerConfig.from_dict(config_dict)
        
        assert config.chip_values == custom_values
        assert config.get_chip_values() == custom_values

    def test_from_dict_invalid_chip_values(self):
        """Test that invalid chip values raise ValueError."""
        config_dict = {
            "buy_in_per_person": 20.0,
            "num_players": 4,
            "chip_colors": {"white": 100},
            "chip_values": [0.5, -1.0, 2.0]  # Negative value should be invalid
        }
        
        with pytest.raises(ValueError, match="All chip values must be positive"):
            PokerConfig.from_dict(config_dict)

    def test_from_dict_zero_chip_value(self):
        """Test that zero chip values raise ValueError."""
        config_dict = {
            "buy_in_per_person": 20.0,
            "num_players": 4,
            "chip_colors": {"white": 100},
            "chip_values": [0.5, 0.0, 2.0]  # Zero value should be invalid
        }
        
        with pytest.raises(ValueError, match="All chip values must be positive"):
            PokerConfig.from_dict(config_dict)

    def test_from_file_minimal_yaml(self):
        """Test loading config from YAML file without chip values."""
        config_data = {
            "buy_in_per_person": 25.0,
            "num_players": 6,
            "chip_colors": {
                "white": 100,
                "red": 80,
                "green": 60
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = PokerConfig.from_yaml_file(temp_path)
            
            assert config.buy_in_per_person == 25.0
            assert config.num_players == 6
            assert config.chip_values is None
            assert config.get_chip_values() == DEFAULT_CHIP_VALUES
        finally:
            Path(temp_path).unlink()

    def test_from_file_with_chip_values(self):
        """Test loading config from YAML file with custom chip values."""
        custom_values = [0.5, 1.0, 3.0, 15.0]
        config_data = {
            "buy_in_per_person": 25.0,
            "num_players": 4,
            "chip_colors": {
                "white": 80,
                "red": 60,
                "green": 40,
                "black": 30
            },
            "chip_values": custom_values
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = PokerConfig.from_yaml_file(temp_path)
            
            assert config.buy_in_per_person == 25.0
            assert config.num_players == 4
            assert config.chip_values == custom_values
            assert config.get_chip_values() == custom_values
        finally:
            Path(temp_path).unlink()

    def test_to_dict_without_chip_values(self):
        """Test converting config to dictionary without chip values."""
        config = PokerConfig(
            buy_in_per_person=20.0,
            num_players=6,
            chip_set=ChipSet({"white": 100, "red": 80}),
        )
        
        # Use to_yaml_file to create a temp file, then read it back
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.to_yaml_file(temp_path)
            
            with open(temp_path, 'r') as f:
                result = yaml.safe_load(f)
            
            expected = {
                "buy_in_per_person": 20.0,
                "num_players": 6,
                "chip_colors": {"white": 100, "red": 80},
            }
            
            assert result == expected
        finally:
            Path(temp_path).unlink()

    def test_to_dict_with_chip_values(self):
        """Test converting config to dictionary with chip values."""
        custom_values = [0.25, 1.0, 5.0]
        config = PokerConfig(
            buy_in_per_person=20.0,
            num_players=6,
            chip_set=ChipSet({"white": 100, "red": 80, "green": 60}),
            chip_values=custom_values,
        )
        
        # Use to_yaml_file to create a temp file, then read it back
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.to_yaml_file(temp_path)
            
            with open(temp_path, 'r') as f:
                result = yaml.safe_load(f)
            
            expected = {
                "buy_in_per_person": 20.0,
                "num_players": 6,
                "chip_colors": {"white": 100, "red": 80, "green": 60},
                "chip_values": custom_values,
            }
            
            assert result == expected
        finally:
            Path(temp_path).unlink()

    def test_default_chip_values_constant(self):
        """Test that DEFAULT_CHIP_VALUES contains expected values."""
        expected_values = [0.05, 0.10, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
        assert DEFAULT_CHIP_VALUES == expected_values

    def test_get_chip_values_returns_copy(self):
        """Test that get_chip_values returns a copy, not the original list."""
        custom_values = [1.0, 5.0, 10.0]
        config = PokerConfig(
            buy_in_per_person=20.0,
            num_players=4,
            chip_set=ChipSet({"white": 100}),
            chip_values=custom_values,
        )
        
        returned_values = config.get_chip_values()
        returned_values.append(999.0)  # Modify the returned list
        
        # Original should be unchanged
        assert config.chip_values == custom_values
        assert 999.0 not in config.chip_values
