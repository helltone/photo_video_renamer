#!/usr/bin/env python3
"""
Tests for Photo and Video Metadata Renamer
"""

import os
import sys
import tempfile
import shutil
import hashlib
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from PIL import Image
import io

# Import the module to test
import photo_video_renamer as pvr


class TestIsProcessableMediaFile(unittest.TestCase):
    """Tests for is_processable_media_file function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_valid_image_file(self):
        """Test that valid image file returns True."""
        # Create a valid test image
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)

        is_valid, error = pvr.is_processable_media_file(img_path)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_file_too_small(self):
        """Test that very small files are rejected."""
        small_file = os.path.join(self.test_dir, "tiny.jpg")
        with open(small_file, 'wb') as f:
            f.write(b'small')  # Less than 100 bytes

        is_valid, error = pvr.is_processable_media_file(small_file)
        self.assertFalse(is_valid)
        self.assertIn("too small", error.lower())

    def test_nonexistent_file(self):
        """Test that nonexistent file returns False."""
        fake_path = os.path.join(self.test_dir, "nonexistent.jpg")
        is_valid, error = pvr.is_processable_media_file(fake_path)
        self.assertFalse(is_valid)
        self.assertIn("cannot access", error.lower())

    def test_corrupted_image(self):
        """Test that corrupted image file is rejected."""
        corrupt_file = os.path.join(self.test_dir, "corrupt.jpg")
        with open(corrupt_file, 'wb') as f:
            f.write(b'x' * 200)  # Random bytes, not a valid image

        is_valid, error = pvr.is_processable_media_file(corrupt_file)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_unsupported_format(self):
        """Test that unsupported file format is rejected."""
        txt_file = os.path.join(self.test_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("This is not an image" * 20)  # Make it bigger than 100 bytes

        is_valid, error = pvr.is_processable_media_file(txt_file)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Unsupported format")


class TestGenerateHash(unittest.TestCase):
    """Tests for generate_hash function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_hash_generation(self):
        """Test that hash is generated correctly."""
        test_file = os.path.join(self.test_dir, "test.dat")
        with open(test_file, 'wb') as f:
            f.write(b'test content')

        file_hash = pvr.generate_hash(test_file)
        self.assertEqual(len(file_hash), 8)
        self.assertTrue(all(c in '0123456789abcdef' for c in file_hash))

    def test_hash_consistency(self):
        """Test that same content produces same hash."""
        test_file1 = os.path.join(self.test_dir, "test1.dat")
        test_file2 = os.path.join(self.test_dir, "test2.dat")

        content = b'identical content'
        with open(test_file1, 'wb') as f:
            f.write(content)
        with open(test_file2, 'wb') as f:
            f.write(content)

        hash1 = pvr.generate_hash(test_file1)
        hash2 = pvr.generate_hash(test_file2)
        self.assertEqual(hash1, hash2)

    def test_hash_different_for_different_content(self):
        """Test that different content produces different hashes."""
        test_file1 = os.path.join(self.test_dir, "test1.dat")
        test_file2 = os.path.join(self.test_dir, "test2.dat")

        with open(test_file1, 'wb') as f:
            f.write(b'content one')
        with open(test_file2, 'wb') as f:
            f.write(b'content two')

        hash1 = pvr.generate_hash(test_file1)
        hash2 = pvr.generate_hash(test_file2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_partial_for_large_files(self):
        """Test that large files only hash first portion."""
        test_file = os.path.join(self.test_dir, "large.dat")
        # Create 20MB file
        with open(test_file, 'wb') as f:
            f.write(b'x' * (20 * 1024 * 1024))

        # Hash with 1MB limit
        file_hash = pvr.generate_hash(test_file, partial_size_mb=1)
        self.assertEqual(len(file_hash), 8)

    def test_hash_error_handling(self):
        """Test hash generation with nonexistent file."""
        fake_file = os.path.join(self.test_dir, "nonexistent.dat")
        file_hash = pvr.generate_hash(fake_file)
        self.assertEqual(file_hash, "00000000")


class TestGetImageMetadata(unittest.TestCase):
    """Tests for get_image_metadata function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_image_dimensions(self):
        """Test that image dimensions are extracted correctly."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (640, 480), color='blue')
        img.save(img_path)

        date_taken, width, height = pvr.get_image_metadata(img_path)
        self.assertEqual(width, 640)
        self.assertEqual(height, 480)
        self.assertIsInstance(date_taken, datetime)

    def test_image_fallback_to_mtime(self):
        """Test that image without EXIF falls back to modification time."""
        img_path = os.path.join(self.test_dir, "test.png")
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        date_taken, width, height = pvr.get_image_metadata(img_path)
        self.assertIsNotNone(date_taken)
        self.assertIsInstance(date_taken, datetime)

    def test_invalid_image_file(self):
        """Test error handling for invalid image."""
        invalid_path = os.path.join(self.test_dir, "invalid.jpg")
        with open(invalid_path, 'wb') as f:
            f.write(b'not an image')

        date_taken, width, height = pvr.get_image_metadata(invalid_path)
        self.assertIsNone(date_taken)
        self.assertIsNone(width)
        self.assertIsNone(height)


class TestGetVideoMetadata(unittest.TestCase):
    """Tests for get_video_metadata function."""

    @patch('photo_video_renamer.subprocess.run')
    def test_video_metadata_extraction(self, mock_run):
        """Test video metadata extraction with mocked ffprobe."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [{
                "codec_type": "video",
                "width": 1920,
                "height": 1080
            }],
            "format": {
                "tags": {
                    "creation_time": "2023-12-25T14:30:45.000000Z"
                }
            }
        }
        '''
        mock_run.return_value = mock_result

        date_taken, width, height = pvr.get_video_metadata("test.mp4")
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1080)
        self.assertIsInstance(date_taken, datetime)
        self.assertEqual(date_taken.year, 2023)
        self.assertEqual(date_taken.month, 12)
        self.assertEqual(date_taken.day, 25)

    @patch('photo_video_renamer.subprocess.run')
    def test_video_without_creation_time(self, mock_run):
        """Test video metadata when no creation_time in metadata."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [{
                "codec_type": "video",
                "width": 1280,
                "height": 720
            }],
            "format": {
                "tags": {}
            }
        }
        '''
        mock_run.return_value = mock_result

        # Mock getmtime to return known timestamp
        with patch('photo_video_renamer.os.path.getmtime', return_value=1609459200.0):
            date_taken, width, height = pvr.get_video_metadata("test.mp4")
            self.assertIsInstance(date_taken, datetime)
            self.assertEqual(width, 1280)
            self.assertEqual(height, 720)

    @patch('photo_video_renamer.subprocess.run')
    def test_video_ffprobe_failure(self, mock_run):
        """Test handling of ffprobe failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error processing video"
        mock_run.return_value = mock_result

        date_taken, width, height = pvr.get_video_metadata("test.mp4")
        self.assertIsNone(date_taken)
        self.assertIsNone(width)
        self.assertIsNone(height)


class TestFindMediaFilesRecursively(unittest.TestCase):
    """Tests for find_media_files_recursively function."""

    def setUp(self):
        """Create temporary directory structure."""
        self.test_dir = tempfile.mkdtemp()
        # Create subdirectories
        self.subdir1 = os.path.join(self.test_dir, "dir1")
        self.subdir2 = os.path.join(self.test_dir, "dir2")
        os.makedirs(self.subdir1)
        os.makedirs(self.subdir2)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_finds_image_files(self):
        """Test that image files are found recursively."""
        # Create test images
        img1_path = os.path.join(self.test_dir, "test1.jpg")
        img2_path = os.path.join(self.subdir1, "test2.png")

        for path in [img1_path, img2_path]:
            img = Image.new('RGB', (100, 100))
            img.save(path)

        found_files = list(pvr.find_media_files_recursively(self.test_dir))
        found_names = [os.path.basename(f) for f in found_files]

        self.assertIn("test1.jpg", found_names)
        self.assertIn("test2.png", found_names)

    def test_skips_hidden_files(self):
        """Test that hidden files (starting with .) are skipped."""
        # Create hidden file
        hidden_img = os.path.join(self.test_dir, ".hidden.jpg")
        img = Image.new('RGB', (100, 100))
        img.save(hidden_img)

        found_files = list(pvr.find_media_files_recursively(self.test_dir))
        found_names = [os.path.basename(f) for f in found_files]

        self.assertNotIn(".hidden.jpg", found_names)

    def test_skips_unsupported_formats(self):
        """Test that unsupported file formats are skipped."""
        # Create text file
        txt_file = os.path.join(self.test_dir, "readme.txt")
        with open(txt_file, 'w') as f:
            f.write("Not an image")

        found_files = list(pvr.find_media_files_recursively(self.test_dir))
        found_names = [os.path.basename(f) for f in found_files]

        self.assertNotIn("readme.txt", found_names)

    def test_case_insensitive_extensions(self):
        """Test that file extensions are case-insensitive."""
        # Create images with different case extensions
        img_upper = os.path.join(self.test_dir, "test.JPG")
        img_lower = os.path.join(self.test_dir, "test2.jpg")

        for path in [img_upper, img_lower]:
            img = Image.new('RGB', (100, 100))
            img.save(path)

        found_files = list(pvr.find_media_files_recursively(self.test_dir))
        found_names = [os.path.basename(f) for f in found_files]

        self.assertIn("test.JPG", found_names)
        self.assertIn("test2.jpg", found_names)


class TestCopyAndRenameFile(unittest.TestCase):
    """Tests for copy_and_rename_file function."""

    def setUp(self):
        """Create temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)

    def test_dry_run_mode(self):
        """Test that dry run doesn't copy files."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (640, 480))
        img.save(img_path)

        result = pvr.copy_and_rename_file(img_path, self.output_dir, dry_run=True)
        self.assertTrue(result)

        # Check that no files were created in output
        all_files = []
        for root, dirs, files in os.walk(self.output_dir):
            all_files.extend(files)
        self.assertEqual(len(all_files), 0)

    def test_file_renaming_format(self):
        """Test that file is renamed with correct format."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (640, 480))
        img.save(img_path)

        metadata = (datetime(2023, 12, 25, 14, 30, 45, 123400), 640, 480)
        result = pvr.copy_and_rename_file(
            img_path, self.output_dir, dry_run=False, cached_metadata=metadata
        )
        self.assertTrue(result)

        # Find the created file
        found_files = []
        for root, dirs, files in os.walk(self.output_dir):
            found_files.extend(files)

        self.assertEqual(len(found_files), 1)
        filename = found_files[0]

        # Check filename format: YYYY-MM-DD_HH.MM.SS.SSSS_WIDTHxHEIGHT_HASH.ext
        self.assertTrue(filename.startswith("2023-12-25_14.30.45.1234"))
        self.assertIn("640x480", filename)
        self.assertTrue(filename.endswith(".jpg"))

    def test_directory_structure_creation(self):
        """Test that year/month directory structure is created."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        metadata = (datetime(2023, 6, 15, 10, 0, 0), 100, 100)
        pvr.copy_and_rename_file(
            img_path, self.output_dir, cached_metadata=metadata
        )

        # Check that 2023/June directory was created
        expected_dir = os.path.join(self.output_dir, "2023", "June")
        self.assertTrue(os.path.isdir(expected_dir))

    def test_skip_existing_file(self):
        """Test that existing files are skipped."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        metadata = (datetime(2023, 1, 1, 0, 0, 0), 100, 100)

        # Copy first time
        result1 = pvr.copy_and_rename_file(
            img_path, self.output_dir, cached_metadata=metadata
        )
        self.assertTrue(result1)

        # Try to copy again
        result2 = pvr.copy_and_rename_file(
            img_path, self.output_dir, cached_metadata=metadata
        )
        self.assertTrue(result2)  # Should still return True (skipped)

    def test_in_place_mode(self):
        """Test that in-place mode moves files instead of copying."""
        img_path = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        metadata = (datetime(2023, 3, 15, 12, 0, 0), 100, 100)
        result = pvr.copy_and_rename_file(
            img_path, self.test_dir, in_place=True, cached_metadata=metadata
        )
        self.assertTrue(result)

        # Original file should not exist
        self.assertFalse(os.path.exists(img_path))

        # New file should exist in year/month structure
        expected_dir = os.path.join(self.test_dir, "2023", "March")
        self.assertTrue(os.path.isdir(expected_dir))


class TestProcessDirectory(unittest.TestCase):
    """Integration tests for process_directory function."""

    def setUp(self):
        """Create temporary directories."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)

    def test_process_multiple_files(self):
        """Test processing multiple image files."""
        # Create test images with different content (so different hashes)
        for i in range(3):
            img_path = os.path.join(self.test_dir, f"test{i}.jpg")
            # Use different colors to get different file content and hashes
            colors = ['red', 'green', 'blue']
            img = Image.new('RGB', (200, 200), color=colors[i])
            img.save(img_path)

        # Process directory
        pvr.process_directory(self.test_dir, self.output_dir)

        # Count processed files
        processed_files = []
        for root, dirs, files in os.walk(self.output_dir):
            processed_files.extend(files)

        self.assertEqual(len(processed_files), 3)

    def test_invalid_input_directory(self):
        """Test handling of invalid input directory."""
        fake_dir = os.path.join(self.test_dir, "nonexistent")
        pvr.process_directory(fake_dir, self.output_dir)
        # Should handle gracefully without crashing

    def test_empty_directory(self):
        """Test processing empty directory."""
        # Process empty directory
        pvr.process_directory(self.test_dir, self.output_dir)
        # Should handle gracefully without crashing


class TestSupportedFormats(unittest.TestCase):
    """Tests for supported format constants."""

    def test_supported_formats_defined(self):
        """Test that format constants are defined."""
        self.assertIsNotNone(pvr.SUPPORTED_IMAGE_FORMATS)
        self.assertIsNotNone(pvr.SUPPORTED_VIDEO_FORMATS)
        self.assertIsNotNone(pvr.SUPPORTED_FORMATS)

    def test_supported_formats_union(self):
        """Test that SUPPORTED_FORMATS is union of image and video formats."""
        union = pvr.SUPPORTED_IMAGE_FORMATS | pvr.SUPPORTED_VIDEO_FORMATS
        self.assertEqual(pvr.SUPPORTED_FORMATS, union)

    def test_format_coverage(self):
        """Test that common formats are included."""
        # Check image formats
        self.assertIn('.jpg', pvr.SUPPORTED_IMAGE_FORMATS)
        self.assertIn('.png', pvr.SUPPORTED_IMAGE_FORMATS)
        self.assertIn('.heic', pvr.SUPPORTED_IMAGE_FORMATS)

        # Check video formats
        self.assertIn('.mp4', pvr.SUPPORTED_VIDEO_FORMATS)
        self.assertIn('.mov', pvr.SUPPORTED_VIDEO_FORMATS)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
