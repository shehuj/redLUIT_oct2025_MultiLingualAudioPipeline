#!/usr/bin/env python3
"""
Audio Processing Script for GitHub Workflows
Processes MP3 files through AWS Transcribe, Translate, and Polly,
and uploads all outputs to structured S3 prefixes.
"""

import os
import json
import time
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
import logging
import sys
import urllib.request

# Environment variables expected:
#   S3_BUCKET_NAME   : the S3 bucket where results will be stored
#   ENV_PREFIX       : e.g., 'beta' or 'prod'
#   TARGET_LANGUAGE  : language code for translation (e.g., 'es')
#   SOURCE_LANGUAGE  : language code for transcription (e.g., 'en-US')
#   INPUT_FOLDER     : folder path where .mp3 files reside (default: 'audio_inputs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio processing pipeline with AWS services."""
    
    def __init__(self, bucket_name, env_prefix, target_language='es', source_language='en-US'):
        self.bucket_name = bucket_name
        self.env_prefix = env_prefix.rstrip('/')  # ensure no trailing slash
        self.target_language = target_language
        self.source_language = source_language
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3')
        self.transcribe_client = boto3.client('transcribe')
        self.translate_client = boto3.client('translate')
        self.polly_client = boto3.client('polly')
        
        logger.info(f"Initialized AudioProcessor with bucket: {bucket_name}")
        logger.info(f"Environment prefix: {self.env_prefix}")
        logger.info(f"Source language: {source_language}, Target language: {target_language}")
    
    def upload_to_s3(self, file_path, s3_key):
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded {file_path} to {s3_uri}")
            return s3_uri
        except ClientError as e:
            logger.error(f"Failed to upload {file_path} to S3: {e}")
            raise
    
    def transcribe_audio(self, s3_uri, job_name):
        try:
            logger.info(f"Starting transcription job: {job_name}")
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='mp3',
                LanguageCode=self.source_language
            )
            
            # Wait for job to complete
            max_tries = 60
            while max_tries > 0:
                max_tries -= 1
                job = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = job['TranscriptionJob']['TranscriptionJobStatus']
                if status == 'COMPLETED':
                    logger.info(f"Transcription job {job_name} completed")
                    transcript_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    with urllib.request.urlopen(transcript_uri) as response:
                        transcript_data = json.loads(response.read())
                        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                    return transcript_text
                elif status == 'FAILED':
                    failure_reason = job['TranscriptionJob'].get('FailureReason', 'Unknown')
                    logger.error(f"Transcription job failed: {failure_reason}")
                    raise Exception(f"Transcription failed: {failure_reason}")
                logger.info(f"Transcription job status: {status}, waiting...")
                time.sleep(10)
            
            raise Exception("Transcription job timed out")
        except ClientError as e:
            logger.error(f"Transcription error: {e}")
            raise
        # Note: Avoid cleanup here unless necessary.
    
    def translate_text(self, text, source_lang=None):
        try:
            source_lang_code = source_lang or self.source_language.split('-')[0]
            logger.info(f"Translating text from {source_lang_code} to {self.target_language}")
            max_length = 10000
            if len(text) <= max_length:
                result = self.translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode=source_lang_code,
                    TargetLanguageCode=self.target_language
                )
                return result['TranslatedText']
            else:
                translated_chunks = []
                sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_length:
                        current_chunk += sentence
                    else:
                        result = self.translate_client.translate_text(
                            Text=current_chunk,
                            SourceLanguageCode=source_lang_code,
                            TargetLanguageCode=self.target_language
                        )
                        translated_chunks.append(result['TranslatedText'])
                        current_chunk = sentence
                if current_chunk:
                    result = self.translate_client.translate_text(
                        Text=current_chunk,
                        SourceLanguageCode=source_lang_code,
                        TargetLanguageCode=self.target_language
                    )
                    translated_chunks.append(result['TranslatedText'])
                return ' '.join(translated_chunks)
        except ClientError as e:
            logger.error(f"Translation error: {e}")
            raise
    
    def synthesize_speech(self, text, output_path):
        try:
            voice_mapping = {
                'es': 'Lucia',
                'fr': 'Celine',
                'de': 'Marlene',
                'it': 'Carla',
                'pt': 'Ines',
                'ja': 'Mizuki',
                'ko': 'Seoyeon',
                'zh': 'Zhiyu',
                'ar': 'Zeina',
                'hi': 'Aditi',
                'ru': 'Tatyana',
                'nl': 'Lotte',
                'pl': 'Ewa',
                'tr': 'Filiz',
            }
            voice_id = voice_mapping.get(self.target_language, 'Joanna')
            logger.info(f"Synthesizing speech with voice: {voice_id}")
            
            max_length = 3000
            text_chunks = [text] if len(text) <= max_length else []
            if not text_chunks:
                sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
                current = ""
                for sentence in sentences:
                    if len(current) + len(sentence) < max_length:
                        current += sentence
                    else:
                        text_chunks.append(current)
                        current = sentence
                if current:
                    text_chunks.append(current)
            
            audio_chunks = []
            for chunk in text_chunks:
                response = self.polly_client.synthesize_speech(
                    Text=chunk,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine='neural'
                )
                audio_chunks.append(response['AudioStream'].read())
            
            with open(output_path, 'wb') as f:
                for chunk in audio_chunks:
                    f.write(chunk)
            
            logger.info(f"Synthesized speech saved to {output_path}")
            return output_path
        except ClientError as e:
            logger.error(f"Speech synthesis error: {e}")
            raise
    
    def process_file(self, input_file):
        file_path = Path(input_file)
        filename = file_path.stem
        timestamp = int(time.time())
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {file_path.name}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Step 1: Upload original audio
            audio_s3_key = f"{self.env_prefix}/audio_inputs/{file_path.name}"
            s3_uri = self.upload_to_s3(str(file_path), audio_s3_key)
            
            # Step 2: Transcribe
            job_name = f"transcribe-{filename}-{timestamp}"
            transcript = self.transcribe_audio(s3_uri, job_name)
            
            transcript_key = f"{self.env_prefix}/transcripts/{filename}.txt"
            transcript_path = f"/tmp/{filename}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as fw:
                fw.write(transcript)
            self.upload_to_s3(transcript_path, transcript_key)
            logger.info(f"Transcript saved to s3://{self.bucket_name}/{transcript_key}")
            
            # Step 3: Translate
            translated_text = self.translate_text(transcript)
            translation_key = f"{self.env_prefix}/translations/{filename}_{self.target_language}.txt"
            translation_path = f"/tmp/{filename}_{self.target_language}_translation.txt"
            with open(translation_path, 'w', encoding='utf-8') as fw:
                fw.write(translated_text)
            self.upload_to_s3(translation_path, translation_key)
            logger.info(f"Translation saved to s3://{self.bucket_name}/{translation_key}")
            
            # Step 4: Synthesize speech
            output_audio_path = f"/tmp/{filename}_{self.target_language}.mp3"
            self.synthesize_speech(translated_text, output_audio_path)
            audio_output_key = f"{self.env_prefix}/audio_outputs/{filename}_{self.target_language}.mp3"
            self.upload_to_s3(output_audio_path, audio_output_key)
            logger.info(f"Synthesized audio saved to s3://{self.bucket_name}/{audio_output_key}")
            
            logger.info(f"\nSuccessfully processed {file_path.name}\n")
        except Exception as e:
            logger.error(f"\nError processing {file_path.name}: {e}\n")
            raise

def main():
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    env_prefix = os.environ.get('ENV_PREFIX')
    target_language = os.environ.get('TARGET_LANGUAGE', 'es')
    source_language = os.environ.get('SOURCE_LANGUAGE', 'en-US')
    input_folder = os.environ.get('INPUT_FOLDER', 'audio_inputs')
    
    if not bucket_name or not env_prefix:
        logger.error("Both S3_BUCKET_NAME and ENV_PREFIX env variables are required")
        sys.exit(1)
    
    processor = AudioProcessor(
        bucket_name=bucket_name,
        env_prefix=env_prefix,
        target_language=target_language,
        source_language=source_language
    )
    
    input_path = Path(input_folder)
    if not input_path.exists():
        logger.error(f"Input folder does not exist: {input_folder}")
        sys.exit(1)
    
    mp3_files = list(input_path.glob('*.mp3'))
    if not mp3_files:
        logger.warning(f"No MP3 files found in {input_folder}")
        sys.exit(0)
    
    logger.info(f"Found {len(mp3_files)} MP3 file(s) to process")
    success = error = 0
    
    for mp3 in mp3_files:
        try:
            processor.process_file(mp3)
            success += 1
        except Exception as e:
            logger.error(f"Failed to process {mp3.name}: {e}")
            error += 1
    
    logger.info(f"\n{'='*60}")
    logger.info("Processing Complete")
    logger.info(f"{'='*60}")
    logger.info(f"Total files: {len(mp3_files)}, Successful: {success}, Failed: {error}")
    
    if error > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
