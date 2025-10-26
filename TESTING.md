# Testing Guide

This document explains how to run and understand the tests for the Photo and Video Metadata Renamer.

## Test Suite Overview

The test suite contains **31 comprehensive tests** covering all major functionality:

- File validation and processable media detection
- Hash generation and consistency
- Image metadata extraction
- Video metadata extraction (with mocked ffprobe)
- File discovery and recursive search
- File copying and renaming logic
- Directory processing and integration tests
- Format support and constants

## Running Tests

### Quick Start

```bash
# Activate virtual environment
source bin/activate

# Run all tests
python -m unittest test_photo_video_renamer -v
```

### Alternative: Run specific test classes

```bash
# Test only hash generation
python -m unittest test_photo_video_renamer.TestGenerateHash -v

# Test only image metadata
python -m unittest test_photo_video_renamer.TestGetImageMetadata -v

# Test file validation
python -m unittest test_photo_video_renamer.TestIsProcessableMediaFile -v
```

### Alternative: Run specific test methods

```bash
# Run a single test
python -m unittest test_photo_video_renamer.TestGenerateHash.test_hash_consistency -v
```

## Test Coverage

### 1. File Validation Tests (`TestIsProcessableMediaFile`)
- ✓ Valid image files are accepted
- ✓ Files too small (<100 bytes) are rejected
- ✓ Nonexistent files are handled gracefully
- ✓ Corrupted image files are rejected
- ✓ Unsupported formats are rejected

### 2. Hash Generation Tests (`TestGenerateHash`)
- ✓ Hash generation produces 8-character hex strings
- ✓ Same content produces same hash (consistency)
- ✓ Different content produces different hashes
- ✓ Large files use partial hashing (performance)
- ✓ Error handling for missing files

### 3. Image Metadata Tests (`TestGetImageMetadata`)
- ✓ Image dimensions are extracted correctly
- ✓ Falls back to modification time when EXIF missing
- ✓ Invalid image files return None values

### 4. Video Metadata Tests (`TestGetVideoMetadata`)
- ✓ Video metadata extraction (mocked ffprobe)
- ✓ Handles videos without creation_time metadata
- ✓ Graceful handling of ffprobe failures

### 5. File Discovery Tests (`TestFindMediaFilesRecursively`)
- ✓ Finds image files recursively
- ✓ Skips hidden files (starting with .)
- ✓ Skips unsupported file formats
- ✓ Case-insensitive file extension matching

### 6. Copy and Rename Tests (`TestCopyAndRenameFile`)
- ✓ Dry run mode doesn't create files
- ✓ Correct filename format (YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext)
- ✓ Creates year/month directory structure
- ✓ Skips existing files (duplicate detection)
- ✓ In-place mode moves files correctly

### 7. Integration Tests (`TestProcessDirectory`)
- ✓ Processes multiple files correctly
- ✓ Handles invalid input directories
- ✓ Handles empty directories

### 8. Format Support Tests (`TestSupportedFormats`)
- ✓ Format constants are defined
- ✓ SUPPORTED_FORMATS is union of image and video formats
- ✓ Common formats are included

## Test Output

Successful test run shows:

```
Ran 31 tests in 0.3s

OK
```

## Continuous Integration

The test suite is designed to run quickly (~0.3 seconds) and can be integrated into CI/CD pipelines:

```bash
# Example CI command
source bin/activate && python -m unittest test_photo_video_renamer
```

## Test Dependencies

The tests use Python's built-in `unittest` framework, so no additional test dependencies are required. However, the same runtime dependencies apply:

- Pillow (PIL)
- pillow_heif

For development tools, see `requirements-dev.txt`.

## Writing New Tests

When adding new functionality, follow these guidelines:

1. **Create a test class** for the new function or module:
   ```python
   class TestNewFeature(unittest.TestCase):
       def setUp(self):
           # Setup code

       def tearDown(self):
           # Cleanup code
   ```

2. **Use descriptive test names** that explain what is being tested:
   ```python
   def test_feature_handles_edge_case(self):
       """Test that feature correctly handles edge case."""
   ```

3. **Use temporary directories** for file-based tests:
   ```python
   self.test_dir = tempfile.mkdtemp()
   # ... tests ...
   shutil.rmtree(self.test_dir)
   ```

4. **Mock external dependencies** like ffprobe:
   ```python
   @patch('photo_video_renamer.subprocess.run')
   def test_video_processing(self, mock_run):
       mock_run.return_value = MagicMock(returncode=0, stdout='...')
   ```

## Test Maintenance

- Run tests before committing changes
- Update tests when changing functionality
- Add tests for bug fixes to prevent regression
- Keep test execution time under 1 second when possible

## Troubleshooting

### Tests fail with "No module named 'PIL'"

Activate the virtual environment:
```bash
source bin/activate
```

### Tests fail with temporary directory errors

Ensure you have write permissions in `/tmp` or set `TMPDIR`:
```bash
export TMPDIR=/path/to/writable/temp
```

### ffprobe-related tests fail

Video tests use mocked ffprobe, so they should work without ffmpeg installed. If they fail, check the mock setup.

## Code Coverage

To generate coverage reports (requires `coverage` package):

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m unittest test_photo_video_renamer
coverage report
coverage html  # Generates HTML report in htmlcov/
```

Expected coverage: **~85-90%** (some error handling paths are hard to test)
