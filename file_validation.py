import os
import re
from fastapi import HTTPException
from configurations.config import settings
from filetype import guess

MAX_FILE_SIZE = settings.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS
ALLOWED_MIME_TYPES = settings.ALLOWED_MIME_TYPES
MIME_CHECKING = settings.MIME_CHECKING

def validate_file(filename: str, contents: bytes):
    """
    Validates the uploaded file for:
    - Filename presence
    - File extension whitelist
    - MIME type correctness
    - Maximum allowed file size
    """
    print(f"Validating file: {filename}")
    print(f"File size: {len(contents)} bytes")
    
    if not filename:
        raise HTTPException(400, "No filename provided")
        
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {ext} not supported")
    
    kind = guess(contents)
    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "File type is not accepted")
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File size exceeds the limit of {MAX_FILE_SIZE} bytes.")

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes the filename by:
    - Stripping path info
    - Replacing special characters with underscores
    """
    filename = os.path.basename(filename)
    return re.sub(r'[^\w\-.]', '_', filename)