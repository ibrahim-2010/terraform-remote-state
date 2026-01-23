resource "aws_security_group" "ssh_access" {
  name        = "${var.project_name}-${var.environment}-ssh"
  description = "Security group allowing SSH access"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-ssh"
    Environment = var.environment
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.ssh_access.id

  description = "Allow SSH from anywhere"
  ip_protocol = "tcp"
  from_port   = 22
  to_port     = 22

  # WARNING: 0.0.0.0/0 allows SSH from anywhere!
  # For better security, replace with your IP: "YOUR.IP.ADDRESS.HERE/32"
  cidr_ipv4 = "203.0.113.45/32"

  tags = {
    Name = "Allow SSH"
  }
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.ssh_access.id

  description = "Allow all outbound traffic"
  ip_protocol = "-1" # -1 means all protocols

  cidr_ipv4 = "0.0.0.0/0" # Allow to anywhere

  tags = {
    Name = "Allow all outbound"
  }
}
