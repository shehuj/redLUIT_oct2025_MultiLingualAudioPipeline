# redLUIT_MultiLinualAudioPipeline_Oct2025_
Miles Stone Project 02

# claudIQ Audio Processing Pipeline  
> Event-driven AWS pipeline: Upload MP3 → Transcribe → Translate → Polly → Output to S3 (prefixed by environment)

## Table of Contents  
1. [Overview](#overview)  
2. [Motivation](#motivation)  
3. [Architecture](#architecture)  
4. [Features](#features)  
5. [Getting Started](#gettingstarted)  
   - [Prerequisites](#prerequisites)  
   - [Deploying Infrastructure (Terraform)](#deploying-infrastructure-terraform)  
   - [Building & Deploying Lambda](#building-and-deploying-lambda)  
   - [Uploading Audio Files (GitHub Actions)](#uploading-audio-files-github-actions)  
6. [Usage](#usage)  
   - [Workflow Summary](#workflow-summary)  
   - [Environment Separation (beta/prod)](#environment-separation-betaprod)  
   - [S3 Prefixes & Outputs](#s3-prefixes-outputs)  
7. [Configuration](#configuration)  
   - [Terraform Variables](#terraform-variables)  
   - [Lambda Environment Variables](#lambda-environment-variables)  
8. [Monitoring & Logging](#monitoring-and-logging)  
9. [Security & Cost Governance](#security-and-cost-governance)  
10. [Troubleshooting](#troubleshooting)  
11. [Contributing](#contributing)  
12. [License & Acknowledgements](#license-and-acknowledgements)  

---

## 1. Overview  
This repository contains a production-ready event-driven audio processing pipeline built on AWS for the claudIQ brand. The pipeline is triggered by an upload of a `.mp3` file into an S3 bucket (under `audio_inputs/`). A Lambda function responds to the event, performs: transcription via Amazon Transcribe → translation via Amazon Translate → text-to-speech via Amazon Polly. Final outputs (transcript text, translation text, audio outputs) are stored in structured S3 prefixes under an environment namespace (e.g., `beta/` or `prod/`). The build and upload of MP3 files is handled by a lightweight GitHub Actions workflow (no processing logic there).

---

## 2. Motivation  
- **Scalability & decoupling**: By moving processing logic out of GitHub Actions into a Lambda/S3 event-trigger architecture, we free CI/CD from heavy compute and allow multiple files to be processed asynchronously.  
- **Environment separation**: Enable distinct “beta” vs “prod” pathways (prefixes, metadata) so that testing and production runs stay isolated.  
- **Automated media workflows**: For audio uploads in e.g. aviation/consulting contexts, this pipeline automates transcription, translation and voice synthesis — saving manual effort and enabling reuse across languages.  
- **Ops-ready**: Incorporates monitoring, tagging, encryption, and Infrastructure-as-Code for repeatability and governance.

---

## 3. Architecture  
Here’s a high-level diagram of how the pipeline works:

1. User or workflow uploads `*.mp3` file to S3 bucket under `audio_inputs/` prefix, with metadata `env={beta|prod}` (or filename convention).  
2. S3 generates a **ObjectCreated:Put** event (filtered to `.mp3` under `audio_inputs/`) configured to trigger a Lambda function.  
3. Lambda handler:  
   - Reads bucket/key from event.  
   - Determines `env` (metadata or parsing filename).  
   - Starts Amazon Transcribe job for the MP3.  
   - Option A: Polls for job completion (simple) **or** Option B: uses EventBridge + secondary Lambda for long jobs.  
   - Downloads transcript text, stores clean text to `env/transcripts/{filename}.txt`.  
   - For each target language configured: calls Amazon Translate → stores `env/translations/{filename}_{lang}.txt`; calls Amazon Polly → synthesises audio → stores `env/audio_outputs/{filename}_{lang}.mp3`.  
4. Outputs live in the S3 bucket, partitioned by environment.  
5. Monitoring/alerts/metrics: CloudWatch logs, metrics on job durations/failures, resource tags for cost allocation.

---

## 4. Features  
- **Automated and event-driven**: No manual polling or human steps once upload happens.  
- **Environment aware**: Supports `beta` vs `prod` contexts via metadata or naming convention.  
- **Multi-language support**: Translate into multiple target languages, synthesise voice per language.  
- **Infrastructure as Code**: Terraform modules deploy bucket, Lambda, IAM, event notifications.  
- **CI/CD friendly**: GitHub Actions for building/deploying Lambda and for uploading audio input.  
- **Built with security & ops in mind**: Encryption at rest, least-privilege IAM, tagging for cost/governance.

---

## 5. Getting Started  
### Prerequisites  
- AWS account with permissions to create S3, Lambda, IAM, Transcribe, Translate, Polly.  
- Terraform v1.x installed.  
- AWS CLI configured or GitHub Actions configured with AWS credentials.  
- GitHub repository with required secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc).  
- MP3 audio file ready to upload under `audio_inputs/`.

### Deploying Infrastructure (Terraform)  
```bash
cd terraform/
terraform init
terraform plan \
  -var="env=beta" \
  -var="bucket_name=claudIQ-audio-beta-bucket" \
  -var="lambda_handler_s3_key=lambda_src/deploy.zip" \
  -var="target_languages=[\"es\",\"fr\"]" \
  -var='voice_mapping={ "es" = "Lucia", "fr" = "Celine" }'
terraform apply -auto-approve

Repeat or modify for env=prod with production bucket and languages.

Building & Deploying Lambda
`./scripts/package_lambda.sh
# This packages lambda_src into deploy.zip`

Push code to GitHub and the .github/workflows/build_and_deploy_lambda.yml workflow will take care of artifact and Terraform apply.

## Uploading Audio Files (GitHub Actions:

Trigger the upload_audio.yml workflow via GitHub Actions (manually or on a branch). You’ll supply env input (beta or prod). It uploads .mp3 files from audio_inputs/ folder to the S3 bucket under audio_inputs/, tagging with metadata env={beta|prod}.

6. Usage

Workflow Summary
	1.	Place yourfile.mp3 into audio_inputs/ folder in your repo.
	2.	Run Upload Audio File workflow, select env=beta (for example).
	3.	S3 receives object → triggers Lambda → pipeline executes.
	4.	After completion, head to S3 bucket:
	•	beta/transcripts/yourfile.txt
	•	beta/translations/yourfile_es.txt, beta/translations/yourfile_fr.txt
	•	beta/audio_outputs/yourfile_es.mp3, beta/audio_outputs/yourfile_fr.mp3

Environment Separation (beta/prod)
	•	Filenames or S3 object metadata determine env (fallback default is prod).
	•	Use separate buckets or shared bucket with prefix beta/ vs prod/ to isolate test vs production data.
	•	Tag all AWS resources with Environment=beta/prod to enable cost tracking.

S3 Prefixes & Outputs
	•	Input prefix: audio_inputs/{filename}.mp3
	•	Transcript: {env}/transcripts/{filename}.txt
	•	Translations: {env}/translations/{filename}_{lang}.txt
	•	Audio outputs: {env}/audio_outputs/{filename}_{lang}.mp3

7. Configuration

Terraform Variables

Defined in variables.tf, key ones include:
	•	env: “beta” or “prod”
	•	bucket_name: S3 bucket
	•	lambda_handler_s3_key: path to Lambda zip
	•	target_languages: list of language codes (e.g., ["es","fr"])
	•	voice_mapping: map language code → Polly voice ID

Lambda Environment Variables

Configured in lambda.tf under environment block:
	•	OUTPUT_BUCKET: S3 bucket for results
	•	TARGET_LANGUAGES: comma-separated list of target languages (e.g., es,fr)
	•	VOICE_MAPPING_JSON: JSON string mapping language codes to voice IDs
	•	ENV_PREFIX: default environment (e.g., prod) used if metadata not present

You may optionally add: LOG_LEVEL, TRANSCRIBE_LANGUAGE_CODE, etc.

8. Monitoring & Logging
	•	Lambda logs appear in CloudWatch under the function’s log group.
	•	Monitor metrics: invocation count, errors, duration, throttles.
	•	Create CloudWatch alarms for: high error rate, long execution times, increased cost alerts.
	•	Tag resources (Project=claudIQ, Environment=beta/prod) for cost allocation and governance.
	•	If job duration grows, consider migrating to asynchronous mode (use EventBridge rule for Transcribe job completion) or the AWS Step Functions orchestration pattern.

9. Security & Cost Governance
	•	S3 bucket: versioning enabled; server-side encryption (SSE-S3 or SSE-KMS).
	•	Block public access on the bucket (aws_s3_bucket_public_access_block).
	•	IAM role for Lambda follows least-privilege: only required actions for S3, Transcribe, Translate, Polly.
	•	Tagging is mandatory for cost tracking and accountability (Environment, Project).
	•	Set lifecycle rules for output prefixes to transition to Glacier or delete after retention period (especially for test data in beta).
	•	Monitor usage of Transcribe/Translate/Polly (costly services) and set budget alerts.


10. Troubleshooting


11. Contributing

We welcome contributions to this project! Please follow these guidelines:
	•	Fork the repository and create a feature branch (e.g., feature-async-orchestration).
	•	Ensure all commits follow conventional commit style (e.g., feat: add eventbridge for transcribe).
	•	Write unit tests for Lambda logic (e.g., in lambda_src/tests/).
	•	Update documentation and README if you add or change a feature.
	•	Submit a Pull Request and we will review.
	•	For major changes, open an issue to discuss the architecture before coding.

################################################################################################################
“My README is the first handshake my project gives the world.”

So I make sure it is informative, clear and helps others onboard quickly.