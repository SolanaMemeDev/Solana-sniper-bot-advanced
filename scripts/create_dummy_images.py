from PIL import Image, ImageDraw, ImageFont
import os

def create_dummy_image(filename, text):
    # Create a 1280x720 image (16:9 aspect ratio)
    img = Image.new('RGB', (1280, 720), color='#1F2937')
    d = ImageDraw.Draw(img)
    
    # Add some text
    d.text((640, 360), text, fill='white', anchor="mm", font=None)
    
    # Save the image
    img.save(f'src/frontend/static/images/agents/{filename}.png')

# Create dummy images
create_dummy_image('trading-assistant', 'Trading Assistant')
create_dummy_image('research', 'Research Agent')
create_dummy_image('feature1', 'Feature 1') 