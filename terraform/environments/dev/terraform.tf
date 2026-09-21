terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }

    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  required_version = ">= 1.16"

  backend "s3" {
    bucket="medicare-pipeline-tf-state-cjk-2026"
    key = "environments/dev/terraform.tfstate"
    region = "us-east-1"
    use_lockfile = true
    encrypt = true
  }
}