# MP4 Transcriber - Quick Reference

## 🚀 Common Commands

### Check System
```bash
python main.py check
```

### Single File Transcription
```bash
python main.py transcribe --input video.mp4 --model base --lang ru
```

### Single File with Speaker Labels
```bash
python main.py transcribe --input video.mp4 --diarize --diarization-backend pyannote
```

### Batch Processing
```bash
python main.py batch --input ./videos --output ./transcripts --model medium
```

### Batch Processing with No-op Backend
```bash
python main.py batch --input ./videos --diarize --diarization-backend noop
```

### View Available Models
```bash
python main.py models
```

---

## ⚙️ Configuration (.env)

```env
WHISPER_MODEL=base      # tiny, base, small, medium, large
LANGUAGE=ru             # Language code (ru, en, es, etc.)
DEVICE=cpu              # cpu only (in this version)
OUTPUT_DIR=./transcripts
MAX_WORKERS=2
LOG_LEVEL=INFO
DIARIZATION_BACKEND=pyannote   # noop, pyannote
```

---

## 📦 Output Formats

- **txt** - Plain text transcript
- **srt** - Subtitle format for video players
- **vtt** - Web subtitle format
- **json** - Full metadata with timestamps

Default: All formats are generated

When diarization is enabled, TXT/SRT/VTT output includes speaker labels and JSON includes `speaker_segments` and `speakers`.

---

## 🎯 Model Selection Guide

| Use Case | Recommended Model |
|----------|------------------|
| Quick test | `tiny` |
| Fast transcription | `base` |
| Good balance | `small` |
| Production quality | `medium` |
| Maximum accuracy | `large` |

---

## 💡 Tips

1. **Faster processing**: Use smaller model (`tiny` or `base`)
2. **Better accuracy**: Use `medium` or `large`
3. **Russian language**: Works best with `medium` model
4. **Batch jobs**: Can be interrupted and resumed
5. **File organization**: Keep videos in `./videos` folder
6. **Speaker labels**: Use `--diarize` only when optional diarization packages are installed

---

## 🔧 Troubleshooting

**FFmpeg not found:**
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

**Missing Python packages:**
```bash
pip install -r requirements.txt
```

**Check installation:**
```bash
python main.py check
```

**Optional diarization smoke test:**
```bash
python main.py diarization-smoke --backend noop
```

---

## 📁 Project Structure

```
mp4-transcriber/
├── main.py              # CLI entry point
├── transcriber.py       # Core transcription
├── batch_processor.py   # Batch processing
├── config.py            # Configuration
├── utils/               # Utilities
│   ├── logger.py
│   ├── file_handler.py
│   └── time_formatter.py
├── tests/               # Unit tests
├── videos/              # Input files
└── transcripts/         # Output files
```

---

## 📖 Documentation

- Full documentation: [README.md](README.md)
- Setup guide: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Run tests: `python tests/test_transcriber.py`

---

**Quick Start:** Install → Configure → `python main.py check` → Transcribe!
