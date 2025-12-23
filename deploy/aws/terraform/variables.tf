variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "waexpense"
}

variable "environment" {
  description = "Environment name (dev/stage/prod)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.20.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = false
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDRs"
  type        = list(string)
  default     = ["10.20.0.0/24", "10.20.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of private subnet CIDRs"
  type        = list(string)
  default     = ["10.20.10.0/24", "10.20.11.0/24"]
}

variable "frontend_bucket_name" {
  description = "Optional override for the frontend hosting bucket"
  type        = string
  default     = ""
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_username" {
  description = "Database admin username"
  type        = string
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "waexpense"
}

variable "container_port" {
  description = "Container port exposed by FastAPI"
  type        = number
  default     = 8000
}


variable "backend_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Fargate task memory (MB)"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Number of backend tasks"
  type        = number
  default     = 1
}

variable "backend_image" {
  description = "Override container image URI for backend (default uses ECR repo + :latest)"
  type        = string
  default     = ""
}

variable "backend_lambda_image" {
  description = "Container image URI for backend Lambda functions"
  type        = string
  default     = ""
}

variable "backend_lambda_memory" {
  description = "Backend Lambda memory size (MB)"
  type        = number
  default     = 512
}

variable "backend_lambda_timeout" {
  description = "Backend Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "inbound_queue_name" {
  description = "SQS queue name for inbound webhook messages"
  type        = string
  default     = "inbound"
}

variable "outbound_queue_name" {
  description = "SQS queue name for outbound WhatsApp messages"
  type        = string
  default     = "outbound"
}

variable "app_name" {
  description = "APP_NAME value"
  type        = string
  default     = "WA Expense Tracker"
}

variable "debug" {
  description = "Enable FastAPI debug (false in production)"
  type        = bool
  default     = false
}


variable "external_text_parser_url" {
  description = "External parser endpoint"
  type        = string
  default     = ""
}

variable "whatsapp_phone_number_id" {
  description = "WhatsApp Cloud API phone number id"
  type        = string
}

variable "login_code_expiry_minutes" {
  description = "Expiry minutes for login codes"
  type        = number
  default     = 10
}

variable "plain_env_overrides" {
  description = "Map of extra plaintext environment variables to inject"
  type        = map(string)
  default     = {}
}

variable "secret_env_parameters" {
  description = "Map of ENV_VAR_NAME => SSM parameter ARN (SecureString)"
  type        = map(string)
  default     = {}
}

variable "lambda_text_parser_name" {
  description = "Lambda function name for the text parser"
  type        = string
  default     = "waexpense-text-parser"
}

variable "lambda_text_parser_role_name" {
  description = "Existing IAM role name for the text parser Lambda"
  type        = string
  default     = "waexpense-text-parser-role"
}

variable "lambda_text_parser_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_text_parser_handler" {
  description = "Lambda handler entrypoint"
  type        = string
  default     = "handler.lambda_handler"
}

variable "lambda_text_parser_memory" {
  description = "Lambda memory size (MB)"
  type        = number
  default     = 256
}

variable "lambda_text_parser_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 20
}

variable "lambda_text_parser_env" {
  description = "Environment variables for the text parser Lambda"
  type        = map(string)
  default     = {}
}

variable "enable_bedrock_policy" {
  description = "Attach Bedrock invoke permissions to the Lambda role"
  type        = bool
  default     = true
}

variable "bedrock_model_arns" {
  description = "List of Bedrock model ARNs allowed for InvokeModel"
  type        = list(string)
  default     = ["*"]
}

variable "enable_text_parser_api" {
  description = "Provision an HTTP API Gateway for the text parser Lambda"
  type        = bool
  default     = true
}
