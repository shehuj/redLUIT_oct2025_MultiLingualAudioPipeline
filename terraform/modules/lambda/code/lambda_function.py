import os
import boto3
import uuid
import time

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')
translate = boto3.client('translate')
polly = boto3.client('polly')

def lambda_handler(event, context):
    bucket = os.environ['S3_BUCKET']
    target_lang = os.environ['TARGET_LANG']
    environment = os.environ['ENVIRONMENT']

    # assume record from S3 event
    for record in event['Records']:
        key = record['s3']['object']['key']
        if not key.startswith("audio_inputs/") or not key.endswith(".mp3"):
            continue

        filename = key.split('/')[-1].replace('.mp3','')
        job_name = f"{filename}-{uuid.uuid4()}"

        # start transcription
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f"s3://{bucket}/{key}"},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=bucket,
            OutputKey=f"{environment}/transcripts/{filename}.json"
        )
        # wait for completion — simple polling
        while True:
            result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = result['TranscriptionJob']['TranscriptionJobStatus']
            if status in ['COMPLETED','FAILED']:
                break
            time.sleep(5)

        if status == 'FAILED':
            raise Exception("Transcription job failed")

        transcript_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
        # download transcript
        transcript_obj = s3.get_object(Bucket=bucket,
                                       Key=f"{environment}/transcripts/{filename}.json")
        transcript_text = transcript_obj['Body'].read().decode('utf-8')

        # translate
        response = translate.translate_text(
            Text=transcript_text,
            SourceLanguageCode='en',
            TargetLanguageCode=target_lang
        )
        translated_text = response['TranslatedText']

        # store translation
        s3.put_object(
            Bucket=bucket,
            Key=f"{environment}/translations/{filename}_{target_lang}.txt",
            Body=translated_text
        )

        # synthesize speech
        polly_resp = polly.synthesize_speech(
            Text=translated_text,
            OutputFormat='mp3',
            VoiceId='Joanna'
        )
        audio_stream = polly_resp['AudioStream'].read()

        # upload audio
        s3.put_object(
            Bucket=bucket,
            Key=f"{environment}/audio_outputs/{filename}_{target_lang}.mp3",
            Body=audio_stream
        )

    return {
        'statusCode': 200,
        'body': f"Processed file {filename}"
    }