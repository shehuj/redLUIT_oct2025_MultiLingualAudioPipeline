terraform {
  backend "s3" {
    bucket = var.backend_bucket
    key    = "${var.env}/terraform.tfstate"
    region = var.aws_region
  }
}