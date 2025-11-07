import pytest
import handler
import boto3
from botocore.stub import Stubber

@pytest.fixture
def fake_event():
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "mybucket"},
                    "object": {"key": "audio_inputs/testfile.mp3"}
                }
            }
        ]
    }

def test_get_metadata_env_no_metadata(monkeypatch):
    # stub s3.head_object to raise
    s3 = boto3.client('s3')
    stub = Stubber(s3)
    stub.add_client_error('head_object', expected_params={'Bucket':'mybucket','Key':'audio_inputs/testfile.mp3'})
    stub.activate()
    monkeypatch.setattr(handler, 's3', s3)
    env = handler.get_metadata_env("mybucket", "audio_inputs/testfile.mp3")
    assert env == handler.ENV_PREFIX

def test_lambda_handler_skip_non_mp3(monkeypatch):
    evt = {"Records":[{"s3":{"bucket":{"name":"b"},"object":{"key":"audio_inputs/file.txt"}}}]}
    result = handler.lambda_handler(evt, None)
    assert result["body"] == "Skipped non-mp3"

def test_lambda_handler_start_transcription(monkeypatch):
    evt = {"Records":[{"s3":{"bucket":{"name":"b"},"object":{"key":"audio_inputs/file.mp3"}}}]}
    
    # Stub s3.head_object to return metadata
    s3 = boto3.client('s3')
    s3_stub = Stubber(s3)
    s3_stub.add_response('head_object', {'Metadata': {'env': 'testenv'}}, {'Bucket':'b','Key':'audio_inputs/file.mp3'})
    s3_stub.activate()
    monkeypatch.setattr(handler, 's3', s3)
    
    # Stub transcribe.start_transcription_job
    transcribe = boto3.client('transcribe')
    transcribe_stub = Stubber(transcribe)