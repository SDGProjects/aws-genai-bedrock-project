# General variables
variable "region" {
  default     = "us-east-1"
  description = "The region you want to deploy the solution"
}

variable "project_name" {
  default     = "flask-chatbot-with-rag"
  description = "the name for resource"
}

variable "default_embedding_model_id" {
  default     = "amazon.titan-embed-text-v1"
  description = "The name of the foundation model"
}
