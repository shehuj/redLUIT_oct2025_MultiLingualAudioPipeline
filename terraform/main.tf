provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "multilingua_bucket" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.multilingua_bucket.id
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
    actions   = ["s3:*"]
    resources = [
      aws_s3_bucket.multilingua_bucket.arn,
      "${aws_s3_bucket.multilingua_bucket.arn}/*",
    ]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    effect = "Allow"
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}       

/*
resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.multilingua_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucketAccess"
        Effect = "Allow"
        Principal = {
          AWS = var.some_role_arn
        }
        Action   = "s3:ListBucket"
        Resource = "arn:aws:s3:::${aws_s3_bucket.multilingua_bucket.id}"
      },
      {
        Sid    = "ObjectReadWrite"
        Effect = "Allow"
        Principal = {
#          AWS = var.some_role_arn
        }
        Action   = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${aws_s3_bucket.multilingua_bucket.id}/*"
      }
    ]
  })
}

*/
