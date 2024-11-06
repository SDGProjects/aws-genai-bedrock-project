output "bedrock_execution_role_arn" {
  value = aws_iam_role.bedrock_execution_role.arn
}

output "genai_frontend_s3_bucket_name" {
  value = module.genai_frontend_s3_bucket.s3_bucket_id
}

output "genai_knowledge_base_s3_bucket_website_endpoint" {
  value = module.genai_knowledge_base_s3_bucket.s3_bucket_website_endpoint
}

output "genai_knowledge_base_s3_bucket_name" {
  value = module.genai_knowledge_base_s3_bucket.s3_bucket_id
}

