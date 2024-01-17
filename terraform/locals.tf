data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "random_id" "random" {
  byte_length = 4
}

locals {
  account_id     = data.aws_caller_identity.current.account_id
  region         = data.aws_region.current.name
  s3_bucket_name = "amazon-bedrock-knowledge-base-${random_id.random.hex}"
  rag_data      = fileset("${path.module}/../rag_data/", "*")
}

output "rag_data" {
  value = local.rag_data
}
