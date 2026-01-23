resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  #   # Prevent accidental deletion of this important bucket!
  #   # In production, set this to true

  force_destroy = true # Set to false in production!

  tags = {
    Name        = "Terraform State Bucket"
    Purpose     = "terraform-state"
    Environment = var.environment
  }
}

# Versioning keeps every version of your state file.
# If something goes wrong, you can recover a previous version!

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# State files contain sensitive information (passwords, keys, etc.)
# Encryption protects this data at rest in S3.

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      # AES256 is the simplest encryption option
      # For higher security, use "aws:kms" with a KMS key
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access to the bucket
# State files should NEVER be public!
# This setting prevents accidental public exposure.

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
