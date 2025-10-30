#!/usr/bin/env python3
"""
Audio Processing Script for GitHub Workflows
Processes MP3 files through AWS Transcribe, Translate, and Polly
"""

import os
import json
import time
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio processing pipeline with AWS services"""
    
    def __init__(self, bucket_name, target_language='es', source_language='en-US'):
        """
        Initialize the audio processor
        
        Args:
            bucket_name: S3 bucket name for uploads
            target_language: Target language code for translation (default: 'es' for Spanish)
            source_language: Source language code for transcription (default: 'en-US')
        """
        self.bucket_name = bucket_name
        self.target_language = target_language
        self.source_language = source_language
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3')
        self.transcribe_client = boto3.client('transcribe')
        self.translate_client = boto3.client('translate')
        self.polly_client = boto3.client('polly')
        
        logger.info(f"Initialized AudioProcessor with bucket: {bucket_name}")
        logger.info(f"Source language: {source_language}, Target language: {target_language}")
    
    def upload_to_s3(self, file_path, s3_key):
        """
        Upload a file to S3
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (path in bucket)
        
        Returns:
            S3 URI of uploaded file
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded {file_path} to {s3_uri}")
            return s3_uri
        except ClientError as e:
            logger.error(f"Failed to upload {file_path} to S3: {e}")
            raise
    
    def transcribe_audio(self, s3_uri, job_name):
        """
        Transcribe audio using Amazon Transcribe
        
        Args:
            s3_uri: S3 URI of the audio file
            job_name: Unique name for the transcription job
        
        Returns:
            Transcript text
        """
        try:
            # Start transcription job
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
                job = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = job['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    logger.info(f"Transcription job {job_name} completed")
                    transcript_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    # Download and extract transcript
                    import urllib.request
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
        finally:
            # Clean up transcription job
            try:
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                logger.info(f"Cleaned up transcription job: {job_name}")
            except:
                pass
    
    def translate_text(self, text, source_lang='en'):
        """
        Translate text using Amazon Translate
        
        Args:
            text: Text to translate
            source_lang: Source language code (default: 'en')
        
        Returns:
            Translated text
        """
        try:
            logger.info(f"Translating text from {source_lang} to {self.target_language}")
            
            # Amazon Translate has a 10,000 character limit per request
            # Split text if necessary
            max_length = 10000
            if len(text) <= max_length:
                result = self.translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode=source_lang,
                    TargetLanguageCode=self.target_language
                )
                return result['TranslatedText']
            else:
                # Split by sentences and translate in chunks
                translated_chunks = []
                current_chunk = ""
                
                sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_length:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            result = self.translate_client.translate_text(
                                Text=current_chunk,
                                SourceLanguageCode=source_lang,
                                TargetLanguageCode=self.target_language
                            )
                            translated_chunks.append(result['TranslatedText'])
                        current_chunk = sentence
                
                if current_chunk:
                    result = self.translate_client.translate_text(
                        Text=current_chunk,
                        SourceLanguageCode=source_lang,
                        TargetLanguageCode=self.target_language
                    )
                    translated_chunks.append(result['TranslatedText'])
                
                return ' '.join(translated_chunks)
        
        except ClientError as e:
            logger.error(f"Translation error: {e}")
            raise
    
    def synthesize_speech(self, text, output_path):
        """
        Synthesize speech using Amazon Polly
        
        Args:
            text: Text to synthesize
            output_path: Local path to save the audio file
        
        Returns:
            Path to the generated audio file
        """
        try:
            # Map language codes to Polly voice IDs
            voice_mapping = {
                'es': 'Lucia',      # Spanish
                'fr': 'Celine',     # French
                'de': 'Marlene',    # German
                'it': 'Carla',      # Italian
                'pt': 'Ines',       # Portuguese
                'ja': 'Mizuki',     # Japanese
                'ko': 'Seoyeon',    # Korean
                'zh': 'Zhiyu',      # Chinese
                'ar': 'Zeina',      # Arabic
                'hi': 'Aditi',      # Hindi
                'ru': 'Tatyana',    # Russian
                'nl': 'Lotte',      # Dutch
                'pl': 'Ewa',        # Polish
                'tr': 'Filiz',      # Turkish
            }
            
            voice_id = voice_mapping.get(self.target_language, 'Joanna')
            
            logger.info(f"Synthesizing speech with voice: {voice_id}")
            
            # Polly has a 3000 character limit per request
            max_length = 3000
            audio_chunks = []
            
            # Split text into chunks if necessary
            text_chunks = []
            if len(text) <= max_length:
                text_chunks = [text]
            else:
                sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_length:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            text_chunks.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    text_chunks.append(current_chunk)
            
            # Synthesize each chunk
            for chunk in text_chunks:
                response = self.polly_client.synthesize_speech(
                    Text=chunk,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine='neural' if voice_id in ['Lucia', 'Celine', 'Marlene', 'Carla'] else 'standard'
                )
                
                audio_chunks.append(response['AudioStream'].read())
            
            # Combine audio chunks and save
            with open(output_path, 'wb') as file:
                for chunk in audio_chunks:
                    file.write(chunk)
            
            logger.info(f"Synthesized speech saved to {output_path}")
            return output_path
        
        except ClientError as e:
            logger.error(f"Speech synthesis error: {e}")
            raise
    
    def process_file(self, input_file):
        """
        Process a single audio file through the entire pipeline
        
        Args:
            input_file: Path to the input MP3 file
        """
        file_path = Path(input_file)
        filename = file_path.stem
        timestamp = int(time.time())
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {file_path.name}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Step 1: Upload original audio to S3
            logger.info("Step 1: Uploading audio to S3...")
            audio_s3_key = f"audio_inputs/{file_path.name}"
            s3_uri = self.upload_to_s3(str(file_path), audio_s3_key)
            
            # Step 2: Transcribe audio
            logger.info("\nStep 2: Transcribing audio...")
            job_name = f"transcribe-{filename}-{timestamp}"
            transcript = self.transcribe_audio(s3_uri, job_name)
            
            # Save transcript to S3
            transcript_key = f"transcripts/{filename}.txt"
            transcript_path = f"/tmp/{filename}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            self.upload_to_s3(transcript_path, transcript_key)
            logger.info(f"Transcript saved to s3://{self.bucket_name}/{transcript_key}")
            
            # Step 3: Translate text
            logger.info("\nStep 3: Translating text...")
            source_lang = self.source_language.split('-')[0]  # Extract 'en' from 'en-US'
            translated_text = self.translate_text(transcript, source_lang)
            
            # Save translation to S3
            translation_key = f"translations/{filename}_{self.target_language}.txt"
            translation_path = f"/tmp/{filename}_{self.target_language}_translation.txt"
            with open(translation_path, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            self.upload_to_s3(translation_path, translation_key)
            logger.info(f"Translation saved to s3://{self.bucket_name}/{translation_key}")
            
            # Step 4: Synthesize speech
            logger.info("\nStep 4: Synthesizing speech...")
            output_audio_path = f"/tmp/{filename}_{self.target_language}.mp3"
            self.synthesize_speech(translated_text, output_audio_path)
            
            # Upload synthesized audio to S3
            output_audio_key = f"audio_outputs/{filename}_{self.target_language}.mp3"
            self.upload_to_s3(output_audio_path, output_audio_key)
            logger.info(f"Synthesized audio saved to s3://{self.bucket_name}/{output_audio_key}")
            
            logger.info(f"\nSuccessfully processed {file_path.name}\n")
            
        except Exception as e:
            logger.error(f"\nError processing {file_path.name}: {e}\n")
            raise


def main():
    """Main execution function"""
    
    # Get configuration from environment variables
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    target_language = os.environ.get('TARGET_LANGUAGE', 'es')
    source_language = os.environ.get('SOURCE_LANGUAGE', 'en-US')
    input_folder = os.environ.get('INPUT_FOLDER', 'audio_inputs')
    
    if not bucket_name:
        logger.error("S3_BUCKET_NAME environment variable is required")
        exit(1)
    
    # Initialize processor
    processor = AudioProcessor(
        bucket_name=bucket_name,
        target_language=target_language,
        source_language=source_language
    )
    
    # Find all MP3 files in the input folder
    input_path = Path(input_folder)
    if not input_path.exists():
        logger.error(f"Input folder does not exist: {input_folder}")
        exit(1)
    
    mp3_files = list(input_path.glob('*.mp3'))
    
    if not mp3_files:
        logger.warning(f"No MP3 files found in {input_folder}")
        exit(0)
    
    logger.info(f"Found {len(mp3_files)} MP3 file(s) to process")
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for mp3_file in mp3_files:
        try:
            processor.process_file(mp3_file)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {mp3_file}: {e}")
            error_count += 1
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing Complete")
    logger.info(f"{'='*60}")
    logger.info(f"Total files: {len(mp3_files)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {error_count}")
    
    if error_count > 0:
        exit(1)


if __name__ == "__main__":
    main()