import boto3
from configurations.config import settings
from datetime import datetime, timedelta, timezone
from file_validation import validate_file, sanitize_filename
import tempfile
import os
from fastapi import HTTPException
from logger_util import LogWriter

s3 = boto3.client('s3')
BUCKET_NAME = settings.BUCKET_NAME
TIME_WINDOW = settings.TIME_WINDOW
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS

def upload_file_to_s3(file_path, s3_key):
    s3.upload_file(file_path, BUCKET_NAME, s3_key)

def download_file_from_s3(s3_key, file_path):
    s3.download_file(BUCKET_NAME, s3_key, file_path)

def scan_bucket_for_recent_media(bucket_name, logger: LogWriter, minutes=TIME_WINDOW):
    now = datetime.now(timezone.utc)
    time_window = now - timedelta(minutes=minutes)

    response = s3.list_objects_v2(Bucket=bucket_name)
    media_files = []

    for obj in response.get("Contents", []):
        key = obj["Key"]
        last_modified = obj["LastModified"]

        if key.lower().endswith(tuple(ALLOWED_EXTENSIONS)) and last_modified >= time_window:
            try:
                sanitized_name = sanitize_filename(key)
                
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    
                s3.download_file(bucket_name, key, tmp_path)
                
                with open(tmp_path, "rb") as f:
                    contents = f.read()
                    
                validate_file(sanitized_name, contents)
                media_files.append((key, tmp_path))
                
            except Exception as e:
                print(f"Skipping file {key}: {e}")
                timestamp_str = datetime.now().strftime("%I:%M:%S %p")
                logger.write(
                    f"Filename: {sanitized_name}\n"
                    f"Processing Status: Failed\n"
                    f"Error: {str(e)}\n"
                    )
            except HTTPException as e:
                timestamp_str = datetime.now().strftime("%I:%M:%S %p")
                logger.write(
                    f"Filename: {sanitized_name}\n"
                    f"Processing Status: Failed\n"
                    f"Error: {e.detail}\n"
                    )

    return media_files
