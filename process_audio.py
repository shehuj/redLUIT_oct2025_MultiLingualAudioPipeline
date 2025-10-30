import boto3, json, time, os, sys
from urllib.parse import urlparse

aws_region = os.getenv("AWS_REGION")
s3_bucket  = os.getenv("S3_BUCKET")
env_prefix = os.getenv("ENV_PREFIX")
target_lang = os.getenv("TARGET_LANG", "es")

s3 = boto3.client('s3', region_name=aws_region)
transcribe = boto3.client('transcribe', region_name=aws_region)
translate = boto3.client('translate', region_name=aws_region)
polly = boto3.client('polly', region_name=aws_region)

def process_audio(file_path):
    filename = os.path.basename(file_path).split('.')[0]
    s3_key = f"audio_inputs/{os.path.basename(file_path)}"

    print(f"Uploading {file_path} → s3://{s3_bucket}/{s3_key}")
    s3.upload_file(file_path, s3_bucket, s3_key)

    job_name = f"{filename}-{int(time.time())}"
    media_uri = f"s3://{s3_bucket}/{s3_key}"
    print("Starting Transcription job:", job_name)

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=s3_bucket,
        OutputKey=f"{env_prefix}/transcripts/{filename}.json"
    )

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        state = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if state in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)

    transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    obj = urlparse(transcript_uri)
    transcript_key = obj.path.split('/', 3)[-1]
    transcript_file = f"/tmp/{filename}.json"
    s3.download_file(s3_bucket, transcript_key, transcript_file)

    text_data = json.load(open(transcript_file))
    transcript_text = text_data["results"]["transcripts"][0]["transcript"]

    s3.put_object(
        Bucket=s3_bucket,
        Key=f"{env_prefix}/transcripts/{filename}.txt",
        Body=transcript_text
    )

    translated = translate.translate_text(
        Text=transcript_text,
        SourceLanguageCode="en",
        TargetLanguageCode=target_lang
    )["TranslatedText"]

    s3.put_object(
        Bucket=s3_bucket,
        Key=f"{env_prefix}/translations/{filename}_{target_lang}.txt",
        Body=translated
    )

    speech = polly.synthesize_speech(
        Text=translated, OutputFormat="mp3", VoiceId="Lupe"
    )
    audio_bytes = speech["AudioStream"].read()

    s3.put_object(
        Bucket=s3_bucket,
        Key=f"{env_prefix}/audio_outputs/{filename}_{target_lang}.mp3",
        Body=audio_bytes
    )

    print(f"Completed {filename} ({env_prefix})")

if __name__ == "__main__":
    for f in os.listdir("audio_inputs"):
        if f.endswith(".mp3"):
            process_audio(os.path.join("audio_inputs", f))
