"""
CooRPost - Coordinated Post Detection for Facebook and Social Media

This package provides tools for detecting and analyzing coordinated behavior
on social media platforms, particularly Facebook.

Main modules:
    - detect: Core coordination detection algorithms
    - network: Network generation and analysis
    - stats: Statistical analysis functions
    - utils: Utility functions for data preparation
    - viz: Visualization tools
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .detect import detect_groups
from .network import generate_coordinated_network
from .stats import account_stats, group_stats, network_summary
from .utils import prep_data, compute_image_hash
from .viz import visualize_network

__all__ = [
    "detect_groups",
    "generate_coordinated_network",
    "account_stats",
    "group_stats",
    "network_summary",
    "prep_data",
    "compute_image_hash",
    "visualize_network",
]
