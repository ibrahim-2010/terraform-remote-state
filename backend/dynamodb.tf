resource "aws_dynamodb_table" "terraform_lock" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST" 


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
