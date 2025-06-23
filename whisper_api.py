"""
OpenAI Whisper API integration for serverless deployment
Lightweight alternative to SubsAI for Vercel compatibility
"""

import mimetypes
import os
import asyncio
import datetime
from zoneinfo import ZoneInfo
import shutil
from typing import List, Tuple
from openai import OpenAI
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from s3 import upload_file_to_s3, scan_bucket_for_recent_media
from logger_util import LogWriter
from configurations.config import settings

# OpenAI client initialization
client = OpenAI(api_key=settings.OPENAI_API_KEY)

BUCKET_NAME = settings.BUCKET_NAME


def transcribe_with_openai_api(audio_file_path: str, original_filename: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    Returns path to generated VTT file
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Call OpenAI Whisper API
            mime_type, _ = mimetypes.guess_type(original_filename)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=(original_filename, audio_file, mime_type),
                response_format="vtt"  # Direct VTT output
            )
        
        # Save VTT content to file
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
        vtt_filename = os.path.join("/tmp", f"{base_name}.vtt")
        
        with open(vtt_filename, "w", encoding="utf-8") as vtt_file:
            vtt_file.write(transcript)
        
        return vtt_filename
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API transcription failed: {str(e)}")


async def run_openai_batch_transcription():
    """
    Batch transcription using OpenAI Whisper API
    Maintains same workflow as SubsAI version but serverless-compatible
    """
    # Create output directory with timestamp
    local_timezone = ZoneInfo('America/Chicago')
    date_str = datetime.datetime.now(local_timezone).strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now(local_timezone).strftime("%I-%M-%S")
    date_time_str = f"{date_str}_{timestamp}"
    output_dir = os.path.join("/tmp", date_time_str)  # Use /tmp for serverless
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "log.txt")
    logger = LogWriter(log_path)
    
    # Initialize log file with start message
    logger.write(f"OpenAI Whisper API batch transcription started at {timestamp}")
    logger.write(f"Output directory: {output_dir}")
    logger.write(f"Using OpenAI Whisper API (serverless mode)\n")

    try:
        # Scan S3 bucket for recent media files
        media_files = scan_bucket_for_recent_media(BUCKET_NAME, logger=logger)
        
        if not media_files:
            logger.write("No recent media files found in S3 bucket\n")
        else:
            logger.write(f"Found {len(media_files)} media files to process:\n")
            
            for key, local_path in media_files:
                logger.write(f"Processing file: {key}")
                try:
                    # Use OpenAI API instead of SubsAI
                    vtt_path = transcribe_with_openai_api(local_path, original_filename=key)
                    
                    vtt_filename = os.path.basename(vtt_path)
                    final_vtt_path = os.path.join(output_dir, vtt_filename)
                    os.replace(vtt_path, final_vtt_path)
                    logger.write(f"Successfully generated VTT using OpenAI API: {vtt_filename}")

                    # Clean up local media file
                    os.remove(local_path)
                    logger.write(f"Cleaned up local file: {local_path}\n")
                    
                except Exception as e:
                    logger.write(f"Error processing {key}: {str(e)}\n")
                    # Clean up on error
                    if os.path.exists(local_path):
                        os.remove(local_path)

        # Upload results to S3
        logger.write("Uploading files to S3...")
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                upload_file_to_s3(file_path, f"{date_time_str}/{filename}")
                logger.write(f"Uploaded to S3: {filename}")
            except Exception as e:
                logger.write(f"Error uploading {filename}: {str(e)}")

        # Upload log file to S3
        try:
            upload_file_to_s3(log_path, f"{date_time_str}/log.txt")
        except Exception as e:
            logger.write(f"Error uploading log file: {str(e)}")
                
    finally:
        # Clean up temporary folder
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)


def get_api_usage_estimate(audio_duration_minutes: float) -> dict:
    """
    Estimate OpenAI API costs for transcription
    """
    cost_per_minute = 0.006  # $0.006 per minute as of 2024
    estimated_cost = audio_duration_minutes * cost_per_minute
    
    return {
        "duration_minutes": audio_duration_minutes,
        "cost_per_minute_usd": cost_per_minute,
        "estimated_cost_usd": round(estimated_cost, 4)
    }
    
if __name__ == "__main__":
    asyncio.run(run_openai_batch_transcription())