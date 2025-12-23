terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, length(var.public_subnet_cidrs))
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.2"

  name               = local.name_prefix
  cidr               = var.vpc_cidr
  azs                = local.azs
  private_subnets    = var.private_subnet_cidrs
  public_subnets     = var.public_subnet_cidrs
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.enable_nat_gateway

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# ECR repositories for backend and optional frontend containers
resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_iam_policy_document" "lambda_ecr_pull" {
  statement {
    sid = "LambdaEcrPull"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability"
    ]
  }
}

resource "aws_ecr_repository_policy" "backend_lambda_pull" {
  repository = aws_ecr_repository.backend.name
  policy     = data.aws_iam_policy_document.lambda_ecr_pull.json
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name_prefix}-frontend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Buckets
resource "aws_s3_bucket" "frontend" {
  bucket = var.frontend_bucket_name != "" ? var.frontend_bucket_name : "${local.name_prefix}-frontend"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "receipts" {
  bucket = "${local.name_prefix}-receipts"
}

resource "aws_s3_bucket_public_access_block" "receipts" {
  bucket                  = aws_s3_bucket.receipts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# RDS
resource "aws_db_subnet_group" "this" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "db" {
  name        = "${local.name_prefix}-db-sg"
  description = "DB access from ECS"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda-sg"
  description = "Lambda access to RDS and VPC endpoints"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "vpc_endpoints" {
  name        = "${local.name_prefix}-endpoints-sg"
  description = "Allow Lambda to reach VPC endpoints"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}

resource "aws_security_group_rule" "db_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  description              = "ECS to DB"
  security_group_id        = aws_security_group.db.id
  source_security_group_id = aws_security_group.lambda.id
}

resource "aws_security_group_rule" "db_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.db.id
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_db_instance" "this" {
  identifier_prefix      = "${local.name_prefix}-pg"
  engine                 = "postgres"
  engine_version         = "17.5"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  username               = var.db_username
  password               = var.db_password
  db_name                = var.db_name
  port                   = 5432
  skip_final_snapshot    = true
  deletion_protection    = false
  publicly_accessible    = false
}

# Serverless backend: API Gateway + Lambda + SQS
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_vpc" {
  name               = "${local.name_prefix}-lambda-vpc"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_basic" {
  role       = aws_iam_role.lambda_vpc.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_network" {
  role       = aws_iam_role.lambda_vpc.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role" "lambda_public" {
  name               = "${local.name_prefix}-lambda-public"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_public_basic" {
  role       = aws_iam_role.lambda_public.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_sqs_queue" "inbound" {
  name = "${local.name_prefix}-${var.inbound_queue_name}"
}

resource "aws_sqs_queue" "outbound" {
  name = "${local.name_prefix}-${var.outbound_queue_name}"
}

resource "aws_iam_role_policy" "lambda_vpc_sqs" {
  name = "${local.name_prefix}-lambda-vpc-sqs"
  role = aws_iam_role.lambda_vpc.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.inbound.arn,
          aws_sqs_queue.outbound.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_public_sqs" {
  name = "${local.name_prefix}-lambda-public-sqs"
  role = aws_iam_role.lambda_public.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.inbound.arn,
          aws_sqs_queue.outbound.arn
        ]
      }
    ]
  })
}

data "aws_ssm_parameter" "lambda_secrets" {
  for_each = var.secret_env_parameters
  name     = each.value
}

locals {
  lambda_secrets = { for key, value in data.aws_ssm_parameter.lambda_secrets : key => value.value }
  base_env = merge(
    {
      APP_NAME                 = var.app_name
      DEBUG                    = tostring(var.debug)
      DATABASE_URL             = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${var.db_name}"
      WHATSAPP_PHONE_NUMBER_ID = var.whatsapp_phone_number_id
      EXTERNAL_TEXT_PARSER_URL = var.external_text_parser_url
      LOGIN_CODE_EXPIRY_MINUTES = tostring(var.login_code_expiry_minutes)
      INBOUND_QUEUE_URL        = aws_sqs_queue.inbound.id
      OUTBOUND_QUEUE_URL       = aws_sqs_queue.outbound.id
    },
    var.plain_env_overrides,
    local.lambda_secrets
  )
}

resource "aws_lambda_function" "backend_api" {
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda_vpc.arn
  package_type  = "Image"
  image_uri     = var.backend_lambda_image != "" ? var.backend_lambda_image : "${aws_ecr_repository.backend.repository_url}:latest"
  memory_size   = var.backend_lambda_memory
  timeout       = var.backend_lambda_timeout

  vpc_config {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [aws_security_group.lambda.id]
  }

  image_config {
    command = ["app.lambda_handlers.api.lambda_handler"]
  }

  environment {
    variables = local.base_env
  }
}

resource "aws_lambda_function" "expense_worker" {
  function_name = "${local.name_prefix}-worker"
  role          = aws_iam_role.lambda_vpc.arn
  package_type  = "Image"
  image_uri     = var.backend_lambda_image != "" ? var.backend_lambda_image : "${aws_ecr_repository.backend.repository_url}:latest"
  memory_size   = var.backend_lambda_memory
  timeout       = var.backend_lambda_timeout

  vpc_config {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [aws_security_group.lambda.id]
  }

  image_config {
    command = ["app.lambda_handlers.expense_worker.lambda_handler"]
  }

  environment {
    variables = local.base_env
  }
}

resource "aws_lambda_function" "webhook_ingest" {
  function_name = "${local.name_prefix}-webhook"
  role          = aws_iam_role.lambda_public.arn
  package_type  = "Image"
  image_uri     = var.backend_lambda_image != "" ? var.backend_lambda_image : "${aws_ecr_repository.backend.repository_url}:latest"
  memory_size   = var.backend_lambda_memory
  timeout       = var.backend_lambda_timeout

  image_config {
    command = ["app.lambda_handlers.webhook_ingest.lambda_handler"]
  }

  environment {
    variables = local.base_env
  }
}

resource "aws_lambda_function" "outbound_sender" {
  function_name = "${local.name_prefix}-outbound"
  role          = aws_iam_role.lambda_public.arn
  package_type  = "Image"
  image_uri     = var.backend_lambda_image != "" ? var.backend_lambda_image : "${aws_ecr_repository.backend.repository_url}:latest"
  memory_size   = var.backend_lambda_memory
  timeout       = var.backend_lambda_timeout

  image_config {
    command = ["app.lambda_handlers.outbound_sender.lambda_handler"]
  }

  environment {
    variables = local.base_env
  }
}

resource "aws_lambda_event_source_mapping" "inbound_worker" {
  event_source_arn = aws_sqs_queue.inbound.arn
  function_name    = aws_lambda_function.expense_worker.arn
}

resource "aws_lambda_event_source_mapping" "outbound_sender" {
  event_source_arn = aws_sqs_queue.outbound.arn
  function_name    = aws_lambda_function.outbound_sender.arn
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "backend" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "webhook" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.webhook_ingest.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "webhook_get" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "GET /webhook"
  target    = "integrations/${aws_apigatewayv2_integration.webhook.id}"
}

resource "aws_apigatewayv2_route" "webhook_post" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "POST /webhook"
  target    = "integrations/${aws_apigatewayv2_integration.webhook.id}"
}

resource "aws_apigatewayv2_route" "backend_root" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "backend_proxy" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "backend_api" {
  statement_id  = "AllowApiGatewayBackend"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}

resource "aws_lambda_permission" "webhook_api" {
  statement_id  = "AllowApiGatewayWebhook"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_ingest.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}

resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
}
