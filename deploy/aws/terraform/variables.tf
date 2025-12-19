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

variable "health_check_path" {
  description = "ALB health check path"
  type        = string
  default     = "/health"
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
