#!/usr/bin/env python3
"""
Photo and Video Metadata Renamer
Recursively finds photos and videos in input directory and copies them to a structured output directory,
organizing them into year/month folders and renaming them based on metadata in format: 
YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH
Output directory defaults to input_path + '_renamed'
Use --in-place to move files within the same directory structure instead of copying
"""

import os
import sys
import hashlib
import shutil
import subprocess
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import argparse
import json
from pillow_heif import register_heif_opener

register_heif_opener()


def get_image_metadata(image_path):
    """Extract metadata from image file."""
    try:
        with Image.open(image_path) as image:
            # Get image dimensions
            width, height = image.size
            
            # Get EXIF data
            exifdata = image.getexif()
            
            # Extract date/time
            date_taken = None
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                data = exifdata.get(tag_id)
                
                if tag == "DateTime" or tag == "DateTimeOriginal":
                    try:
                        date_taken = datetime.strptime(data, "%Y:%m:%d %H:%M:%S")
                        break
                    except ValueError:
                        continue
            
            # If no EXIF date, use file modification time
            if date_taken is None:
                mtime = os.path.getmtime(image_path)
                date_taken = datetime.fromtimestamp(mtime)
            
            return date_taken, width, height
            
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None, None, None


def get_video_metadata(video_path):
    """Extract metadata from video file using ffprobe."""
    try:
        # Use ffprobe to get video metadata
        cmd = [
            'ffprobe', 
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffprobe failed for {video_path}: {result.stderr}")
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        
        # Get video stream (first video stream found)
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise Exception("No video stream found")
        
        # Get dimensions
        width = video_stream.get('width')
        height = video_stream.get('height')
        
        if not width or not height:
            raise Exception("Could not determine video dimensions")
        
        # Try to get creation date from metadata
        date_taken = None
        format_info = data.get('format', {})
        tags = format_info.get('tags', {})
        
        # Try different date fields
        date_fields = ['creation_time', 'date', 'datetime']
        for field in date_fields:
            if field in tags:
                try:
                    # Handle ISO format datetime
                    date_str = tags[field]
                    if 'T' in date_str:
                        date_str = date_str.replace('T', ' ').split('.')[0]
                        if date_str.endswith('Z'):
                            date_str = date_str[:-1]
                    date_taken = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    break
                except ValueError:
                    continue
        
        # If no metadata date, use file modification time
        if date_taken is None:
            mtime = os.path.getmtime(video_path)
            date_taken = datetime.fromtimestamp(mtime)
        
        return date_taken, width, height
        
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return None, None, None


def get_file_metadata(file_path):
    """Get metadata from photo or video file."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Video formats
    if file_ext in {'.mov', '.mp4'}:
        return get_video_metadata(file_path)
    # Image formats (including HEIC)
    else:
        return get_image_metadata(file_path)


def generate_hash(file_path, length=8):
    """Generate hash from file content."""
    hash_obj = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()[:length]
    except Exception as e:
        print(f"Error generating hash for {file_path}: {e}")
        return "00000000"


def copy_and_rename_file(file_path, output_dir, dry_run=False, in_place=False):
    """Copy and rename photo or video to output directory based on metadata."""
    filename = os.path.basename(file_path)
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Get metadata
    date_taken, width, height = get_file_metadata(file_path)
    
    if date_taken is None or width is None or height is None:
        print(f"Could not extract metadata from {filename}")
        return False
    
    # Generate hash
    file_hash = generate_hash(file_path)
    
    # Format date with microseconds (4 digits)
    microseconds = str(date_taken.microsecond).zfill(6)[:4]
    date_str = date_taken.strftime("%Y-%m-%d_%H.%M.%S")
    date_str += f".{microseconds}"
    
    # Create structured folder: year/month (month as readable name)
    year = date_taken.strftime("%Y")
    month = date_taken.strftime("%B")  # Full month name (e.g., "January")
    structured_dir = os.path.join(output_dir, year, month)
    
    # Create new filename
    new_filename = f"{date_str}_{width}x{height}_{file_hash}{file_ext}"
    new_path = os.path.join(structured_dir, new_filename)
    
    # Check if file already exists and skip if it does
    if os.path.exists(new_path):
        if dry_run:
            operation = "move" if in_place else "copy"
            print(f"Would skip (already exists): {filename} -> {os.path.relpath(new_path, output_dir)}")
        else:
            print(f"Skipped (already exists): {filename} -> {os.path.relpath(new_path, output_dir)}")
        return True
    
    # Handle duplicate filenames by adding counter (this part is now redundant but kept for safety)
    counter = 1
    original_new_path = new_path
    while os.path.exists(new_path):
        name_without_ext = os.path.splitext(original_new_path)[0]
        new_path = f"{name_without_ext}_{counter:03d}{file_ext}"
        counter += 1
    
    if dry_run:
        operation = "move" if in_place else "copy"
        print(f"Would {operation}: {filename} -> {os.path.relpath(new_path, output_dir)}")
        return True
    
    # Create directory structure if it doesn't exist
    os.makedirs(structured_dir, exist_ok=True)
    
    try:
        if in_place:
            shutil.move(file_path, new_path)
            print(f"Moved: {filename} -> {os.path.relpath(new_path, output_dir)}")
        else:
            shutil.copy2(file_path, new_path)
            print(f"Copied: {filename} -> {os.path.relpath(new_path, output_dir)}")
        return True
    except Exception as e:
        operation = "moving" if in_place else "copying"
        print(f"Error {operation} {filename}: {e}")
        return False


def find_media_files_recursively(directory_path):
    """Generate all image and video files recursively in directory and subdirectories."""
    supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.heic', '.mov', '.mp4'}
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Skip dot-prefixed files (hidden files like .DS_Store, thumbnails, etc.)
            if file.startswith('.'):
                continue
            if os.path.splitext(file)[1].lower() in supported_formats:
                yield os.path.join(root, file)


def process_directory(input_directory, output_directory, dry_run=False, start_year_month=None, in_place=False):
    """Process all images and videos in directory recursively and copy/move to structured output."""
    if not os.path.isdir(input_directory):
        print(f"Input directory not found: {input_directory}")
        return
    
    # Get all media files and their metadata for sorting
    print("Scanning media files and extracting metadata...")
    media_files_with_metadata = []
    
    for file_path in find_media_files_recursively(input_directory):
        date_taken, width, height = get_file_metadata(file_path)
        if date_taken is not None:
            media_files_with_metadata.append((file_path, date_taken))
        else:
            print(f"Skipping {os.path.basename(file_path)} - could not extract metadata")
    
    if not media_files_with_metadata:
        print("No supported image or video files with valid metadata found in directory tree")
        return
    
    # Sort files by creation time (oldest first)
    media_files_with_metadata.sort(key=lambda x: x[1])
    
    # Filter files to start from specified year/month if provided
    if start_year_month:
        try:
            start_year, start_month = map(int, start_year_month.split('/'))
            filtered_files = []
            for file_path, date_taken in media_files_with_metadata:
                if date_taken.year > start_year or (date_taken.year == start_year and date_taken.month >= start_month):
                    filtered_files.append(file_path)
            media_files = filtered_files
            print(f"Found {len(media_files)} files from {start_year_month} onwards (sorted by creation time)")
        except ValueError:
            print(f"Invalid year/month format: {start_year_month}. Expected format: YYYY/MM")
            return
    else:
        media_files = [file_path for file_path, _ in media_files_with_metadata]
        print(f"Processing all {len(media_files)} files sorted by creation time")
    
    # Create output directory if it doesn't exist and not in dry run mode
    if not dry_run and not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")
    
    success_count = 0
    total_count = 0
    
    print("Processing media files...")
    for file_path in media_files:
        total_count += 1
        if copy_and_rename_file(file_path, output_directory, dry_run, in_place):
            success_count += 1
    
    if total_count == 0:
        print("No files to process after filtering")
    else:
        print(f"\nProcessed {success_count}/{total_count} files successfully")


def main():
    parser = argparse.ArgumentParser(description="Copy and rename photos and videos based on metadata to new directory")
    parser.add_argument("input_path", help="Input directory path containing photos and videos")
    parser.add_argument("--output", "-o", help="Output directory path (defaults to input_path_renamed)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied/renamed without actually doing it")
    parser.add_argument("--from-date", help="Start copying from this year/month onwards (format: YYYY/MM). Files will be sorted by creation time and copying will start from this date.")
    parser.add_argument("--in-place", action="store_true", help="Move files within the same directory structure into year/month folders instead of copying to a new location")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_path):
        print(f"Input path not found: {args.input_path}")
        sys.exit(1)
    
    if not os.path.isdir(args.input_path):
        print(f"Input path must be a directory: {args.input_path}")
        sys.exit(1)
    
    # Handle in-place vs normal operation
    if args.in_place:
        if args.output:
            print("Warning: --output is ignored when using --in-place")
        output_directory = args.input_path
    else:
        # Determine output directory
        if args.output:
            output_directory = args.output
        else:
            # Create output directory with '_renamed' suffix
            output_directory = args.input_path.rstrip('/') + '_renamed'
        
        # Check if output directory already exists
        if os.path.exists(output_directory) and not args.dry_run:
            response = input(f"Output directory '{output_directory}' already exists. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                sys.exit(0)
    
    process_directory(args.input_path, output_directory, args.dry_run, args.from_date, args.in_place)


if __name__ == "__main__":
    main()