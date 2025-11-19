terraform {
  backend "s3" {
    bucket = var.backend_bucket
    dynamodb_table = "dyning-table"
    key    = "${var.env}/terraform.tfstate"
    region = var.aws_region
  }
}
