# This uses Terraform's tls provider to generate a secure key pair.
# RSA 4096-bit is a good secure choice.

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# This uploads the public key to AWS so EC2 can use it.

resource "aws_key_pair" "deployer" {
  key_name   = "${var.project_name}-${var.environment}-key"
  public_key = tls_private_key.ssh.public_key_openssh

  tags = {
    Name        = "${var.project_name}-${var.environment}-key"
    Environment = var.environment
  }
}


# IMPORTANT: The private key file must have restricted permissions (600)
# This means only you can read it - required by SSH!

resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/private-key.pem"
  file_permission = "0600" # Owner can read/write, no one else
}

# =============================================================================
# IMPORTANT: Add private-key.pem to .gitignore!
# =============================================================================
# Never commit private keys to Git!
# Add this line to your .gitignore:
#   *.pem
#   private-key.pem
