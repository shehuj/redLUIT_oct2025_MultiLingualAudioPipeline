audio-pipeline/
├── README.md
├── .github/
│   └── workflows/
│       ├── upload_audio.yml
│       └── build_and_deploy_lambda.yml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── iam.tf
│   ├── s3.tf
│   └── lambda.tf
├── lambda_src/
│   ├── handler.py
│   ├── requirements.txt
│   └── tests/
│       └── test_handler.py
└── scripts/
    └── package_lambda.sh


# claudIQ Audio Processing Pipeline  
This repository contains an event-driven audio processing pipeline built for AWS.  
It listens for `.mp3` uploads to an S3 bucket (`audio_inputs/` prefix), triggers a Lambda that runs:  
- Amazon Transcribe → Transcript  
- Amazon Translate → Translated text  
- Amazon Polly → Synthesised speech  

Results are written into structured prefixes (`transcripts/`, `translations/`, `audio_outputs/`) under environment prefixes (e.g., `beta/`, `prod/`).  
  
## Components  
- Terraform module under `terraform/` to create S3 bucket, Lambda, IAM roles, S3 event notifications.  
- Lambda function under `lambda_src/` (Python 3.11) with logic.  
- GitHub Actions workflows under `.github/workflows/` for (1) building & deploying the Lambda, and (2) uploading MP3 files tagged with environment metadata.  
- Packaging script `scripts/package_lambda.sh` to create deployment artifact.  

## Getting Started  
1. Configure AWS credentials and region.  
2. In `terraform/`, set variables (bucket names, env, etc) and run:  
   ```bash
   terraform init  
   terraform plan  
   terraform apply  