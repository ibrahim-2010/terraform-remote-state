# Output the S3 bucket name
output "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

# Output the S3 bucket ARN (Amazon Resource Name)
output "state_bucket_arn" {
  description = "ARN of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

# Output the DynamoDB table name
output "lock_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_lock.name
}

# Output the DynamoDB table ARN
output "lock_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_lock.arn
}

# Output the AWS region
output "aws_region" {
  description = "AWS region where resources are created"
  value       = "us-east-1"
}

# =============================================================================
# IMPORTANT: Save these values!
# =============================================================================
# After running "terraform apply", copy these values.
# You'll need them for the compute/ module to configure the remote backend.
#
# Example backend configuration (for compute/main.tf):
#
# terraform {
#   backend "s3" {
#     bucket         = "<state_bucket_name from above>"
#     key            = "compute/terraform.tfstate"
#     region         = "<aws_region from above>"
#     encrypt        = true
#     dynamodb_table = "<lock_table_name from above>"
#   }
# }
