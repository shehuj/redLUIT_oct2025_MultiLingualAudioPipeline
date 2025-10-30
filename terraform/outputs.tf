output "bucket_name" {
  value = aws_s3_bucket.multilingua_bucket
}
output "bucket_arn" {
  value = aws_s3_bucket.multilingua_bucket.arn
}
output "bucket_region" {
  value = aws_s3_bucket.multilingua_bucket.region
}