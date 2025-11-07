variable "bucket_arn" {
  type = string
}

variable "bucket_id" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "bucket_region" {
  type = string
}

variable "env" {
  type    = string
  default = "beta"
}

variable "target_lang" {
  type    = string
  default = "es"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "lambda_arn" {
  type = string
}