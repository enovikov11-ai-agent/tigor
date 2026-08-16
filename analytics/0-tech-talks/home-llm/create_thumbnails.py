#!/usr/bin/env python3
from PIL import Image
import os
import sys

def create_thumbnail(input_path, output_path, max_size=1000):
    """Create a thumbnail with max dimension of max_size pixels"""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode:
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background

            # Calculate new size maintaining aspect ratio
            width, height = img.size
            if width > height:
                if width > max_size:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_width, new_height = width, height
            else:
                if height > max_size:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width, new_height = width, height

            # Resize and save
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            print(f"Created: {output_path} ({new_width}x{new_height})")
            return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False

# List of all images
images = [
    "/home/coder/presentation/images/image1.png",
    "/home/coder/presentation/images/image2.png",
    "/home/coder/presentation/images/image3.png",
    "/home/coder/presentation/images/image4.png",
    "/home/coder/presentation/images/image5.png",
    "/home/coder/presentation/images/image6.png",
    "/home/coder/presentation/images/image7.png",
    "/home/coder/presentation/images/image8.jpg",
    "/home/coder/presentation/images/image9.jpg",
    "/home/coder/presentation/images/image10.png",
    "/home/coder/presentation/images/image11.jpg",
    "/home/coder/presentation/images/image12.jpg",
    "/home/coder/presentation/images/image13.png",
    "/home/coder/presentation/images/image14.jpg",
    "/home/coder/presentation/images/image15.png",
    "/home/coder/presentation/images/image16.jpg",
    "/home/coder/presentation/images/image17.png",
    "/home/coder/presentation/images/image18.png",
    "/home/coder/presentation/images/image19.png",
    "/home/coder/presentation/images/image20.png",
    "/home/coder/presentation/images/image21.png",
    "/home/coder/presentation/images/image22.jpg",
    "/home/coder/presentation/images/image23.png",
    "/home/coder/presentation/images/image24.png",
    "/home/coder/presentation/images/image25.png",
    "/home/coder/presentation/images/image26.png",
    "/home/coder/presentation/images/image27.jpg",
    "/home/coder/presentation/images/image28.png",
    "/home/coder/presentation/images/image29.png",
    "/home/coder/presentation/images/image30.jpg",
    "/home/coder/presentation/images/image31.png",
    "/home/coder/presentation/images/image32.jpg",
    "/home/coder/presentation/images/image33.jpg",
    "/home/coder/presentation/images/image34.jpg",
    "/home/coder/presentation/images/image35.gif",
    "/home/coder/presentation/images/image36.gif",
]

os.makedirs("/home/coder/presentation/thumbnails", exist_ok=True)

for img_path in images:
    filename = os.path.basename(img_path)
    name_without_ext = os.path.splitext(filename)[0]
    output_path = f"/home/coder/presentation/thumbnails/{name_without_ext}.jpg"
    create_thumbnail(img_path, output_path)

print("\nAll thumbnails created successfully!")
