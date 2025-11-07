data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/code"
  output_path = "${path.module}/lambda_package.zip"
}

resource "aws_lambda_function" "audio_pipeline" {
  function_name = var.function_name
  runtime       = "python3.12"
  role          = var.role_arn
  handler       = "lambda_function.lambda_handler"
  filename      = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      S3_BUCKET   = var.bucket_name
      TARGET_LANG = var.target_lang
      ENVIRONMENT = var.env
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.audio_pipeline.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.bucket_name}"
}

output "lambda_arn" {
  value = aws_lambda_function.audio_pipeline.arn
}