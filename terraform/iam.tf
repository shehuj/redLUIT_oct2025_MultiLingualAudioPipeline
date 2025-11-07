data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.env}-audio-pipeline-lambda-role"

  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json

  tags = {
    Environment = var.env
    Project     = "claudIQ-audioPipeline"
  }
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:HeadObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.audio_pipeline.arn,
      "${aws_s3_bucket.audio_pipeline.arn}/*"
    ]
  }

  statement {
    actions = [
      "transcribe:StartTranscriptionJob",
      "transcribe:GetTranscriptionJob"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "translate:TranslateText"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "polly:SynthesizeSpeech"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "${var.env}-audio-pipeline-lambda-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}