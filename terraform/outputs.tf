output "bucket_name" {
  value = aws_s3_bucket.audio_bucket.bucket
}
output "bucket_arn" {
  value = aws_s3_bucket.audio_bucket.arn
}
output "bucket_region" {
  value = aws_s3_bucket.audio_bucket.region
}