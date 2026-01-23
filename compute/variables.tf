# Variables for Compute Configuration
# =====================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "terraform-state"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
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

# =============================================================================
# EC2 Configuration
# =============================================================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro" # Free tier eligible!
}

variable "ami_id" {
  description = "AMI ID for EC2 instance (leave empty to use latest Amazon Linux 2)"
  type        = string
  default     = ""
}

# =============================================================================
# Remote Backend Configuration (from backend/ outputs)
# =============================================================================
# These values come from the backend/ module outputs.
# You'll set these after running terraform apply in backend/

variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  type        = string
  default     = "" # Set this from backend outputs!
}

variable "lock_table_name" {
  description = "Name of the DynamoDB table for state locking"
  type        = string
  default     = "" # Set this from backend outputs!
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "terraform-remote-state"
    ManagedBy = "terraform"
  }
}
