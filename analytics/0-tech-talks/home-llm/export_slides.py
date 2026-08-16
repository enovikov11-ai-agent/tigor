#!/usr/bin/env python3
"""
Export PowerPoint slides to JPG images with max dimension of 1000px
"""
import os
import sys
from pptx import Presentation
from PIL import Image
import io

def export_slides_to_jpg(pptx_path, output_dir="slides", max_size=1000):
    """
    Export PowerPoint slides to JPG images

    Note: python-pptx doesn't directly support rendering slides to images.
    We'll need to use LibreOffice or other tools for actual conversion.
    """
    print(f"PowerPoint file: {pptx_path}")

    # Check if file exists
    if not os.path.exists(pptx_path):
        print(f"Error: File {pptx_path} not found!")
        return False

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load presentation to get slide count
    try:
        prs = Presentation(pptx_path)
        slide_count = len(prs.slides)
        print(f"Found {slide_count} slides in presentation")
    except Exception as e:
        print(f"Error loading presentation: {e}")
        return False

    # We need LibreOffice to convert PPTX to images
    print("\nUsing LibreOffice to convert slides to images...")

    # Create temporary directory for full-size exports
    temp_dir = os.path.join(output_dir, "temp_full_size")
    os.makedirs(temp_dir, exist_ok=True)

    # Convert PPTX to PDF first, then to images using pdftoppm or similar
    # LibreOffice exports each slide separately when converting to PDF
    pdf_path = os.path.join(temp_dir, "presentation.pdf")
    cmd = f'libreoffice --headless --convert-to pdf --outdir "{temp_dir}" "{pptx_path}"'
    print(f"Running: {cmd}")
    result = os.system(cmd)

    if result != 0:
        print(f"Error: LibreOffice conversion failed with code {result}")
        return False

    # Convert PDF to PNG images using pdftoppm
    print("\nConverting PDF pages to PNG images...")
    pdf_file = os.path.join(temp_dir, "presentation.pdf")
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file not created at {pdf_file}")
        return False

    # Use pdftoppm to convert PDF to images (one per page)
    cmd = f'pdftoppm -png "{pdf_file}" "{os.path.join(temp_dir, "slide")}"'
    print(f"Running: {cmd}")
    result = os.system(cmd)

    if result != 0:
        print(f"Error: pdftoppm conversion failed with code {result}")
        return False

    # Now resize the exported images to max 1000px
    print(f"\nResizing images to max {max_size}px...")
    exported_files = sorted([f for f in os.listdir(temp_dir) if f.endswith('.png')])

    if not exported_files:
        print("No PNG files found after conversion!")
        return False

    for i, filename in enumerate(exported_files, 1):
        input_path = os.path.join(temp_dir, filename)
        output_path = os.path.join(output_dir, f"slide_{i:02d}.jpg")

        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if necessary
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

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Clean up temporary directory
    print("\nCleaning up temporary files...")
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)

    print(f"\nAll slides exported successfully to {output_dir}/")
    return True

if __name__ == "__main__":
    pptx_file = "/home/coder/presentation/presentation.pptx"
    output_directory = "/home/coder/presentation/slides"

    success = export_slides_to_jpg(pptx_file, output_directory, max_size=1000)
    sys.exit(0 if success else 1)
