provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "multilingua_bucket" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.audio_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.multilingua_bucket.id
  policy = data.aws_iam_policy_document.bucket_policy.json
}

data "aws_iam_policy_document" "bucket_policy" {
  statement {
    actions   = ["s3:GetObject", 
                 "s3:ListBucket",
                 "s3:DeleteObject",
                 "s3:PutObjectAcl",
                 "s3:PutObjectTagging",
                 "s3:GetObjectTagging",
                 "s3:PutObject"]
    resources = ["${aws_s3_bucket.multilingua_bucket.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}   

