# ✅ Installation Checklist

Use this checklist to ensure your MP4 Transcriber is properly set up.

## Pre-Installation

- [ ] Python 3.9+ installed (`python --version`)
- [ ] pip is available (`pip --version`)
- [ ] Git installed (if cloning repository)

## Step 1: FFmpeg Installation

### Windows
- [ ] FFmpeg downloaded from https://ffmpeg.org/download.html
- [ ] FFmpeg extracted to `C:\ffmpeg` or similar location
- [ ] FFmpeg bin directory added to PATH
- [ ] Terminal restarted after PATH update
- [ ] FFmpeg verified: `ffmpeg -version`

### macOS
- [ ] Homebrew installed (if needed)
- [ ] FFmpeg installed: `brew install ffmpeg`
- [ ] FFmpeg verified: `ffmpeg -version`

### Linux
- [ ] FFmpeg installed: `sudo apt install ffmpeg`
- [ ] FFmpeg verified: `ffmpeg -version`

## Step 2: Python Dependencies

- [ ] Navigate to project directory
- [ ] Run: `pip install -r requirements.txt`
- [ ] Wait for installation to complete (may take 5-10 minutes)
- [ ] No error messages during installation

### Verify Python Packages

Check each package individually:

- [ ] `python -c "import whisper; print('✓ Whisper')"`
- [ ] `python -c "import torch; print('✓ PyTorch')"`
- [ ] `python -c "import ffmpeg; print('✓ ffmpeg-python')"`
- [ ] `python -c "import tqdm; print('✓ tqdm')"`
- [ ] `python -c "import dotenv; print('✓ python-dotenv')"`
- [ ] `python -c "import click; print('✓ click')"`

## Step 3: Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Edit `.env` file with preferred settings
- [ ] Set `WHISPER_MODEL=base` (recommended for start)
- [ ] Set `LANGUAGE=ru` or your preferred language
- [ ] Verify `OUTPUT_DIR=./transcripts`

## Step 4: System Verification

- [ ] Run: `python main.py check`
- [ ] All dependencies show as installed
- [ ] FFmpeg path is displayed
- [ ] Configuration values are correct
- [ ] No error messages

## Step 5: First Test

### Option A: With Sample Video
- [ ] Place test video in `./videos` folder
- [ ] Run: `python main.py transcribe --input ./videos/test.mp4`
- [ ] Wait for transcription to complete
- [ ] Check `./transcripts` folder for output files
- [ ] Open and review transcript files

### Option B: Without Video (Test Only)
- [ ] Run: `python main.py models`
- [ ] View available Whisper models table
- [ ] Confirm CLI is working correctly

## Troubleshooting

If any step fails:

1. **FFmpeg issues:**
   - Reinstall FFmpeg
   - Verify PATH environment variable
   - Restart terminal/command prompt

2. **Python package issues:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Permission issues:**
   - Run terminal as Administrator (Windows)
   - Use sudo (Linux/macOS)

4. **Memory issues:**
   - Use smaller model: `--model tiny` or `--model base`
   - Close other applications
   - Check available disk space

## Post-Installation

After successful setup:

- [ ] Read [README.md](README.md) for full documentation
- [ ] Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
- [ ] Explore different Whisper models
- [ ] Try batch processing with multiple videos
- [ ] Experiment with different output formats

## Success Criteria

Your installation is successful when:

✅ `python main.py check` shows all green checkmarks  
✅ You can run `python main.py models` without errors  
✅ Single file transcription completes successfully  
✅ Output files appear in `./transcripts` folder  
✅ Batch processing works with multiple videos  

---

## Quick Command Reference

```bash
# Check system
python main.py check

# View models
python main.py models

# Transcribe single file
python main.py transcribe --input video.mp4 --model base --lang ru

# Batch process folder
python main.py batch --input ./videos --model medium

# Get help
python main.py --help
python main.py transcribe --help
python main.py batch --help
```

---

**Need Help?** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.
