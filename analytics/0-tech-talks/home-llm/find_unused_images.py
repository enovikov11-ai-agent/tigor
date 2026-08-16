#!/usr/bin/env python3
"""
Script to find unused images in the presentation.
Compares images in ./images/ directory with images referenced in index.html
"""

import os
import re
from pathlib import Path

def get_images_from_directory(images_dir="./images"):
    """Get all image files from the images directory"""
    if not os.path.exists(images_dir):
        print(f"Error: Directory '{images_dir}' not found")
        return set()

    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
    images = set()

    for file in os.listdir(images_dir):
        if Path(file).suffix.lower() in image_extensions:
            images.add(file)

    return images

def get_images_from_html(html_file="index.html"):
    """Extract all image references from index.html"""
    if not os.path.exists(html_file):
        print(f"Error: File '{html_file}' not found")
        return set()

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all image references in src attributes
    # Pattern matches: src="images/imagename.ext" or src="./images/imagename.ext"
    pattern = r'src=["\'](?:\./)?images/([^"\']+)["\']'
    matches = re.findall(pattern, content)

    return set(matches)

def main():
    print("=" * 60)
    print("Unused Images Finder")
    print("=" * 60)

    # Get images from directory
    dir_images = get_images_from_directory()
    print(f"\nTotal images in ./images/ directory: {len(dir_images)}")

    # Get images referenced in HTML
    html_images = get_images_from_html()
    print(f"Total images referenced in index.html: {len(html_images)}")

    # Find unused images
    unused_images = dir_images - html_images

    print("\n" + "=" * 60)
    if unused_images:
        print(f"UNUSED IMAGES ({len(unused_images)}):")
        print("=" * 60)
        for img in sorted(unused_images):
            print(f"  - {img}")
    else:
        print("All images are being used!")
        print("=" * 60)

    # Show which images are being used (optional)
    print(f"\n" + "=" * 60)
    print(f"USED IMAGES ({len(html_images)}):")
    print("=" * 60)
    for img in sorted(html_images):
        print(f"  - {img}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Total images in directory: {len(dir_images)}")
    print(f"Images used in HTML: {len(html_images)}")
    print(f"Unused images: {len(unused_images)}")
    print(f"Usage percentage: {(len(html_images)/len(dir_images)*100):.1f}%")

if __name__ == "__main__":
    main()
