output "iam_user_name" {
  description = "Name of the IAM user"
  value       = aws_iam_user.terraform_deployer.name
}

output "iam_user_arn" {
  description = "ARN of the IAM user"
  value       = aws_iam_user.terraform_deployer.arn
}

output "access_key_id" {
  description = "Access Key ID for the IAM user"
  value       = aws_iam_access_key.terraform_deployer.id
}

output "secret_access_key" {
  description = "Secret Access Key for the IAM user (KEEP THIS SECRET!)"
  value       = aws_iam_access_key.terraform_deployer.secret
  sensitive   = true
}

#   terraform output -raw secret_access_key
#
# This will display the actual value.
# IMMEDIATELY copy it to a secure location (password manager, etc.)
