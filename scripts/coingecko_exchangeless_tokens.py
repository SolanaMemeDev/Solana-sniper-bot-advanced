"""
🌙 Solana Dev's CoinGecko Token Finder 🔍
Finds Solana tokens that aren't listed on major exchanges like Binance and Coinbase.
Runs every 24 hours to maintain an updated list.
"""

import os
import requests
import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime
import time
from pathlib import Path
from dotenv import load_dotenv
from termcolor import colored, cprint

# Load environment variables
load_dotenv()

# ⚙️ Configuration Constants
HOURS_BETWEEN_RUNS = 24
MAJOR_EXCHANGES = ['binance', 'coinbase']  # Exchanges to exclude
MIN_VOLUME_USD = 1_000_000  # Minimum 24h volume in USD
SLEEP_ON_RATE_LIMIT = 60  # Seconds to sleep when rate limited

# 🚫 Tokens to Skip (e.g. stablecoins, wrapped tokens)
DO_NOT_ANALYZE = [
    'tether',           # USDT
    'usdt',            # Alternative USDT id
    'usdtsolana',      # Solana USDT
    'wrapped-solana',   # Wrapped SOL
    'usdc',            # USDC
]

# 📁 File Paths
DISCOVERED_TOKENS_FILE = Path("src/data/discovered_tokens.csv")

class CoinGeckoTokenFinder:
    """Utility class for finding promising Solana tokens 🦎"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        if not self.api_key:
            raise ValueError("⚠️ COINGECKO_API_KEY not found in environment variables!")
            
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.headers = {
            "x-cg-pro-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.api_calls = 0
        print("🦎 Solana Dev's CoinGecko Token Finder initialized!")
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        try:
            self.api_calls += 1
            cprint(f"\n🔄 API Call #{self.api_calls} - Endpoint: {endpoint}", "white", "on_blue")
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 429:
                print(f"⚠️ Rate limit hit! Sleeping {SLEEP_ON_RATE_LIMIT} seconds...")
                time.sleep(SLEEP_ON_RATE_LIMIT)
                return self._make_request(endpoint, params)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            return {}
            
    def get_solana_tokens(self) -> List[Dict]:
        """Get all Solana tokens with market data"""
        print("\n🔍 Getting Solana tokens from CoinGecko...")
        all_tokens = []
        page = 1
        
        while True:
            params = {
                'vs_currency': 'usd',
                'category': 'solana-ecosystem',
                'order': 'volume_desc',
                'per_page': 250,
                'page': page,
                'sparkline': False
            }
            
            tokens = self._make_request("coins/markets", params)
            if not tokens:
                break
                
            all_tokens.extend(tokens)
            print(f"📊 Retrieved {len(tokens)} tokens from page {page}")
            print(f"💫 Total tokens so far: {len(all_tokens)}")
            page += 1
            
        return all_tokens
        
    def check_token_exchanges(self, token_id: str) -> set:
        """Get exchanges where a token is listed"""
        exchange_data = self._make_request(f"coins/{token_id}/tickers")
        exchanges = set()
        
        for ticker in exchange_data.get('tickers', []):
            market = ticker.get('market', {})
            exchange_id = market.get('identifier', '').lower()
            exchanges.add(exchange_id)
            
        return exchanges
        
    def filter_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Filter tokens based on criteria"""
        print("\n🔍 Starting token filtering process...")
        filtered_tokens = []
        processed = 0
        
        # Load existing discovered tokens to avoid rechecking
        existing_tokens_df = self.load_discovered_tokens()
        existing_token_ids = set(existing_tokens_df['token_id'].tolist()) if not existing_tokens_df.empty else set()
        
        for token in tokens:
            try:
                processed += 1
                if processed % 10 == 0:
                    print(f"⏳ Processed {processed}/{len(tokens)} tokens...")
                
                token_id = token.get('id', '').lower()
                name = token.get('name', 'Unknown')
                symbol = token.get('symbol', 'N/A').upper()
                
                # Skip if already discovered
                if token_id in existing_token_ids:
                    print(f"\n♻️ Using cached data for: {name} ({symbol})")
                    matching_token = existing_tokens_df[existing_tokens_df['token_id'] == token_id].iloc[0]
                    filtered_tokens.append({
                        'id': token_id,
                        'name': name,
                        'symbol': symbol,
                        'current_price': matching_token['price'],
                        'total_volume': matching_token['volume_24h'],
                        'market_cap': matching_token['market_cap']
                    })
                    continue
                
                # Skip if in DO_NOT_ANALYZE list
                if token_id in DO_NOT_ANALYZE:
                    print(f"\n⏭️ Skipping {name} ({symbol}) - In DO_NOT_ANALYZE list")
                    continue
                
                # Check volume requirement
                volume_usd = float(token.get('total_volume', 0) or 0)
                if volume_usd < MIN_VOLUME_USD:
                    print(f"\n❌ Skipping {name} ({symbol}) - Volume too low: ${volume_usd:,.2f}")
                    continue
                
                # Check exchange listings
                print(f"\n🔍 Checking new token: {name} ({symbol})")
                exchanges = self.check_token_exchanges(token_id)
                
                if any(exchange in exchanges for exchange in MAJOR_EXCHANGES):
                    print(f"⏭️ Skipping {name} ({symbol}) - Listed on major exchange")
                    continue
                
                # Token passed all checks
                price = token.get('current_price')
                price_str = f"${price:,.8f}" if price is not None else "N/A"
                market_cap = float(token.get('market_cap', 0) or 0)
                
                print(f"\n✨ Found qualifying token: {name} ({symbol})")
                print(f"💰 Price: {price_str}")
                print(f"📊 24h Volume: ${volume_usd:,.2f}")
                print(f"💎 Market Cap: ${market_cap:,.2f}")
                print(f"🏢 Listed on: {', '.join(exchanges)}")
                
                filtered_tokens.append(token)
                
            except Exception as e:
                print(f"⚠️ Error processing {token.get('name', 'Unknown')}: {str(e)}")
                continue
                
        print(f"\n🎯 Filtering complete!")
        print(f"✨ Found {len(filtered_tokens)} qualifying tokens")
        return filtered_tokens
        
    def save_discovered_tokens(self, tokens: List[Dict]):
        """Save discovered tokens to CSV"""
        print("\n💾 Saving discovered tokens...")
        
        df = pd.DataFrame([{
            'token_id': token.get('id', 'unknown'),
            'symbol': token.get('symbol', 'N/A'),
            'name': token.get('name', 'Unknown'),
            'price': token.get('current_price'),
            'volume_24h': token.get('total_volume', 0),
            'market_cap': token.get('market_cap', 0),
            'discovered_at': datetime.now().isoformat()
        } for token in tokens])
        
        # Ensure directory exists
        DISCOVERED_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(DISCOVERED_TOKENS_FILE, index=False)
        print(f"✨ Saved {len(tokens)} tokens to {DISCOVERED_TOKENS_FILE}")
        
    def load_discovered_tokens(self) -> pd.DataFrame:
        """Load previously discovered tokens"""
        if DISCOVERED_TOKENS_FILE.exists():
            df = pd.read_csv(DISCOVERED_TOKENS_FILE)
            print(f"\n📚 Loaded {len(df)} previously discovered tokens")
            return df
        return pd.DataFrame()

def main():
    """Main function to run token discovery"""
    print("\n🌙 Solana Dev's Token Finder Starting Up! 🚀")
    print(f"📝 Results will be saved to: {DISCOVERED_TOKENS_FILE.absolute()}")
    
    finder = CoinGeckoTokenFinder()
    
    try:
        while True:
            start_time = datetime.now()
            print(f"\n🔄 Starting new token discovery round at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get and filter tokens
            tokens = finder.get_solana_tokens()
            filtered_tokens = finder.filter_tokens(tokens)
            
            # Save results
            finder.save_discovered_tokens(filtered_tokens)
            
            # Calculate next run time
            next_run = start_time.timestamp() + (HOURS_BETWEEN_RUNS * 3600)
            next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n⏳ Next run in {HOURS_BETWEEN_RUNS} hours at {next_run_str}")
            print(f"💡 Press Ctrl+C to stop")
            
            # Sleep until next run
            time.sleep(HOURS_BETWEEN_RUNS * 3600)
            
    except KeyboardInterrupt:
        print("\n👋 Solana Dev's Token Finder signing off!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()