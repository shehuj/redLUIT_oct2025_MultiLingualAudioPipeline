variable "bucket_name" { 
    description = "value for the S3 bucket name"
    type = string
    default = "multilingua_pipeline_bucket"
    }
variable "aws_region"  { 
    type = string 
    default = "us-east-1" 
    description = "AWS Region" 
}
