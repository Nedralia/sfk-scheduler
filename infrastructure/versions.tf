terraform {
  required_version = ">= 1.7.5"

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
  backend "s3" {
    bucket  = "sfk-scheduler-tfstate"
    key     = "sfk-scheduler/terraform.tfstate"
    region  = "eu-north-1"
    encrypt = true
    profile = "nedralia"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "nedralia"
}