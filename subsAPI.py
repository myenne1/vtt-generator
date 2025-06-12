"""
Batch VTT Generator API

This FastAPI script allows users to upload multiple .mp3 or .mp4 files, transcribes them
using the SubsAI (OpenAI Whisper-based) library, and generates corresponding .vtt files.
All output files and logs are saved inside a timestamped folder.

To run the script:
    uvicorn subsAPI:app --reload

Endpoint:
    POST /batch-generate-vtt
        - Accepts multiple files via multipart/form-data
        - Returns JSON response with per-file success or error info
"""

import re
import shutil
from configurations.config import settings
import os
import asyncio

from typing import List
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from subsai import SubsAI
import boto3
from s3 import upload_file_to_s3, scan_bucket_for_recent_media
from logger_util import LogWriter

app = FastAPI()

s3 = boto3.client('s3')

BUCKET_NAME = settings.BUCKET_NAME

@app.post("/batch-generate-vtt")
async def batch_generate_vtt():
    await run_batch_generate_transcription()
    return JSONResponse(content={"message": "Batch transcription completed"})

async def run_batch_generate_transcription():
    # Create output directory with timestamp
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now().strftime("%I-%M-%S")
    date_time_str = f"{date_str}_{timestamp}"
    output_dir = os.path.join(date_time_str)
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "log.txt")
    logger = LogWriter(log_path)
    
    # Initialize log file with start message
    logger.write(f"Batch transcription started at {timestamp}")
    logger.write(f"Output directory: {output_dir}\n")

    media_files = scan_bucket_for_recent_media(BUCKET_NAME, logger=logger)
    
    if not media_files:
        logger.write("No recent media files found in S3 bucket\n")
    else:
        logger.write(f"Found {len(media_files)} media files to process:\n")
        
        for key, local_path in media_files:
            logger.write(f"Processing file: {key}")
            try:
                vtt_path = run_subsai(local_path, original_filename=key)
                
                vtt_filename = os.path.basename(vtt_path)
                final_vtt_path = os.path.join(output_dir, vtt_filename)
                os.replace(vtt_path, final_vtt_path)
                logger.write(f"Successfully generated VTT: {vtt_filename}")

                os.remove(local_path)
                logger.write(f"Cleaned up local file: {local_path}\n")
            except Exception as e:
                logger.write(f"Error processing {key}: {str(e)}\n")

    logger.write("Uploading files to S3...")
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        try:
            upload_file_to_s3(file_path, f"{date_time_str}/{filename}")
            logger.write(f"Uploaded to S3: {filename}")
        except Exception as e:
            logger.write(f"Error uploading {filename}: {str(e)}")

    # Upload log file to S3
    upload_file_to_s3(log_path, f"{date_time_str}/log.txt")
    
    # Clean up folder
    shutil.rmtree(output_dir)

def run_subsai(media_path, original_filename):
    subs_ai = SubsAI()
    model = subs_ai.create_model('openai/whisper', {'model_type': 'base'})
    subs = subs_ai.transcribe(media_path, model)
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    vtt_filename = f"{base_name}.vtt"
    subs.save(vtt_filename)
    return vtt_filename

if __name__ == "__main__":
    asyncio.run(run_batch_generate_transcription())