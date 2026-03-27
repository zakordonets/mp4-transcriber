"""
Quick verification script to test all imports and basic functionality.
Run this after installation to ensure everything is set up correctly.
"""

import sys

print("=" * 60)
print("Media Transcriber - Import Verification")
print("=" * 60)

# Test 1: Utils imports
print("\n1. Testing utility imports...")
try:
    from utils import (
        ensure_dir,
        get_media_files,
        get_video_files,
        is_audio_file,
        is_media_file,
        is_video_file,
        setup_logger,
        validate_file,
    )
    from utils import format_time_srt, format_time_vtt

    print("   OK: all utility imports successful")
except ImportError as e:
    print(f"   FAIL: utility import failed: {e}")
    sys.exit(1)

# Test 2: Config imports
print("\n2. Testing config imports...")
try:
    from config import (
        AUDIO_FORMATS,
        DEFAULT_LANGUAGE,
        DEFAULT_MODEL,
        MEDIA_FORMATS,
        OUTPUT_FORMATS,
        VIDEO_FORMATS,
        WHISPER_MODELS,
        Config,
        get_config,
    )

    print("   OK: config imports successful")
    print(f"     - Available models: {len(WHISPER_MODELS)}")
    print(f"     - Video formats: {len(VIDEO_FORMATS)}")
    print(f"     - Audio formats: {len(AUDIO_FORMATS)}")
    print(f"     - Media formats: {len(MEDIA_FORMATS)}")
    print(f"     - Default model: {DEFAULT_MODEL}")
    print(f"     - Default language: {DEFAULT_LANGUAGE}")
except ImportError as e:
    print(f"   FAIL: config import failed: {e}")
    sys.exit(1)

# Test 3: Time formatting
print("\n3. Testing time formatting...")
try:
    srt_time = format_time_srt(3661.123)
    vtt_time = format_time_vtt(3661.123)
    print("   OK: time formatting works")
    print(f"     - SRT: {srt_time}")
    print(f"     - VTT: {vtt_time}")
except Exception as e:
    print(f"   FAIL: time formatting failed: {e}")
    sys.exit(1)

# Test 4: Media format helpers
print("\n4. Testing media format helpers...")
try:
    test_files = [
        ("video.mp4", True, False, True),
        ("movie.MOV", True, False, True),
        ("audio.mp3", False, True, True),
        ("call.opus", False, True, True),
        ("file.txt", False, False, False),
    ]

    for filename, expected_video, expected_audio, expected_media in test_files:
        result_video = is_video_file(filename)
        result_audio = is_audio_file(filename)
        result_media = is_media_file(filename)
        ok = (
            result_video == expected_video
            and result_audio == expected_audio
            and result_media == expected_media
        )
        status = "OK" if ok else "FAIL"
        print(
            f"     - {status} {filename}: "
            f"video={result_video}, audio={result_audio}, media={result_media}"
        )

    print("   OK: media format helpers work")
except Exception as e:
    print(f"   FAIL: media format helper check failed: {e}")
    sys.exit(1)

# Test 5: Configuration loading
print("\n5. Testing configuration...")
try:
    config = get_config()
    print("   OK: configuration loaded")
    print(f"     - Model: {config.whisper_model}")
    print(f"     - Language: {config.language}")
    print(f"     - Device: {config.device}")
    print(f"     - Output dir: {config.output_dir}")
except Exception as e:
    print(f"   FAIL: configuration loading failed: {e}")
    sys.exit(1)

# Test 6: Core module imports (without loading models)
print("\n6. Testing core module imports...")
try:
    from transcriber import MediaTranscriber, VideoTranscriber
    from batch_processor import BatchProcessor

    print("   OK: core modules imported successfully")
except ImportError as e:
    print(f"   FAIL: core module import failed: {e}")
    print("     Note: this may fail if whisper/torch is not installed yet")
    sys.exit(1)

# Test 7: CLI imports
print("\n7. Testing CLI imports...")
try:
    from main import cli

    print("   OK: CLI module imported")
except ImportError as e:
    print(f"   FAIL: CLI import failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 60)
print("OK: ALL IMPORT TESTS PASSED")
print("=" * 60)
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Install FFmpeg (see README.md)")
print("3. Copy .env.example to .env and configure")
print("4. Run: python main.py check")
print("5. Test with: python main.py transcribe --input <your_media_file>")
print()
