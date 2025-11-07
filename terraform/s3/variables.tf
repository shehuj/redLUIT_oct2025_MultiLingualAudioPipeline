variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Unique name for the S3 bucket that will host the website"
  type        = string
  default     = "multilingual-audiopipeline"
}