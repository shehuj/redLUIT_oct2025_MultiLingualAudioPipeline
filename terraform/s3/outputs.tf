output "bucket_name" {
  value       = aws_s3_bucket.website_bucket.bucket
  description = "Name of the S3 bucket created"
}

output "website_endpoint" {
  value       = aws_s3_bucket_website_configuration.website.website_endpoint
  description = "URL of the hosted website"
}