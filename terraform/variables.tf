variable "env" {
  type        = string
  description = "Environment name (beta or prod)"
}

variable "region" {
  type        = string
  description = "AWS Region"
  default     = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket for audio pipeline"
}

variable "lambda_handler_s3_key" {
  type        = string
  description = "S3 key / path for Lambda deployment zip"
}

variable "target_languages" {
  type        = list(string)
  description = "List of target language codes for translation"
  default     = ["es", "fr"]
}

variable "voice_mapping" {
  type        = map(string)
  description = "Mapping of language code → Polly voice id"
  default     = {
    "es" = "Lucia"
    "fr" = "Celine"
  }
}