"""
🌙 Solana Dev's Strategies Package
"""

from .base_strategy import BaseStrategy

# We only need to export BaseStrategy - custom strategies will be loaded dynamically
__all__ = ['BaseStrategy'] 