resource "aws_iam_user" "terraform_deployer" {
  name = "terraform-deployer"
  path = "/system/" # Organizational path (optional)

  tags = {
    Name        = "Terraform Deployer"
    Purpose     = "terraform-automation"
    Description = "User for running Terraform commands"
  }
}


# These keys allow programmatic access to AWS.
# You'll use these to configure AWS CLI or Terraform.
#
resource "aws_iam_access_key" "terraform_deployer" {
  user = aws_iam_user.terraform_deployer.name
}


resource "aws_iam_user_policy_attachment" "terraform_deployer" {
  user       = aws_iam_user.terraform_deployer.name
  policy_arn = aws_iam_policy.terraform_state_access.arn
}
