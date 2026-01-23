resource "aws_instance" "web_server" {
  # Use the AMI we found in main.tf, or a specific AMI ID
  ami           = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  tags = {
    Name = "terraform-state-dev"
  }

  # Use the first available subnet
  subnet_id = data.aws_subnets.default.ids[0]

  # Attach our SSH key pair
  key_name = aws_key_pair.deployer.key_name

  # Attach our security group
  vpc_security_group_ids = [aws_security_group.ssh_access.id]

  # Give the instance a public IP so we can SSH to it
  associate_public_ip_address = true

  # User data runs when the instance first boots
  # This installs some helpful tools
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y htop vim wget curl
    echo "Hello from Terraform!" > /home/ec2-user/welcome.txt
  EOF

  # Root volume configuration
  root_block_device {
    volume_size = 8     # GB
    volume_type = "gp2" # General Purpose SSD
    encrypted   = true  # Encrypt the volume
  }
}

#   tags = {
#     Name        = "${var.project_name}-${var.environment}-server"
#     Environment = var.environment
#   }
# }

# =============================================================================
# OPTIONAL: Elastic IP (Static Public IP)
# =============================================================================
# Without an Elastic IP, the public IP changes when you stop/start the instance.
# Elastic IP gives you a permanent public IP address.
#
# resource "aws_eip" "web_server" {
#   instance = aws_instance.web_server.id
#   domain   = "vpc"
#
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-eip"
#     Environment = var.environment
#   }
# }
