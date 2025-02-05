'''
this script opens all the wallets in a csv file in new tabs. 
just place the csv there
'''


import pandas as pd
import webbrowser
import time
import psutil
import os
import sys

# Configuration Constants
FILE_PATH = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/private_data/bigfollow.csv"
OPENS_PER_BATCH = 30
TARGET_COLUMN = "wallet_address"  # Column containing the wallet addresses
BASE_URL = "https://gmgn.ai/sol/address/"  # Base URL for GMGN.ai

def count_browser_tabs():
    """Count approximate number of open browser tabs"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
            return len(proc.children())
    return 0

def open_wallet_tabs(csv_path, batch_size=OPENS_PER_BATCH):
    print("🌙 Solana Dev's Smart Tab Opener Starting Up! 🚀")
    print(f"📂 Opening CSV file: {csv_path}")
    
    # Verify file exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        return
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"📊 CSV loaded successfully with {len(df)} rows")
        print(f"📑 Available columns: {', '.join(df.columns)}")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
        
    if TARGET_COLUMN not in df.columns:
        print(f"❌ Error: Column '{TARGET_COLUMN}' not found in CSV!")
        return
        
    # Get wallet addresses and construct full URLs
    wallet_addresses = df[TARGET_COLUMN].tolist()
    urls = []
    for addr in wallet_addresses:
        # Clean the address and skip if empty
        addr = addr.strip() if isinstance(addr, str) else str(addr).strip()
        if not addr:
            continue
        # If it's already a full URL, use it as is, otherwise construct it
        if addr.startswith('http'):
            urls.append(addr)
        else:
            urls.append(f"{BASE_URL}{addr}")
    
    # Debug: Print first few URLs
    print("\n🔍 First few URLs to open:")
    for i, url in enumerate(urls[:3]):
        print(f"   {i+1}. {url}")
    print()
    
    print(f"🎯 Found {len(urls)} links to process from column '{TARGET_COLUMN}' in batches of {batch_size}!")
    
    current_index = 0
    opened_tabs = 0
    
    while current_index < len(urls):
        # If we have less than batch_size tabs open, open more
        if opened_tabs < batch_size and current_index < len(urls):
            try:
                url = urls[current_index]
                print(f"🌐 Attempting to open: {url}")
                
                # Skip empty URLs
                if not url:
                    print("⚠️ Skipping empty URL")
                    current_index += 1
                    continue
                
                webbrowser.open_new_tab(url)
                print(f"✨ Opened tab {current_index + 1}/{len(urls)}")
                current_index += 1
                opened_tabs += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"❌ Error opening {url}: {str(e)}")
                current_index += 1  # Skip problematic URLs
        else:
            user_input = input("\n🌜 Solana Dev says: Press Enter after closing some tabs... " +
                             f"({len(urls) - current_index} links remaining)\n")
            opened_tabs = 0  # Reset the counter after user closes tabs
    
    print("🎉 All done! Solana Dev's tab opener completed successfully!")
    print("💫 Remember to smash that like button and follow for more tools!")

if __name__ == "__main__":
    open_wallet_tabs(FILE_PATH)
