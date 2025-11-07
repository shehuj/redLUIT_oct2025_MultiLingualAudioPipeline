output "lambda_function_arn" {
  description = "ARN of the audio processing Lambda"
  value       = aws_lambda_function.audio_processor.arn
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket used for audio pipeline"
  value       = aws_s3_bucket.audio_pipeline.bucket
}