output "alb_dns_name" {
  description = "Public DNS for the API load balancer"
  value       = aws_lb.api.dns_name
}

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
