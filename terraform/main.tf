provider "aws" {
  region = var.aws_region
}

module "s3" {
  source      = "./modules/s3"
  bucket_name = var.bucket_name
}

module "iam" {
  source     = "./modules/iam"
  bucket_arn = module.s3.bucket_arn
}

module "lambda" {
  source        = "./modules/lambda"
  function_name = "multilingual‐audio-${var.env}"
  role_arn      = module.iam.lambda_role_arn
  bucket_name   = var.bucket_name
  env           = var.env
  target_lang   = var.target_lang
}

resource "aws_s3_bucket_notification" "audio_trigger" {
  bucket = module.s3.bucket_id

  lambda_function {
    lambda_function_arn = module.lambda.lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "audio_inputs/"
    filter_suffix       = ".mp3"
  }

  depends_on = [module.lambda.lambda_permission]
}