"""
🌙 Solana Dev's Twitter Login Script

SETUP INSTRUCTIONS:
1. First, create a .env file in your project root with:
   TWITTER_USERNAME=your_username
   TWITTER_EMAIL=your_email
   TWITTER_PASSWORD=your_password

2. Install required packages:
   pip install twikit==2.2.1  # Specific version required
   pip install python-dotenv
   pip install termcolor
   pip install httpx

3. Run this script once to generate cookies.json
4. After successful login, you can use the cookies.json for other scripts

NOTE: If you get login errors, try:
- Logging into Twitter manually first
- Waiting a few minutes between attempts
- Checking if your account needs verification
"""

from datetime import datetime
import time
import requests
import os
import asyncio

# Patch httpx before importing twikit
import httpx
original_client = httpx.Client

def patched_client(*args, **kwargs):
    # Add browser-like headers
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    
    kwargs['headers'].update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    })
    
    kwargs.pop('proxy', None)
    return original_client(*args, **kwargs)

httpx.Client = patched_client

from twikit import Client
from twikit.errors import TooManyRequests, BadRequest
from termcolor import cprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    try:
        # Get credentials from env
        USERNAME = os.getenv('TWITTER_USERNAME')
        EMAIL = os.getenv('TWITTER_EMAIL')
        PASSWORD = os.getenv('TWITTER_PASSWORD')

        if not all([USERNAME, EMAIL, PASSWORD]):
            cprint("❌ Error: Missing Twitter credentials in .env file!", "red")
            cprint("🔍 Please check the setup instructions at the top of this file.", "yellow")
            exit(1)

        # Initialize client
        client = Client()
        
        cprint("🌙 Solana Dev's Twitter Login Script", "cyan")
        cprint("🔑 Attempting to log in...", "cyan")

        # Add delay before login
        time.sleep(3)

        # Login using credentials from .env
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )

        time.sleep(2)  # Small delay after login

        # Save cookies
        client.save_cookies("cookies.json")
        cprint("✅ Login successful! Cookies saved.", "green")
        cprint("🚀 You can now use other scripts that require Twitter login!", "green")

    except BadRequest as e:
        cprint(f"❌ Login request failed: {str(e)}", "red")
        cprint("🔍 This might be due to Twitter's automation detection.", "yellow")
        cprint("💡 Try these solutions:", "yellow")
        cprint("1. Wait a few minutes and try again", "yellow")
        cprint("2. Try logging in manually on Twitter first", "yellow")
        cprint("3. Check if your account needs verification", "yellow")
    except TooManyRequests as e:
        cprint(f"❌ Rate limited: {str(e)}", "red")
    except Exception as e:
        cprint(f"❌ Unexpected error: {str(e)}", "red")
        # Print the full error for debugging
        import traceback
        cprint(f"🔍 Debug info: {traceback.format_exc()}", "yellow")

if __name__ == "__main__":
    asyncio.run(main())