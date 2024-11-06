data "aws_iam_policy_document" "bedrock_execution_policy" {
  statement {
    sid       = "ListBedrockFMs"
    effect    = "Allow"
    actions   = ["bedrock:ListFoundationModels", "bedrock:ListCustomModels"]
    resources = ["*"]
  }
  statement {
    sid       = "AllowInvokeBedrockEmbeddingFM"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${var.region}::foundation-model/${var.default_embedding_model_id}"]
  }
  statement {
    sid       = "AllowCreateBedrockKnowledgeBase"
    effect    = "Allow"
    actions   = ["bedrock:CreateKnowledgeBase"]
    resources = ["arn:aws:iam::${local.account_id}:user/*"]
  }
  statement {
    sid       = "AllowOpenSearchCollections"
    effect    = "Allow"
    actions   = ["aoss:APIAccessAll"]
    resources = ["arn:aws:aoss:${var.region}:${local.account_id}:collection/*"]
  }
  statement {
    sid       = "S3ListBucketStatement"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.genai_knowledge_base_s3_bucket_name}"]
  }
  statement {
    sid       = "AllowGetObjectFromBucket"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${local.genai_knowledge_base_s3_bucket_name}/*"]
  }
}

resource "aws_iam_policy" "bedrock_execution_policy" {
  name   = "AmazonBedrockExecutionPolicyForKnowledgeBase"
  policy = data.aws_iam_policy_document.bedrock_execution_policy.json
}

# bedrock_execution_role data source for assume_role_policy
data "aws_iam_policy_document" "bedrock_execution_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock:${var.region}:${local.account_id}:knowledge-base/*"]
    }
  }
}

resource "aws_iam_role" "bedrock_execution_role" {
  # IAM Role name format MUST have prefix "AmazonBedrockExecutionRoleForKnowledgeBase_"
  # Otherwise the Bedrock service will throw an error -_-
  # https://repost.aws/questions/QUtRamAlJ6ToWfhHInwmYJtg/user-arn-is-not-authorized-to-perform-bedrock-createknowledgebase#ANPQ1Oh__2Rx-s1z06U9RKGw
  name               = "AmazonBedrockExecutionRoleForKnowledgeBase_Default"
  assume_role_policy = data.aws_iam_policy_document.bedrock_execution_role.json
}

resource "aws_iam_role_policy_attachment" "bedrock_execution_role" {
  policy_arn = aws_iam_policy.bedrock_execution_policy.arn
  role       = aws_iam_role.bedrock_execution_role.name
}
