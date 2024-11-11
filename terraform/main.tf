data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  s3_bucket_suffix                    = "${var.region}-${local.account_id}"
  genai_frontend_s3_bucket_name       = "genai-frontend-${local.s3_bucket_suffix}"
  genai_knowledge_base_s3_bucket_name = "genai-knowledge-base-${local.s3_bucket_suffix}"
}

########################################
# Frontend Website Resources
########################################
module "genai_frontend_cdn" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "3.4.1"

  aliases = [] # "example.example.com"

  comment             = "GenAI Bedrock Frontend CDN"
  enabled             = true
  is_ipv6_enabled     = false
  price_class         = "PriceClass_All"
  retain_on_delete    = false
  wait_for_deployment = false

  default_root_object = "index.html"

  create_origin_access_control = true

  origin_access_control = {
    genai-s3-bucket = {
      description      = "GenAI S3 Bucket Origin Access Identity"
      origin_type      = "s3",
      signing_behavior = "always",
      signing_protocol = "sigv4"
    }
  }

  origin = {
    genai-s3-bucket = {
      domain_name           = module.genai_frontend_s3_bucket.s3_bucket_bucket_regional_domain_name
      origin_access_control = "genai-s3-bucket"
    }
  }

  default_cache_behavior = {
    target_origin_id       = "genai-s3-bucket"
    viewer_protocol_policy = "allow-all"
    use_forwarded_values   = false

    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"
    response_headers_policy_id = "60669652-455b-4ae9-85a4-c4c02393f86c"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true
    query_string    = true
  }
}

module "genai_frontend_s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.2.1"

  bucket = local.genai_frontend_s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  attach_policy = true
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal",
        Effect = "Allow",
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject",
        Resource = "arn:aws:s3:::${local.genai_frontend_s3_bucket_name}/*",
        Condition = {
          StringEquals = {
            "AWS:SourceArn" : "arn:aws:cloudfront::${local.account_id}:distribution/${module.genai_frontend_cdn.cloudfront_distribution_id}"
          }
        }
      }
    ]
  })

  versioning = {
    enabled = true
  }
}

resource "aws_s3_object" "index" {
  bucket = module.genai_frontend_s3_bucket.s3_bucket_id
  key    = "index.html"
  source = "../static-site/index.html"

  server_side_encryption = "AES256"
  content_type           = "text/html"
}

resource "aws_s3_object" "error" {
  bucket = module.genai_frontend_s3_bucket.s3_bucket_id
  key    = "error.html"
  source = "../static-site/error.html"

  server_side_encryption = "AES256"
  content_type           = "text/html"
}

########################################
# Backend Website Resources
########################################

module "genai_knowledge_base_s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.2.1"

  bucket = local.genai_knowledge_base_s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}
