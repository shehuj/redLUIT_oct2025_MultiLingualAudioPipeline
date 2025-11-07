variable "bucket_name" {
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