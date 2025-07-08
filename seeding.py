from fastapi import HTTPException
import os
import boto3
from faster_whisper import WhisperModel
from botocore.exceptions import NoCredentialsError, ClientError
from configurations.config import settings
import time
import datetime

# Load Whisper model
model = WhisperModel("base.en", device='auto', compute_type='int8')

def transcribe_with_whisper(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper
    Returns path to generated VTT file
    """
    try:
        start_time = time.time()  
        
        segments, _ = model.transcribe(audio_file_path)
        
        vtt_content = "WEBVTT\n\n"
        for i, segment in enumerate(segments):
            start = format_time(segment.start)
            end = format_time(segment.end)
            text = segment.text.strip()
            vtt_content += f"{start} --> {end}\n{text}\n\n"

        base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        vtt_filename = os.path.join("/tmp", f"{base_name}.vtt")
        with open(vtt_filename, "w", encoding="utf-8") as f:
            f.write(vtt_content)
            
        elapsed_time = time.time() - start_time
        print(f"Time taken: {elapsed_time * 1000:.2f} ms")
        
        return vtt_filename

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

def convert_to_vtt(result):
    """
    Convert Whisper result to VTT format
    """
    vtt_content = "WEBVTT\n\n"
    
    for segment in result['segments']:
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        text = segment['text'].strip()
        
        vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
    
    return vtt_content

def create_timestamped_folder() -> str:
    """
    Create a timestamped folder with format YYYY-MM-DD_HH-MM-SS
    Returns the full path to the created directory
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = timestamp
    
    # Create the directory if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created timestamped folder: {folder_path}")
    
    return folder_path

def format_time(seconds):
    """
    Format time in seconds to VTT time format (HH:MM:SS.mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def create_s3_client():
    """
    Create and return S3 client with credentials from settings
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        return s3_client
    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating S3 client: {str(e)}"
        )

def upload_to_s3(file_path: str, s3_key: str) -> str:
    """
    Upload file to S3 bucket
    Returns S3 URL of uploaded file
    """
    try:
        s3_client = create_s3_client()
        s3_client.upload_file(file_path, settings.BUCKET_NAME, s3_key)
        
        return f"https://{settings.BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}"
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading to S3: {str(e)}"
        )

def download_from_s3(s3_key: str, local_path: str) -> str:
    """
    Download file from S3 bucket to local path
    Returns local file path
    """
    try:
        s3_client = create_s3_client()
        s3_client.download_file(settings.BUCKET_NAME, s3_key, local_path)
        
        return local_path
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading from S3: {str(e)}"
        )

def get_s3_pages(bucket_name: str, prefix: str = ""):
    """
    List objects in S3 bucket with optional prefix
    Returns list of object keys
    """
    try:
        s3_client = create_s3_client()
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, PageSize=500)
        yield from pages
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing S3 objects: {str(e)}"
        )

def batch_upload_files(input_path: str = 'input', prefix: str = 'media/'):
    """
    Batch upload all media files from input directory to S3 bucket
    """
    if not os.path.exists(input_path):
        raise Exception(f'Input path "{input_path}" does not exist. Please create it with all mp3/mp4 files.')
    
    uploaded_files = []
    failed_files = []
    
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext in ['.mp3', '.mp4', '.wav', '.m4a', '.flac']:
                try:
                    s3_key = f"{prefix}{filename}"
                    s3_url = upload_to_s3(file_path, s3_key)
                    uploaded_files.append({'filename': filename, 'url': s3_url})
                    print(f"✓ Uploaded: {filename} -> {s3_key}")
                except Exception as e:
                    failed_files.append({'filename': filename, 'error': str(e)})
                    print(f"✗ Failed to upload {filename}: {str(e)}")
            else:
                print(f"⚠ Skipped {filename} (unsupported format)")
    
    return {
        'uploaded': uploaded_files,
        'failed': failed_files,
        'total_uploaded': len(uploaded_files),
        'total_failed': len(failed_files)
    }

def process_local_files(input_path: str = 'input', output_path: str = 'output'):
    """
    Process local media files and generate VTT files
    """
    if not os.path.exists(input_path):
        raise Exception(f'Input path "{input_path}" does not exist. Please create it with all mp3/mp4 files.')

    # Create timestamped folder directly
    timestamped_output = create_timestamped_folder()
    
    processed_files = []
    failed_files = []
    
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext in ['.mp3', '.mp4', '.wav', '.m4a', '.flac']:
                try:
                    print(f"Processing: {filename}")
                    vtt_path = transcribe_with_whisper(file_path)
                    
                    output_filename = f"{os.path.splitext(filename)[0]}.vtt"
                    final_path = os.path.join(timestamped_output, output_filename)
                    
                    os.rename(vtt_path, final_path)
                    processed_files.append({'input': filename, 'output': output_filename})
                    print(f"✓ Generated: {output_filename}")
                    
                except Exception as e:
                    failed_files.append({'filename': filename, 'error': str(e)})
                    print(f"✗ Failed to process {filename}: {str(e)}")
            else:
                print(f"⚠ Skipped {filename} (unsupported format)")
    
    return {
        'processed': processed_files,
        'failed': failed_files,
        'total_processed': len(processed_files),
        'total_failed': len(failed_files)
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='VTT Generator Seeding Script')
    parser.add_argument('--action', choices=['upload', 'process'], required=True,
                       help='Action to perform: upload files to S3 or process files locally')
    parser.add_argument('--input', default='input', help='Input directory path (default: input)')
    parser.add_argument('--output', default='output', help='Output directory path (default: output)')
    parser.add_argument('--prefix', default='media/', help='S3 prefix for uploads (default: media/)')
    
    args = parser.parse_args()
    
    if args.action == 'upload':
        print("Starting batch upload to S3...")
        result = batch_upload_files(args.input, args.prefix)
        print(f"\nUpload Summary:")
        print(f"✓ Successfully uploaded: {result['total_uploaded']} files")
        print(f"✗ Failed uploads: {result['total_failed']} files")
        
    elif args.action == 'process':
        print("Starting local file processing...")
        result = process_local_files(args.input, args.output)
        print(f"\nProcessing Summary:")
        print(f"✓ Successfully processed: {result['total_processed']} files")
        print(f"✗ Failed processing: {result['total_failed']} files")