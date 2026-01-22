variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "terraform-state"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# Set to true when using LocalStack for local development
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

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "terraform-remote-state"
    ManagedBy = "terraform"
  }
}
