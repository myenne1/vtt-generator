"""
Vercel-compatible FastAPI application for closed captioning service
"""

import sys
import os
from urllib import request
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configurations.config import settings
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from api.whisper_api import run_openai_batch_transcription
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import boto3
from openai import OpenAI
from datetime import datetime



app = FastAPI(
    title="Closed Captioning Service", 
    version="1.0.0",
    description="""
    A serverless FastAPI service for generating WebVTT subtitle files from audio/video files using OpenAI's Whisper API.
    
    ## Endpoints
    - **GET /**: Service status check
    - **GET /health**: Comprehensive health check with S3 and OpenAI connectivity tests
    - **POST /batch-generate-vtt**: Process media files from S3 bucket and generate VTT files
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

API_KEY = settings.API_KEY
RATE_LIMIT = settings.RATE_LIMIT

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Please try again later"}
    )
    
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail= "Unauthorized")

@app.get("/")
async def root():
    return {"message": "Closed Captioning Service is running"}

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint that tests:
    - Service status
    - S3 connectivity
    - OpenAI API connectivity
    - Configuration validation
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Closed Captioning Service",
        "version": "1.0.0",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Check S3 connectivity
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Test bucket access
        s3_client.head_bucket(Bucket=settings.BUCKET_NAME)
        
        health_status["checks"]["s3"] = {
            "status": "healthy",
            "message": f"Successfully connected to bucket: {settings.BUCKET_NAME}",
            "region": settings.AWS_REGION
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["s3"] = {
            "status": "unhealthy",
            "message": f"S3 connection failed: {str(e)}"
        }
    
    # Check OpenAI API connectivity
    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Test API connectivity with a minimal request
        models = openai_client.models.list()
        
        health_status["checks"]["openai"] = {
            "status": "healthy",
            "message": "OpenAI API connection successful",
            "models_available": len(models.data) > 0
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["openai"] = {
            "status": "unhealthy",
            "message": f"OpenAI API connection failed: {str(e)}"
        }
    
    # Check configuration
    config_issues = []
    if not settings.OPENAI_API_KEY:
        config_issues.append("OPENAI_API_KEY not set")
    if not settings.BUCKET_NAME:
        config_issues.append("BUCKET_NAME not set")
    if not settings.AWS_ACCESS_KEY_ID:
        config_issues.append("AWS_ACCESS_KEY_ID not set")
    if not settings.AWS_SECRET_ACCESS_KEY:
        config_issues.append("AWS_SECRET_ACCESS_KEY not set")
    
    if config_issues:
        overall_healthy = False
        health_status["checks"]["configuration"] = {
            "status": "unhealthy",
            "message": f"Configuration issues: {', '.join(config_issues)}"
        }
    else:
        health_status["checks"]["configuration"] = {
            "status": "healthy",
            "message": "All required configuration values are set"
        }
    
    # Update overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.post("/batch-generate-vtt")
@limiter.limit(RATE_LIMIT)
async def batch_generate_vtt(request: Request, _: str = Depends(verify_api_key)):
    """
    Batch generate VTT files from media files in S3 bucket
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        print("Batch transcription started...")
        result = await run_openai_batch_transcription()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Batch transcription failed: {str(e)}"}
        )
