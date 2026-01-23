# SSH Key Pair - STARTER FILE
# ============================
# TODO: Create an SSH key pair for EC2 access!
#
# What is SSH?
#   - SSH = Secure Shell
#   - A way to securely connect to remote servers
#   - Uses encryption to protect your connection
#
# What is a Key Pair?
#   - Two related keys: Public and Private
#   - Public Key: Put on the server (safe to share)
#   - Private Key: Keep on your computer (NEVER share!)
#   - Like a lock and key - public key is the lock, private key opens it
#
# How it works:
#   1. Generate a key pair
#   2. Public key goes to EC2 (stored in ~/.ssh/authorized_keys)
#   3. Private key stays on your computer
#   4. When you connect, SSH uses your private key to prove identity
#
# Requirements:
#   1. Generate a new RSA key pair using tls_private_key
#   2. Create an AWS key pair from the public key
#   3. Save the private key to a local file
#   4. Set correct permissions on the private key file
#
# See README.md for detailed explanations!

# =============================================================================
# STEP 1: Generate SSH Key Pair
# =============================================================================
# TODO: Uncomment and create the SSH key pair
#
# This uses Terraform's tls provider to generate a secure key pair.
# RSA 4096-bit is a good secure choice.
#
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# =============================================================================
# STEP 2: Create AWS Key Pair
# =============================================================================
# TODO: Uncomment and create the AWS key pair
#
# This uploads the public key to AWS so EC2 can use it.
#
resource "aws_key_pair" "deployer" {
  key_name   = "${var.project_name}-${var.environment}-key"
  public_key = tls_private_key.ssh.public_key_openssh

  tags = {
    Name        = "${var.project_name}-${var.environment}-key"
    Environment = var.environment
  }
}

# =============================================================================
# STEP 3: Save Private Key to Local File
# =============================================================================
# TODO: Uncomment to save the private key locally
#
# IMPORTANT: The private key file must have restricted permissions (600)
# This means only you can read it - required by SSH!
#
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
