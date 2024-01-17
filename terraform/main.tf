terraform {
  required_version = ">= 1.5"

  # Optional: Uncomment this block to use local terraform state
  # backend "local" {
  #   path = "terraform.tfstate"
  # }

  # Update bucket with your own bucket name
  backend "s3" {
    bucket = "terraform-state-bucket-gbzfds"
    key    = "amazon-bedrock/flask-chatbot-with-rag/terraform.tfstate"
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
      Name   = var.project_name
      Region = var.region
    }
  }
}

resource "aws_s3_bucket" "bedrock_knowledge_base" {
  bucket        = local.s3_bucket_name
  force_destroy = true

  tags = {
    Name        = local.s3_bucket_name
    Environment = terraform.workspace
  }
}

resource "aws_s3_bucket_ownership_controls" "bedrock_knowledge_base" {
  bucket = aws_s3_bucket.bedrock_knowledge_base.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "bedrock_knowledge_base" {
  bucket                  = aws_s3_bucket.bedrock_knowledge_base.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_acl" "bedrock_knowledge_base" {
  bucket = aws_s3_bucket.bedrock_knowledge_base.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "bedrock_knowledge_base" {
  bucket = aws_s3_bucket.bedrock_knowledge_base.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_object" "rag_data" {
  for_each = toset(local.rag_data)

  bucket = aws_s3_bucket.bedrock_knowledge_base.bucket
  key    = each.value
  source = "${path.module}/../rag_data/${each.value}"

  # Trigger updates when the value changes
  etag = filemd5("${path.module}/../rag_data/${each.value}")
}
