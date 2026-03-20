"""
Command-line interface for MP4 Transcriber.
Provides commands for single file transcription, batch processing, and system checks.
"""

import sys
import platform
from pathlib import Path

import click

from config import (
    WHISPER_MODELS, OUTPUT_FORMATS, VIDEO_FORMATS,
    get_config, reload_config
)
from transcriber import VideoTranscriber
from batch_processor import BatchProcessor
from utils.logger import setup_logger
from utils.file_handler import validate_file, get_video_files


logger = setup_logger("CLI")


@click.group()
@click.version_option(version="1.0.0", prog_name="MP4 Transcriber")
def cli():
    """
    MP4 Transcriber - Convert video files to text using Whisper ASR.
    
    Supports batch processing, multiple export formats, and Russian language.
    """
    pass


@cli.command()
@click.option(
    '--input', '-i',
    'input_file',
    required=True,
    type=click.Path(exists=True),
    help='Path to input video file'
)
@click.option(
    '--model', '-m',
    type=click.Choice(WHISPER_MODELS, case_sensitive=False),
    default=None,
    help=f'Whisper model to use (default from .env or {WHISPER_MODELS[1]})'
)
@click.option(
    '--lang', '-l',
    'language',
    default=None,
    help='Language code for transcription (default from .env or "ru")'
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    default=None,
    help='Output directory for transcripts (default from .env)'
)
@click.option(
    '--formats', '-f',
    'output_formats',
    default='txt,srt,vtt,json',
    show_default=True,
    help='Comma-separated list of output formats (txt,srt,vtt,json)'
)
def transcribe(input_file: str, model: str, language: str, output_dir: str, output_formats: str):
    """
    Transcribe a single video file.
    
    Example:
        python main.py transcribe --input video.mp4 --model medium --lang ru
    """
    # Parse output formats
    formats = [f.strip().lower() for f in output_formats.split(',')]
    
    # Validate formats
    for fmt in formats:
        if fmt not in OUTPUT_FORMATS:
            click.echo(click.style(f"Error: Invalid format '{fmt}'. Must be one of {OUTPUT_FORMATS}", fg='red'))
            sys.exit(1)
    
    try:
        # Load configuration
        config = get_config()
        
        # Override with command-line options
        model_name = model or config.whisper_model
        lang = language or config.language
        out_dir = output_dir or config.output_dir
        
        click.echo(click.style(f"\n🎬 MP4 Transcriber", bold=True))
        click.echo(f"Input file:  {Path(input_file).resolve()}")
        click.echo(f"Model:       {model_name}")
        click.echo(f"Language:    {lang}")
        click.echo(f"Output dir:  {out_dir}")
        click.echo(f"Formats:     {', '.join(formats)}")
        click.echo("-" * 60)
        
        # Initialize transcriber
        transcriber = VideoTranscriber(
            model_name=model_name,
            language=lang,
            device='cpu',
            output_dir=out_dir
        )
        
        # Transcribe file
        result = transcriber.transcribe(
            input_file,
            output_formats=formats,
            save_outputs=True
        )
        
        # Display results
        click.echo("\n" + click.style("✓ Transcription Complete!", fg='green', bold=True))
        click.echo(f"Detected language: {result.get('language', 'unknown')}")
        click.echo(f"Segments: {len(result.get('segments', []))}")
        click.echo(f"Text length: {len(result.get('text', ''))} characters")
        
        if result.get('segments'):
            click.echo("\nPreview (first segment):")
            click.echo(f"  {result['segments'][0]['text']}")
        
        click.echo()
        
    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo(click.style("\n⚠ Transcription cancelled by user", fg='yellow'))
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        logger.exception("Transcription failed")
        sys.exit(1)


@cli.command()
@click.option(
    '--input', '-i',
    'input_folder',
    required=True,
    type=click.Path(exists=True),
    help='Path to folder containing video files'
)
@click.option(
    '--output', '-o',
    'output_dir',
    type=click.Path(),
    default=None,
    help='Output directory for transcripts (default from .env)'
)
@click.option(
    '--model', '-m',
    type=click.Choice(WHISPER_MODELS, case_sensitive=False),
    default=None,
    help=f'Whisper model to use (default from .env)'
)
@click.option(
    '--lang', '-l',
    'language',
    default=None,
    help='Language code for transcription (default from .env)'
)
@click.option(
    '--workers', '-w',
    type=int,
    default=2,
    show_default=True,
    help='Number of workers (sequential processing only)'
)
@click.option(
    '--formats', '-f',
    'output_formats',
    default='txt,srt,vtt,json',
    show_default=True,
    help='Comma-separated list of output formats'
)
def batch(input_folder: str, output_dir: str, model: str, language: str, workers: int, output_formats: str):
    """
    Batch process all video files in a folder.
    
    Example:
        python main.py batch --input ./videos --output ./transcripts --workers 2
    """
    # Parse output formats
    formats = [f.strip().lower() for f in output_formats.split(',')]
    
    # Validate formats
    for fmt in formats:
        if fmt not in OUTPUT_FORMATS:
            click.echo(click.style(f"Error: Invalid format '{fmt}'. Must be one of {OUTPUT_FORMATS}", fg='red'))
            sys.exit(1)
    
    try:
        # Load configuration
        config = get_config()
        
        # Override with command-line options
        model_name = model or config.whisper_model
        lang = language or config.language
        out_dir = output_dir or config.output_dir
        
        click.echo(click.style(f"\n📦 Batch Processing Mode", bold=True))
        click.echo(f"Input folder:  {Path(input_folder).resolve()}")
        click.echo(f"Model:         {model_name}")
        click.echo(f"Language:      {lang}")
        click.echo(f"Output dir:    {out_dir}")
        click.echo(f"Workers:       {workers} (sequential)")
        click.echo(f"Formats:       {', '.join(formats)}")
        click.echo("-" * 60)
        
        # Check if folder has video files
        video_files = get_video_files(input_folder)
        if not video_files:
            click.echo(click.style(f"No video files found in {input_folder}", fg='yellow'))
            sys.exit(0)
        
        click.echo(f"Found {len(video_files)} video files\n")
        
        # Initialize transcriber
        transcriber = VideoTranscriber(
            model_name=model_name,
            language=lang,
            device='cpu',
            output_dir=out_dir
        )
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            transcriber=transcriber,
            max_workers=workers
        )
        
        # Process folder
        results = batch_processor.process_folder(
            input_folder,
            output_formats=formats
        )
        
        # Display summary
        click.echo("\n" + "=" * 60)
        click.echo(click.style("BATCH PROCESSING SUMMARY", bold=True))
        click.echo("=" * 60)
        click.echo(f"Total files:     {results['total']}")
        click.echo(click.style(f"Successful:      {results['successful']}", fg='green'))
        
        if results['failed'] > 0:
            click.echo(click.style(f"Failed:          {results['failed']}", fg='red'))
        
        if results['skipped'] > 0:
            click.echo(click.style(f"Skipped:         {results['skipped']}", fg='yellow'))
        
        click.echo("=" * 60)
        
        # Exit with error code if any failures
        if results['failed'] > 0:
            sys.exit(1)
        
    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo(click.style("\n⚠ Batch processing cancelled by user", fg='yellow'))
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        logger.exception("Batch processing failed")
        sys.exit(1)


@cli.command()
def check():
    """
    Check system dependencies and configuration.
    
    Verifies ffmpeg installation, Python packages, and displays system info.
    """
    import subprocess
    import shutil
    
    click.echo(click.style("\n🔍 System Check", bold=True))
    click.echo("=" * 60)
    
    # System information
    click.echo("\nSystem Information:")
    click.echo(f"  Python version:   {platform.python_version()}")
    click.echo(f"  OS:               {platform.system()} {platform.release()}")
    click.echo(f"  Architecture:     {platform.machine()}")
    
    # Check ffmpeg
    click.echo("\nFFmpeg Check:")
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        click.echo(click.style(f"  ✓ FFmpeg found:   {ffmpeg_path}", fg='green'))
        
        # Get ffmpeg version
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_line = result.stdout.split('\n')[0]
            click.echo(f"    Version:        {version_line}")
        except Exception:
            pass
    else:
        click.echo(click.style("  ✗ FFmpeg NOT found", fg='red'))
        click.echo("    Please install ffmpeg:")
        click.echo("      Windows:  choco install ffmpeg")
        click.echo("      macOS:    brew install ffmpeg")
        click.echo("      Linux:    sudo apt install ffmpeg")
    
    # Check Python packages
    click.echo("\nPython Packages:")
    packages = [
        ('whisper', 'openai-whisper'),
        ('torch', 'PyTorch'),
        ('ffmpeg', 'ffmpeg-python'),
        ('tqdm', 'tqdm'),
        ('dotenv', 'python-dotenv'),
        ('click', 'click')
    ]
    
    all_installed = True
    for module_name, package_name in packages:
        try:
            __import__(module_name)
            click.echo(click.style(f"  ✓ {package_name:<25} Installed", fg='green'))
        except ImportError:
            click.echo(click.style(f"  ✗ {package_name:<25} NOT INSTALLED", fg='red'))
            all_installed = False
    
    # Check configuration
    click.echo("\nConfiguration:")
    try:
        config = get_config()
        click.echo(f"  Model:          {config.whisper_model}")
        click.echo(f"  Language:       {config.language}")
        click.echo(f"  Device:         {config.device}")
        click.echo(f"  Output Dir:     {config.output_dir}")
        click.echo(f"  Log Level:      {config.log_level}")
    except Exception as e:
        click.echo(click.style(f"  Error loading config: {e}", fg='red'))
    
    # Final status
    click.echo("\n" + "=" * 60)
    if all_installed and ffmpeg_path:
        click.echo(click.style("✓ All dependencies are installed!", fg='green', bold=True))
    else:
        click.echo(click.style("⚠ Some dependencies are missing. Please install them.", fg='yellow', bold=True))
        click.echo("\nTo install Python dependencies:")
        click.echo("  pip install -r requirements.txt")
    
    click.echo()


@cli.command()
def models():
    """
    Display available Whisper models and their characteristics.
    """
    click.echo(click.style("\n🎯 Available Whisper Models", bold=True))
    click.echo("=" * 70)
    click.echo(f"{'Model':<12} {'Parameters':<15} {'VRAM':<12} {'Speed':<15} {'Quality'}")
    click.echo("-" * 70)
    click.echo(f"{'tiny':<12} {'39M':<15} {'~1GB':<12} {'~32x':<15} {'Basic'}")
    click.echo(f"{'base':<12} {'74M':<15} {'~1GB':<12} {'~16x':<15} {'Good'}")
    click.echo(f"{'small':<12} {'244M':<15} {'~2GB':<12} {'~6x':<15} {'Better'}")
    click.echo(f"{'medium':<12} {'769M':<15} {'~5GB':<12} {'~2x':<15} {'Excellent'}")
    click.echo(f"{'large':<12} {'1550M':<15} {'~10GB':<12} {'1x':<15} {'Best'}")
    click.echo("=" * 70)
    click.echo("\nNotes:")
    click.echo("  • Speed is relative to real-time audio (lower = faster)")
    click.echo("  • VRAM shown is approximate GPU memory requirement")
    click.echo("  • For CPU-only mode, processing will be slower")
    click.echo("  • Recommended: 'base' for quick tests, 'medium' for production")
    click.echo()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
