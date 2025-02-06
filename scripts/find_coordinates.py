"""
🎯 Solana Dev's Coordinate Finder
A simple tool to find screen coordinates and test cursor movements
"""

import pyautogui
import time
from termcolor import cprint
import json
from pathlib import Path

# Disable pyautogui's fail-safe (optional)

# pyautogui.FAILSAFE = False

def print_position():
    """Print current mouse position with Solana Dev style"""
    try:
        print("\n🎯 Press Ctrl+C to save current position or quit")
        while True:
            # Get current position
            x, y = pyautogui.position()
            
            # Clear previous line (works in most terminals)
            print('\033[K', end='\r')
            
            # Print current position with style
            print(f"🎯 Current position: ({x}, {y})", end='\r')
            
            # Small delay to prevent high CPU usage
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n✨ Final position:", pyautogui.position())
        save = input("\nSave this position? (y/n): ").lower().strip()
        if save == 'y':
            save_position(*pyautogui.position())
        print("\n👋 Solana Dev's Coordinate Finder shutting down...")

def save_position(x, y):
    """Save current position to config file"""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("src/data/code_runner")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save coordinates
        config = {
            "target_x": x,
            "target_y": y,
            "screen_index": 0
        }
        
        with open(data_dir / "cursor_config.json", 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"\n✨ Position saved: ({x}, {y})")
        
        # Ask to test the position
        test = input("\nTest this position? (y/n): ").lower().strip()
        if test == 'y':
            test_movement()
        
    except Exception as e:
        print(f"\n❌ Error saving position: {e}")

def test_movement():
    """Test movement to saved position"""
    try:
        # Load saved position
        data_dir = Path("src/data/code_runner")
        config_file = data_dir / "cursor_config.json"
        
        if not config_file.exists():
            print("\n❌ No saved position found! Save a position first.")
            return
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        x, y = config["target_x"], config["target_y"]
        
        # Store current position
        current_x, current_y = pyautogui.position()
        
        print(f"\n🚀 Moving to saved position ({x}, {y}) in 3...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        
        # Move to saved position
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(1)
        
        # Move back to original position
        pyautogui.moveTo(current_x, current_y, duration=1)
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"\n❌ Error testing movement: {e}")

def main():
    """Main function with Solana Dev style intro"""
    # Clear screen
    print('\033c')
    
    # Print fancy header
    cprint("=" * 60, "cyan")
    cprint("🌙 Solana Dev's Coordinate Finder 🎯", "cyan")
    cprint("=" * 60, "cyan")
    cprint("\n📍 Move your cursor to find coordinates", "yellow")
    cprint("Instructions:", "yellow")
    cprint("  1. Move cursor to desired position", "cyan")
    cprint("  2. Press Ctrl+C to save position", "cyan")
    cprint("  3. Choose whether to test movement", "cyan")
    print("\n")
    
    # Start tracking
    print_position()

if __name__ == "__main__":
    main() 