resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda‐exec‐role‐${var.bucket_arn}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "lambda‐policy‐${var.bucket_arn}"
  description = "Permissions for audio pipeline Lambda"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        Effect   = "Allow",
        Resource = "${var.bucket_arn}/*"
      },
      {
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "translate:TranslateText"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "polly:SynthesizeSpeech"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_exec_role.arn
}