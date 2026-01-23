# This policy allows:
#   - Reading and writing to the S3 state bucket
#   - Reading and writing locks in DynamoDB

resource "aws_iam_policy" "terraform_state_access" {
  name        = "TerraformStateAccess"
  description = "Policy for accessing Terraform state in S3 and DynamoDB lock table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 Bucket Access
      {
        Sid    = "S3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",       # List objects in bucket
          "s3:GetBucketLocation" # Get bucket region
        ]
        # NOTE: Replace with your actual bucket ARN from backend outputs
        # Or use a variable: var.state_bucket_arn
        Resource = "arn:aws:s3:::terraform-state-dev-bf19b78d"
      },
      # S3 Object Access
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",   # Read state file
          "s3:PutObject",   # Write state file
          "s3:DeleteObject" # Delete old state versions
        ]
        # Allow access to all objects in the bucket
        Resource = "arn:aws:s3:::terraform-state-dev-bf19b78d"
      },
      # DynamoDB Lock Table Access
      {
        Sid    = "DynamoDBLockAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",   # Read lock status
          "dynamodb:PutItem",   # Create lock
          "dynamodb:DeleteItem" # Release lock
        ]
        # NOTE: Replace with your actual table ARN
        Resource = "arn:aws:dynamodb:us-east-1:985149164729:table/terraform-state-lock"
      }
    ]
  })

  tags = {
    Name    = "Terraform State Access Policy"
    Purpose = "terraform"
  }
}

resource "aws_iam_policy" "ec2_management" {
  name        = "TerraformEC2Management"
  description = "Policy for managing EC2 instances with Terraform"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EC2FullAccess"
        Effect = "Allow"
        Action = [
          "ec2:*" # Full EC2 access - restrict in production!
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach EC2 policy to user

resource "aws_iam_user_policy_attachment" "terraform_deployer_ec2" {
  user       = aws_iam_user.terraform_deployer.name
  policy_arn = aws_iam_policy.ec2_management.arn
}
