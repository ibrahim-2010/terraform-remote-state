output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web_server.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.web_server.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.web_server.private_ip
}

output "key_pair_name" {
  description = "Name of the SSH key pair"
  value       = aws_key_pair.deployer.key_name
}

output "private_key_file" {
  description = "Path to the private key file"
  value       = local_file.private_key.filename
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.ssh_access.id
}

# =============================================================================
# SSH Connection Command
# =============================================================================
# This is the most useful output - a ready-to-use SSH command!
#
# output "ssh_command" {
#   description = "Command to SSH into the EC2 instance"
#   value       = "ssh -i ${local_file.private_key.filename} ec2-user@${aws_instance.web_server.public_ip}"
# }

# =============================================================================
# After running terraform apply, connect with:
# =============================================================================
#
# Option 1: Use the ssh_command output
#   terraform output -raw ssh_command
#   # Copy and run the command
#
# Option 2: Manual command
#   ssh -i compute/private-key.pem ec2-user@<public_ip>
#
# Option 3: If using Elastic IP
#   ssh -i compute/private-key.pem ec2-user@<elastic_ip>
#
# First time connecting? You'll see a fingerprint warning.
# Type "yes" to continue.
