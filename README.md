# Closed Captioning Service

A serverless FastAPI-based service that automatically generates WebVTT subtitle files from audio/video files using OpenAI's Whisper API. The service monitors AWS S3 buckets for new media files and processes them in batches, optimized for Vercel deployment with comprehensive logging and error handling.

## 🚀 Features

- **Serverless Deployment**: Fully compatible with Vercel for zero-maintenance scaling
- **OpenAI Whisper API**: Uses OpenAI's hosted Whisper service (no local ML dependencies)
- **S3 Integration**: Automatically monitors S3 buckets for new media files
- **Batch Processing**: Processes multiple files in a single operation
- **Smart File Detection**: Configurable time window to detect recently uploaded files
- **Robust Error Handling**: Individual file failures don't stop batch processing
- **Comprehensive Logging**: Detailed logs with timestamps and error tracking
- **File Validation**: Security-focused validation with MIME type checking
- **Automatic Cleanup**: Temporary files are cleaned up after processing

## 📋 Requirements

- OpenAI API key (for Whisper transcription)
- AWS S3 bucket access
- Vercel account (for deployment)

## 🛠️ Installation & Deployment

### 1. Clone the Repository
```bash
git clone https://github.com/myenne1/ClosedCaptioning.git
cd ClosedCaptioning
```

### 2. Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Deploy to Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## ⚙️ Configuration

### 1. Environment Variables
Configure the following environment variables in your Vercel dashboard or `.env.vercel` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# File Processing Settings
MAX_FILE_SIZE=104857600  # 100MB in bytes
ALLOWED_EXTENSIONS=[".mp3", ".mp4"]
TIME_WINDOW=15  # Minutes to look back for recent files

# S3 Configuration
BUCKET_NAME=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
```

### 2. AWS S3 Setup
1. Create an S3 bucket for media file processing
2. Ensure your AWS credentials have permissions for:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:ListBucket`

### 3. OpenAI API Setup
1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add credits to your OpenAI account
3. Note: Whisper API costs $0.006 per minute of audio

## 🚀 Running the Service

### Production (Vercel)
The service automatically runs on Vercel with:
- **Endpoint**: `https://your-app.vercel.app/batch-generate-vtt`
- **Cron Job**: Daily processing at 10 AM UTC (configured in `vercel.json`)
- **Automatic Scaling**: Handles traffic spikes automatically

### Local Development
```bash
# Start the FastAPI server
uvicorn api.main:app --reload

# Server available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Direct Processing
```bash
# Run batch processing directly
python -m api.whisper_api
```

## 🧪 Testing

### 1. Test Deployed Service
```bash
# Test your deployed Vercel endpoint
curl -X POST "https://your-app.vercel.app/batch-generate-vtt"
```

### 2. Test Locally
```bash
# Start local server
uvicorn api.main:app --reload

# Test endpoint
curl -X POST "http://localhost:8000/batch-generate-vtt"

### 3. Upload Test Files
Upload `.mp3` or `.mp4` files to your S3 bucket, then trigger processing via the API.

## 📁 Project Structure

```
ClosedCaptioning/
├── api/
│   └── main.py                # FastAPI application (Vercel entry point)
├── whisper_api.py             # OpenAI Whisper API integration
├── s3.py                      # S3 integration and file scanning
├── file_validation.py         # File validation and security
├── logger_util.py             # Logging utilities
├── configurations/
│   └── config.py              # Pydantic settings management
├── requirements.txt           # Python dependencies (serverless-optimized)
├── vercel.json                # Vercel deployment configuration
└── README.md                  # This file
```

## 🔄 How It Works

1. **Serverless Trigger**: API endpoint or cron job triggers batch processing
2. **File Detection**: Service scans S3 bucket for files uploaded within configured time window
3. **Download & Validate**: Files are downloaded to `/tmp` and validated for security
4. **OpenAI Transcription**: Each file is processed through OpenAI's Whisper API
5. **VTT Generation**: Subtitle files are generated in WebVTT format
6. **Upload Results**: Generated VTT files and logs are uploaded back to S3
7. **Cleanup**: Temporary files are automatically removed

## 📤 Output Structure

Results are organized in timestamped directories in your S3 bucket:
```
your-bucket/
└── 2025-06-23_09-30-45/
    ├── audio1.vtt          # Generated subtitles
    ├── video1.vtt          # Generated subtitles
    └── log.txt             # Processing log
```

## 🔧 API Endpoints

### POST /batch-generate-vtt
Triggers batch processing of recent files in the configured S3 bucket using OpenAI Whisper API.

**Response:**
```json
{
  "message": "Batch transcription completed successfully"
}
```

## 💰 Cost Considerations

- **OpenAI Whisper API**: $0.006 per minute of audio
- **Vercel**: Free tier includes 100GB-hours/month of serverless function usage

**Example costs:**
- 10 minutes of audio: ~$0.06
- 1 hour of audio: ~$0.36
- 10 hours of audio: ~$3.60

## 🐛 Troubleshooting

### Common Issues

**1. Vercel Deployment Issues**
- Check function logs in Vercel dashboard
- Ensure all environment variables are set
- Verify `requirements.txt` contains only serverless-compatible dependencies

**2. File Processing Errors**
- Supported formats: MP3, MP4
- Maximum file size: 100MB
- Files must be uploaded to S3 within the configured time window

**3. Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run locally
uvicorn api.main:app --reload
```

## 🔒 Security

- File validation includes MIME type checking
- Temporary files are automatically cleaned up
- AWS credentials should use minimal required permissions
- OpenAI API key should be kept secure and rotated regularly
