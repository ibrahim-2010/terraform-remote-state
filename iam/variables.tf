variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "terraform-state"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "use_localstack" {
  description = "Whether to use LocalStack (true) or real AWS (false)"
  type        = bool
  default     = true
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}

# These should match the outputs from the backend/ module
variable "state_bucket_arn" {
  description = "ARN of the S3 bucket for Terraform state (from backend module)"
  type        = string
  default     = "" # Will be set after creating backend
}

variable "lock_table_arn" {
  description = "ARN of the DynamoDB table for state locking (from backend module)"
  type        = string
  default     = "" # Will be set after creating backend
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "terraform-remote-state"
    ManagedBy = "terraform"
  }
}
