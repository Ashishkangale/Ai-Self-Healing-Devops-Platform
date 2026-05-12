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
  default     = "C:/Users/kanga/.ssh/id_rsa.pub"
}

variable "allowed_cidr" {
  description = "Your IP address for SSH access (find at https://whatismyip.com, add /32)"
  type        = string
  default     = "0.0.0.0/0"   
}
