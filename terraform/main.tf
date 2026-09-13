terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "app" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "security-automation-vpc"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.app.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "security-automation-public-a"
  }
}


resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.app.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "security-automation-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.app.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "security-automation-private-b"
  }
}

resource "aws_security_group" "alb" {
  name        = "security-automation-alb"
  description = "Restricted ingress for application load balancer"
  vpc_id      = aws_vpc.app.id

  ingress {
    description = "HTTPS from trusted network only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    description = "Allow outbound traffic within the application VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = {
    Name = "security-automation-alb"
  }
}

resource "aws_security_group" "app" {
  name        = "security-automation-app"
  description = "Application security group"
  vpc_id      = aws_vpc.app.id

  ingress {
    description     = "Application traffic only from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow outbound traffic within the application VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = {
    Name = "security-automation-app"
  }
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "security-automation-assignment/app-secrets"
  description             = "Application secrets for the Security Automation assignment"
  recovery_window_in_days = 7

  tags = {
    Name = "security-automation-app-secrets"
  }
}

resource "aws_ecs_cluster" "app" {
  name = "security-automation-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_iam_role" "ecs_execution" {
  name = "security-automation-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "app" {
  family                   = "security-automation-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([{
    name      = "security-automation-app"
    image     = var.app_image
    essential = true

    cpu    = 256
    memory = 512

    user = "appuser"

    readonlyRootFilesystem = true

    linuxParameters = {
      capabilities = {
        drop = ["ALL"]
      }

      initProcessEnabled = true
    }

    secrets = [
      {
        name      = "SECRET_KEY"
        valueFrom = var.secret_arn
      }
    ]

    portMappings = [
      {
        containerPort = 8000
        protocol      = "tcp"
      }
    ]
  }])
}

resource "aws_ecs_service" "app" {
  name            = "security-automation-app"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.app.arn

  desired_count = 1
  launch_type   = "FARGATE"

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "security-automation-app"
    container_port   = 8000
  }

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]

    security_groups = [
      aws_security_group.app.id
    ]

    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

resource "aws_lb" "app" {
  name               = "security-automation-alb"
  internal           = true
  load_balancer_type = "application"
  drop_invalid_header_fields = true

  subnets = [
  aws_subnet.private_a.id,
  aws_subnet.private_b.id
]
  security_groups = [
    aws_security_group.alb.id
  ]
}

resource "aws_lb_target_group" "app" {
  name        = "security-automation-app"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.app.id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    port                = "8000"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"

  certificate_arn = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}