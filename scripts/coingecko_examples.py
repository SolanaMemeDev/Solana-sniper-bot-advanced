"""
🦎 Solana Dev's CoinGecko API Examples
All API endpoints with easy toggle functionality

Created by Solana Dev 🌙
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://pro-api.coingecko.com/api/v3"
RESULTS_DIR = Path("src/data/coingecko_results")

# Create results directory
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Toggle which endpoints to test
ENABLED_TESTS = {
    # Basic endpoints
    "ping": True,                    # Check API server status
    "api_usage": True,              # Check account's API usage
    
    # Simple endpoints
    "simple_price": True,           # Get current prices
    "token_price": True,            # Get token prices on a platform
    "supported_currencies": True,    # Get supported vs currencies
    
    # Coins endpoints
    "coins_list": True,             # Get list of all coins
    "coins_markets": True,          # Get market data
    "coin_data": True,              # Get data for a specific coin
    "coin_tickers": True,           # Get trading data
    "coin_history": True,           # Get historical data
    "coin_market_chart": True,      # Get market chart data
    "coin_ohlc": True,              # Get OHLC data
    
    # Exchange endpoints
    "exchanges_list": True,         # Get list of exchanges
    "exchange_rates": True,         # Get exchange rates
    
    # Global endpoints
    "global_data": True,            # Get global crypto data
    "global_defi": True,            # Get global DeFi data
    "global_market_cap": True,      # Get historical market cap
    
    # Search endpoints
    "search": True,                 # Search for coins/exchanges
    "trending": True,               # Get trending coins
    
    # Other endpoints
    "asset_platforms": True,        # Get list of asset platforms
    "companies_holdings": True,     # Get company holdings
}

class CoinGeckoExamples:
    """Class to demonstrate all CoinGecko API endpoints"""
    
    def __init__(self):
        self.headers = {
            "x-cg-pro-api-key": COINGECKO_API_KEY,
            "Content-Type": "application/json"
        }
        print("🦎 Solana Dev's CoinGecko Examples Initialized!")
        
    def save_response(self, endpoint: str, response: dict):
        """Save API response to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{endpoint}_{timestamp}.json"
        filepath = RESULTS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(response, f, indent=2)
        print(f"💾 Saved {endpoint} response to {filepath}")
        
    def make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request with error handling"""
        try:
            url = f"{BASE_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            
            print(f"\n🔍 Testing endpoint: {endpoint}")
            print(f"URL: {url}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.save_response(endpoint.replace('/', '_'), data)
                return data
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {str(e)}")
            return None
            
    def test_ping(self):
        """Test /ping endpoint"""
        if not ENABLED_TESTS["ping"]:
            return
        return self.make_request("ping")
        
    def test_api_usage(self):
        """Test /key endpoint"""
        if not ENABLED_TESTS["api_usage"]:
            return
        return self.make_request("key")
        
    def test_simple_price(self):
        """Test /simple/price endpoint"""
        if not ENABLED_TESTS["simple_price"]:
            return
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd,eur",
            "include_24hr_vol": True,
            "include_24hr_change": True
        }
        return self.make_request("simple/price", params)
        
    def test_token_price(self):
        """Test /simple/token_price endpoint"""
        if not ENABLED_TESTS["token_price"]:
            return
        params = {
            "contract_addresses": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI token
            "vs_currencies": "usd,eth"
        }
        return self.make_request("simple/token_price/ethereum", params)
        
    def test_supported_currencies(self):
        """Test /simple/supported_vs_currencies endpoint"""
        if not ENABLED_TESTS["supported_currencies"]:
            return
        return self.make_request("simple/supported_vs_currencies")
        
    def test_coins_list(self):
        """Test /coins/list endpoint"""
        if not ENABLED_TESTS["coins_list"]:
            return
        return self.make_request("coins/list")
        
    def test_coins_markets(self):
        """Test /coins/markets endpoint"""
        if not ENABLED_TESTS["coins_markets"]:
            return
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": True
        }
        return self.make_request("coins/markets", params)
        
    def test_coin_data(self):
        """Test /coins/{id} endpoint"""
        if not ENABLED_TESTS["coin_data"]:
            return
        params = {
            "localization": False,
            "tickers": True,
            "market_data": True,
            "community_data": True,
            "developer_data": True
        }
        return self.make_request("coins/bitcoin", params)
        
    def test_coin_tickers(self):
        """Test /coins/{id}/tickers endpoint"""
        if not ENABLED_TESTS["coin_tickers"]:
            return
        params = {
            "exchange_ids": "binance,coinbase",
            "include_exchange_logo": True
        }
        return self.make_request("coins/bitcoin/tickers", params)
        
    def test_coin_history(self):
        """Test /coins/{id}/history endpoint"""
        if not ENABLED_TESTS["coin_history"]:
            return
        params = {
            "date": "30-12-2023",
            "localization": False
        }
        return self.make_request("coins/bitcoin/history", params)
        
    def test_coin_market_chart(self):
        """Test /coins/{id}/market_chart endpoint"""
        if not ENABLED_TESTS["coin_market_chart"]:
            return
        params = {
            "vs_currency": "usd",
            "days": "7",
            "interval": "daily"
        }
        return self.make_request("coins/bitcoin/market_chart", params)
        
    def test_coin_ohlc(self):
        """Test /coins/{id}/ohlc endpoint"""
        if not ENABLED_TESTS["coin_ohlc"]:
            return
        params = {
            "vs_currency": "usd",
            "days": "7"
        }
        return self.make_request("coins/bitcoin/ohlc", params)
        
    def test_exchanges_list(self):
        """Test /exchanges endpoint"""
        if not ENABLED_TESTS["exchanges_list"]:
            return
        return self.make_request("exchanges")
        
    def test_exchange_rates(self):
        """Test /exchange_rates endpoint"""
        if not ENABLED_TESTS["exchange_rates"]:
            return
        return self.make_request("exchange_rates")
        
    def test_global_data(self):
        """Test /global endpoint"""
        if not ENABLED_TESTS["global_data"]:
            return
        return self.make_request("global")
        
    def test_global_defi(self):
        """Test /global/decentralized_finance_defi endpoint"""
        if not ENABLED_TESTS["global_defi"]:
            return
        return self.make_request("global/decentralized_finance_defi")
        
    def test_global_market_cap(self):
        """Test /global/market_cap_chart endpoint"""
        if not ENABLED_TESTS["global_market_cap"]:
            return
        params = {
            "days": "7"
        }
        return self.make_request("global/market_cap_chart", params)
        
    def test_search(self):
        """Test /search endpoint"""
        if not ENABLED_TESTS["search"]:
            return
        params = {
            "query": "bitcoin"
        }
        return self.make_request("search", params)
        
    def test_trending(self):
        """Test /search/trending endpoint"""
        if not ENABLED_TESTS["trending"]:
            return
        return self.make_request("search/trending")
        
    def test_asset_platforms(self):
        """Test /asset_platforms endpoint"""
        if not ENABLED_TESTS["asset_platforms"]:
            return
        return self.make_request("asset_platforms")
        
    def test_companies_holdings(self):
        """Test /companies/public_treasury/{coin_id} endpoint"""
        if not ENABLED_TESTS["companies_holdings"]:
            return
        return self.make_request("companies/public_treasury/bitcoin")
        
    def run_all_tests(self):
        """Run all enabled tests"""
        print("\n🚀 Starting CoinGecko API Tests...")
        print(f"💾 Results will be saved to: {RESULTS_DIR}")
        
        # Basic endpoints
        self.test_ping()
        self.test_api_usage()
        
        # Simple endpoints
        self.test_simple_price()
        self.test_token_price()
        self.test_supported_currencies()
        
        # Coins endpoints
        self.test_coins_list()
        self.test_coins_markets()
        self.test_coin_data()
        self.test_coin_tickers()
        self.test_coin_history()
        self.test_coin_market_chart()
        self.test_coin_ohlc()
        
        # Exchange endpoints
        self.test_exchanges_list()
        self.test_exchange_rates()
        
        # Global endpoints
        self.test_global_data()
        self.test_global_defi()
        self.test_global_market_cap()
        
        # Search endpoints
        self.test_search()
        self.test_trending()
        
        # Other endpoints
        self.test_asset_platforms()
        self.test_companies_holdings()
        
        print("\n✨ All enabled tests completed!")
        print(f"📁 Check {RESULTS_DIR} for results")

if __name__ == "__main__":
    tester = CoinGeckoExamples()
    tester.run_all_tests()
