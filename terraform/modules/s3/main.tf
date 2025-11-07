resource "aws_s3_bucket" "audio_bucket" {
  bucket = var.bucket_name

  versioning {
    enabled = true
  }

  lifecycle_rule {
    enabled = true
    prefix  = ""
    expiration {
      days = 30
    }
  }
}

output "bucket_name" {
  value = aws_s3_bucket.audio_bucket.id
}

output "bucket_arn" {
  value = aws_s3_bucket.audio_bucket.arn
}

output "bucket_id" {
  value = aws_s3_bucket.audio_bucket.id
}

output "bucket_region" {
  value = aws_s3_bucket.audio_bucket.region
}