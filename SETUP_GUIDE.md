# MP4 Transcriber - Setup Guide

## Quick Start Installation

Follow these steps to get your MP4 Transcriber up and running:

### Step 1: Install FFmpeg

**Windows (using Chocolatey):**
```powershell
choco install ffmpeg
```

**Windows (manual installation):**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH environment variable
4. Restart your terminal

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Verify FFmpeg installation:**
```bash
ffmpeg -version
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `openai-whisper` - ASR model from OpenAI
- `ffmpeg-python` - Python bindings for FFmpeg
- `torch` - PyTorch for neural network inference
- `tqdm` - Progress bars
- `python-dotenv` - Environment configuration
- `click` - CLI framework

**Note:** First-time installation may take several minutes as PyTorch and Whisper are large packages.

### Optional: Speaker Diarization Support

Install these packages only if you plan to use `--diarize` with the `pyannote` backend:

```bash
pip install -r requirements-diarization.txt
```

Notes:
- Keep the base installation unchanged if you do not need speaker labeling.
- `python main.py check` will show whether the optional backend is available.
- For `pyannote`, set a Hugging Face token in your environment if the model requires it.

### Step 3: Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env file with your preferences:
# - WHISPER_MODEL=base (recommended starting point)
# - LANGUAGE=ru (for Russian) or en (for English)
# - OUTPUT_DIR=./transcripts
# - DIARIZATION_BACKEND=pyannote (optional)
# - HF_TOKEN=... or HUGGING_FACE_HUB_TOKEN=... (only for pyannote)
```

### Step 4: Verify Installation

```bash
# Run system check
python main.py check

# If all checks pass, you're ready to go!
```

If you installed optional diarization dependencies, also run:

```bash
python main.py diarization-smoke --backend noop
```

### Step 5: Test Transcription

```bash
# Test with a sample video file
python main.py transcribe --input ./videos/sample.mp4 --model base --lang ru
```

---

## Troubleshooting Common Issues

### Issue: "No module named 'whisper'"

**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: "FFmpeg not found"

**Windows users:** Make sure FFmpeg is in your PATH. Test with:
```powershell
ffmpeg -version
```

If command not found, restart your terminal after installing FFmpeg.

### Issue: Slow download speeds

The Whisper model needs to be downloaded on first use. This can take time depending on your internet connection.

**Model sizes:**
- tiny: ~140 MB
- base: ~150 MB
- small: ~480 MB
- medium: ~1.5 GB
- large: ~3 GB

Models are cached after first download.

### Issue: Out of memory errors

**Solution:** Use a smaller model:
```bash
python main.py transcribe --input video.mp4 --model tiny
```

Or reduce video quality before processing.

---

## First Transcription Workflow

1. **Prepare your video file**
   - Place it in the `./videos` folder (or any location)
   - Supported formats: MP4, MOV, AVI, MKV, WebM

2. **Run transcription**
   ```bash
   python main.py transcribe --input ./videos/my_video.mp4
   ```

3. **Find your transcripts**
   - Check the `./transcripts` folder
   - Files will be named after your video: `my_video.txt`, `my_video.srt`, etc.

4. **Review results**
   - Open TXT file for plain text
   - Open SRT file in video player for subtitles
   - Open JSON file for detailed analysis

---

## Batch Processing Example

To transcribe all videos in a folder:

```bash
python main.py batch --input ./videos --output ./transcripts --model base
```

The processor will:
1. Find all video files in the folder
2. Process them one by one with progress bar
3. Skip any that fail (continuing with the rest)
4. Provide a summary at the end

---

## Performance Tips

1. **Choose the right model:**
   - For quick tests: `tiny` or `base`
   - For production: `medium`
   - For best quality: `large` (if you have resources)

2. **CPU optimization:**
   - Close other applications
   - Ensure good cooling (prevents thermal throttling)
   - Consider processing shorter segments

3. **File organization:**
   - Keep videos in dedicated folder
   - Use descriptive filenames
   - Clean up old transcripts regularly

---

## Next Steps

After successful setup:
- Read the full [README.md](README.md) for advanced usage
- Explore different Whisper models with `python main.py models`
- Try batch processing for multiple files
- Experiment with different output formats

---

**Need Help?**
- Check the FAQ section in README.md
- Review troubleshooting in README.md
- Open an issue on GitHub
