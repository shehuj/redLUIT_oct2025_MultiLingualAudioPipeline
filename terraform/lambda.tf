resource "aws_lambda_function" "audio_processor" {
  filename         = var.lambda_handler_s3_key
  function_name    = "${var.env}-audio-pipeline-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 900   # up to 15 minutes
  memory_size      = 1024

  environment {
    variables = {
      OUTPUT_BUCKET      = aws_s3_bucket.audio_pipeline.bucket
      TARGET_LANGUAGES   = join(",", var.target_languages)
      VOICE_MAPPING_JSON = jsonencode(var.voice_mapping)
      ENV_PREFIX         = var.env
    }
  }

  tags = {
    Environment = var.env
    Project     = "claudIQ-audioPipeline"
  }
}

resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.audio_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.audio_pipeline.arn
}