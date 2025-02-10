"""
🌙 Solana Dev's Base Strategy Class
All custom strategies should inherit from this
"""

class BaseStrategy:
    def __init__(self, name: str):
        self.name = name

    def generate_signals(self) -> dict:
        """
        Generate trading signals
        Returns:
            dict: {
                'token': str,          # Token address
                'signal': float,       # Signal strength (0-1)
                'direction': str,      # 'BUY', 'SELL', or 'NEUTRAL'
                'metadata': dict       # Optional strategy-specific data
            }
        """
        raise NotImplementedError("Strategy must implement generate_signals()") 