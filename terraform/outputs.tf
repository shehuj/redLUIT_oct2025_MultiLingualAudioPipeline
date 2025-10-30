output "bucket_name" {
  value = aws_s3_bucket.audio_bucket.bucket
}
output "bucket_arn" {
  value = aws_s3_bucket.audio_bucket.arn
}
output "bucket_region" {
  value = aws_s3_bucket.audio_bucket.region
}
output "bucket_creation_date" {
  value = aws_s3_bucket.audio_bucket.creation_date
}
output "bucket_policy" {
  value = aws_s3_bucket.audio_bucket.policy
}
output "bucket_versioning" {
  value = aws_s3_bucket.audio_bucket.versioning
}