output "frontend_bucket" {
  description = "S3 bucket for hosting the frontend build"
  value       = aws_s3_bucket.frontend.bucket
}

output "receipts_bucket" {
  description = "S3 bucket storing receipt uploads"
  value       = aws_s3_bucket.receipts.bucket
}

output "ecr_backend_repo" {
  description = "ECR repository URL for the backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repo" {
  description = "ECR repository URL for the frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "db_address" {
  description = "RDS endpoint for connecting from migration jobs"
  value       = aws_db_instance.this.address
}

output "backend_api_endpoint" {
  description = "HTTP API Gateway endpoint for the backend"
  value       = aws_apigatewayv2_api.backend.api_endpoint
}

output "text_parser_lambda_name" {
  description = "Lambda function name for the text parser"
  value       = aws_lambda_function.text_parser.function_name
}

output "text_parser_api_endpoint" {
  description = "HTTP API endpoint for the text parser Lambda"
  value       = var.enable_text_parser_api ? aws_apigatewayv2_api.text_parser[0].api_endpoint : null
}
