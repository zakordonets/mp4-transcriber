# Media Transcriber

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automated media transcription tool using OpenAI Whisper and ffmpeg.** Convert common video and speech-audio files to text with support for multiple languages (optimized for Russian), batch processing, and export to TXT, SRT, VTT, and JSON.

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [CLI Commands](#cli-commands)
  - [Python API](#python-api)
- [Speaker Diarization](#speaker-diarization)
- [Whisper Models](#-whisper-models)
- [Configuration](#-configuration)
- [Output Formats](#-output-formats)
- [FAQ](#-faq)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

- **Multi-format Support**: Process MP4, MOV, AVI, MKV, WebM, MP3, WAV, M4A, AAC, OGG, and OPUS files
- **Multiple Export Formats**: TXT, SRT (subtitles), VTT (web subtitles), JSON (full metadata)
- **Batch Processing**: Transcribe entire folders of supported media files automatically
- **Language Support**: Optimized for Russian, supports 90+ languages via Whisper
- **Optional Speaker Diarization**: Label speakers with the `pyannote` backend when needed
- **Progress Tracking**: Real-time progress bars during batch processing
- **Error Handling**: Skip-on-error strategy ensures batch jobs complete
- **Logging**: Detailed console and file logging for debugging
- **CPU Only**: No GPU required, works on any system
- **Easy Configuration**: Environment-based configuration via `.env` file

---

## 📦 Installation

### System Requirements

### Minimum

- **OS**: Windows, macOS, or Linux
- **Python**: 3.9 or higher
- **CPU**: 2-core CPU
- **RAM**: 8 GB
- **Disk space**: 5-10 GB free
- **System dependency**: FFmpeg available in `PATH`

### Recommended

- **CPU**: 4 or more cores
- **RAM**: 16 GB
- **Storage**: SSD with 10-20 GB free
- **Use case**: recommended for batch processing, longer recordings, and `small`/`medium` Whisper models

### For Larger Models

- **`tiny` / `base`**: suitable for most CPU-only setups
- **`small`**: more comfortable with 16 GB RAM
- **`medium` / `large`**: best with 16-32 GB RAM and extra disk space for model cache and temporary WAV files

### Optional Speaker Diarization

If you use `--diarize` with the `pyannote` backend, you also need:

- `torchaudio >=2.2.0,<2.9`
- `pyannote.audio >=3.1.0,<4.0.0`
- A Hugging Face token in `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN` when the selected pyannote model requires it

### Notes

- This project currently runs in **CPU-only** mode; a GPU is not required.
- Whisper models are downloaded on first use and cached locally.
- Model cache sizes are approximately:
  - `tiny`: ~140 MB
  - `base`: ~150 MB
  - `small`: ~480 MB
  - `medium`: ~1.5 GB
  - `large`: ~3 GB
- Output files and temporary extracted audio require additional free disk space beyond the model cache.
- Run `python main.py check` after installation to verify the environment.

### Prerequisites

1. **Python 3.9 or higher**
   ```bash
   python --version
   ```

2. **FFmpeg** (required for audio extraction)

   **Windows:**
   ```powershell
   choco install ffmpeg
   # or download from https://ffmpeg.org/download.html
   ```

   **macOS:**
   ```bash
   brew install ffmpeg
   ```

   **Linux:**
   ```bash
   sudo apt update && sudo apt install ffmpeg
   ```

### Install Python Dependencies

```bash
# Clone or navigate to the project directory
cd mp4-transcriber

# Install dependencies
pip install -r requirements.txt

# Optional speaker diarization support
# pip install -r requirements-diarization.txt
```

### Setup Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
# WHISPER_MODEL=base
# LANGUAGE=ru
# OUTPUT_DIR=./transcripts
```

---

## 🚀 Quick Start

### 1. Check System Dependencies

```bash
python main.py check
```

This verifies that FFmpeg and all Python packages are installed correctly.

### 2. Transcribe a Single File

```bash
python main.py transcribe --input ./media/interview.mp4 --model medium --lang ru
```

### 3. Batch Process a Folder

```bash
python main.py batch --input ./media --output ./transcripts --model base
```

That's it! Your transcripts will be saved in the `./transcripts` folder.

---

## 💻 Usage

### CLI Commands

#### Transcribe Single File

```bash
python main.py transcribe --input <media_file> [OPTIONS]
```

**Options:**
- `--input, -i`: Path to input media file; repeat the option to merge multiple files into one transcript
- `--model, -m`: Whisper model (tiny|base|small|medium|large)
- `--lang, -l`: Language code (default: ru)
- `--output-dir, -o`: Output directory (default: ./transcripts)
- `--output-name`: Custom basename for generated transcript files when combining inputs
- `--formats, -f`: Output formats comma-separated (default: txt,srt,vtt,json)
- `--diarize`: Enable optional speaker diarization
- `--diarization-backend`: Backend to use for diarization (`noop` or `pyannote`)
- `--diarize-strict`: Fail the command if diarization cannot run

**Examples:**
```bash
# Basic transcription with default settings
python main.py transcribe --input interview.mp4

# Specify model and language
python main.py transcribe --input meeting.m4a --model small --lang en

# Export only to SRT format
python main.py transcribe --input interview.mov --formats srt

# Transcribe with speaker diarization
python main.py transcribe --input interview.mov --diarize --diarization-backend pyannote

# Merge two media files into one continuous transcript
python main.py transcribe --input part1.mp4 --input part2.m4a --output-name lecture_day1

# Same scenario via the dedicated combine command
python main.py combine-transcribe --input part1.mp4 --input part2.m4a --output-name lecture_day1
```

#### Batch Processing

```bash
python main.py batch --input <folder_path> [OPTIONS]
```

**Options:**
- `--input, -i`: Path to folder with supported media files (required)
- `--output, -o`: Output directory (default: ./transcripts)
- `--model, -m`: Whisper model (default: from .env)
- `--lang, -l`: Language code (default: from .env)
- `--workers, -w`: Number of workers (default: 2, sequential processing)
- `--formats, -f`: Output formats (default: txt,srt,vtt,json)
- `--diarize`: Enable optional speaker diarization
- `--diarization-backend`: Backend to use for diarization (`noop` or `pyannote`)
- `--diarize-strict`: Fail the command if diarization cannot run

**Examples:**
```bash
# Process all supported media files in a folder
python main.py batch --input ./media

# Custom output and model
python main.py batch --input ./lectures --output ./subs --model medium

# Process with specific language
python main.py batch --input ./interviews --lang en --formats txt,json

# Batch process with no-op diarization backend
python main.py batch --input ./media --diarize --diarization-backend noop
```

#### System Check

```bash
python main.py check
```

Displays:
- System information
- FFmpeg installation status
- Python package versions
- Current configuration

#### View Available Models

```bash
python main.py models
```

Shows comparison table of all Whisper models with speed/quality metrics.

---

### Python API

Use the transcriber programmatically in your Python code:

```python
from transcriber import VideoTranscriber
from batch_processor import BatchProcessor

# Initialize transcriber
transcriber = VideoTranscriber(
    model_name="medium",
    language="ru",
    device="cpu",
    output_dir="./transcripts"
)

# Transcribe single file
result = transcriber.transcribe(
    "./media/interview.mp4",
    output_formats=["txt", "srt"],
    save_outputs=True
)

# Transcribe with optional diarization
diarized_result = transcriber.transcribe(
    "./media/interview.mp4",
    output_formats=["json"],
    save_outputs=True,
    diarize=True,
    diarization_backend="pyannote",
)

print(f"Speaker segments: {len(diarized_result.get('speaker_segments', []))}")
print(f"Speakers: {diarized_result.get('speakers', [])}")

print(f"Text: {result['text']}")
print(f"Segments: {len(result['segments'])}")
print(f"Language: {result['language']}")

# Transcribe multiple media files as one continuous transcript
combined_result = transcriber.transcribe_many(
    ["./media/part1.mp4", "./media/part2.m4a"],
    output_formats=["txt", "json"],
    save_outputs=True,
    output_basename="lecture_day1",
)
print(combined_result["source_files"])

# Batch processing
batch = BatchProcessor(transcriber, max_workers=2)
results = batch.process_folder("./media")

print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
```

---

## 🎙 Speaker Diarization

Speaker diarization is optional and does not affect the default transcription path.

### Available Backends

- `noop`: no-op backend for smoke testing and environments without diarization packages
- `pyannote`: optional backend for real speaker labeling

### How to Use

```bash
python main.py transcribe --input interview.mp4 --diarize
python main.py transcribe --input interview.mp4 --diarize --diarization-backend pyannote
python main.py batch --input ./media --diarize
python main.py diarization-smoke --backend noop
```

### Behavior

- Without `--diarize`, the application behaves exactly as before.
- If the backend is unavailable, the CLI exits with a clear message.
- In permissive mode, diarization failures keep the transcript and add a warning.
- JSON output includes `speaker_segments`, `speakers`, and speaker labels on segments when diarization succeeds.

---

## 🎯 Whisper Models

| Model | Parameters | VRAM Required | Speed (relative) | Quality | Best For |
|-------|-----------|---------------|------------------|---------|----------|
| **tiny** | 39M | ~1 GB | ~32x | Basic | Quick tests, low-resource devices |
| **base** | 74M | ~1 GB | ~16x | Good | General use, fast transcription |
| **small** | 244M | ~2 GB | ~6x | Better | Improved accuracy |
| **medium** | 769M | ~5 GB | ~2x | Excellent | Production use, high accuracy |
| **large** | 1550M | ~10 GB | 1x | Best | Maximum accuracy, powerful systems |

**Recommendations:**
- **For testing**: `tiny` or `base`
- **For production**: `medium`
- **For best quality**: `large` (if you have resources)

**Note:** Speed is relative to real-time audio. "32x" means 32 seconds of audio processed per 1 second of wall-clock time.

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Whisper model selection
WHISPER_MODEL=base

# Language code (ISO 639-1)
LANGUAGE=ru

# Device for inference (cpu only in this version)
DEVICE=cpu

# Output directory for transcripts
OUTPUT_DIR=./transcripts

# Workers for batch processing (sequential mode)
MAX_WORKERS=2

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Optional: default diarization backend when --diarize is used
DIARIZATION_BACKEND=pyannote

# Optional: Hugging Face token for pyannote
# HF_TOKEN=hf_your_token_here
# HUGGING_FACE_HUB_TOKEN=hf_your_token_here
```

### Supported Languages

Whisper supports 90+ languages. Common codes:
- `ru` - Russian
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `zh` - Chinese
- `ja` - Japanese

The model will auto-detect the language if not specified, but setting it improves accuracy.

---

## 📄 Output Formats

### TXT (Plain Text)
```
Привет! Это пример транскрибации видео.
Здесь только текст без временных меток.
```

### SRT (SubRip Subtitles)
```srt
1
00:00:00,000 --> 00:00:03,500
Привет! Это пример транскрибации видео.

2
00:00:03,500 --> 00:00:07,000
Здесь только текст без временных меток.
```

### VTT (WebVTT)
```vtt
WEBVTT

00:00:00.000 --> 00:00:03.500
Привет! Это пример транскрибации видео.

00:00:03.500 --> 00:00:07.000
Здесь только текст без временных меток.
```

### JSON (Full Metadata)
```json
{
  "text": "Привет! Это пример...",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Привет! Это пример..."
    }
  ],
  "language": "ru",
  "source_file": "./media/interview.mp4",
  "source_files": ["./media/interview.mp4"]
}
```

---

## ❓ FAQ

### How accurate is the transcription?

Accuracy depends on:
- **Model size**: Larger models = better accuracy
- **Audio quality**: Clear audio = better results
- **Background noise**: Noise reduces accuracy
- **Speaker accent**: May affect recognition
- **Language**: Works best with widely-spoken languages

For Russian, `medium` model provides excellent results.

### Can I transcribe files with multiple speakers?

Yes. Speaker diarization is available via the optional `pyannote` backend. Use `python main.py check` to see whether it is installed, or `python main.py diarization-smoke --backend noop` for a dependency-free smoke test.

Quick smoke test:
```powershell
python main.py diarization-smoke --backend pyannote
```

If you only want to verify the CLI path without loading the model, use:
```powershell
python main.py diarization-smoke --backend noop
```

### How long does transcription take?

Processing time depends on:
- Recording length
- Model size
- Hardware (CPU speed)

**Approximate speeds (CPU only):**
- `tiny`: ~32x faster than real-time
- `base`: ~16x
- `small`: ~6x
- `medium`: ~2x
- `large`: ~1x

Example: 10-minute video with `base` model ≈ 40 seconds.

### What input formats are supported?

- MP4 (.mp4)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)
- WebM (.webm)
- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- AAC (.aac)
- OGG (.ogg)
- OPUS (.opus)

### Can I use this without installing FFmpeg?

No, FFmpeg is required for audio extraction and normalization from supported media files. It's a free, open-source tool that must be installed separately.

### Does this work offline?

Yes! Once Whisper models are downloaded, everything runs locally on your machine. No internet connection required during transcription.

### Where are the models stored?

Whisper models are cached in:
- **Windows**: `C:\Users\<user>\.cache\whisper`
- **Linux/macOS**: `~/.cache/whisper`

First run downloads the model; subsequent uses load from cache.

---

## 🔧 Troubleshooting

### "FFmpeg not found" error

**Solution:** Install FFmpeg (see [Installation](#installation)) and ensure it's in your system PATH.

Verify installation:
```bash
ffmpeg -version
```

### "CUDA out of memory" error

This version is CPU-only. If you're trying to use GPU, modify the code to add CUDA support. The current implementation intentionally excludes GPU to simplify setup.

### Transcription is very slow

**Solutions:**
1. Use a smaller model (`tiny` or `base`)
2. Use shorter files when possible
3. Close other applications
4. Consider adding GPU support (requires code changes)

### "ModuleNotFoundError: No module named 'whisper'"

**Solution:** Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Non-English characters look wrong

Ensure your text editor supports UTF-8 encoding. All output files are saved with UTF-8 encoding by default.

### Batch processing stops midway

Check:
1. Disk space availability
2. File permissions
3. Log files for specific errors
4. Memory usage

The skip-on-error strategy should continue processing remaining files.

---

## 📝 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2026 Media Transcriber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check the full docs in the repository
- **Archived docs**: See [docs/archive](docs/archive/)

---

**Made with ❤️ using OpenAI Whisper and FFmpeg**
