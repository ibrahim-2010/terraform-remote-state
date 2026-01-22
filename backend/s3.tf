resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  
  force_destroy = true

  tags = {
    Name        = "Terraform State Bucket"
    Purpose     = "terraform-state"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

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

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
