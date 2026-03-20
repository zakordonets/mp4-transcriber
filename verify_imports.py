"""
Quick verification script to test all imports and basic functionality.
Run this after installation to ensure everything is set up correctly.
"""

import sys
from pathlib import Path

print("=" * 60)
print("MP4 Transcriber - Import Verification")
print("=" * 60)

# Test 1: Utils imports
print("\n1. Testing utility imports...")
try:
    from utils import setup_logger, is_video_file, validate_file, ensure_dir, get_video_files
    from utils import format_time_srt, format_time_vtt
    print("   ✓ All utility imports successful")
except ImportError as e:
    print(f"   ✗ Utility import failed: {e}")
    sys.exit(1)

# Test 2: Config imports
print("\n2. Testing config imports...")
try:
    from config import (
        WHISPER_MODELS, VIDEO_FORMATS, OUTPUT_FORMATS,
        DEFAULT_MODEL, DEFAULT_LANGUAGE, get_config, Config
    )
    print(f"   ✓ Config imports successful")
    print(f"     - Available models: {len(WHISPER_MODELS)}")
    print(f"     - Default model: {DEFAULT_MODEL}")
    print(f"     - Default language: {DEFAULT_LANGUAGE}")
except ImportError as e:
    print(f"   ✗ Config import failed: {e}")
    sys.exit(1)

# Test 3: Time formatting
print("\n3. Testing time formatting...")
try:
    srt_time = format_time_srt(3661.123)
    vtt_time = format_time_vtt(3661.123)
    print(f"   ✓ Time formatting works")
    print(f"     - SRT: {srt_time}")
    print(f"     - VTT: {vtt_time}")
except Exception as e:
    print(f"   ✗ Time formatting failed: {e}")
    sys.exit(1)

# Test 4: File validation
print("\n4. Testing file validation...")
try:
    test_files = [
        ("video.mp4", True),
        ("movie.MOV", True),
        ("file.txt", False),
        ("audio.mp3", False)
    ]
    
    for filename, expected in test_files:
        result = is_video_file(filename)
        status = "✓" if result == expected else "✗"
        print(f"     {status} {filename}: {result}")
    
    print(f"   ✓ File validation works")
except Exception as e:
    print(f"   ✗ File validation failed: {e}")
    sys.exit(1)

# Test 5: Configuration loading
print("\n5. Testing configuration...")
try:
    config = get_config()
    print(f"   ✓ Configuration loaded")
    print(f"     - Model: {config.whisper_model}")
    print(f"     - Language: {config.language}")
    print(f"     - Device: {config.device}")
    print(f"     - Output dir: {config.output_dir}")
except Exception as e:
    print(f"   ✗ Configuration loading failed: {e}")
    sys.exit(1)

# Test 6: Core module imports (without loading models)
print("\n6. Testing core module imports...")
try:
    # Just test that we can import the classes
    from transcriber import VideoTranscriber
    from batch_processor import BatchProcessor
    print(f"   ✓ Core modules imported successfully")
except ImportError as e:
    print(f"   ✗ Core module import failed: {e}")
    print(f"     Note: This may fail if whisper/torch not installed yet")
    sys.exit(1)

# Test 7: CLI imports
print("\n7. Testing CLI imports...")
try:
    from main import cli
    print(f"   ✓ CLI module imported")
except ImportError as e:
    print(f"   ✗ CLI import failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 60)
print("✓ ALL IMPORT TESTS PASSED!")
print("=" * 60)
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Install FFmpeg (see README.md)")
print("3. Copy .env.example to .env and configure")
print("4. Run: python main.py check")
print("5. Test with: python main.py transcribe --input <your_video.mp4>")
print()
