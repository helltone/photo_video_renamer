# Photo and Video Metadata Renamer

A Python tool that recursively finds photos and videos in a directory and organizes them into a structured output directory, renaming them based on metadata in a standardized format.

## Features

- **Metadata-based naming**: Files are renamed using the format `YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext`
- **Organized structure**: Files are organized into `year/month` folders (e.g., `2023/December/`)
- **Recursive processing**: Processes all files in subdirectories
- **Multiple formats supported**: 
  - Images: JPG, JPEG, PNG, TIFF, TIF, BMP, GIF, WebP, HEIC
  - Videos: MOV, MP4
- **Smart date extraction**: Uses EXIF data for images and metadata for videos, falls back to file modification time
- **Duplicate handling**: Automatically handles duplicate files with hash-based detection and skips existing files
- **Dry run mode**: Preview what would be renamed without making changes
- **Flexible operation modes**: Copy to new location or reorganize in-place
- **Date filtering**: Option to process files starting from a specific year/month

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

### Process Files from Specific Date
```bash
python photo_video_renamer.py /path/to/photos --from-date 2023/06
```

### In-Place Organization
```bash
python photo_video_renamer.py /path/to/photos --in-place
```
This reorganizes files within the same directory into year/month folders instead of copying to a new location.

### Command Line Options
- `input_path`: Directory containing photos and videos (required)
- `-o, --output`: Custom output directory path (ignored when using --in-place)
- `--dry-run`: Preview changes without copying/moving files
- `--from-date YYYY/MM`: Start processing from specific year/month (files sorted by creation time)
- `--in-place`: Move files within same directory structure into year/month folders

## File Naming Format

Files are renamed using this format:
```
YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext
```

### Example Output Structure
```
output_directory/
├── 2023/
│   ├── December/
│   │   ├── 2023-12-25_14.30.45.1234_1920x1080_a1b2c3d4.jpg
│   │   └── 2023-12-31_23.59.59.9999_3840x2160_f5e6d7c8.mp4
│   └── November/
│       └── 2023-11-15_10.20.30.5678_1024x768_b2c3d4e5.png
└── 2024/
    └── January/
        └── 2024-01-01_00.00.01.0000_1280x720_c3d4e5f6.heic
```

### Filename Components
Example: `2023-12-25_14.30.45.1234_1920x1080_a1b2c3d4.jpg`

- `2023-12-25_14.30.45.1234`: Date and time from metadata (with 4-digit microseconds)
- `1920x1080`: Image/video dimensions (width x height)
- `a1b2c3d4`: MD5 hash (first 8 characters) for duplicate detection
- `.jpg`: Original file extension (preserved)

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

## Processing Behavior

- **File sorting**: All files are sorted by creation time (oldest first) before processing
- **Duplicate detection**: Files with identical content (same hash) are skipped if they already exist
- **Date filtering**: When using `--from-date`, only files from that year/month onwards are processed
- **Directory structure**: Files are organized into `year/month_name` folders (e.g., `2023/December`)

## Error Handling

- Files that can't be processed are skipped with error messages
- Existing files in the output directory are automatically skipped
- Missing metadata falls back to file modification time
- Hash generation failures use a default value (`00000000`)
- Invalid date formats in `--from-date` are rejected with error message

## Notes

- Hidden files (starting with '.') are automatically skipped
- Default behavior copies files to new location; use `--in-place` to move within same directory
- Month folders use full month names (January, February, etc.) for better readability
- All operations can be previewed safely using `--dry-run` before execution