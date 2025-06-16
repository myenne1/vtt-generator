# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **FastAPI-based closed captioning service** that automatically generates WebVTT subtitle files from audio/video files using OpenAI's Whisper model. The service has evolved from a simple file upload system to an **AWS S3-integrated batch processing system** that monitors S3 buckets for new media files and processes them automatically.

## Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (ffmpeg required for Whisper)
brew install ffmpeg  # macOS
# sudo apt install ffmpeg  # Ubuntu/Debian

# Install SubsAI from GitHub
pip install git+https://github.com/absadiki/subsai

# Clone with submodules if needed
git clone --recurse-submodules <repo-url>
```

### Running the Service
```bash
# Start the FastAPI server with auto-reload
uvicorn subsAPI:app --reload

# Run batch processing directly (bypasses API)
python subsAPI.py
```

### Testing
```bash
# Open test.html in browser for manual testing
# API endpoint: POST /batch-generate-vtt
# Service runs on: http://localhost:8000
```

## Architecture Overview

### Core Components
- **`subsAPI.py`**: Main FastAPI application with batch processing endpoint
- **`s3.py`**: S3 integration for file upload/download and bucket monitoring
- **`file_validation.py`**: File validation, sanitization and security checks
- **`logger_util.py`**: Simple logging utility for processing status

### Processing Flow
1. **S3 Monitoring**: Scans S3 bucket for recently uploaded media files (within configurable time window)
2. **File Processing**: Downloads qualifying files, validates them, and processes through Whisper
3. **VTT Generation**: Creates WebVTT subtitle files using SubsAI wrapper
4. **Output Management**: Saves results in timestamped directories and uploads back to S3
5. **Cleanup**: Removes local temporary files after processing

### Configuration System
- **`configurations/config.py`**: Pydantic settings class for type-safe configuration
- **`configurations/configs.env`**: Environment variables (contains AWS credentials)
- **`configurations/.env.example`**: Template for environment setup

Key settings:
- `MAX_FILE_SIZE`: 100MB limit
- `ALLOWED_EXTENSIONS`: [".mp3", ".mp4"]
- `TIME_WINDOW`: Minutes to look back for recent S3 files
- `BUCKET_NAME`: S3 bucket name for processing
- AWS credentials for S3 access

### Dependencies
- **FastAPI + Uvicorn**: Web framework and ASGI server
- **OpenAI Whisper**: Speech-to-text transcription
- **SubsAI**: Wrapper library for speech recognition models
- **Boto3**: AWS SDK for S3 integration
- **Pydantic**: Data validation and settings management

## Key Technical Details

### File Processing
- Supports `.mp3` and `.mp4` files only
- Validates file types using both extension and MIME type checking
- Maximum file size: 100MB
- Automatic filename sanitization for security

### S3 Integration
- Monitors S3 bucket for files uploaded within specified time window
- Downloads files to temporary locations for processing
- Uploads generated VTT files and logs back to S3
- Organized output in timestamped directories

### Output Structure
```
2025-06-11_03-48-07/
├── audio1.vtt
├── audio2.vtt
└── log.txt
```

### Error Handling
- Comprehensive logging of all processing steps
- Individual file error handling (one failure doesn't stop batch)
- Cleanup of temporary files even on errors
- Detailed error messages in log files

## Development Notes

### Current Branch Structure
- `main`: Stable releases
- `iter2`: Current development branch with S3 integration
- `dev`: General development branch
- `batching`: Legacy batch processing implementation

### SubsAI Integration
- Uses SubsAI as a Git submodule (`subsai/` directory)
- Configured to use OpenAI Whisper 'base' model
- Generates WebVTT format subtitles

### Security Considerations
- File validation prevents malicious uploads
- Filename sanitization prevents path traversal
- MIME type checking beyond extension validation
- AWS credentials stored in environment variables