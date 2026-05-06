variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "public_key_path" {
  description = "Path to your SSH public key file"
  type        = string
  # Windows users: change this to your full path, e.g.:
  # default = "C:/Users/kanga/.ssh/id_rsa.pub"
  default     = "C:/Users/kanga/.ssh/id_rsa.pub"
}

variable "allowed_cidr" {
  description = "Your IP address for SSH access (find at https://whatismyip.com, add /32)"
  type        = string
  default     = "0.0.0.0/0"   # ← Change to YOUR_IP/32 for security, e.g. "103.45.67.89/32"
}
