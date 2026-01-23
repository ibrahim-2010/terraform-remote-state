resource "aws_dynamodb_table" "terraform_lock" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST" # No need to set capacity, pay only for what you use
  hash_key     = "LockID"

  #   # IMPORTANT: The hash key MUST be named "LockID"
  #   # This is required by Terraform's S3 backend
  #   hash_key = "LockID"

  #   # Define the LockID attribute
  #   # Type "S" means String

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Lock Table"
    Purpose     = "terraform-lock"
    Environment = var.environment
  }
}
