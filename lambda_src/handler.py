import os
import boto3
import time
import uuid
import json
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')
translate = boto3.client('translate')
polly = boto3.client('polly')

OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
TARGET_LANGUAGES = os.environ.get('TARGET_LANGUAGES', '').split(',')
VOICE_MAPPING = json.loads(os.environ.get('VOICE_MAPPING_JSON', '{}'))
ENV_PREFIX = os.environ.get('ENV_PREFIX', 'prod')

def get_metadata_env(bucket: str, key: str) -> str:
    """Reads S3 object metadata to find env tag, else returns ENV_PREFIX."""
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        metadata = head.get('Metadata', {})
        env = metadata.get('env')
        if env:
            logger.info(f"Found metadata env={env} on object {key}")
            return env
    except Exception as e:
        logger.warning(f"Could not get metadata for {bucket}/{key}: {e}")
    # fallback: parse filename
    if key.startswith("audio_inputs/beta-"):
        return "beta"
    return ENV_PREFIX

def start_transcription(bucket: str, key: str, job_name: str, env: str):
    media_uri = f"s3://{bucket}/{key}"
    logger.info(f"Starting transcription job for {media_uri}")
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=OUTPUT_BUCKET,
        OutputKey=f"{env}/transcripts/{job_name}.json"
    )
    return response

def wait_for_transcription(job_name: str):
    logger.info(f"Waiting for transcription job {job_name} to complete")
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job = status['TranscriptionJob']
        if job['TranscriptionJobStatus'] in ('COMPLETED', 'FAILED'):
            return job
        logger.info(f"Job {job_name} status {job['TranscriptionJobStatus']} … sleeping")
        time.sleep(10)

def download_transcript(uri: str) -> str:
    logger.info(f"Downloading transcript from {uri}")
    import urllib.request
    with urllib.request.urlopen(uri) as f:
        data = json.load(f)
    return data['results']['transcripts'][0]['transcript']

def upload_text(bucket: str, key: str, text: str):
    logger.info(f"Uploading text to s3://{bucket}/{key}")
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode('utf-8'))

def synthesize_speech(text: str, language: str, voice_id: str) -> bytes:
    logger.info(f"Calling Polly for language {language}, voice {voice_id}")
    resp = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId=voice_id, LanguageCode=language)
    return resp['AudioStream'].read()

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    record = event['Records'][0]['s3']
    bucket = record['bucket']['name']
    key = unquote_plus(record['object']['key'])
    if not key.lower().endswith('.mp3'):
        logger.info(f"Skipping non-mp3 file: {key}")
        return {"statusCode": 200, "body": "Skipped non-mp3"}

    env = get_metadata_env(bucket, key)
    base_filename = os.path.splitext(os.path.basename(key))[0]
    job_name = f"{env}-{base_filename}-{uuid.uuid4().hex[:8]}"

    # Start transcription
    start_transcription(bucket, key, job_name, env)

    # Wait for completion
    job = wait_for_transcription(job_name)
    if job['TranscriptionJobStatus'] == 'FAILED':
        msg = job.get('FailureReason', 'Unknown reason')
        logger.error(f"Transcription job failed: {msg}")
        raise RuntimeError(f"Transcription failed: {msg}")

    transcript_uri = job['Transcript']['TranscriptFileUri']
    transcript_text = download_transcript(transcript_uri)

    # Upload clean transcript text
    transcript_key = f"{env}/transcripts/{base_filename}.txt"
    upload_text(OUTPUT_BUCKET, transcript_key, transcript_text)

    # Translate + Polly per language
    for lang in TARGET_LANGUAGES:
        translated_resp = translate.translate_text(Text=transcript_text, SourceLanguageCode='en', TargetLanguageCode=lang)
        translated = translated_resp['TranslatedText']
        translation_key = f"{env}/translations/{base_filename}_{lang}.txt"
        upload_text(OUTPUT_BUCKET, translation_key, translated)

        voice_id = VOICE_MAPPING.get(lang)
        if not voice_id:
            logger.warning(f"No voice mapping configured for language {lang}, skipping Polly")
            continue

        audio_bytes = synthesize_speech(translated, lang, voice_id)
        audio_key = f"{env}/audio_outputs/{base_filename}_{lang}.mp3"
        logger.info(f"Uploading synthesized audio to s3://{OUTPUT_BUCKET}/{audio_key}")
        s3.put_object(Bucket=OUTPUT_BUCKET, Key=audio_key, Body=audio_bytes)

    return {
        "statusCode": 200,
        "body": f"Processed file {key} in env {env}"
    }