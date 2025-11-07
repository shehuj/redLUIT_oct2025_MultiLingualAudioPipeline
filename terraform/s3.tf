resource "aws_s3_bucket" "audio_pipeline" {
  bucket = var.bucket_name
  acl    = "private"

  tags = {
    Environment = var.env
    Project     = "claudIQ-audioPipeline"
  }

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_notification" "audio_upload" {
  bucket = aws_s3_bucket.audio_pipeline.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.audio_processor.arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "audio_inputs/"
    filter_suffix       = ".mp3"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}