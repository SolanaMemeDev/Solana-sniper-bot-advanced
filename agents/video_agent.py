"""
🎬 Solana Dev's Video Agent
Built with love by Solana Dev 🚀

This agent converts text to speech and combines it with background videos.

future ideas
- be descriptive with the broll video names in /raw_vids and later, the ai can match names with topics

"""

import os
from pathlib import Path
from dotenv import load_dotenv
import elevenlabs
import time
import traceback
import random
import subprocess
import math

# Text Input Settings
USE_TEXT_FILE = True  # Whether to use input text file by default
INPUT_TEXT_FILE = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/tweets/generated_tweets_20250127_092231.txt"

# Processing Settings
PLAY_AUDIO = False  # Whether to play audio after generation (slower if True)
DELAY_BETWEEN_REQUESTS = 1  # Seconds to wait between API calls

# Audio Settings
VOICE_ID = "Q1lWKMtcxmb76WQDCHTX"  # Default voice ID
MODEL_ID = "eleven_multilingual_v2"  # Default model
OUTPUT_FORMAT = "mp3_44100_128"  # High quality audio

# Video Settings
RAW_VIDS_DIR = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/videos/raw_vids")
FINAL_VIDS_DIR = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/videos")
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']

# Output Settings
AUDIO_DIR = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/videos/audio")

class VideoAgent:
    """Solana Dev's Video Agent 🎬"""
    
    def __init__(self):
        """Initialize the Video Agent"""
        load_dotenv()
        
        # Set ElevenLabs API key
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("🚨 ELEVENLABS_API_KEY not found in environment variables!")
        elevenlabs.set_api_key(api_key)
        
        # Create output directories if they don't exist
        self.audio_dir = AUDIO_DIR
        self.raw_vids_dir = RAW_VIDS_DIR
        self.final_vids_dir = FINAL_VIDS_DIR
        
        for dir_path in [self.audio_dir, self.raw_vids_dir, self.final_vids_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("🎬 Video Agent initialized!")
        print(f"📂 Audio files will be saved to: {self.audio_dir}")
        print(f"🎥 Raw videos directory: {self.raw_vids_dir}")
        print(f"🎞️ Final videos will be saved to: {self.final_vids_dir}")
    
    def _get_input_text(self, text=None):
        """Get input text from either file or direct input"""
        if USE_TEXT_FILE:
            try:
                print(f"📖 Reading from file: {INPUT_TEXT_FILE}")
                with open(INPUT_TEXT_FILE, 'r') as f:
                    # Read all lines and filter out empty ones
                    lines = []
                    for line in f:
                        line = line.strip()
                        # Skip empty lines or lines with just whitespace
                        if not line:
                            continue
                        # Skip lines that are just separators (like "..." or "---")
                        if all(c in '.-_=' for c in line):
                            continue
                        lines.append(line)
                    
                    print(f"📝 Found {len(lines)} non-empty lines to process")
                    return lines
                    
            except Exception as e:
                print(f"❌ Error reading text file: {str(e)}")
                print("⚠️ Falling back to direct text input if provided")
                
        return [text] if text else []
    
    def _sanitize_filename(self, text):
        """Create a safe filename from text"""
        # Take first 30 chars of text and remove invalid filename chars
        safe_text = "".join(c if c.isalnum() else '_' for c in text[:30]).rstrip('_')
        return safe_text
    
    def _get_random_video(self):
        """Get a random video file from the raw_vids directory"""
        video_files = []
        for ext in SUPPORTED_VIDEO_FORMATS:
            video_files.extend(list(self.raw_vids_dir.glob(f"*{ext}")))
        
        if not video_files:
            raise ValueError(f"❌ No video files found in {self.raw_vids_dir}")
        
        return random.choice(video_files)
    
    def _get_first_five_words(self, text):
        """Get first five words from text for filename"""
        # Split text into words and take first five
        words = text.split()[:5]
        # Join with underscores and make filename safe
        return self._sanitize_filename('_'.join(words))
    
    def _combine_audio_video(self, audio_file, video_file, text):
        """Combine audio and video files using ffmpeg with precise duration matching"""
        # Create filename from first five words of text
        video_name = self._get_first_five_words(text)
        output_file = self.final_vids_dir / f"{video_name}.mp4"
        
        try:

            # Get video duration
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 
                  'default=noprint_wrappers=1:nokey=1', str(video_file)]
            video_duration = float(subprocess.check_output(cmd).decode().strip())
            
            # Get audio duration
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                  'default=noprint_wrappers=1:nokey=1', str(audio_file)]
            audio_duration = float(subprocess.check_output(cmd).decode().strip())
            
            # If video is shorter than audio, create precise loop
            if video_duration < audio_duration:
                temp_file = self.final_vids_dir / "temp_loop.mp4"
                
                # Calculate number of full loops needed and remaining time
                full_loops = math.floor(audio_duration / video_duration)
                remaining_time = audio_duration % video_duration
                
                if remaining_time > 0:
                    # Create filter complex for precise loop + remaining portion
                    filter_complex = (
                        f"[0:v]loop={full_loops}:1:0[full];"  # Full loops
                        f"[0:v]trim=0:{remaining_time}[part];"  # Remaining portion
                        "[full][part]concat=n=2:v=1:a=0[v]"  # Concatenate them
                    )
                else:
                    # Just loop the exact number of times needed
                    filter_complex = f"[0:v]loop={full_loops-1}:1:0[v]"
                
                print(f"🎬 Creating precise loop: {full_loops} full + {remaining_time:.2f}s")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(video_file),
                    '-filter_complex', filter_complex,
                    '-map', '[v]',
                    '-t', str(audio_duration),
                    str(temp_file)
                ]
                subprocess.run(cmd, check=True)
                video_file = temp_file
            
            # Combine audio and video
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_file),
                '-i', str(audio_file),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                str(output_file)
            ]
            
            subprocess.run(cmd, check=True)
            
            # Clean up temp file if it exists
            if 'temp_file' in locals():
                temp_file.unlink()
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error combining audio and video: {str(e)}")
            raise
    
    def _video_exists(self, text):
        """Check if a video with these first five words already exists"""
        video_name = self._get_first_five_words(text)
        expected_path = self.final_vids_dir / f"{video_name}.mp4"
        return expected_path.exists()
    
    def generate_audio(self, text=None):
        """Generate audio files from text input and combine with random videos"""
        try:
            # Get input text lines
            text_lines = self._get_input_text(text)
            
            if not text_lines:
                print("❌ No input text provided and couldn't read from file")
                return None
            
            print(f"\n📊 Text Analysis:")
            print(f"Total lines to process: {len(text_lines):,}")
            print("=" * 50)
            
            # Process each line
            for i, line in enumerate(text_lines, 1):
                print(f"\n🔄 Processing line {i}/{len(text_lines)}")
                print(f"Text: {line[:100]}..." if len(line) > 100 else f"Text: {line}")
                
                try:
                    # Skip very short lines or likely headers
                    if len(line) < 10 or line.endswith(':'):
                        print("⏩ Skipping short line or header")
                        continue
                    
                    # Check if video already exists
                    if self._video_exists(line):
                        video_name = self._get_first_five_words(line)
                        print(f"🔄 Skipping duplicate video: {video_name}.mp4")
                        continue
                        
                    # Generate audio using simpler API
                    audio = elevenlabs.generate(
                        text=line,
                        voice=VOICE_ID,
                        model=MODEL_ID
                    )
                    
                    # Create filename from text
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    safe_name = self._sanitize_filename(line)
                    audio_filename = f"audio_{timestamp}_{safe_name}.mp3"
                    audio_filepath = self.audio_dir / audio_filename
                    
                    # Save audio file
                    with open(audio_filepath, 'wb') as f:
                        f.write(audio)
                    
                    print(f"✨ Generated audio: {audio_filename}")
                    
                    # Get random video and combine with audio
                    video_file = self._get_random_video()
                    print(f"🎥 Selected random video: {video_file.name}")
                    
                    final_video = self._combine_audio_video(audio_filepath, video_file, line)
                    print(f"🎞️ Created final video: {final_video.name}")
                    
                    # Play audio if enabled
                    if PLAY_AUDIO:
                        print("🔊 Playing audio...")
                        elevenlabs.play(audio)
                    
                    # Delay between requests
                    if i < len(text_lines):
                        time.sleep(DELAY_BETWEEN_REQUESTS)
                        
                except Exception as e:
                    print(f"⚠️ Error processing line {i}: {str(e)}")
                    traceback.print_exc()
                    continue
            
            print(f"\n🎉 Processing complete!")
            print(f"📂 Audio files saved in: {self.audio_dir}")
            print(f"🎬 Final videos saved in: {self.final_vids_dir}")
            
        except Exception as e:
            print(f"❌ Error in processing: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    agent = VideoAgent()
    
    # Example usage with direct text
    test_text = "Solana Dev's AI agents are revolutionizing trading with deep seek integration."
    
    # If USE_TEXT_FILE is True, it will use the file instead of test_text
    agent.generate_audio(test_text)
