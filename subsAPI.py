import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from subsai import SubsAI

app = FastAPI()

@app.post("/generate-vtt")
async def generate_vtt(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename
    
    allowed_extensions = {".mp3", ".mp4"}
    _, ext = os.path.splitext(filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only mp3 and mp4 are allowed.")
    
    with open(filename, "wb") as f:
        f.write(contents)
    
    vtt_path = run_subsai(filename)

    return FileResponse(vtt_path, media_type='text/vtt', filename=os.path.basename(vtt_path))


def run_subsai(filename):
    subs_ai = SubsAI()
    model = subs_ai.create_model('openai/whisper', {'model_type': 'base'})
    subs = subs_ai.transcribe(filename, model)
    
    basename, _ = os.path.splitext(filename)
    vtt_filename = f"{basename}.vtt"
    
    subs.save(vtt_filename)
    return vtt_filename