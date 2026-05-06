terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ─── VPC + NETWORKING (this is the fix) ──────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "smart-devops-platform-vpc"
    Project = "smart-devops-platform"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "smart-devops-platform-igw"
    Project = "smart-devops-platform"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name    = "smart-devops-platform-subnet"
    Project = "smart-devops-platform"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name    = "smart-devops-platform-rt"
    Project = "smart-devops-platform"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ─── SECURITY GROUP ──────────────────────────────────────────────────────────

resource "aws_security_group" "app_sg" {
  name        = "smart-devops-platform-sg"
  description = "Security group for Smart DevOps Platform"
  vpc_id      = aws_vpc.main.id   # ← now explicitly set

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Application Port"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "smart-devops-platform-sg"
    Project = "smart-devops-platform"
    Env     = "dev"
  }
}

# ─── SSH KEY ─────────────────────────────────────────────────────────────────

resource "aws_key_pair" "deployer" {
  key_name   = "smart-devops-platform-key"
  public_key = file(var.public_key_path)

  tags = {
    Name    = "smart-devops-platform-key"
    Project = "smart-devops-platform"
  }
}

# ─── EC2 INSTANCE ────────────────────────────────────────────────────────────

resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  subnet_id              = aws_subnet.public.id           # ← placed in our subnet
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io python3-pip git curl
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ubuntu
    mkdir -p /opt/ai-engine /opt/scripts /opt/dashboard /var/log/app
    chown -R ubuntu:ubuntu /opt/ai-engine /opt/scripts /opt/dashboard /var/log/app
  EOF

  tags = {
    Name    = "smart-devops-platform-server"
    Project = "smart-devops-platform"
    Env     = "dev"
  }
}

# ─── ELASTIC IP ──────────────────────────────────────────────────────────────

resource "aws_eip" "app_eip" {
  instance = aws_instance.app_server.id
  domain   = "vpc"

  tags = {
    Name    = "smart-devops-platform-eip"
    Project = "smart-devops-platform"
  }
}
