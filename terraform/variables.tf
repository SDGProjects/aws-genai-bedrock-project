# General variables
variable "region" {
  type        = string
  default     = "us-east-1"
  description = "The region in which to create the resources"
}

variable "project_name" {
  type        = string
  default     = "aws-genai-bedrock-project"
  description = "The name of the project"
}

variable "default_embedding_model_id" {
  type        = string
  default     = "amazon.titan-embed-text-v1"
  description = "The name of the foundation model"
}
