#!/usr/bin/env python3
"""
Setup Validation Script
Validates that all required configuration is in place
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def check_env_var(var_name, required=True):
    """Check if an environment variable is set"""
    value = os.environ.get(var_name)
    if not value and required:
        print(f"❌ Missing required environment variable: {var_name}")
        return False
    elif value:
        print(f"✅ {var_name}: {value}")
        return True
    else:
        print(f"⚠️  Optional variable not set: {var_name}")
        return True

def check_aws_credentials():
    """Verify AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials valid")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not configured")
        print("   Run: aws configure")
        return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def check_s3_bucket(bucket_name):
    """Check if S3 bucket exists and is accessible"""
    try:
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket accessible: {bucket_name}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ S3 bucket does not exist: {bucket_name}")
            print(f"   Create it with: aws s3 mb s3://{bucket_name}")
        elif error_code == '403':
            print(f"❌ No permission to access S3 bucket: {bucket_name}")
        else:
            print(f"❌ Error accessing S3 bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking S3 bucket: {e}")
        return False

def check_aws_services():
    """Check if required AWS services are accessible"""
    services = {
        'transcribe': 'Amazon Transcribe',
        'translate': 'Amazon Translate',
        'polly': 'Amazon Polly'
    }
    
    all_ok = True
    for service, name in services.items():
        try:
            client = boto3.client(service)
            # Try a simple operation to verify access
            if service == 'transcribe':
                client.list_transcription_jobs(MaxResults=1)
            elif service == 'translate':
                client.translate_text(Text='test', SourceLanguageCode='en', TargetLanguageCode='es')
            elif service == 'polly':
                client.describe_voices()
            
            print(f"✅ {name} accessible")
        except Exception as e:
            print(f"❌ {name} not accessible: {e}")
            all_ok = False
    
    return all_ok

def check_directory_structure():
    """Verify required directories exist"""
    dirs = ['audio_inputs', '.github/workflows']
    all_ok = True
    
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_ok = False
    
    return all_ok

def check_files():
    """Verify required files exist"""
    files = [
        'process_audio.py',
        'requirements.txt',
        '.github/workflows/on_pull_request.yml',
        '.github/workflows/on_merge.yml'
    ]
    all_ok = True
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 60)
    print("Audio Processing Pipeline - Setup Validation")
    print("=" * 60)
    print()
    
    checks = []
    
    # Check environment variables
    print("📝 Environment Variables:")
    checks.append(check_env_var('S3_BUCKET'))
    checks.append(check_env_var('TARGET_LANGUAGE'))
    checks.append(check_env_var('AWS_REGION'))
    check_env_var('ENVIRONMENT', required=False)
    print()
    
    # Check AWS credentials
    print("🔑 AWS Credentials:")
    checks.append(check_aws_credentials())
    print()
    
    # Check S3 bucket
    bucket = os.environ.get('S3_BUCKET')
    if bucket:
        print("🪣 S3 Bucket:")
        checks.append(check_s3_bucket(bucket))
        print()
    
    # Check AWS services
    print("☁️  AWS Services:")
    checks.append(check_aws_services())
    print()
    
    # Check directory structure
    print("📁 Directory Structure:")
    checks.append(check_directory_structure())
    print()
    
    # Check files
    print("📄 Required Files:")
    checks.append(check_files())
    print()
    
    # Summary
    print("=" * 60)
    if all(checks):
        print("✅ All checks passed! You're ready to process audio files.")
        print()
        print("Next steps:")
        print("1. Add .mp3 files to audio_inputs/ folder")
        print("2. Commit and push to create a pull request")
        print("3. Review outputs in beta/ environment")
        print("4. Merge to deploy to prod/ environment")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()