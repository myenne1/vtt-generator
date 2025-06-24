"""
Vercel-compatible FastAPI application for closed captioning service
"""

import sys
import os
from urllib import request
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configurations.config import settings
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from api.whisper_api import run_openai_batch_transcription

app = FastAPI(title="Closed Captioning Service", version="1.0.0")
API_KEY = settings.API_KEY

@app.get("/")
async def root():
    return {"message": "Closed Captioning Service is running"}

@app.post("/batch-generate-vtt")
async def batch_generate_vtt(x_api_key: str = Header(...)):
    """
    Batch generate VTT files from media files in S3 bucket
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        print("Batch transcription started...")
        await run_openai_batch_transcription()
        return JSONResponse(content={"message": "Batch transcription completed successfully"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Batch transcription failed: {str(e)}"}
        )