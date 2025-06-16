# Closed Captioning Service

A FastAPI-based service that automatically generates WebVTT subtitle files from audio/video files using OpenAI's Whisper model. The service monitors AWS S3 buckets for new media files and processes them in batches, with comprehensive logging and error handling.

## 🚀 Features

- **S3 Integration**: Automatically monitors S3 buckets for new media files
- **Batch Processing**: Processes multiple files in a single operation
- **Smart File Detection**: Configurable time window to detect recently uploaded files
- **Robust Error Handling**: Individual file failures don't stop batch processing
- **Comprehensive Logging**: Detailed logs with timestamps and error tracking
- **File Validation**: Security-focused validation with MIME type checking
- **Automatic Cleanup**: Temporary files are cleaned up after processing

## 📋 Requirements

- Python 3.8+
- FFmpeg (required by Whisper)
- AWS S3 bucket access
- OpenAI Whisper compatible hardware

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone --recurse-submodules <your-repo-url>
cd ClosedCaptioning
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Install SubsAI
pip install git+https://github.com/absadiki/subsai
```

### 4. Install System Dependencies
```bash
# macOS (using Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg

# Windows (using Scoop)
scoop install ffmpeg
```

## ⚙️ Configuration

### 1. Environment Setup
Copy the example environment file and configure it:
```bash
cp configurations/.env.example configurations/configs.env
```

### 2. Required Configuration
Edit `configurations/configs.env` with your settings:

```bash
# File Processing Settings
MAX_FILE_SIZE=104857600  # 100MB in bytes
ALLOWED_EXTENSIONS=[".mp3", ".mp4"]
ALLOWED_MIME_TYPES=["audio/mpeg", "video/mp4"]  # IMPORTANT: Use proper MIME types
MIME_CHECKING=true

# S3 Configuration
BUCKET_NAME=your-s3-bucket-name
TIME_WINDOW=15  # Minutes to look back for recent files

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
```

### 3. AWS S3 Setup
1. Create an S3 bucket for media file processing
2. Ensure your AWS credentials have permissions for:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:ListBucket`

## 🚀 Running the Service

### Method 1: Web API Server
```bash
# Start the FastAPI server with auto-reload
uvicorn subsAPI:app --reload

# Server will be available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Method 2: Direct Batch Processing
```bash
# Run batch processing directly (no API server)
python subsAPI.py
```

## 🧪 Testing

### 1. Test S3 Integration
Upload `.mp3` or `.mp4` files to your configured S3 bucket, then:
```bash
curl -X POST http://localhost:8000/batch-generate-vtt
```

### 2. Browser Testing
Open `test.html` in your browser for a simple upload interface.
Ensure uvicorn is running.

### 3. Command Line Testing
```bash
# Test API endpoint
curl -X POST "http://localhost:8000/batch-generate-vtt" \
     -H "Content-Type: application/json"
```

### 4. Verify Configuration
```bash
# Check if your environment is properly configured
python -c "from configurations.config import settings; print(f'Bucket: {settings.BUCKET_NAME}')"
```

## 📁 Project Structure

```
ClosedCaptioning/
├── subsAPI.py                  # Main FastAPI application
├── s3.py                      # S3 integration and file scanning
├── file_validation.py         # File validation and security
├── logger_util.py             # Logging utilities
├── configurations/
│   ├── config.py              # Pydantic settings management
│   ├── configs.env            # Your environment variables
│   └── .env.example           # Configuration template
├── requirements.txt           # Python dependencies
├── test.html                  # Browser testing interface
└── subsai/                    # SubsAI submodule
```

## 🔄 How It Works

1. **File Detection**: Service scans your S3 bucket for files uploaded within the configured time window
2. **Download & Validate**: Files are downloaded to temporary locations and validated for security
3. **Transcription**: Each file is processed through OpenAI Whisper using SubsAI
4. **VTT Generation**: Subtitle files are generated in WebVTT format
5. **Upload Results**: Generated VTT files and logs are uploaded back to S3
6. **Cleanup**: Temporary files are automatically removed

## 📤 Output Structure

Results are organized in timestamped directories in your S3 bucket:
```
your-bucket/
└── 2025-06-16_10-30-45/
    ├── audio1.vtt          # Generated subtitles
    ├── video1.vtt          # Generated subtitles
    └── log.txt             # Processing log
```

## 🔧 API Endpoints

### POST /batch-generate-vtt
Triggers batch processing of recent files in the configured S3 bucket.

**Response:**
```json
{
  "message": "Batch transcription completed"
}
```

### GET /docs
FastAPI automatic documentation interface.

## 🐛 Troubleshooting

### Common Issues

**1. MIME Type Validation Errors**
- Ensure `ALLOWED_MIME_TYPES` uses proper MIME types, not file extensions
- Correct: `["audio/mpeg", "video/mp4"]`
- Wrong: `[".mp3", ".mp4"]`

**2. S3 Permission Errors**
```bash
# Verify AWS credentials
aws s3 ls s3://your-bucket-name/

# Test S3 access
python -c "import boto3; print(boto3.client('s3').list_buckets())"
```

**3. FFmpeg Not Found**
```bash
# Verify ffmpeg installation
ffmpeg -version

# If not installed, install using the system dependency commands above
```

**4. SubsAI Import Errors**
```bash
# Reinstall SubsAI
pip uninstall subsai
pip install git+https://github.com/absadiki/subsai
```