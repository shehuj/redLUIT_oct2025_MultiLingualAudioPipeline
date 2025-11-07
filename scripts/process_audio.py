#!/usr/bin/env python3
"""
Audio Processing Script for GitHub Workflows:
- Uploads .mp3 files from audio_inputs/
- Calls Amazon Transcribe to generate transcript
- Calls Amazon Translate to translate into target language
- Calls Amazon Polly to synthesize translated speech
- Uploads all outputs to S3 under the structure:
    {env_prefix}/transcripts/{filename}.txt
    {env_prefix}/translations/{filename}_{lang}.txt
    {env_prefix}/audio_outputs/{filename}_{lang}.mp3
"""

import os
import json
import time
import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import urllib.request
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, bucket_name, env_prefix, target_language='es', source_language='en-US'):
        self.bucket_name = bucket_name
        self.env_prefix = env_prefix.rstrip('/')
        self.target_language = target_language
        self.source_language = source_language

        self.s3_client = boto3.client('s3')
        self.transcribe_client = boto3.client('transcribe')
        self.translate_client = boto3.client('translate')
        self.polly_client = boto3.client('polly')

        logger.info(f"Initialized AudioProcessor → bucket: {bucket_name}, env: {self.env_prefix}")
        logger.info(f"Source language: {source_language}, Target language: {target_language}")

    def upload_to_s3(self, file_path, s3_key):
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded {file_path} → {s3_uri}")
            return s3_uri
        except ClientError as e:
            logger.error(f"Upload to S3 failed: {e}")
            raise

    def transcribe_audio(self, s3_uri, job_name):
        try:
            logger.info(f"Start Transcribe job: {job_name}")
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='mp3',
                LanguageCode=self.source_language
            )

            # poll for status
            while True:
                resp = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = resp['TranscriptionJob']['TranscriptionJobStatus']
                logger.info(f"Transcription status: {status}")
                if status == 'COMPLETED':
                    transcript_uri = resp['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    logger.info(f"Transcript available at {transcript_uri}")
                    with urllib.request.urlopen(transcript_uri) as response:
                        data = json.loads(response.read())
                        transcript_text = data['results']['transcripts'][0]['transcript']
                    return transcript_text
                if status == 'FAILED':
                    reason = resp['TranscriptionJob'].get('FailureReason', 'Unknown')
                    logger.error(f"Transcription failed: {reason}")
                    raise Exception(f"Transcription failed: {reason}")
                time.sleep(10)
        except ClientError as e:
            logger.error(f"Transcribe API error: {e}")
            raise

    def translate_text(self, text):
        try:
            logger.info(f"Translating text to {self.target_language}")
            resp = self.translate_client.translate_text(
                Text=text,
                SourceLanguageCode=self.source_language.split('-')[0],
                TargetLanguageCode=self.target_language
            )
            return resp['TranslatedText']
        except ClientError as e:
            logger.error(f"Translate API error: {e}")
            raise

    def synthesize_speech(self, text, output_path):
        try:
            voice_map = {
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
                'tr': 'Filiz'
            }
            voice_id = voice_map.get(self.target_language, 'Joanna')
            logger.info(f"Synthesizing speech with voice: {voice_id}")

            resp = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
            audio_stream = resp['AudioStream'].read()
            with open(output_path, 'wb') as f:
                f.write(audio_stream)
            logger.info(f"Speech file written: {output_path}")
            return output_path
        except ClientError as e:
            logger.error(f"Polly API error: {e}")
            raise

    def process_file(self, mp3_path):
        file = Path(mp3_path)
        filename = file.stem
        timestamp = int(time.time())
        logger.info(f"Processing file: {file.name}")

        # Upload input
        input_key = f"{self.env_prefix}/audio_inputs/{file.name}"
        s3_uri = self.upload_to_s3(str(file), input_key)

        # Transcribe
        job_name = f"job-{filename}-{timestamp}"
        transcript_text = self.transcribe_audio(s3_uri, job_name)

        # Save transcript locally & upload
        transcript_local = f"/tmp/{filename}.txt"
        with open(transcript_local, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        transcript_key = f"{self.env_prefix}/transcripts/{filename}.txt"
        self.upload_to_s3(transcript_local, transcript_key)

        # Translate
        translated = self.translate_text(transcript_text)
        translation_local = f"/tmp/{filename}_{self.target_language}.txt"
        with open(translation_local, 'w', encoding='utf-8') as f:
            f.write(translated)
        translation_key = f"{self.env_prefix}/translations/{filename}_{self.target_language}.txt"
        self.upload_to_s3(translation_local, translation_key)

        # Synthesize
        audio_out_local = f"/tmp/{filename}_{self.target_language}.mp3"
        self.synthesize_speech(translated, audio_out_local)
        audio_out_key = f"{self.env_prefix}/audio_outputs/{filename}_{self.target_language}.mp3"
        self.upload_to_s3(audio_out_local, audio_out_key)

        logger.info(f"Finished processing: {file.name}")

def main():
    bucket = os.getenv('S3_BUCKET_NAME')
    env_prefix = os.getenv('ENV_PREFIX')
    target_lang = os.getenv('TARGET_LANGUAGE', 'es')
    source_lang = os.getenv('SOURCE_LANGUAGE', 'en-US')
    input_folder = os.getenv('INPUT_FOLDER', 'audio_inputs')

    if not bucket or not env_prefix:
        logger.error("Environment variables S3_BUCKET_NAME and ENV_PREFIX are required.")
        sys.exit(1)

    proc = AudioProcessor(bucket_name=bucket,
                          env_prefix=env_prefix,
                          target_language=target_lang,
                          source_language=source_lang)

    folder = Path(input_folder)
    if not folder.exists():
        logger.error(f"Input folder not found: {input_folder}")
        sys.exit(1)

    files = list(folder.glob('*.mp3'))
    if not files:
        logger.info(f"No .mp3 files found in {input_folder}.")
        sys.exit(0)

    logger.info(f"Found {len(files)} audio file(s).")
    success = 0
    failure = 0
    for f in files:
        try:
            proc.process_file(f)
            success += 1
        except Exception as err:
            logger.error(f"Error processing {f.name}: {err}")
            failure +=1

    logger.info("========== Summary ==========")
    logger.info(f"Total files: {len(files)}, Success: {success}, Failure: {failure}")
    if failure > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
