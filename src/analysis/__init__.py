"""
Image analysis and comparison functionality.

This module provides tools for analyzing image differences using AI
and performing automated image comparisons.
"""

from .image_analyzer import OpenRouterClient, ImageAnalyzer
from .comparison import generate_comparison

__all__ = ['OpenRouterClient', 'ImageAnalyzer', 'generate_comparison']
