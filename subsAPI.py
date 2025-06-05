"""
Batch VTT Generator API

This FastAPI app allows users to upload multiple .mp3 or .mp4 files, transcribes them
using the SubsAI (OpenAI Whisper-based) library, and generates corresponding .vtt files.
All output files and logs are saved inside a timestamped folder.

To run the server:
    uvicorn subsAPI:app --reload

Endpoint:
    POST /batch-generate-vtt
        - Accepts multiple files via multipart/form-data
        - Returns JSON response with per-file success or error info
"""

import os
from typing import List
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from subsai import SubsAI

app = FastAPI()

@app.post("/batch-generate-vtt")
async def batch_generate_vtt(files: List[UploadFile] = File(...)):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    date_time_str = f"{date_str} - {timestamp}"
    output_dir = os.path.join(date_time_str)
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "log.txt")

    results = []
    
    for file in files:
        filename = os.path.basename(file.filename)
        log_entry = f"Filename: {filename}\n"

        try:
            contents = await file.read()
            media_path = os.path.join(output_dir, filename)
            with open(media_path, "wb") as f:
                f.write(contents)

            vtt_path = run_subsai(media_path, output_dir)
            timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
            log_entry += f"Processing Status: Success\nTime: {timestamp}\n\n"
            results.append({"input": filename, "vtt": vtt_path})
        except Exception as e:
            error_msg = str(e)
            log_entry += f"Processing Status: Failed\nError: {error_msg}\n\n"
            results.append({"input": filename, "error": error_msg})

        with open(log_path, "a") as log_file:
            log_file.write(log_entry)

    return JSONResponse(content=results)


def run_subsai(media_path, output_dir):
    subs_ai = SubsAI()
    model = subs_ai.create_model('openai/whisper', {'model_type': 'base'})
    subs = subs_ai.transcribe(media_path, model)

    base_name, _ = os.path.splitext(os.path.basename(media_path))
    vtt_filename = f"{base_name}.vtt"
    vtt_path = os.path.join(output_dir, vtt_filename)
    subs.save(vtt_path)
    return vtt_path