# main.tf

terraform {
  backend "s3" {
    bucket = "hospital-erp-tfstate"       # 생성한 S3 버킷 이름
    key    = "terraform.tfstate"
    region = "ap-northeast-2"
  }
}

locals {
  app_name = "hospital-erp"
  region   = "ap-northeast-2"
  # 예: hospital-erp-dev, hospital-erp-prod
  full_name = "${local.app_name}-${var.environment}"
}

provider "aws" {
  region = local.region
}

# 내 계정 ID 조회 (IAM 권한 설정용)
data "aws_caller_identity" "current" {}

# 1. 필수 리소스 (로그, ECR, 클러스터)
resource "aws_cloudwatch_log_group" "main" {
  name = "/ecs/${local.full_name}"
}

resource "aws_ecr_repository" "repo" {
  name         = local.full_name
  force_delete = true
}

resource "aws_ecs_cluster" "main" {
  name = "${local.full_name}-cluster"
}

# 2. IAM Role & Policy (Execution Role)
resource "aws_iam_role" "exec" {
  name = "${local.full_name}-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "exec_basic" {
  role       = aws_iam_role.exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# [중요] ECS가 파라미터 스토어의 비밀번호를 읽을 수 있는 권한 추가
resource "aws_iam_role_policy" "password_access" {
  name = "password-access"
  role = aws_iam_role.exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          "arn:aws:ssm:${local.region}:${data.aws_caller_identity.current.account_id}:parameter/hospital-erp/*"
        ]
      }
    ]
  })
}

# 3. 보안 그룹 (Security Groups)
resource "aws_security_group" "alb" {
  name   = "${local.full_name}-alb-sg"
  vpc_id = var.vpc_id # 변수 사용

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name   = "${local.full_name}-ecs-sg"
  vpc_id = var.vpc_id # 변수 사용

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. 로드 밸런서 (ALB)
resource "aws_lb" "main" {
  name               = "${local.full_name}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids # 변수 사용
}

resource "aws_lb_target_group" "main" {
  name        = "${local.full_name}-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id # 변수 사용

  health_check {
    path                = "/admin/login/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# 5. ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = local.full_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu     # 변수 사용
  memory                   = var.memory  # 변수 사용
  execution_role_arn       = aws_iam_role.exec.arn

  container_definitions = jsonencode([
    {
      name  = "django-app"
      image = aws_ecr_repository.repo.repository_url
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      secrets = [
        # 환경(var.environment)에 따라 파라미터 스토어 경로 결정
        { name = "DJANGO_SECRET_KEY", valueFrom = "/hospital-erp/${var.environment}/django-secret-key" },
        { name = "DATABASE_URL",      valueFrom = "/hospital-erp/${var.environment}/database-url" }
      ]
      environment = [
        { name = "DEBUG", value = var.environment == "prod" ? "0" : "1" },
        { name = "ALLOWED_HOSTS" , value = "*" }
      ]
    }
  ])
}

# 6. ECS Service
resource "aws_ecs_service" "main" {
  name            = "${local.full_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids # 변수 사용
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "django-app"
    container_port   = 8000
  }
}

output "website_url" {
  value = "http://${aws_lb.main.dns_name}"
}
