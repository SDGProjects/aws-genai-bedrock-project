output "bedrock_execution_role_arn" {
  value = aws_iam_role.bedrock_execution_role.arn
}

output "frontend_s3_bucket_name" {
  value = module.genai_frontend_s3_bucket.s3_bucket_id
}

output "knowledge_base_s3_bucket_name" {
  value = module.genai_knowledge_base_s3_bucket.s3_bucket_id
}

output "cloudfront_id" {
  value = module.genai_frontend_cdn.cloudfront_distribution_id
}

output "cloudfront_domain_name" {
  value = module.genai_frontend_cdn.cloudfront_distribution_domain_name
}
