# Multilingual Audio Pipeline – Infrastructure as Code

## Overview
This Terraform project deploys an event-driven AWS pipeline using:
- Amazon S3 for storage of audio inputs and outputs  
- AWS Lambda for processing (.mp3 → transcript → translation → speech)  
- Amazon Transcribe, Amazon Translate, and Amazon Polly for AI services  
- GitHub Actions (not shown here) trigger uploads and deploy infrastructure.

## Setup
1. Create an S3 bucket for Terraform state backend.  
2. Set the following variables:
   - `aws_region`
   - `backend_bucket`
   - `bucket_name`
   - `env` (beta or prod)  
   - `target_lang` (e.g., `es`, `fr`)  
3. Initialize Terraform:

terraform init
terraform plan -var=“bucket_name=your-bucket” -var=“env=beta”
terraform apply

## Directory structure

terraform/
├── backend.tf
├── variables.tf
├── outputs.tf
├── main.tf
├── modules/
│   ├── s3/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── iam/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── lambda/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── code/
│           ├── lambda_function.py
│           └── requirements.txt
├── scripts/
│   └── build_lambda.sh
└── README.md

## Usage
1. Upload `.mp3` files to `s3://<bucket>/audio_inputs/` (via GitHub Actions or manually).  
2. Lambda is triggered, transcribes, translates, synthesizes, and writes results to:
   - `s3://<bucket>/<env>/transcripts/{filename}.txt`
   - `s3://<bucket>/<env>/translations/{filename}_{lang}.txt`
   - `s3://<bucket>/<env>/audio_outputs/{filename}_{lang}.mp3`  
3. Verify outputs in the S3 console or via AWS CLI.

## GitHub Actions
- PR workflows should deploy with `env=beta`.  
- Merge to `main` should deploy with `env=prod`.

## Notes
- Ensure Transcribe, Translate, Polly services are enabled in the AWS region.  
- Adjust IAM permissions to fit your security policy (least privilege).  
- You can extend retention, add Step Functions, API Gateway for queries, etc.
