from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image():
    # Create a 300x300 white image
    img = Image.new('RGB', (300, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a gray rectangle border
    draw.rectangle([(10, 10), (290, 290)], outline='gray', width=2)
    
    # Add text
    text = "No Image"
    text_color = 'gray'
    
    # Try to use a system font
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate text position (center)
    x = (300 - text_width) // 2
    y = (300 - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill=text_color)
    
    # Save the image
    if not os.path.exists('static'):
        os.makedirs('static')
    img.save('static/placeholder.jpg', 'JPEG')

if __name__ == '__main__':
    create_placeholder_image() 