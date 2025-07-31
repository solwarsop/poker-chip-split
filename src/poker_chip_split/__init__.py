"""Poker Chip Split Calculator.

A Python package for calculating optimal poker chip splits based on buy-in amounts
and available chip colors.
"""

__version__ = "0.1.0"

from .calculator import ChipSplitCalculator
from .models import ChipDistribution, ChipSet

__all__ = ["ChipDistribution", "ChipSet", "ChipSplitCalculator"]
