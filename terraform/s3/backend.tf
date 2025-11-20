terraform {
  backend "s3" {
    bucket         = "ec2-shutdown-lambda-bucket"   # must exist before terraform init
    key            = "multi-lingual-audio-pipeline/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "dyning_table"
    encrypt        = true
  }
}
