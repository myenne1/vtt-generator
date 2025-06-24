"""
Vercel-compatible FastAPI application for closed captioning service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configurations.config import settings
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from api.whisper_api import run_openai_batch_transcription
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware



app = FastAPI(title="Closed Captioning Service", version="1.0.0")

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

@app.post("/batch-generate-vtt")
@limiter.limit(RATE_LIMIT)
async def batch_generate_vtt(request: Request, _: str = Depends(verify_api_key)):
    """
    Batch generate VTT files from media files in S3 bucket
    """
    try:
        print("Batch transcription started...")
        result = await run_openai_batch_transcription()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Batch transcription failed: {str(e)}"}
        )