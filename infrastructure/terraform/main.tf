# Terraform Configuration
# Infrastructure as Code برای MS Neuroplatform

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
  
  backend "s3" {
    bucket = "ms-neuroplatform-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

# ============================================================================
# Variables
# ============================================================================

variable "environment" {
  description = "Environment (staging, production)"
  type        = string
  default     = "staging"
}

variable "deployment_color" {
  description = "Deployment color for blue-green (blue, green)"
  type        = string
  default     = "blue"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# ============================================================================
# Providers
# ============================================================================

provider "aws" {
  region = var.region
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# ============================================================================
# VPC
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "ms-neuroplatform-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ms-neuroplatform-igw-${var.environment}"
  }
}

# ============================================================================
# Subnets
# ============================================================================

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "ms-neuroplatform-public-${count.index + 1}-${var.environment}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "ms-neuroplatform-private-${count.index + 1}-${var.environment}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# ECS Cluster
# ============================================================================

resource "aws_ecs_cluster" "main" {
  name = "ms-neuroplatform-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
  }
}

# ============================================================================
# ECS Task Definitions
# ============================================================================

resource "aws_ecs_task_definition" "user_management" {
  family                   = "user-management-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([
    {
      name  = "user-management"
      image = "${var.docker_username}/user-management:latest"
      
      portMappings = [
        {
          containerPort = 8001
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/user-management-${var.environment}"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ============================================================================
# ECS Services
# ============================================================================

resource "aws_ecs_service" "user_management" {
  name            = "user-management-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.user_management.arn
  desired_count   = var.environment == "production" ? 3 : 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.user_management.arn
    container_name   = "user-management"
    container_port   = 8001
  }

  tags = {
    Environment = var.environment
  }
}

# ============================================================================
# Application Load Balancer
# ============================================================================

resource "aws_lb" "main" {
  name               = "ms-neuroplatform-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production"

  tags = {
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "user_management" {
  name     = "user-management-${var.environment}"
  port     = 8001
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.user_management.arn
  }
}

# ============================================================================
# Security Groups
# ============================================================================

resource "aws_security_group" "alb" {
  name        = "ms-neuroplatform-alb-${var.environment}"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
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
    Name = "ms-neuroplatform-alb-${var.environment}"
  }
}

resource "aws_security_group" "ecs" {
  name        = "ms-neuroplatform-ecs-${var.environment}"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "From ALB"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ms-neuroplatform-ecs-${var.environment}"
  }
}

# ============================================================================
# RDS (PostgreSQL)
# ============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "ms-neuroplatform-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "ms-neuroplatform-db-subnet-${var.environment}"
  }
}

resource "aws_db_instance" "main" {
  identifier             = "ms-neuroplatform-${var.environment}"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = var.environment == "production" ? "db.t3.medium" : "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  db_name                = "ms_neuroplatform"
  username               = "postgres"
  password               = var.db_password
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  skip_final_snapshot    = var.environment != "production"

  tags = {
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "ms-neuroplatform-rds-${var.environment}"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = {
    Name = "ms-neuroplatform-rds-${var.environment}"
  }
}

# ============================================================================
# Outputs
# ============================================================================

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "DNS name of the load balancer"
}

output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

