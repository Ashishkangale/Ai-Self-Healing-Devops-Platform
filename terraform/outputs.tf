# ─────────────────────────────────────────────────────────────────────────────
# Terraform Outputs — printed after `terraform apply`
# ─────────────────────────────────────────────────────────────────────────────

output "ec2_public_ip" {
  description = "Elastic IP of the EC2 instance"
  value       = aws_eip.app_eip.public_ip
}

output "ec2_instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.app_server.id
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.app_eip.public_ip}"
}

output "app_url" {
  description = "Application URL"
  value       = "http://${aws_eip.app_eip.public_ip}:8080"
}

output "health_check_url" {
  description = "Health check endpoint"
  value       = "http://${aws_eip.app_eip.public_ip}:8080/health"
}
