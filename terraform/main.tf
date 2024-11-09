data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  account_id       = data.aws_caller_identity.current.account_id
  s3_bucket_suffix = "${var.region}-${local.account_id}"
  genai_frontend_s3_bucket_name = "genai-frontend-${local.s3_bucket_suffix}"
  genai_knowledge_base_s3_bucket_name = "genai-knowledge-base-${local.s3_bucket_suffix}"
}

########################################
# Frontend Website Resources
########################################
module "genai_frontend_cdn" {
  source = "terraform-aws-modules/cloudfront/aws"
  version = "3.4.1"

  aliases = [] # "example.example.com"

  comment             = "GenAI Bedrock Frontend CDN"
  enabled             = true
  is_ipv6_enabled     = false
  price_class         = "PriceClass_All"
  retain_on_delete    = false
  wait_for_deployment = false

  create_origin_access_identity = true
  origin_access_identities = {
    s3_bucket_one = "GenAIS3BucketOrigin"
  }

  origin = {
    genai-s3-bucket = {
      domain_name = module.genai_frontend_s3_bucket.s3_bucket_bucket_regional_domain_name
      s3_origin_config = {
        origin_access_identity = "s3_bucket_one"
      }
    }
  }

  default_cache_behavior = {
    target_origin_id           = "genai-s3-bucket"
    viewer_protocol_policy     = "allow-all"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true
    query_string    = true
  }
}

module "genai_frontend_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "4.2.1"

  bucket = local.genai_frontend_s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  website = {
    index_document = "index.html"
    error_document = "error.html"
  }

  versioning = {
    enabled = true
  }
}

########################################
# Backend Website Resources
########################################

module "genai_knowledge_base_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "4.2.1"

  bucket = local.genai_knowledge_base_s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}

/*
resource "aws_lexv2models_bot" "example" {
  name        = "example"
  description = "Example description"
  data_privacy {
    child_directed = false
  }
  idle_session_ttl_in_seconds = 60
  role_arn                    = aws_iam_role.example.arn
  type                        = "Bot"

  tags = {
    foo = "bar"
  }
}

resource "aws_iam_role" "test" {
  name = "test"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lexv2.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    created_by = "aws"
  }
}

resource "aws_iam_role_policy_attachment" "test" {
  role       = aws_iam_role.test.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonLexFullAccess"
}

resource "aws_lexv2models_bot" "test" {
  name                        = "botens_namn"
  idle_session_ttl_in_seconds = 60
  role_arn                    = aws_iam_role.test.arn

  data_privacy {
    child_directed = true
  }
}

resource "aws_lexv2models_bot_locale" "test" {
  locale_id                        = "en_US"
  bot_id                           = aws_lexv2models_bot.test.id
  bot_version                      = "DRAFT"
  n_lu_intent_confidence_threshold = 0.7
}

resource "aws_lexv2models_bot_version" "test" {
  bot_id = aws_lexv2models_bot.test.id
  locale_specification = {
    (aws_lexv2models_bot_locale.test.locale_id) = {
      source_bot_version = "DRAFT"
    }
  }
}

resource "aws_lexv2models_intent" "example" {
  bot_id      = aws_lexv2models_bot.test.id
  bot_version = aws_lexv2models_bot_locale.test.bot_version
  name        = "botens_namn"
  locale_id   = aws_lexv2models_bot_locale.test.locale_id
}
*/
