terraform {
  required_version = ">= 1.5"

  backend "s3" {
    bucket = "terraform-state-us-east-1-853297241922"
    key    = "projects/aws-genai-bedrock-project/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Name        = var.project_name
      Region      = var.region
      Environment = terraform.workspace
      Repo        = "aws-genai-bedrock-project"
      Path        = path.module
    }
  }
}
