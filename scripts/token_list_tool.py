"""
This is a tool that allows you to put any wallets to track and then see exactly their tokens they have in their solana wallet. 
And what's cool about it is that you can look at the change of tokens in their list to see if they bought a new token and what that token is. 

it uses the helius rpc so for RPC_ENDPOINT you need to set the helius rpc endpoint. 
"""

import os
import json
import requests
from typing import List, Dict
import time

# List of wallets to track - Add your wallet addresses here! 🎯
WALLETS_TO_TRACK = [
    "4wgfCBf2WwLSRKLef9iW7JXZ2AfkxUxGM4XcKpHm3Sin",  # Example wallet
    # Add more wallets here...
]

class TokenAccountTracker:
    def __init__(self):
        self.rpc_endpoint = os.getenv("RPC_ENDPOINT")
        if not self.rpc_endpoint:
            raise ValueError("⚠️ Please set RPC_ENDPOINT environment variable!")
        print(f"🌐 Connected to Helius RPC endpoint... Solana Dev is ready! 🚀")

    def get_token_accounts(self, wallet_address: str) -> Dict:
        """Get all token accounts for a specific wallet address"""
        print(f"🔍 Solana Dev is fetching token accounts for {wallet_address}...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": "moon-dev-rocks",
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {
                    "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
        }

        try:
            response = requests.post(self.rpc_endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching token accounts: {str(e)}")
            return None

    def track_all_wallets(self):
        """Track token accounts for all wallets in the WALLETS_TO_TRACK list"""
        print(f"🚀 Solana Dev's Token Tracker starting up...")
        print(f"📋 Tracking {len(WALLETS_TO_TRACK)} wallets...")
        
        results = {}
        for wallet in WALLETS_TO_TRACK:
            token_accounts = self.get_token_accounts(wallet)
            if token_accounts and "result" in token_accounts:
                parsed_accounts = []
                for account in token_accounts["result"]["value"]:
                    parsed_data = account["account"]["data"]["parsed"]["info"]
                    parsed_accounts.append({
                        "mint": parsed_data["mint"],
                        "amount": parsed_data["tokenAmount"]["uiAmountString"],
                        "decimals": parsed_data["tokenAmount"]["decimals"]
                    })
                results[wallet] = parsed_accounts
                print(f"✅ Found {len(parsed_accounts)} token accounts for {wallet}")
            time.sleep(0.5)  # Be nice to the API 😊
        
        return results

def main():
    tracker = TokenAccountTracker()
    results = tracker.track_all_wallets()
    
    # Pretty print the results
    print("\n🎉 Solana Dev's Final Report:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()