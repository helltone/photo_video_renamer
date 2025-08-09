# Photo and Video Metadata Renamer

A Python tool that recursively finds photos and videos in a directory and copies them to a flat output directory, renaming them based on metadata in a standardized format.

## Features

- **Metadata-based naming**: Files are renamed using the format `YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext`
- **Recursive processing**: Processes all files in subdirectories
- **Multiple formats supported**: 
  - Images: JPG, JPEG, PNG, TIFF, TIF, BMP, GIF, WebP, HEIC
  - Videos: MOV, MP4
- **Smart date extraction**: Uses EXIF data for images and metadata for videos, falls back to file modification time
- **Duplicate handling**: Automatically handles duplicate files with hash-based detection
- **Dry run mode**: Preview what would be renamed without making changes
- **Flat output structure**: All files are copied to a single output directory

## Installation

### Requirements
- Python 3.6+
- ffprobe (part of FFmpeg) for video metadata extraction

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install FFmpeg
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Basic Usage
```bash
python photo_video_renamer.py /path/to/photos
```
This creates an output directory named `/path/to/photos_renamed`.

### Custom Output Directory
```bash
python photo_video_renamer.py /path/to/photos -o /path/to/output
```

### Dry Run (Preview Only)
```bash
python photo_video_renamer.py /path/to/photos --dry-run
```

### Command Line Options
- `input_path`: Directory containing photos and videos (required)
- `-o, --output`: Custom output directory path (optional)
- `--dry-run`: Preview changes without copying files

## File Naming Format

Files are renamed using this format:
```
YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext
```

### Example
```
2023-12-25_14.30.45.1234_1920x1080_a1b2c3d4.jpg
```

Where:
- `2023-12-25_14.30.45.1234`: Date and time from metadata (with microseconds)
- `1920x1080`: Image/video dimensions
- `a1b2c3d4`: MD5 hash (first 8 characters) for duplicate detection
- `.jpg`: Original file extension

## Metadata Sources

- **Images**: EXIF data (DateTime or DateTimeOriginal tags)
- **Videos**: FFprobe metadata (creation_time, date, datetime fields)
- **Fallback**: File modification time if no metadata is found

## Supported File Formats

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- BMP (.bmp)
- GIF (.gif)
- WebP (.webp)
- HEIC (.heic)

### Videos
- MP4 (.mp4)
- MOV (.mov)

## Error Handling

- Files that can't be processed are skipped with error messages
- Existing files in the output directory are skipped
- Missing metadata falls back to file modification time
- Hash generation failures use a default value

## Notes

- Hidden files (starting with '.') are automatically skipped
- The tool preserves original files - they are copied, not moved
- All output files are placed in a flat directory structure regardless of input directory hierarchy