# Vercel Deployment Guide

## Prerequisites
1. Install Vercel CLI: `npm i -g vercel`
2. Have AWS credentials ready for S3 access
3. Ensure your S3 bucket is set up and accessible

## Deployment Steps

### 1. Login to Vercel
```bash
vercel login
```

### 2. Configure Environment Variables
In your Vercel dashboard or via CLI, set these variables:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key  
- `AWS_REGION`: Your AWS region (e.g., us-east-1)
- `BUCKET_NAME`: Your S3 bucket name
- `MAX_FILE_SIZE`: 104857600 (100MB)
- `ALLOWED_EXTENSIONS`: .mp3,.mp4
- `TIME_WINDOW`: 60 (minutes)

### 3. Deploy
```bash
vercel --prod
```

## Important Limitations

### Vercel Function Limits
- **Execution Time**: 5 minutes max (300 seconds)
- **Memory**: 1GB max
- **Payload Size**: 4.5MB max
- **Temporary Storage**: 512MB max

### Recommendations
1. **File Size**: Keep media files under 50MB for reliable processing
2. **Processing Time**: Large files may timeout - consider chunking
3. **Memory Usage**: Whisper models can be memory-intensive
4. **Cold Starts**: First request may be slower due to model loading

### Monitoring
- Check Vercel Function logs for processing status
- Monitor S3 bucket for successful outputs
- Set up alerts for failed executions

## Cron Jobs
The service is configured to run every 6 hours automatically via Vercel Cron Jobs.
You can modify the schedule in `vercel.json`.

## Testing
Test the deployment:
```bash
curl -X POST https://your-vercel-domain.vercel.app/batch-generate-vtt
```
EOF < /dev/null