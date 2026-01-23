terraform {
  required_version = ">= 1.2"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }

  # ===========================================================================
  # TODO: Configure the S3 Remote Backend
  # ===========================================================================
  # Uncomment this block AFTER creating the backend resources!
  #
  # Replace the values with outputs from the backend/ module:
  #   - bucket: from output "state_bucket_name"
  #   - dynamodb_table: from output "lock_table_name"
  #   - region: from output "aws_region"
  #
  backend "s3" {
    bucket         = "terraform-state-dev-2669aeb5" # Your bucket name
    key            = "compute/terraform.tfstate"    # Path in the bucket
    region         = "us-east-1"                    # AWS region
    encrypt        = true                           # Enable encryption
    dynamodb_table = "terraform-state-lock"         # Lock table name

  }
}


# Provider Configuration
provider "aws" {
  region = "us-east-1"

  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      s3       = var.localstack_endpoint
      dynamodb = var.localstack_endpoint
      iam      = var.localstack_endpoint
      ec2      = var.localstack_endpoint
      sts      = var.localstack_endpoint
    }
  }

  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_requesting_account_id  = var.use_localstack

  access_key = var.use_localstack ? "test" : null
  secret_key = var.use_localstack ? "test" : null

  default_tags {
    tags = var.tags
  }
}

# Get the latest Amazon Linux 2 AMI , I used ubuntu cos Linux 2 is not free eligible
data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Get a subnet in the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
