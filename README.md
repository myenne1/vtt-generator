# Closed Captioning Service

This is a FastAPI backend that accepts audio or video files and generates corresponding `.vtt` caption files using the OpenAI Whisper model through the SubsAI wrapper. It supports batch uploads and creates a timestamped folder containing all outputs and a log file.

## Features

- Accepts multiple `.mp3` or `.mp4` files in one request
- Generates `.vtt` subtitle files for each input
- Saves output files in a folder named by date and time
- Generates a log file documenting success or errors for each file

## API Endpoint

### POST /batch-generate-vtt

**Description**: Accepts multiple media files and returns paths to generated `.vtt` files or error messages.

**Request**:
- Content-Type: multipart/form-data
- Field: `files` (multiple files allowed)
- File types: `.mp3`, `.mp4`

## Installation

1. Clone the Repository with subsai submodule:
```sh
git clone --recurse-submodules https://github.com/your-username/closed-captioning-service.git
cd closed-captioning-service
```

2. Create and activate a virtual environment
```sh
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install dependencies
```sh
pip install -r requirements.txt
```

4. Start the server
```sh
uvicorn subsAPI:app --reload
```

## Testing the Service
- Test using browser

Open the `test.html` file and select a folder to upload

## Output

- Each upload creates a folder like: 
```sh
2025-06-05 - 02:02:22 PM/
├── audio1.mp3
├── audio1.vtt
├── audio2.mp4
├── audio2.vtt
└── log.txt
```
`log.txt` includes the filename, status (Success/Failed), timestamp, and any error messages.
