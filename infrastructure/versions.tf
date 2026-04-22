terraform {
  required_version = ">= 1.10.0"

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.5"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # S3 bucket must exist before running terraform init.
  # Create it once with the AWS CLI:
  #
  #   aws s3api create-bucket \
  #     --bucket sfk-scheduler-tfstate \
  #     --region eu-north-1 \
  #     --create-bucket-configuration LocationConstraint=eu-north-1
  #
  #   aws s3api put-bucket-versioning \
  #     --bucket sfk-scheduler-tfstate \
  #     --versioning-configuration Status=Enabled
  backend "s3" {
    bucket       = "sfk-scheduler-tfstate"
    key          = "sfk-scheduler/terraform.tfstate"
    region       = "eu-north-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region
}