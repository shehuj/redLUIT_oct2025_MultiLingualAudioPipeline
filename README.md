# Audio Processing Pipeline - Dev/Prod Deployment

Automated audio transcription, translation, and synthesis using AWS services with separate development and production environments.

## Architecture Overview

```
Pull Request → Dev Environment (Test)
      ↓
   Merge to Main → Production Environment (Live)
```

### Workflow Structure

1. **`on_pull_request.yml`** - Development Environment
   - Triggers on pull requests
   - Deploys to dev S3 bucket
   - Posts results as PR comments
   - Safe testing environment

2. **`on_merge.yml`** - Production Environment
   - Triggers on merge to main/master
   - Deploys to production S3 bucket
   - Creates issues on failure
   - Optional Slack notifications
   - Production safety checks

## Features

- Upload MP3 files to Amazon S3
- Transcribe audio using Amazon Transcribe
- Translate text to multiple languages using Amazon Translate
- Synthesize translated speech using Amazon Polly
- Separate dev and production environments
- Automated PR comments with results
- Failure notifications and issue creation
- Organized S3 output structure

## Output Structure

### Development Environment
```
s3://your-dev-bucket/
├── audio_inputs/
├── transcripts/
├── translations/
└── audio_outputs/
```

### Production Environment
```
s3://your-prod-bucket/
├── audio_inputs/
├── transcripts/
├── translations/
└── audio_outputs/
```

## Setup Instructions

### 1. AWS Setup

#### Create Two S3 Buckets

```bash
# Development bucket
aws s3 mb s3://your-company-audio-dev

# Production bucket
aws s3 mb s3://your-company-audio-prod
```

#### Create IAM Roles/Users

Create two separate IAM roles or users:
- One for development environment
- One for production environment

Both need the same permissions (see `iam-policy-example.json`), but scoped to their respective buckets.

**Development IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": [
        "arn:aws:s3:::your-company-audio-dev",
        "arn:aws:s3:::your-company-audio-dev/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:*",
        "translate:*",
        "polly:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Production IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": [
        "arn:aws:s3:::your-company-audio-prod",
        "arn:aws:s3:::your-company-audio-prod/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:*",
        "translate:*",
        "polly:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. GitHub Repository Setup

#### Create Repository Secrets

Go to **Settings → Secrets and variables → Actions** and create:

**Common Secrets:**
- `AWS_REGION` - Your AWS region (e.g., `us-east-1`)

**Development Environment (Option A - OIDC - Recommended):**
- `DEV_AWS_ROLE_ARN` - IAM role ARN for dev environment
- `DEV_S3_BUCKET_NAME` - Development S3 bucket name

**Development Environment (Option B - Access Keys):**
- `DEV_AWS_ACCESS_KEY_ID` - Development AWS access key
- `DEV_AWS_SECRET_ACCESS_KEY` - Development AWS secret key
- `DEV_S3_BUCKET_NAME` - Development S3 bucket name

**Production Environment (Option A - OIDC - Recommended):**
- `PROD_AWS_ROLE_ARN` - IAM role ARN for production
- `PROD_S3_BUCKET_NAME` - Production S3 bucket name

**Production Environment (Option B - Access Keys):**
- `PROD_AWS_ACCESS_KEY_ID` - Production AWS access key
- `PROD_AWS_SECRET_ACCESS_KEY` - Production AWS secret key
- `PROD_S3_BUCKET_NAME` - Production S3 bucket name

**Optional:**
- `SLACK_WEBHOOK_URL` - Slack webhook for production notifications

#### Create GitHub Environments

1. Go to **Settings → Environments**
2. Create two environments:
   - **development** - No special protection rules
   - **production** - Add protection rules:
     - Required reviewers (optional but recommended)
     - Wait timer (optional)
     - Restrict to main/master branch

#### Copy Workflow Files

```bash
mkdir -p .github/workflows
cp on_pull_request.yml .github/workflows/
cp on_merge.yml .github/workflows/
```

### 3. Repository Structure

```
your-repo/
├── .github/
│   └── workflows/
│       ├── on_pull_request.yml
│       └── on_merge.yml
├── audio_inputs/
│   └── (add your .mp3 files here)
├── process_audio.py
├── requirements.txt
└── README.md
```

## Workflow Guide

### Development Workflow (Testing)

1. **Create a new branch:**
   ```bash
   git checkout -b feature/add-new-audio
   ```

2. **Add MP3 files:**
   ```bash
   cp my-audio.mp3 audio_inputs/
   git add audio_inputs/my-audio.mp3
   ```

3. **Push and create PR:**
   ```bash
   git commit -m "Add new audio file"
   git push origin feature/add-new-audio
   # Create PR on GitHub
   ```

4. **Review results:**
   - Workflow runs automatically on PR creation
   - Check the PR comment for processing results
   - Files are processed in **dev environment**
   - No impact on production

5. **Iterate if needed:**
   ```bash
   # Make changes
   git add .
   git commit -m "Fix audio file"
   git push
   # Workflow runs again automatically
   ```

### Production Workflow (Live Deployment)

1. **Merge the PR:**
   - Review the dev processing results
   - Approve and merge the PR to main/master

2. **Automatic production deployment:**
   - Workflow triggers on merge
   - Processes files in **production environment**
   - Creates issue if processing fails
   - Sends Slack notification (if configured)

3. **Verify production:**
   - Check the workflow run logs
   - Verify files in production S3 bucket

### Manual Production Deployment

You can also trigger production manually:

1. Go to **Actions → Audio Processing - Production**
2. Click **Run workflow**
3. Type `PRODUCTION` to confirm
4. Select target language (optional)
5. Click **Run workflow**

> **Safety Feature:** Manual production runs require typing "PRODUCTION" to prevent accidental deployments.

## Monitoring & Notifications

### PR Comments (Development)

When a PR is created or updated, the workflow posts a comment with:
- Processing summary (success/failure counts)
- Environment details
- Processing logs
- S3 bucket information

Example:
```
🎵 Audio Processing Results (Dev Environment)

Summary:
- Total files: 3
- Successful: 3
- Failed: 0

Environment: Development
S3 Bucket: your-company-audio-dev
Target Language: es
```

### Issue Creation (Production)

When production processing fails:
- Automatic GitHub issue is created
- Tagged with `bug`, `production`, `audio-processing`
- Contains error logs and action items
- Links to workflow run and S3 console

### Slack Notifications (Production)

Configure Slack webhook to receive:
- Success/failure status
- File processing counts
- Direct link to workflow run
- Triggered by actor information

## Testing Strategy

### Local Testing

Before creating a PR, test locally:

```bash
# Set environment variables
export S3_BUCKET_NAME="your-company-audio-dev"
export TARGET_LANGUAGE="es"
export AWS_ACCESS_KEY_ID="your-dev-key"
export AWS_SECRET_ACCESS_KEY="your-dev-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Run the script
python process_audio.py
```

### Dev Environment Testing

1. Create PR with test audio files
2. Review automated processing results
3. Verify outputs in dev S3 bucket
4. Make adjustments if needed

### Production Deployment

1. Ensure dev testing is successful
2. Merge PR to trigger production deployment
3. Monitor workflow execution
4. Verify production S3 outputs

## Configuration

### Environment Variables

Both workflows support:

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_BUCKET_NAME` | S3 bucket (dev or prod) | - |
| `TARGET_LANGUAGE` | Translation target | `es` |
| `SOURCE_LANGUAGE` | Transcription source | `en-US` |
| `INPUT_FOLDER` | Input directory | `audio_inputs` |

### Supported Languages

**Translation targets:** `es`, `fr`, `de`, `it`, `pt`, `ja`, `ko`, `zh`, `ar`, `hi`, `ru`, `nl`, `pl`, `tr` and more

**Transcription sources:** `en-US`, `en-GB`, `es-ES`, `fr-FR`, `de-DE` and more

See AWS documentation for complete lists.

## Security Best Practices

1. **Use OIDC authentication** instead of access keys when possible
2. **Separate IAM roles** for dev and production
3. **Limit S3 bucket access** to specific roles only
4. **Enable GitHub environment protection** for production
5. **Require PR reviews** before merging to main
6. **Use branch protection rules** on main/master
7. **Rotate access keys regularly** if using key-based auth
8. **Monitor CloudWatch logs** for unusual activity

## Cost Optimization

### Development Environment
- Process only on PR changes to audio files
- Use smaller/shorter audio samples for testing
- Regularly clean up old dev S3 objects

### Production Environment
- Only runs on merge (controlled deployments)
- Batch process multiple files efficiently
- Set S3 lifecycle policies to archive old files

### Estimated Costs
- **Dev:** ~$0.50-1.00 per PR (depends on file count/length)
- **Prod:** ~$2-5 per deployment (1 hour of audio translated)

## Troubleshooting

### Dev Workflow Not Triggering

**Issue:** PR created but workflow doesn't run

**Solutions:**
- Ensure `.mp3` files are in `audio_inputs/` folder
- Check workflow file is in `.github/workflows/`
- Verify PR isn't from a fork (workflows limited on forks)
- Check Actions are enabled in repository settings

### Production Workflow Not Running

**Issue:** PR merged but production workflow doesn't trigger

**Solutions:**
- Verify merge was to `main` or `master` branch
- Check workflow paths match changed files
- Review Actions logs for errors
- Ensure GitHub environments are configured

### AWS Authentication Failures

**Issue:** Workflow fails with AWS credential errors

**Solutions:**
- Verify all secrets are set correctly
- Check IAM role/user permissions
- Ensure correct AWS region is configured
- Test credentials with AWS CLI locally
- For OIDC, verify trust relationship is configured

### Processing Failures

**Issue:** Files fail to process

**Solutions:**
- Check MP3 file is valid format
- Verify source language matches audio
- Review CloudWatch logs in AWS console
- Check S3 bucket permissions
- Ensure no rate limiting on AWS services

### PR Comments Not Appearing

**Issue:** Dev workflow runs but no PR comment

**Solutions:**
- Verify `pull-requests: write` permission is set
- Check workflow completed successfully
- Review Actions logs for errors
- Ensure not running on fork PR

## Additional Resources

- [AWS Transcribe Documentation](https://docs.aws.amazon.com/transcribe/)
- [AWS Translate Documentation](https://docs.aws.amazon.com/translate/)
- [AWS Polly Documentation](https://docs.aws.amazon.com/polly/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments)

## Contributing

1. Create a feature branch
2. Add/modify audio files or code
3. Create PR and review dev results
4. Address any review comments
5. Merge to deploy to production

## License

MIT License - Feel free to use and modify.

---

**Questions?** Check the troubleshooting section or create an issue in the repository.