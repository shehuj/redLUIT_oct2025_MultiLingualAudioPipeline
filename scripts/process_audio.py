#!/usr/bin/env python3
"""
Audio Processing Pipeline
Processes MP3 files using AWS Transcribe, Translate, and Polly
"""

import os
import sys
import json
import time
import boto3
from pathlib import Path
from urllib.parse import urlparse

# Configuration from environment variables
S3_BUCKET = os.environ.get('S3_BUCKET')
TARGET_LANGUAGE = os.environ.get('TARGET_LANGUAGE', 'es')  # Default to Spanish
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'beta')  # beta or prod

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)
translate_client = boto3.client('translate', region_name=AWS_REGION)
polly_client = boto3.client('polly', region_name=AWS_REGION)


def upload_to_s3(file_path, s3_key):
    """Upload a file to S3"""
    try:
        print(f"Uploading {file_path} to s3://{S3_BUCKET}/{s3_key}")
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        print(f"✓ Successfully uploaded to S3")
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        print(f"✗ Error uploading to S3: {e}")
        raise


def transcribe_audio(s3_uri, job_name):
    """Transcribe audio using Amazon Transcribe"""
    try:
        print(f"Starting transcription job: {job_name}")
        
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='mp3',
            LanguageCode='en-US'  # Assuming source is English
        )
        
        # Wait for job to complete
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status in ['COMPLETED', 'FAILED']:
                break
            
            print(f"Transcription status: {job_status}. Waiting...")
            time.sleep(5)
        
        if job_status == 'COMPLETED':
            transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            print(f"✓ Transcription completed: {transcript_uri}")
            
            # Download and parse the transcript
            import urllib.request
            with urllib.request.urlopen(transcript_uri) as response:
                transcript_data = json.loads(response.read())
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
            
            return transcript_text
        else:
            raise Exception(f"Transcription failed: {status['TranscriptionJob'].get('FailureReason', 'Unknown')}")
            
    except Exception as e:
        print(f"✗ Error during transcription: {e}")
        raise
    finally:
        # Clean up transcription job
        try:
            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        except:
            pass


def translate_text(text, target_language):
    """Translate text using Amazon Translate"""
    try:
        print(f"Translating text to {target_language}")
        
        # Translate in chunks if text is too long (max 5000 bytes)
        max_chunk_size = 4500
        translated_chunks = []
        
        # Split text into sentences for better translation
        sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk.encode('utf-8')) + len(sentence.encode('utf-8')) < max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    response = translate_client.translate_text(
                        Text=current_chunk.strip(),
                        SourceLanguageCode='en',
                        TargetLanguageCode=target_language
                    )
                    translated_chunks.append(response['TranslatedText'])
                current_chunk = sentence + " "
        
        # Translate remaining chunk
        if current_chunk:
            response = translate_client.translate_text(
                Text=current_chunk.strip(),
                SourceLanguageCode='en',
                TargetLanguageCode=target_language
            )
            translated_chunks.append(response['TranslatedText'])
        
        translated_text = " ".join(translated_chunks)
        print(f"✓ Translation completed")
        return translated_text
        
    except Exception as e:
        print(f"✗ Error during translation: {e}")
        raise


def synthesize_speech(text, target_language):
    """Synthesize speech using Amazon Polly"""
    try:
        print(f"Synthesizing speech in {target_language}")
        
        # Map language codes to Polly voice IDs
        voice_map = {
            'es': 'Lucia',      # Spanish
            'fr': 'Celine',     # French
            'de': 'Marlene',    # German
            'it': 'Carla',      # Italian
            'pt': 'Vitoria',    # Portuguese
            'ja': 'Mizuki',     # Japanese
            'ko': 'Seoyeon',    # Korean
            'zh': 'Zhiyu',      # Chinese
            'ar': 'Zeina',      # Arabic
            'hi': 'Aditi',      # Hindi
        }
        
        voice_id = voice_map.get(target_language, 'Joanna')  # Default to English
        
        # Polly has a 3000 character limit, so we need to chunk
        max_chunk_size = 2900
        audio_chunks = []
        
        # Split text into chunks
        words = text.split()
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 < max_chunk_size:
                current_chunk += word + " "
            else:
                if current_chunk:
                    response = polly_client.synthesize_speech(
                        Text=current_chunk.strip(),
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        Engine='neural' if voice_id in ['Joanna', 'Matthew', 'Lucia'] else 'standard'
                    )
                    audio_chunks.append(response['AudioStream'].read())
                current_chunk = word + " "
        
        # Process remaining chunk
        if current_chunk:
            response = polly_client.synthesize_speech(
                Text=current_chunk.strip(),
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural' if voice_id in ['Joanna', 'Matthew', 'Lucia'] else 'standard'
            )
            audio_chunks.append(response['AudioStream'].read())
        
        # Combine audio chunks
        audio_data = b''.join(audio_chunks)
        print(f"✓ Speech synthesis completed")
        return audio_data
        
    except Exception as e:
        print(f"✗ Error during speech synthesis: {e}")
        raise


def process_audio_file(audio_file_path):
    """Process a single audio file through the pipeline"""
    file_path = Path(audio_file_path)
    filename_base = file_path.stem
    
    print(f"\n{'='*60}")
    print(f"Processing: {file_path.name}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Target Language: {TARGET_LANGUAGE}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Upload original MP3 to S3
        s3_input_key = f"{ENVIRONMENT}/audio_inputs/{file_path.name}"
        s3_uri = upload_to_s3(str(file_path), s3_input_key)
        
        # Step 2: Transcribe audio
        job_name = f"transcribe-{filename_base}-{int(time.time())}"
        transcript_text = transcribe_audio(s3_uri, job_name)
        
        # Save transcript locally
        transcript_file = f"/tmp/{filename_base}.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Upload transcript to S3
        transcript_s3_key = f"{ENVIRONMENT}/transcripts/{filename_base}.txt"
        upload_to_s3(transcript_file, transcript_s3_key)
        
        # Step 3: Translate text
        translated_text = translate_text(transcript_text, TARGET_LANGUAGE)
        
        # Save translation locally
        translation_file = f"/tmp/{filename_base}_{TARGET_LANGUAGE}.txt"
        with open(translation_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        # Upload translation to S3
        translation_s3_key = f"{ENVIRONMENT}/translations/{filename_base}_{TARGET_LANGUAGE}.txt"
        upload_to_s3(translation_file, translation_s3_key)
        
        # Step 4: Synthesize speech
        audio_data = synthesize_speech(translated_text, TARGET_LANGUAGE)
        
        # Save audio locally
        output_audio_file = f"/tmp/{filename_base}_{TARGET_LANGUAGE}.mp3"
        with open(output_audio_file, 'wb') as f:
            f.write(audio_data)
        
        # Upload audio to S3
        audio_s3_key = f"{ENVIRONMENT}/audio_outputs/{filename_base}_{TARGET_LANGUAGE}.mp3"
        upload_to_s3(output_audio_file, audio_s3_key)
        
        print(f"\n{'='*60}")
        print(f"✓ Successfully processed {file_path.name}")
        print(f"  Transcript: s3://{S3_BUCKET}/{transcript_s3_key}")
        print(f"  Translation: s3://{S3_BUCKET}/{translation_s3_key}")
        print(f"  Audio Output: s3://{S3_BUCKET}/{audio_s3_key}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to process {file_path.name}: {e}\n")
        return False


def main():
    """Main function to process all MP3 files in audio_inputs/"""
    
    # Validate required environment variables
    if not S3_BUCKET:
        print("Error: S3_BUCKET environment variable is required")
        sys.exit(1)
    
    print(f"Audio Processing Pipeline")
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Target Language: {TARGET_LANGUAGE}")
    print(f"AWS Region: {AWS_REGION}\n")
    
    # Find all MP3 files in audio_inputs/
    audio_inputs_dir = Path('audio_inputs')
    
    if not audio_inputs_dir.exists():
        print(f"Error: {audio_inputs_dir} directory not found")
        sys.exit(1)
    
    mp3_files = list(audio_inputs_dir.glob('*.mp3'))
    
    if not mp3_files:
        print(f"No MP3 files found in {audio_inputs_dir}/")
        print("Please add .mp3 files to the audio_inputs/ folder and try again.")
        sys.exit(0)
    
    print(f"Found {len(mp3_files)} MP3 file(s) to process\n")
    
    # Process each file
    results = []
    for mp3_file in mp3_files:
        success = process_audio_file(mp3_file)
        results.append((mp3_file.name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful
    
    for filename, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {filename}")
    
    print(f"\nTotal: {len(results)} | Successful: {successful} | Failed: {failed}")
    print(f"{'='*60}\n")
    
    # Exit with error code if any failed
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()