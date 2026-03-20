"""
Unit tests for MP4 Transcriber.

Note: These tests focus on utility functions and configuration.
Full integration tests with Whisper model are not included due to:
- Large model download requirements
- Long execution time
- GPU/CPU resource constraints

Run tests with: pytest tests/
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.time_formatter import format_time_srt, format_time_vtt, parse_srt_time
from utils.file_handler import is_video_file, validate_file, ensure_dir, get_video_files
from config import Config, WHISPER_MODELS, VIDEO_FORMATS, OUTPUT_FORMATS


class TestTimeFormatter:
    """Tests for time formatting utilities."""
    
    def test_format_time_srt_basic(self):
        """Test basic SRT time formatting."""
        assert format_time_srt(0) == "00:00:00,000"
        assert format_time_srt(1.5) == "00:00:01,500"
        assert format_time_srt(60) == "00:01:00,000"
    
    def test_format_time_srt_hours(self):
        """Test SRT time formatting with hours."""
        assert format_time_srt(3600) == "01:00:00,000"
        assert format_time_srt(3661) == "01:01:01,000"
        assert format_time_srt(3661.123) == "01:01:01,123"
    
    def test_format_time_srt_complex(self):
        """Test SRT time formatting with complex values."""
        result = format_time_srt(7384.567)
        assert result == "02:03:04,567"
    
    def test_format_time_vtt_basic(self):
        """Test basic VTT time formatting."""
        assert format_time_vtt(0) == "00:00:00.000"
        assert format_time_vtt(1.5) == "00:00:01.500"
        assert format_time_vtt(60) == "00:01:00.000"
    
    def test_format_time_vtt_hours(self):
        """Test VTT time formatting with hours."""
        assert format_time_vtt(3600) == "01:00:00.000"
        assert format_time_vtt(3661) == "01:01:01.000"
        assert format_time_vtt(3661.123) == "01:01:01.123"
    
    def test_format_time_vtt_consistency(self):
        """Test that VTT uses dot instead of comma."""
        srt_result = format_time_srt(123.456)
        vtt_result = format_time_vtt(123.456)
        
        assert srt_result == "00:02:03,456"
        assert vtt_result == "00:02:03.456"
        # Only difference should be comma vs dot
        assert srt_result.replace(',', '.') == vtt_result
    
    def test_parse_srt_time(self):
        """Test parsing SRT time strings."""
        assert parse_srt_time("00:00:00,000") == 0.0
        assert parse_srt_time("00:00:01,500") == 1.5
        assert parse_srt_time("00:01:00,000") == 60.0
        assert parse_srt_time("01:00:00,000") == 3600.0
        assert parse_srt_time("01:01:01,123") == 3661.123
    
    def test_parse_srt_with_dot(self):
        """Test parsing SRT time with dot separator."""
        # Should handle both comma and dot
        assert parse_srt_time("00:00:01.500") == 1.5
        assert parse_srt_time("01:01:01.123") == 3661.123


class TestFileHandler:
    """Tests for file handling utilities."""
    
    def test_is_video_file_valid(self):
        """Test valid video file extensions."""
        assert is_video_file("video.mp4") is True
        assert is_video_file("video.MOV") is True
        assert is_video_file("video.avi") is True
        assert is_video_file("video.mkv") is True
        assert is_video_file("video.webm") is True
    
    def test_is_video_file_invalid(self):
        """Test invalid video file extensions."""
        assert is_video_file("video.txt") is False
        assert is_video_file("video.mp3") is False
        assert is_video_file("video.jpg") is False
        assert is_video_file("video") is False
    
    def test_is_video_file_with_path(self):
        """Test video file detection with full paths."""
        assert is_video_file("/path/to/video.mp4") is True
        assert is_video_file("C:\\Videos\\movie.mkv") is True
        assert is_video_file("./subtitles/file.srt") is False
    
    def test_validate_file_nonexistent(self):
        """Test file validation with non-existent files."""
        assert validate_file("/nonexistent/path/file.mp4") is False
        assert validate_file("") is False
    
    def test_validate_file_directory(self):
        """Test that directories are not validated as files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert validate_file(tmpdir) is False
    
    def test_ensure_dir_creates(self):
        """Test that ensure_dir creates directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new", "nested", "dir")
            ensure_dir(new_dir)
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_ensure_dir_exists(self):
        """Test ensure_dir with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise error if dir exists
            ensure_dir(tmpdir)
            assert os.path.exists(tmpdir)
    
    def test_get_video_files(self):
        """Test getting video files from folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            video_files = ["test1.mp4", "test2.mov", "test3.avi"]
            other_files = ["readme.txt", "config.json"]
            
            for filename in video_files:
                Path(os.path.join(tmpdir, filename)).touch()
            
            for filename in other_files:
                Path(os.path.join(tmpdir, filename)).touch()
            
            result = get_video_files(tmpdir)
            
            assert len(result) == 3
            assert all(is_video_file(f) for f in result)
    
    def test_get_video_files_empty_folder(self):
        """Test getting video files from empty folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_video_files(tmpdir)
            assert len(result) == 0
    
    def test_get_video_files_nonexistent(self):
        """Test getting video files from non-existent folder."""
        result = get_video_files("/nonexistent/path")
        assert len(result) == 0


class TestConfig:
    """Tests for configuration management."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.whisper_model in WHISPER_MODELS
        assert config.language == "ru" or len(config.language) == 2
        assert config.device == "cpu"
        assert config.max_workers >= 1
    
    def test_config_validation_model(self):
        """Test config validation with invalid model."""
        # Temporarily set invalid model in environment
        old_env = os.environ.get('WHISPER_MODEL')
        os.environ['WHISPER_MODEL'] = 'invalid_model'
        
        try:
            # Force reload
            from config import reload_config
            try:
                reload_config()
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Invalid Whisper model" in str(e)
        finally:
            # Restore environment
            if old_env is not None:
                os.environ['WHISPER_MODEL'] = old_env
            elif 'WHISPER_MODEL' in os.environ:
                del os.environ['WHISPER_MODEL']
            
            reload_config()
    
    def test_config_constants(self):
        """Test that configuration constants are defined."""
        assert len(WHISPER_MODELS) > 0
        assert len(VIDEO_FORMATS) > 0
        assert len(OUTPUT_FORMATS) > 0
        
        assert "base" in WHISPER_MODELS
        assert ".mp4" in VIDEO_FORMATS
        assert "txt" in OUTPUT_FORMATS
        assert "srt" in OUTPUT_FORMATS
        assert "json" in OUTPUT_FORMATS
    
    def test_config_output_formats(self):
        """Test getting output formats from config."""
        config = Config()
        formats = config.get_output_formats()
        
        assert len(formats) > 0
        assert all(fmt in OUTPUT_FORMATS for fmt in formats)


def run_tests():
    """Run all tests manually (alternative to pytest)."""
    import traceback
    
    test_classes = [
        TestTimeFormatter,
        TestFileHandler,
        TestConfig
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    print("\n" + "=" * 60)
    print("Running MP4 Transcriber Tests")
    print("=" * 60)
    
    for test_class in test_classes:
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith('test_')]
        
        print(f"\n{test_class.__name__}:")
        
        for method_name in test_methods:
            total_tests += 1
            try:
                getattr(instance, method_name)()
                passed_tests += 1
                print(f"  ✓ {method_name}")
            except Exception as e:
                failed_tests.append((method_name, str(e), traceback.format_exc()))
                print(f"  ✗ {method_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests:
        print(f"\nFailed tests:")
        for name, error, tb in failed_tests:
            print(f"\n{name}:\n{tb}")
        return False
    else:
        print("✓ All tests passed!")
        return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
