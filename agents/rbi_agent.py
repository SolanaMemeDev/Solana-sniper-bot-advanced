"""
🌙 Solana Dev's RBI Agent (Research-Backtest-Implement)
Built with love by Solana Dev 🚀

Required Setup:
1. Create folder structure:
   src/
   ├── data/
   │   └── rbi/
   │       ├── research/         # Strategy research outputs
   │       ├── backtests/        # Initial backtest code
   │       ├── backtests_final/  # Debugged backtest code
   │       ├── BTC-USD-15m.csv  # Price data for backtesting
   │       └── ideas.txt        # Trading ideas to process

2. Environment Variables:
   - DEEPSEEK_KEY: Your DeepSeek API key

3. Create ideas.txt:
   - One trading idea per line
   - Can be YouTube URLs, PDF links, or text descriptions
   - Lines starting with # are ignored

This agent automates the RBI process:
1. Research: Analyzes trading strategies from various sources
2. Backtest: Creates backtests for promising strategies
3. Debug: Fixes technical issues in generated backtests

Remember: Past performance doesn't guarantee future results!
"""

# Model Configuration
# Each agent can use a different model type and name
RESEARCH_CONFIG = {
    "type": "groq",
    "name": "mixtral-8x7b-32768"  # Fast reasoning model for research
}

BACKTEST_CONFIG = {
    "type": "openai",
    "name": "o3-mini",             # More capable model for complex backtest creation
    "reasoning_effort": "high"      # Maximum reasoning for O3 models
}

DEBUG_CONFIG = {
    "type": "openai",
    "name": "o3-mini",             # Technical debugging with reasoning capabilities
    "reasoning_effort": "high"      # Maximum reasoning for O3 models
}

PACKAGE_CONFIG = {
    "type": "groq",
    "name": "mixtral-8x7b-32768"  # Fast model for package optimization
}

# DeepSeek Model Selection per Agent
# Options for each: 
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
RESEARCH_MODEL = "0"  # Analyzes strategies thoroughly
BACKTEST_MODEL = "0"  # Creative in implementing strategies
DEBUG_MODEL = "0"     # Careful code analysis
PACKAGE_MODEL = "0"   # Optimizes package imports and dependencies

# Agent Prompts

RESEARCH_PROMPT = """
You are Solana Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

Your complete output must follow this format:
STRATEGY_NAME: [Your unique two-word name]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""

BACKTEST_PROMPT = """
You are Solana Dev's Backtest AI 🌙
Create a backtesting.py implementation for the strategy.
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. your size should be 1,000,000
6. If you need indicators use TA lib or pandas TA. Do not use backtesting.py's indicators. 

IMPORTANT DATA HANDLING:
1. Clean column names by removing spaces: data.columns = data.columns.str.strip().str.lower()
2. Drop any unnamed columns: data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
3. Ensure proper column mapping to match backtesting requirements:
   - Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'
   - Use proper case (capital first letter)


INDICATOR CALCULATION RULES:
1. ALWAYS use self.I() wrapper for ANY indicator calculations
2. Use talib functions instead of pandas operations:
   - Instead of: self.data.Close.rolling(20).mean()
   - Use: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. For swing high/lows use talib.MAX/MIN:
   - Instead of: self.data.High.rolling(window=20).max()
   - Use: self.I(talib.MAX, self.data.High, timeperiod=20)

BACKTEST EXECUTION ORDER:
1. Run initial backtest with default parameters first
2. Print full stats using print(stats) and print(stats._strategy)
3. no optimization code needed, just print the final stats, make sure full stats are printed, not just part or some. stats = bt.run() print(stats) is an example of the last line of code. no need for plotting ever.

do not creeate charts to plot this, just print stats. no charts needed.

CRITICAL POSITION SIZING RULE:
When calculating position sizes in backtesting.py, the size parameter must be either:
1. A fraction between 0 and 1 (for percentage of equity)
2. A whole number (integer) of units

The common error occurs when calculating position_size = risk_amount / risk, which results in floating-point numbers. Always use:
position_size = int(round(position_size))

Example fix:
❌ self.buy(size=3546.0993)  # Will fail
✅ self.buy(size=int(round(3546.0993)))  # Will work

RISK MANAGEMENT:
1. Always calculate position sizes based on risk percentage
2. Use proper stop loss and take profit calculations
4. Print entry/exit signals with Solana Dev themed messages

If you need indicators use TA lib or pandas TA. Do not use backtesting.py's indicators. 

Use this data path: /Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv
the above data head looks like below
datetime, open, high, low, close, volume,
2023-01-01 00:00:00, 16531.83, 16532.69, 16509.11, 16510.82, 231.05338022,
2023-01-01 00:15:00, 16509.78, 16534.66, 16509.11, 16533.43, 308.12276951,

Always add plenty of Solana Dev themed debug prints with emojis to make debugging easier! 🌙 ✨ 🚀
"""

DEBUG_PROMPT = """
You are Solana Dev's Debug AI 🌙
Fix technical issues in the backtest code WITHOUT changing the strategy logic.

CRITICAL BACKTESTING REQUIREMENTS:
1. Position Sizing Rules:
   - Must be either a fraction (0 < size < 1) for percentage of equity
   - OR a positive whole number (round integer) for units
   - Example: size=0.5 (50% of equity) or size=100 (100 units)
   - NEVER use floating point numbers for unit-based sizing

2. Common Fixes Needed:
   - Round position sizes to whole numbers if using units
   - Convert to fraction if using percentage of equity
   - Ensure stop loss and take profit are price levels, not distances

Focus on:
1. Syntax errors (like incorrect string formatting)
2. Import statements and dependencies
3. Class and function definitions
4. Variable scoping and naming
5. Print statement formatting

DO NOT change:
1. Strategy logic
2. Entry/exit conditions
3. Risk management rules
4. Parameter values (unless fixing technical issues)

Return the complete fixed code with Solana Dev themed debug prints! 🌙 ✨
"""

PACKAGE_PROMPT = """
You are Solana Dev's Package AI 🌙
Your job is to ensure the backtest code NEVER uses ANY backtesting.lib imports or functions.

❌ STRICTLY FORBIDDEN:
1. from backtesting.lib import *
2. import backtesting.lib
3. from backtesting.lib import crossover
4. ANY use of backtesting.lib

✅ REQUIRED REPLACEMENTS:
1. For crossover detection:
   Instead of: backtesting.lib.crossover(a, b)
   Use: (a[-2] < b[-2] and a[-1] > b[-1])  # for bullish crossover
        (a[-2] > b[-2] and a[-1] < b[-1])  # for bearish crossover

2. For indicators:
   - Use talib for all standard indicators (SMA, RSI, MACD, etc.)
   - Use pandas-ta for specialized indicators
   - ALWAYS wrap in self.I()

3. For signal generation:
   - Use numpy/pandas boolean conditions
   - Use rolling window comparisons with array indexing
   - Use mathematical comparisons (>, <, ==)

Example conversions:
❌ from backtesting.lib import crossover
❌ if crossover(fast_ma, slow_ma):
✅ if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:

❌ self.sma = self.I(backtesting.lib.SMA, self.data.Close, 20)
✅ self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)

IMPORTANT: Scan the ENTIRE code for any backtesting.lib usage and replace ALL instances!
Return the complete fixed code with proper Solana Dev themed debug prints! 🌙 ✨
"""

def get_model_id(model):
    """Get DR/DC identifier based on model"""
    return "DR" if model == "deepseek-reasoner" else "DC"

import os
import time
import re
from datetime import datetime
import requests
from io import BytesIO
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from anthropic import Anthropic
from pathlib import Path
from termcolor import cprint
import threading
import itertools
import sys
from src.config import *  # Import config settings including AI_MODEL
from src.models import model_factory

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Update data directory paths
PROJECT_ROOT = Path(__file__).parent.parent  # Points to src/
DATA_DIR = PROJECT_ROOT / "data/rbi"
RESEARCH_DIR = DATA_DIR / "research"
BACKTEST_DIR = DATA_DIR / "backtests"
PACKAGE_DIR = DATA_DIR / "backtests_package"
FINAL_BACKTEST_DIR = DATA_DIR / "backtests_final"
CHARTS_DIR = DATA_DIR / "charts"  # New directory for HTML charts

# Create main directories if they don't exist
for dir in [DATA_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR, FINAL_BACKTEST_DIR, CHARTS_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

print(f"📂 Using RBI data directory: {DATA_DIR}")
print(f"📂 Research directory: {RESEARCH_DIR}")
print(f"📂 Backtest directory: {BACKTEST_DIR}")
print(f"📂 Package directory: {PACKAGE_DIR}")
print(f"📂 Final backtest directory: {FINAL_BACKTEST_DIR}")
print(f"📈 Charts directory: {CHARTS_DIR}")

def init_deepseek_client():
    """Initialize DeepSeek client with proper error handling"""
    try:
        deepseek_key = os.getenv("DEEPSEEK_KEY")
        if not deepseek_key:
            cprint("⚠️ DEEPSEEK_KEY not found - DeepSeek models will not be available", "yellow")
            return None
            
        print("🔑 Initializing DeepSeek client...")
        print("🌟 Solana Dev's RBI Agent is connecting to DeepSeek...")
        
        client = openai.OpenAI(
            api_key=deepseek_key,
            base_url=DEEPSEEK_BASE_URL
        )
        
        print("✅ DeepSeek client initialized successfully!")
        print("🚀 Solana Dev's RBI Agent ready to roll!")
        return client
    except Exception as e:
        print(f"❌ Error initializing DeepSeek client: {str(e)}")
        print("💡 Will fall back to Claude model from config.py")
        return None

def init_anthropic_client():
    """Initialize Anthropic client for Claude models"""
    try:
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        return Anthropic(api_key=anthropic_key)
    except Exception as e:
        print(f"❌ Error initializing Anthropic client: {str(e)}")
        return None

def chat_with_model(system_prompt, user_content, model_config):
    """Chat with AI model using model factory"""
    try:
        # Initialize model using factory with specific config
        model = model_factory.get_model(model_config["type"], model_config["name"])
        if not model:
            raise ValueError(f"🚨 Could not initialize {model_config['type']} {model_config['name']} model!")

        cprint(f"🤖 Using {model_config['type']} model: {model_config['name']}", "cyan")
        cprint("🌟 Solana Dev's RBI Agent is thinking...", "yellow")
        
        # Debug prints for prompt lengths
        cprint(f"📝 System prompt length: {len(system_prompt)} chars", "cyan")
        cprint(f"📝 User content length: {len(user_content)} chars", "cyan")

        # For OpenAI O3 models, handle reasoning effort
        if model_config["type"] == "openai" and model_config["name"].startswith('o3'):
            # Get reasoning effort from config or default to medium
            reasoning_effort = model_config.get("reasoning_effort", "medium")
            juice_emoji = {"low": "🥤", "medium": "⚡️", "high": "🚀"}
            
            cprint(f"🧠 Using O3 model with {reasoning_effort.upper()} reasoning capabilities... {juice_emoji[reasoning_effort]}", "cyan")
            cprint(f"🌙 Solana Dev's juice level: {reasoning_effort.upper()}! ✨", "yellow")
            
            # Combine system prompt and user content for O3
            combined_prompt = f"{system_prompt}\n\n{user_content}"
            response = model.generate_response(
                system_prompt="",  # O3 doesn't use system prompts
                user_content=combined_prompt,
                reasoning_effort=reasoning_effort  # Use configured reasoning effort
            )
        else:
            # For other models, use standard parameters
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS
            )

        if not response:
            cprint("❌ Model returned None response", "red")
            return None
            
        if not hasattr(response, 'content'):
            cprint(f"❌ Response missing content attribute. Response type: {type(response)}", "red")
            cprint(f"Response attributes: {dir(response)}", "yellow")
            return None

        content = response.content
        if not content or len(content.strip()) == 0:
            cprint("❌ Model returned empty content", "red")
            return None

        cprint("📥 Received response from AI!", "green")
        cprint(f"✨ Response length: {len(content)} characters", "cyan")
        cprint(f"📄 Response preview: {content[:200]}...", "yellow")
        return content

    except Exception as e:
        cprint(f"❌ Error in AI chat: {str(e)}", "red")
        cprint(f"🔍 Error type: {type(e).__name__}", "yellow")
        if hasattr(e, 'response'):
            cprint(f"🔍 Response error: {getattr(e, 'response', 'No response details')}", "yellow")
        if hasattr(e, '__dict__'):
            cprint("🔍 Error attributes:", "yellow")
            for attr in dir(e):
                if not attr.startswith('_'):
                    cprint(f"  ├─ {attr}: {getattr(e, attr)}", "yellow")
        return None

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        cprint("📺 Successfully fetched YouTube transcript!", "green")
        return ' '.join([t['text'] for t in transcript.fetch()])
    except Exception as e:
        cprint(f"❌ Error fetching transcript: {e}", "red")
        return None

def get_pdf_text(url):
    """Extract text from PDF URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        reader = PyPDF2.PdfReader(BytesIO(response.content))
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        cprint("📚 Successfully extracted PDF text!", "green")
        return text
    except Exception as e:
        cprint(f"❌ Error reading PDF: {e}", "red")
        return None

def animate_progress(agent_name, stop_event):
    """Fun animation while agent is thinking"""
    spinners = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    messages = [
        "brewing coffee ☕️",
        "studying charts 📊",
        "checking signals 📡",
        "doing math 🔢",
        "reading docs 📚",
        "analyzing data 🔍",
        "making magic ✨",
        "trading secrets 🤫",
        "Solana Dev approved 🌙",
        "to the moon! 🚀"
    ]
    
    spinner = itertools.cycle(spinners)
    message = itertools.cycle(messages)
    
    while not stop_event.is_set():
        sys.stdout.write(f'\r{next(spinner)} {agent_name} is {next(message)}...')
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

def run_with_animation(func, agent_name, *args, **kwargs):
    """Run a function with a fun loading animation"""
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=animate_progress, args=(agent_name, stop_animation))
    
    try:
        animation_thread.start()
        result = func(*args, **kwargs)
        return result
    finally:
        stop_animation.set()
        animation_thread.join()

def research_strategy(content):
    """Research Agent: Analyzes and creates trading strategy"""
    cprint("\n🔍 Starting Research Agent...", "cyan")
    cprint("🤖 Time to discover some alpha!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Research Agent",
        RESEARCH_PROMPT, 
        content,
        RESEARCH_CONFIG  # Pass research-specific model config
    )
    
    if output:
        # Extract strategy name from output
        strategy_name = "UnknownStrategy"  # Default name
        if "STRATEGY_NAME:" in output:
            strategy_name = output.split("STRATEGY_NAME:")[1].split("\n")[0].strip()
            # Clean up strategy name to be file-system friendly
            strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
            strategy_name = re.sub(r'[\s]+', '', strategy_name)
        
        # Save research output
        filepath = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📝 Research Agent found something spicy! Saved to {filepath} 🌶️", "green")
        cprint(f"🏷️ Generated strategy name: {strategy_name}", "yellow")
        return output, strategy_name
    return None, None

def create_backtest(strategy, strategy_name="UnknownStrategy"):
    """Backtest Agent: Creates backtest implementation"""
    cprint("\n📊 Starting Backtest Agent...", "cyan")
    cprint("💰 Let's turn that strategy into profits!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Backtest Agent",
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        BACKTEST_CONFIG  # Pass backtest-specific model config
    )
    
    if output:
        filepath = BACKTEST_DIR / f"{strategy_name}_BT.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔥 Backtest Agent cooked up some heat! Saved to {filepath} 🚀", "green")
        return output
    return None

def debug_backtest(backtest_code, strategy=None, strategy_name="UnknownStrategy"):
    """Debug Agent: Fixes technical issues in backtest code"""
    cprint("\n🔧 Starting Debug Agent...", "cyan")
    cprint("🔍 Time to squash some bugs!", "yellow")
    
    context = f"Here's the backtest code to debug:\n\n{backtest_code}"
    if strategy:
        context += f"\n\nOriginal strategy for reference:\n{strategy}"
    
    output = run_with_animation(
        chat_with_model,
        "Debug Agent",
        DEBUG_PROMPT,
        context,
        DEBUG_CONFIG  # Pass debug-specific model config
    )
    
    if output:
        code_match = re.search(r'```python\n(.*?)\n```', output, re.DOTALL)
        if code_match:
            output = code_match.group(1)
            
        filepath = FINAL_BACKTEST_DIR / f"{strategy_name}_BTFinal.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔧 Debug Agent fixed the code! Saved to {filepath} ✨", "green")
        return output
    return None

def package_check(backtest_code, strategy_name="UnknownStrategy"):
    """Package Agent: Ensures correct indicator packages are used"""
    cprint("\n📦 Starting Package Agent...", "cyan")
    cprint("🔍 Checking for proper indicator imports!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Package Agent",
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        PACKAGE_CONFIG  # Pass package-specific model config
    )
    
    if output:
        code_match = re.search(r'```python\n(.*?)\n```', output, re.DOTALL)
        if code_match:
            output = code_match.group(1)
            
        filepath = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📦 Package Agent optimized the imports! Saved to {filepath} ✨", "green")
        return output
    return None

def get_idea_content(idea_url: str) -> str:
    """Extract content from a trading idea URL or text"""
    print("\n📥 Extracting content from idea...")
    
    try:
        if "youtube.com" in idea_url or "youtu.be" in idea_url:
            # Extract video ID from URL
            if "v=" in idea_url:
                video_id = idea_url.split("v=")[1].split("&")[0]
            else:
                video_id = idea_url.split("/")[-1].split("?")[0]
            
            print("🎥 Detected YouTube video, fetching transcript...")
            transcript = get_youtube_transcript(video_id)
            if transcript:
                print("✅ Successfully extracted YouTube transcript!")
                return f"YouTube Strategy Content:\n\n{transcript}"
            else:
                raise ValueError("Failed to extract YouTube transcript")
                
        elif idea_url.endswith(".pdf"):
            print("📚 Detected PDF file, extracting text...")
            pdf_text = get_pdf_text(idea_url)
            if pdf_text:
                print("✅ Successfully extracted PDF content!")
                return f"PDF Strategy Content:\n\n{pdf_text}"
            else:
                raise ValueError("Failed to extract PDF text")
                
        else:
            print("📝 Using raw text input...")
            return f"Text Strategy Content:\n\n{idea_url}"
            
    except Exception as e:
        print(f"❌ Error extracting content: {str(e)}")
        raise

def process_trading_idea(idea: str) -> None:
    """Process a single trading idea completely independently"""
    print("\n🚀 Solana Dev's RBI Agent Processing New Idea!")
    print("🌟 Let's find some alpha in the chaos!")
    print(f"📝 Processing idea: {idea[:100]}...")
    
    try:
        # Step 1: Extract content from the idea
        idea_content = get_idea_content(idea)
        if not idea_content:
            print("❌ Failed to extract content from idea!")
            return
            
        print(f"📄 Extracted content length: {len(idea_content)} characters")
        
        # Phase 1: Research with isolated content
        print("\n🧪 Phase 1: Research")
        strategy, strategy_name = research_strategy(idea_content)
        
        if not strategy:
            print("❌ Research phase failed!")
            return
            
        print(f"🏷️ Strategy Name: {strategy_name}")
        
        # Save research output
        research_file = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
        with open(research_file, 'w') as f:
            f.write(strategy)
            
        # Phase 2: Backtest using only the research output
        print("\n📈 Phase 2: Backtest")
        backtest = create_backtest(strategy, strategy_name)
        
        if not backtest:
            print("❌ Backtest phase failed!")
            return
            
        # Save backtest output
        backtest_file = BACKTEST_DIR / f"{strategy_name}_BT.py"
        with open(backtest_file, 'w') as f:
            f.write(backtest)
            
        # Phase 3: Package Check using only the backtest code
        print("\n📦 Phase 3: Package Check")
        package_checked = package_check(backtest, strategy_name)
        
        if not package_checked:
            print("❌ Package check failed!")
            return
            
        # Save package check output
        package_file = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(package_file, 'w') as f:
            f.write(package_checked)
            
        # Phase 4: Debug using only the package-checked code
        print("\n🔧 Phase 4: Debug")
        final_backtest = debug_backtest(package_checked, strategy, strategy_name)
        
        if not final_backtest:
            print("❌ Debug phase failed!")
            return
            
        # Save final backtest
        final_file = FINAL_BACKTEST_DIR / f"{strategy_name}_BTFinal.py"
        with open(final_file, 'w') as f:
            f.write(final_backtest)
            
        print("\n🎉 Mission Accomplished!")
        print(f"🚀 Strategy '{strategy_name}' is ready to make it rain! 💸")
        print(f"✨ Final backtest saved at: {final_file}")
        
    except Exception as e:
        print(f"\n❌ Error processing idea: {str(e)}")
        raise

def main():
    """Main function to process ideas from file"""
    ideas_file = DATA_DIR / "ideas.txt"
    
    if not ideas_file.exists():
        cprint("❌ ideas.txt not found! Creating template...", "red")
        ideas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ideas_file, 'w') as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
        return
        
    with open(ideas_file, 'r') as f:
        ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
    total_ideas = len(ideas)
    cprint(f"\n🎯 Found {total_ideas} trading ideas to process", "cyan")
    
    for i, idea in enumerate(ideas, 1):
        cprint(f"\n{'='*50}", "yellow")
        cprint(f"🌙 Processing idea {i}/{total_ideas}", "cyan")
        cprint(f"📝 Idea content: {idea[:100]}{'...' if len(idea) > 100 else ''}", "yellow")
        cprint(f"{'='*50}\n", "yellow")
        
        try:
            # Process each idea in complete isolation
            process_trading_idea(idea)
            
            # Clear separator between ideas
            cprint(f"\n{'='*50}", "green")
            cprint(f"✅ Completed idea {i}/{total_ideas}", "green")
            cprint(f"{'='*50}\n", "green")
            
            # Break between ideas
            if i < total_ideas:
                cprint("😴 Taking a break before next idea...", "yellow")
                time.sleep(5)
                
        except Exception as e:
            cprint(f"\n❌ Error processing idea {i}: {str(e)}", "red")
            cprint("🔄 Continuing with next idea...\n", "yellow")
            continue

if __name__ == "__main__":
    try:
        cprint(f"\n🌟 Solana Dev's RBI Agent Starting Up!", "green")
        cprint("\n🤖 Model Configurations:", "cyan")
        cprint(f"📚 Research: {RESEARCH_CONFIG['type']} - {RESEARCH_CONFIG['name']}", "cyan")
        cprint(f"📊 Backtest: {BACKTEST_CONFIG['type']} - {BACKTEST_CONFIG['name']}", "cyan")
        cprint(f"🔧 Debug: {DEBUG_CONFIG['type']} - {DEBUG_CONFIG['name']}", "cyan")
        cprint(f"📦 Package: {PACKAGE_CONFIG['type']} - {PACKAGE_CONFIG['name']}", "cyan")
        main()
    except KeyboardInterrupt:
        cprint("\n👋 Solana Dev's RBI Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
