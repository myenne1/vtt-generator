"""
OpenAI Whisper API integration for serverless deployment
Lightweight alternative to SubsAI for Vercel compatibility
"""
from openai import RateLimitError, APIConnectionError, APIStatusError, OpenAIError
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
    
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: Too many requests to the OpenAI API. Please slow down and try again later."
        )
    
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Service  unavailable: Unable to connect to OpenAI servers. Please try again shortly."
        )
    
    except APIStatusError as e:
        if e.status_code == 401:
            raise HTTPException(401, "Invalid or expired OpenAI API Key.") 
        else:    
            raise HTTPException(
                status_code=e.status_code,
                detail=f"OpenAI API error: {e.message or 'Unexpected response from OpenAI'}"
            )
        
    except OpenAIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API error: {str(e)}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error during transcription: {str(e)}"
        )

async def run_openai_batch_transcription():
    local_timezone = ZoneInfo('America/Chicago')
    timestamp = datetime.datetime.now(local_timezone).strftime("%Y-%m-%d_%I-%M-%S")
    output_dir, log_path, logger = setup_transcription_directory(timestamp)
    empty_s3_flag = False

    success_count = 0
    failure_count = 0
    error_summary = []

    try:
        media_files = scan_bucket_for_recent_media(BUCKET_NAME, logger=logger)
        
        if media_files:
            success_count, failure_count, error_summary = await process_batch_files(media_files, output_dir, logger)
            upload_output_to_s3(output_dir, timestamp, logger)
            upload_log_file_to_s3(log_path, timestamp, logger)
        else:
            empty_s3_flag = True
    finally:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    return summarize_batch_results(success_count, failure_count, error_summary, empty_s3_flag)

def setup_transcription_directory(timestamp):
    output_dir = os.path.join("/tmp", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "log.txt")
    logger = LogWriter(log_path)
    logger.write(f"OpenAI Whisper API batch transcription started at {timestamp}")
    logger.write(f"Output directory: {output_dir}")
    logger.write("Using OpenAI Whisper API (serverless mode)\n")
    return output_dir, log_path, logger

async def process_batch_files(media_files, output_dir, logger):
    success_count = 0
    failure_count = 0
    error_summary = []

    for key, local_path in media_files:
        logger.write(f"Processing file: {key}")
        try:
            vtt_path = transcribe_with_openai_api(local_path, original_filename=key)
            final_path = os.path.join(output_dir, os.path.basename(vtt_path))
            os.replace(vtt_path, final_path)
            logger.write(f"Successfully generated VTT: {os.path.basename(vtt_path)}")
            os.remove(local_path)
            logger.write(f"Cleaned up local file: {local_path}\n")
            success_count += 1
        except Exception as e:
            logger.write(f"Error processing {key}: {str(e)}\n")
            error_summary.append(f"{key}: {str(e)}")
            failure_count += 1
            if os.path.exists(local_path):
                os.remove(local_path)

    return success_count, failure_count, error_summary

def upload_output_to_s3(output_dir, timestamp, logger):
    logger.write("Uploading files to S3...")
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        try:
            upload_file_to_s3(file_path, f"{timestamp}/{filename}")
            logger.write(f"Uploaded to S3: {filename}")
        except Exception as e:
            logger.write(f"Error uploading {filename}: {str(e)}")

def upload_log_file_to_s3(log_path, timestamp, logger):
    try:
        upload_file_to_s3(log_path, f"{timestamp}/log.txt")
    except Exception as e:
        logger.write(f"Error uploading log file: {str(e)}")

def summarize_batch_results(success_count, failure_count, error_summary, empty_s3_flag):
    if success_count == 0:
        if empty_s3_flag:
            return {"status": "failed", "message": "No files to transcribe"}
        else:
            return {"status": "failed", "message": "All files failed to transcribe.", "errors": error_summary}
        
    elif failure_count > 0:
        return {
            "status": "partial_success",
            "message": f"{success_count} files succeeded, {failure_count} failed.",
            "errors": error_summary,
        }
    else:
        return {"status": "success", "message": "All files transcribed successfully."}
            
if __name__ == "__main__":
    asyncio.run(run_openai_batch_transcription())