"""
🌙 Solana Dev's Chat Agent
Built with love by Solana Dev 🚀

This agent monitors YouTube stream chat and answers questions using a knowledge base.
"""

import sys
from pathlib import Path
# Add project root to Python path for imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import os
import time
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
import pandas as pd
from src.config import *
from src.models import model_factory
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import threading
import shutil
import itertools
import random
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import base64
from PIL import Image
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import csv
import websocket  # Add this import for Restream WebSocket
import requests

# Load environment variables from the project root
env_path = Path(project_root) / '.env'
if not env_path.exists():
    raise ValueError(f"🚨 .env file not found at {env_path}")

load_dotenv(dotenv_path=env_path)

# Model override settings
MODEL_TYPE = "claude"  # Using Claude for chat responses
MODEL_NAME = "claude-3-haiku-20240307"  # Fast, efficient model

# Configuration - All in one place! 🎯
YOUTUBE_CHANNEL_ID = "UCN7D80fY9xMYu5mHhUhXEFw"
USE_RESTREAM = True
SELENIUM_AS_DEFAULT = True
CHECK_INTERVAL = 30.0
SELENIUM_CHECK_INTERVAL = 5.0
LIVE_CHECK_INTERVAL = 900.0
SELENIUM_LIVE_CHECK_INTERVAL = 60.0
USE_FALLBACK = True
MAX_RESPONSE_TIME = 5.0
CONFIDENCE_THRESHOLD = 0.8
MAX_RETRIES = 3
MAX_RESPONSE_TOKENS = 50
CHAT_MEMORY_SIZE = 30
MIN_CHARS_FOR_RESPONSE = 10
DEFAULT_INITIAL_CHATS = 10
NEGATIVITY_THRESHOLD = 0.7
LEADERBOARD_INTERVAL = 10  # Show leaderboard every 10 chats
IGNORED_USERS = ["Nightbot", "StreamElements"]

# Restream configuration
RESTREAM_WEBSOCKET_URL = "wss://chat.restream.io/embed/ws"  # Updated to match embed URL format
RESTREAM_EVENT_SOURCES = {
    2: "Twitch",
    13: "YouTube",
    28: "X/Twitter"
}

# Chat prompts
CHAT_PROMPT = """You are Solana Dev's Live Stream Chat AI Agent. Keep all responses short.
Keep responses concise, friendly, and include emojis.

YOU ARE THE CHAT MODERATOR OF A LIVE STREAM ABOUT CODING.

Knowledge Base:
{knowledge_base}

If the message is NOT in English:
1. First understand what they're saying
2. Respond in English in a way that makes sense given their message
3. Keep the response friendly and conversational

If the message IS in English:
Just respond with a friendly message including emojis.

IMPORTANT: 
- All responses must be very short and concise (under 50 tokens)
- Use knowledge base to answer questions about Solana Dev accurately
- If unsure about something, say "I'll let Solana Dev answer that! 🌙"
- Never share API keys or sensitive information
- Keep the good vibes going with emojis! 😊
"""

NEGATIVITY_CHECK_PROMPT = """You are a content moderator. Analyze this message for negativity, toxicity, or harmful content.
Consider hate speech, insults, excessive profanity, threats, or any form of harmful behavior.

Message: {message}

Rate the negativity from 0.0 to 1.0 where:
0.0 = Completely positive/neutral
1.0 = Extremely negative/toxic

Respond with only a number between 0.0 and 1.0.
"""

PROMPT_777 = """

send back a motivational bible verse

Pick a different verse each time
Send only the verse, no other text.

send back the actual verse in FULL. SEND BACK FULL VERSE
"""

# Add new constants for emojis
USER_EMOJIS = ["👨🏽", "👨🏽", "🧑🏽‍🦱", "👨🏽‍🦱", "👨🏽‍🦳", "👱🏽‍♂️", "👨🏽‍🦰", "👩🏽‍🦱"]
AI_EMOJIS = ["🤖", "🐳", "🐐", "👽", "🧠", "🌚"]
CLOWN_SPAM = "🤡" * 5  # 9 clown emojis for negative messages

# Add lucky emojis for 777 responses
LUCKY_EMOJIS = ["⭐️", "🧠", "😎", "♥️", "💙", "💚", "😇", "🌟", "✨", "💫", "❤️‍🔥"]

# Configuration
QUOTA_BACKOFF_BASE = 2  # Base for exponential backoff
QUOTA_BACKOFF_MAX = 3600  # Maximum backoff of 1 hour

# Add new constants for emojis
LEADERBOARD_EMOJIS = ["🥇", "🥈", "🥉"]

# Add new constants for warning emojis
WARNING_EMOJIS = ["⚠️", "🚫", "❌", "⛔️", "🔴", "💀", "☠️", "🚨"]

# Update config defaults
DEFAULT_CONFIG = {
    "response_prefix": "🤖 Solana Dev AI: ",
    "ignored_users": ["Nightbot", "StreamElements"],
    "command_prefix": "!",
    "initial_chats": DEFAULT_INITIAL_CHATS,
    "leaderboard_interval": 300,
    "use_restream": True,  # Force this to True
    "restream_show_id": None
}

# Add to configuration section
DEBUG_MODE = True  # Add this near other constants
MESSAGE_COOLDOWN = 3  # Reduce from 10 to 3 seconds

# Update constants at the top
LOVE_EMOJIS = ["❤️", "💖", "💝", "💗", "💓", "💞", "💕", "💘", "💟", "💌", "🫶", "💝", "💖", "💗"]
LOVE_SPAM = " ".join(random.sample(LOVE_EMOJIS, 7))  # Random selection of love emojis

class ChatScraper:
    """Fallback scraper for when API quota is exceeded"""
    def __init__(self):
        """Initialize the scraper with robust Chrome options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")  # Updated headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            cprint("🚀 Initializing Chrome driver with enhanced options...", "cyan")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.last_messages = set()
            cprint("✅ Chrome driver initialized successfully!", "green")
        except Exception as e:
            cprint(f"❌ Error initializing Chrome driver: {str(e)}", "red")
            raise
        
    def get_live_stream_url(self, channel_id):
        """Get the current live stream URL with enhanced error handling"""
        try:
            channel_url = f"https://www.youtube.com/channel/{channel_id}/live"
            cprint(f"🔍 Navigating to: {channel_url}", "cyan")
            
            self.driver.get(channel_url)
            time.sleep(5)  # Give page time to load
            
            # Wait for either chat or a specific element that indicates no live stream
            try:
                chat_present = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "yt-live-chat-app, #content"))
                )
                
                # Check if we're actually on a live stream
                current_url = self.driver.current_url
                if "/live" in current_url or "/watch" in current_url:
                    cprint(f"✨ Found live stream!", "green")
                    return current_url
                else:
                    cprint("❌ Channel is not live", "yellow")
                    return None
                    
            except selenium.common.exceptions.TimeoutException:
                cprint("⏳ Timed out waiting for live stream elements", "yellow")
                return None
                
        except Exception as e:
            cprint(f"❌ Error getting live stream URL: {str(e)}", "red")
            # Try to recover by reinitializing the driver
            try:
                self.driver.quit()
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                self.driver = webdriver.Chrome(options=chrome_options)
            except:
                pass
            return None
            
    def get_chat_messages(self):
        """Scrape chat messages using Selenium with improved selectors"""
        try:
            # Wait for chat frame to be present
            chat_frame = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#chatframe"))
            )
            
            # Switch to chat frame
            self.driver.switch_to.frame(chat_frame)
            
            # Wait for chat container with better selector
            chat_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "yt-live-chat-item-list-renderer"))
            )
            
            # Get all message elements with more specific selector
            all_messages = chat_container.find_elements(By.CSS_SELECTOR, "#items yt-live-chat-text-message-renderer")
            
            # Process messages - get all new ones since last check
            new_messages = []
            
            # If this is first run, get exactly DEFAULT_INITIAL_CHATS messages from the end
            if not self.last_messages:  # If this is first run
                messages_to_process = all_messages[-DEFAULT_INITIAL_CHATS:] if len(all_messages) > DEFAULT_INITIAL_CHATS else all_messages
                cprint(f"📥 Found {len(messages_to_process)} initial messages", "cyan")
            else:
                # Otherwise just check last few for new ones
                messages_to_process = all_messages[-5:]  # Check last 5 for new messages
                
            for msg in messages_to_process:
                try:
                    author = msg.find_element(By.CSS_SELECTOR, "#author-name").text
                    content = msg.find_element(By.CSS_SELECTOR, "#message").text
                    msg_id = f"{author}:{content}"
                    
                    if msg_id not in self.last_messages:
                        self.last_messages.add(msg_id)
                        new_messages.append({
                            'user': author,
                            'message': content,
                            'timestamp': datetime.now()
                        })
                        
                        # Keep set size manageable
                        if len(self.last_messages) > 100:
                            self.last_messages.clear()
                except Exception as e:
                    cprint(f"⚠️ Error processing message: {str(e)}", "yellow")
                    continue
            
            # Switch back to default content
            self.driver.switch_to.default_content()
            return new_messages  # Already in chronological order
            
        except Exception as e:
            cprint(f"❌ Error scraping chat: {str(e)}", "red")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return []
            
    def close(self):
        """Clean up resources"""
        try:
            self.driver.switch_to.default_content()  # Make sure we're out of any frames
            self.driver.quit()
        except:
            pass

class YouTubeChatMonitor:
    def __init__(self, api_key):
        """Initialize YouTube chat monitor"""
        self.api_key = api_key
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=api_key
        )
        self.live_chat_id = None
        self.next_page_token = None
        self.last_message_time = datetime.now()
        self.last_live_check = None
        self.video_id = None
        self.using_fallback = SELENIUM_AS_DEFAULT  # Initialize with default setting
        self.scraper = ChatScraper() if SELENIUM_AS_DEFAULT else None  # Create scraper if using Selenium by default
        
    def _init_fallback(self):
        """Initialize fallback scraper"""
        if not self.scraper and USE_FALLBACK:
            cprint("🔄 API quota exceeded - switching to Selenium fallback...", "yellow")
            self.scraper = ChatScraper()
            self.using_fallback = True
            
    def get_live_chat_id(self, channel_id):
        """Get live chat ID with fallback methods"""
        try:
            # Try API first if not already using fallback
            if not self.using_fallback:
                try:
                    chat_id = self._get_chat_id_api(channel_id)
                    if chat_id:
                        return chat_id
                except HttpError as e:
                    if "quota" in str(e).lower():
                        cprint("\n🔄 YouTube API quota exceeded!", "yellow")
                        cprint("🚀 Switching to Selenium fallback mode...", "cyan")
                        self._init_fallback()
                    else:
                        raise
            
            # Try Selenium fallback
            if self.using_fallback:
                if not self.scraper:
                    self._init_fallback()
                url = self.scraper.get_live_stream_url(channel_id)
                if url:
                    cprint(f"✨ Successfully connected to live stream via Selenium!", "green")
                    cprint(f"🔗 Stream URL: {url[:60]}...", "cyan")
                    return "fallback"
                else:
                    cprint("❌ No live stream found via Selenium", "yellow")
                    
            return None
            
        except Exception as e:
            if "quota" in str(e).lower() and not self.using_fallback:
                cprint("\n🔄 YouTube API quota exceeded!", "yellow")
                cprint("🚀 Switching to Selenium fallback mode...", "cyan")
                self._init_fallback()
                # Retry immediately with fallback
                return self.get_live_chat_id(channel_id)
            else:
                cprint(f"❌ Error getting live chat ID: {str(e)}", "red")
            return None
            
    def get_chat_messages(self):
        """Get chat messages with fallback methods"""
        if not self.using_fallback:
            try:
                return self._get_messages_api()
            except HttpError as e:
                if "quota" in str(e).lower():
                    self._init_fallback()
                else:
                    raise
                    
        if self.using_fallback:
            return self.scraper.get_chat_messages()
            
        return []
        
    def _get_chat_id_api(self, channel_id):
        """Get live chat ID using YouTube API"""
        try:
            # Search for active live stream
            request = self.youtube.search().list(
                part="id",
                channelId=channel_id,
                eventType="live",
                type="video",
                fields="items/id/videoId",
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                self.video_id = response['items'][0]['id']['videoId']
                cprint(f"✨ Found live stream: {self.video_id}", "cyan")
                
                # Get chat ID for found video
                request = self.youtube.videos().list(
                    part="liveStreamingDetails",
                    id=self.video_id,
                    fields="items/liveStreamingDetails/activeLiveChatId"
                )
                response = request.execute()
                
                if response.get('items'):
                    chat_id = response['items'][0].get('liveStreamingDetails', {}).get('activeLiveChatId')
                    if chat_id:
                        cprint(f"🎯 Found active live chat! ID: {chat_id[:20]}...", "green")
                        return chat_id
                        
            return None
            
        except HttpError as e:
            if "quota" in str(e).lower():
                raise  # Re-raise quota error to trigger fallback
            cprint(f"❌ Error in API chat ID lookup: {str(e)}", "red")
            return None
            
    def _get_messages_api(self):
        """Get messages using YouTube API"""
        if not self.live_chat_id:
            return []
            
        try:
            request = self.youtube.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part="snippet,authorDetails",
                pageToken=self.next_page_token,
                maxResults=DEFAULT_INITIAL_CHATS  # Use config value instead of hardcoded 3
            )
            response = request.execute()
            
            self.next_page_token = response.get('nextPageToken')
            
            if not response.get('items'):
                return []
                
            messages = []
            for item in response['items']:
                messages.append({
                    'user': item['authorDetails']['displayName'],
                    'message': item['snippet']['displayMessage'],
                    'timestamp': datetime.strptime(
                        item['snippet']['publishedAt'].split('.')[0] + 'Z',
                        '%Y-%m-%dT%H:%M:%SZ'
                    )
                })
                
            return messages
            
        except Exception as e:
            cprint(f"❌ Error getting API messages: {str(e)}", "red")
            return []
            
    def __del__(self):
        """Clean up resources"""
        if self.scraper:
            self.scraper.close()

class RestreamChatHandler:
    """Handler for Restream chat integration"""
    def __init__(self, client_id, client_secret):
        self.embed_token = os.getenv('RESTREAM_EMBED_TOKEN')
        self.messages = []
        self.driver = None
        self.connected = False
        self.message_class = None
        self.chat_agent = None
        self.last_processed_time = 0
        self.message_queue = []
        
        # Initialize Selenium options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--disable-software-rasterizer")
        self.chrome_options.add_argument("--disable-extensions")
        
        # Single set for all processed messages
        self.processed_messages = set()
        
    def set_chat_agent(self, agent):
        """Set reference to ChatAgent for processing questions"""
        self.chat_agent = agent
        
    def process_question(self, username, text):
        """Forward question processing to ChatAgent"""
        if self.chat_agent:
            return self.chat_agent.process_question(username, text)
        return None
        
    def connect(self):
        if not self.embed_token:
            cprint("❌ RESTREAM_EMBED_TOKEN not found in .env!", "red")
            return
            
        try:
            cprint("🔌 Connecting to Restream chat...", "cyan")
            
            service = webdriver.ChromeService()
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            
            embed_url = f"https://chat.restream.io/embed?token={self.embed_token}"
            cprint(f"🌐 Loading chat URL", "cyan")
            self.driver.get(embed_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Debug page source
            cprint("🔍 Looking for chat elements...", "cyan")
            page_source = self.driver.page_source
            
            # Try different class names that might be present
            possible_classes = [
                "chat-message", 
                "message", 
                "chat-item",
                "message-item",
                "chat-line",
                "rs-chat-message",
                "chat-messages",  # Added more possible classes
                "message-wrapper",
                "chat-message-wrapper"
            ]
            
            found_class = None
            for class_name in possible_classes:
                elements = self.driver.find_elements(By.CLASS_NAME, class_name)
                if elements:
                    found_class = class_name
                    cprint(f"✅ Found chat elements using class: {class_name}", "green")
                    break
            
            if found_class:
                self.message_class = found_class
                self.connected = True
                cprint("✅ Connected to Restream chat!", "green")
            else:
                # If no class found, use a default one
                self.message_class = "chat-message"
                cprint("⚠️ Using default message class: chat-message", "yellow")
                self.connected = True
            
            threading.Thread(target=self._poll_messages, daemon=True).start()
            
        except Exception as e:
            cprint(f"❌ Error connecting to Restream: {str(e)}", "red")
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _poll_messages(self):
        while self.connected:
            try:
                if not self.message_class:
                    time.sleep(1)
                    continue
                    
                messages = self.driver.find_elements(By.CLASS_NAME, "message-info-container")
                
                # Process only messages we haven't seen
                for msg in messages[-10:]:
                    try:
                        username = msg.find_element(By.CLASS_NAME, "message-sender").text.strip()
                        text = msg.find_element(By.CLASS_NAME, "chat-text-normal").text.strip()
                        
                        # Create unique message ID
                        msg_id = f"{username}:{text}"
                        
                        # Skip if we've ever seen this message before
                        if msg_id in self.processed_messages:
                            continue
                            
                        # Skip system messages
                        if username == "Restream.io" or not text:
                            continue
                            
                        # Add to processed messages
                        self.processed_messages.add(msg_id)
                        
                        # Get AI response first to check if it's negative
                        ai_response = None
                        if self.chat_agent:
                            ai_response = self.chat_agent.process_question(username, text)
                        
                        # Only display message if it's not getting clowned
                        self._display_chat(username, text, ai_response)
                        
                    except Exception as e:
                        cprint(f"⚠️ Error processing message: {str(e)}", "yellow")
                        continue
                        
                time.sleep(0.5)  # Poll frequently
                
            except Exception as e:
                cprint(f"❌ Error polling messages: {str(e)}", "red")
                time.sleep(1)

    def __del__(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

    def _display_chat(self, username, text, ai_response):
        """Display chat with colored formatting"""
        # For love responses, only show username and hearts - skip their message
        if ai_response == LOVE_SPAM:
            print(f"{random.choice(WARNING_EMOJIS)} ", end="")
            cprint(username, "white", "on_red", end="")
            print(f" {LOVE_SPAM}")
            print()  # Add spacing
            return
        
        # For normal messages, show full chat
        print(f"{random.choice(USER_EMOJIS)} ", end="")
        cprint(username, "white", "on_blue", end="")
        print(f": {text}")
        
        # Display AI response if we have one
        if ai_response:
            # If it's a 777 response, display with cyan background
            if text.strip() == "777":
                print(f"{random.choice(AI_EMOJIS)} ", end="")
                cprint("Solana Dev AI", "white", "on_green", end="")
                print(": ", end="")
                cprint(ai_response, "white", "on_cyan")
            else:
                print(f"{random.choice(AI_EMOJIS)} ", end="")
                cprint("Solana Dev AI", "white", "on_green", end="")
                print(f": {ai_response}")
            print()  # Add spacing

class ChatAgent:
    def __init__(self):
        """Initialize the Chat Agent"""
        cprint("\n🤖 Initializing Solana Dev's Chat Agent...", "cyan")
        
        # Create data directories
        self.data_dir = Path(project_root) / "src" / "data" / "chat_agent"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_path = self.data_dir / "knowledge_base.txt"
        self.chat_log_path = self.data_dir / "chat_history.csv"
        
        # Initialize chat memory
        self.chat_memory = []
        
        # Create knowledge base if it doesn't exist
        if not self.knowledge_base_path.exists():
            self._create_knowledge_base()
        
        # Create chat log if it doesn't exist
        if not self.chat_log_path.exists():
            self._create_chat_log()
            
        # Debug environment variables
        for key in ["OPENAI_KEY", "ANTHROPIC_KEY", "GEMINI_KEY", "GROQ_API_KEY", "DEEPSEEK_KEY", "YOUTUBE_API_KEY"]:
            if os.getenv(key):
                cprint(f"✅ Found {key}", "green")
            else:
                cprint(f"❌ Missing {key}", "red")
        
        # Initialize model using factory
        self.model_factory = model_factory
        self.model = self.model_factory.get_model(MODEL_TYPE, MODEL_NAME)
        
        if not self.model:
            raise ValueError(f"🚨 Could not initialize {MODEL_TYPE} {MODEL_NAME} model! Check API key and model availability.")
        
        self._announce_model()
        
        # Add leaderboard tracking
        self.chat_count_since_last_leaderboard = 0
        self.leaderboard_chat_interval = LEADERBOARD_INTERVAL  # Use the constant we defined (10)
        
        # Initialize appropriate chat system
        if USE_RESTREAM:
            cprint("\n🔄 Attempting to initialize Restream...", "cyan")
            restream_id = os.getenv("RESTREAM_CLIENT_ID")
            restream_secret = os.getenv("RESTREAM_CLIENT_SECRET")
            
            if not restream_id or not restream_secret:
                cprint("❌ Missing Restream credentials in .env!", "red")
                raise ValueError("Missing Restream credentials!")
                
            self.restream_handler = RestreamChatHandler(restream_id, restream_secret)
            self.restream_handler.set_chat_agent(self)  # Set reference to ChatAgent
            self.restream_handler.connect()
            cprint("🎮 Restream chat integration enabled!", "green")
            self.youtube_monitor = None
        else:
            youtube_api_key = os.getenv("YOUTUBE_API_KEY")
            if not youtube_api_key:
                raise ValueError("🚨 YOUTUBE_API_KEY not found in .env!")
            self.youtube_monitor = YouTubeChatMonitor(youtube_api_key)
            self.restream_handler = None
        
        cprint("🎯 Solana Dev's Chat Agent initialized!", "green")
        
    def _create_knowledge_base(self):
        """Create initial knowledge base file"""
        initial_knowledge = """# 🌙 Solana Dev's Knowledge Base

## About Solana Dev
- Passionate about AI, trading, and coding
- Loves adding emojis to everything
- Streams coding sessions on YouTube
- Built multiple AI trading agents

## Projects
- Focus Agent: AI that monitors focus during streams
- Trading Agents: Various AI-powered trading bots
- Model Factory: Unified interface for multiple AI models

## Preferences
- Favorite Language: Python
- Coding Style: Clean, well-documented, with lots of emojis
- Trading Style: AI-assisted with risk management

## Common Commands
- !focus - Check current focus level
- !trade - Check trading status
- !help - List available commands
"""
        self.knowledge_base_path.write_text(initial_knowledge)
        cprint("📚 Created initial knowledge base!", "green")
        
    def _create_chat_log(self):
        """Create empty chat history CSV with all required columns"""
        df = pd.DataFrame(columns=['timestamp', 'user', 'message', 'score'])
        df.to_csv(self.chat_log_path, index=False)
        cprint("📝 Created chat history log with all required columns!", "green")
        
    def _announce_model(self):
        """Announce current model with eye-catching formatting"""
        model_msg = f"🤖 USING MODEL: {MODEL_TYPE.upper()} - {MODEL_NAME} 🤖"
        border = "=" * (len(model_msg) + 4)
        cprint(border, 'white', 'on_blue', attrs=['bold'])
        cprint(f"  {model_msg}  ", 'white', 'on_blue', attrs=['bold'])
        cprint(border, 'white', 'on_blue', attrs=['bold'])
        
    def _load_knowledge_base(self):
        """Load and return the knowledge base content"""
        return self.knowledge_base_path.read_text()
        
    def _log_chat(self, user, question, confidence, response):
        """Log chat interaction to CSV silently"""
        try:
            new_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': user,
                'question': question,
                'confidence': confidence,
                'response': response
            }
            
            df = pd.read_csv(self.chat_log_path)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(self.chat_log_path, index=False)
            
        except Exception as e:
            cprint(f"❌ Error logging chat: {str(e)}", "red")
            
    def _update_chat_memory(self, message):
        """Update the chat memory with new message"""
        self.chat_memory.append(message)
        if len(self.chat_memory) > CHAT_MEMORY_SIZE:
            self.chat_memory.pop(0)  # Remove oldest message

    def _get_random_lucky_emojis(self, count=3):
        """Get random lucky emojis for 777 responses"""
        return ' '.join(random.sample(LUCKY_EMOJIS, count))

    def _should_skip_response(self, message):
        """Check if message should be skipped for response"""
        # Never skip 777 messages
        if message.strip() == "777":
            return False
        
        # Skip if empty
        if not message.strip():
            return True
        
        # Skip if too short
        if len(message.strip()) < MIN_CHARS_FOR_RESPONSE:
            return True
        
        return False

    def _display_chat(self, username, text, ai_response):
        """Display chat with colored formatting"""
        # For love responses, only show username and hearts - skip their message
        if ai_response == LOVE_SPAM:
            print(f"{random.choice(WARNING_EMOJIS)} ", end="")
            cprint(username, "white", "on_red", end="")
            print(f" {LOVE_SPAM}")
            print()  # Add spacing
            return
        
        # For normal messages, show full chat
        print(f"{random.choice(USER_EMOJIS)} ", end="")
        cprint(username, "white", "on_blue", end="")
        print(f": {text}")
        
        # Display AI response if we have one
        if ai_response:
            # If it's a 777 response, display with cyan background
            if text.strip() == "777":
                print(f"{random.choice(AI_EMOJIS)} ", end="")
                cprint("Solana Dev AI", "white", "on_green", end="")
                print(": ", end="")
                cprint(ai_response, "white", "on_cyan")
            else:
                print(f"{random.choice(AI_EMOJIS)} ", end="")
                cprint("Solana Dev AI", "white", "on_green", end="")
                print(f": {ai_response}")
            print()  # Add spacing

    def process_question(self, user, question):
        try:
            # Skip messages from ignored users
            if user in IGNORED_USERS:
                return None
                
            # Check for negativity first
            negativity_prompt = NEGATIVITY_CHECK_PROMPT.format(message=question)
            negativity_response = self.model.generate_response(
                system_prompt=negativity_prompt,
                user_content=question,
                temperature=0.3,
                max_tokens=10
            )
            
            try:
                negativity_score = float(negativity_response.content.strip())
                if negativity_score >= NEGATIVITY_THRESHOLD:
                    return LOVE_SPAM
            except ValueError:
                pass
            
            # Special case for "777"
            if question.strip() == "777":
                verse_response = self.model.generate_response(
                    system_prompt=PROMPT_777,
                    user_content="777",
                    temperature=0.9,
                    max_tokens=MAX_RESPONSE_TOKENS
                )
                emojis = self._get_random_lucky_emojis()
                return f"777 {emojis}\n{verse_response.content.strip()}"
            
            # Get knowledge base content
            knowledge_base = self._load_knowledge_base()
            
            # Format prompt with knowledge base
            formatted_prompt = CHAT_PROMPT.format(
                knowledge_base=knowledge_base
            )
            
            # For simple questions, use a minimal prompt
            if len(question.split()) < 5:
                formatted_prompt = """You are Solana Dev's Live Stream Chat AI Agent. Keep responses short and friendly with emojis."""
            
            # Get response from model
            response = self.model.generate_response(
                system_prompt=formatted_prompt,
                user_content=question,
                temperature=0.7,
                max_tokens=MAX_RESPONSE_TOKENS
            )
            
            return response.content.strip()
            
        except Exception as e:
            cprint(f"❌ Error processing question: {str(e)}", "red")
            return None

    def _get_leaderboard(self):
        """
        🌙 Solana Dev SAYS: Let's see who's leading the chat! 🏆
        """
        try:
            # Read chat history
            df = pd.read_csv(self.chat_log_path)
            
            # Check if score column exists
            if not df.empty and 'score' in df.columns:
                scores = df.groupby('user')['score'].sum().sort_values(ascending=False)
                return scores.head(3)  # Get top 3
            return pd.Series()
        except Exception as e:
            cprint(f"❌ Error getting leaderboard: {str(e)}", "red")
            return pd.Series()
            
    def _format_leaderboard_message(self, scores):
        """
        🌙 Solana Dev SAYS: Format that leaderboard with style! 🎨
        """
        if len(scores) == 0:
            return None
            
        message = "⭐️ 🌟 💫 CHAT CHAMPS 💫 🌟 ⭐️ "
        
        # Simple rank emojis
        rank_decorations = [
            "👑", # First place
            "🥈", # Second place
            "🥉"  # Third place
        ]
        
        # Add some randomized bonus emojis
        bonus_emojis = ["🎯", "🎲", "🎮", "🕹️"]
        
        message += "\n"  # Add spacing after header
        
        for i, (user, score) in enumerate(scores.items()):
            random_bonus = random.choice(bonus_emojis)
            message += f"\n{rank_decorations[i]} {user}: {score} points {random_bonus}"
        
        message += "\n\n✨ ⭐️ 🌟 ⭐️ 💫 ⭐️ 🌟 ⭐️ ✨"
        return message.strip()
        
    def _show_leaderboard(self):
        """
        🌙 Solana Dev SAYS: Time to show off those chat skills! 🚀
        """
        scores = self._get_leaderboard()
        if len(scores) == 0:
            return
            
        message = self._format_leaderboard_message(scores)
        print(f"\n{message}\n")  # Display in console
        # You can add code here to post to chat if needed
        
    def run(self):
        """Main loop for monitoring chat"""
        cprint("\n🎯 Solana Dev's Chat Agent starting...", "cyan", attrs=['bold'])
        print()
        
        cprint(f"📝 Will process last {DEFAULT_INITIAL_CHATS} messages on startup", "cyan")
        cprint(f"⏰ Leaderboard will show every {LEADERBOARD_INTERVAL} chats", "cyan")
        
        # Show initial leaderboard
        cprint("\n🏆 Initial Leaderboard:", "cyan")
        self._show_leaderboard()
        self.chat_count_since_last_leaderboard = 0
        
        if USE_RESTREAM:
            cprint("🎮 Using Restream for chat integration!", "green")
            if not self.restream_handler:
                cprint("❌ Restream handler not initialized - check your credentials!", "red")
                return
            
            # Start Restream handler and just keep main thread alive
            try:
                while True:
                    time.sleep(SELENIUM_CHECK_INTERVAL)
                    
                    # Show leaderboard every LEADERBOARD_INTERVAL chats
                    if self.chat_count_since_last_leaderboard >= LEADERBOARD_INTERVAL:
                        cprint("\n🏆 Time for the leaderboard!", "cyan")
                        self._show_leaderboard()
                        self.chat_count_since_last_leaderboard = 0
                        print()  # Add spacing after leaderboard
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                cprint(f"❌ Error: {str(e)}", "red")
                time.sleep(SELENIUM_CHECK_INTERVAL)
        else:
            # YouTube-only code (only runs if not using Restream)
            cprint("🎥 Using YouTube chat integration!", "green")
            
            while True:
                try:
                    # Get live chat ID if we don't have one
                    if not self.youtube_monitor.live_chat_id:
                        chat_id = self.youtube_monitor.get_live_chat_id(YOUTUBE_CHANNEL_ID)
                        if chat_id:
                            self.youtube_monitor.live_chat_id = chat_id
                            cprint("✅ Connected to YouTube live chat!", "green")
                        else:
                            cprint("⏳ Waiting for active live stream...", "yellow")
                            time.sleep(LIVE_CHECK_INTERVAL)
                            continue
                    
                    # Get and process messages
                    messages = self.youtube_monitor.get_chat_messages()
                    
                    for msg in messages:
                        response = self.process_question(msg['user'], msg['message'])
                        self._display_chat(msg['user'], msg['message'], response)
                        self.chat_count_since_last_leaderboard += 1
                        
                        # Show leaderboard if needed
                        if self.chat_count_since_last_leaderboard >= LEADERBOARD_INTERVAL:
                            self._show_leaderboard()
                            self.chat_count_since_last_leaderboard = 0
                    
                    time.sleep(CHECK_INTERVAL)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    cprint(f"❌ Error in YouTube chat: {str(e)}", "red")
                    time.sleep(CHECK_INTERVAL)

    def _get_user_chat_history(self, username):
        """
        🌙 Solana Dev SAYS: Let's get that chat history! 📚
        """
        try:
            df = pd.read_csv(self.chat_log_path)
            if not df.empty and 'message' in df.columns:
                return df[df['user'] == username]['message'].tolist()
            return []
        except Exception as e:
            cprint(f"❌ Error getting user chat history: {str(e)}", "red")
            return []

    def save_chat_history(self, username, message, score):
        """
        🌙 Solana Dev SAYS: Saving chat history with scores! 📊
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if file exists and has headers
        file_exists = os.path.exists(self.chat_log_path)
        
        with open(self.chat_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                # Write headers if file doesn't exist
                writer.writerow(['timestamp', 'user', 'message', 'score'])
            writer.writerow([timestamp, username, message, score])

def is_meaningful_chat(new_message, chat_history, threshold=0.3):
    """
    🌙 Solana Dev SAYS: Let's keep chats meaningful and fun!
    Determines if a chat is meaningful based on similarity to previous chats
    """
    if len(new_message.split()) < 3:  # Very short messages
        return False
        
    if not chat_history:
        return True
        
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(chat_history + [new_message])
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
    if np.max(similarities) > threshold:
        return False
        
    return True

def evaluate_chat_sentiment(message):
    """
    🌙 Solana Dev SAYS: Let's keep the vibes positive! 🌈
    Simple sentiment evaluation (can be replaced with more complex AI)
    """
    positive_words = ['great', 'awesome', 'love', 'thanks', 'helpful']
    negative_words = ['hate', 'bad', 'awful', 'terrible', 'useless']
    
    message_lower = message.lower()
    positive_score = sum(word in message_lower for word in positive_words)
    negative_score = sum(word in message_lower for word in negative_words)
    
    if positive_score > negative_score:
        #print("🌙 Solana Dev: Positive vibes detected! ")
        return 1
    elif negative_score > positive_score:
        print("🌙 ayo fam lets keep it positive, spam the 777s to increase the vibes in here")
        return -1
    return 0

def update_chat_score(username, message, chat_history):
    """
    🌙 Solana Dev SAYS: Let's track those chat points! 
    """
    if not is_meaningful_chat(message, chat_history):
        return 0
        
    sentiment_score = evaluate_chat_sentiment(message)
    return sentiment_score if sentiment_score != 0 else 1

if __name__ == "__main__":
    try:
        agent = ChatAgent()
        agent.run()
    except KeyboardInterrupt:
        cprint("\n👋 Chat Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
