# AWS Deployment Guide

This document describes a fully automated path to deploy the WhatsApp Expense Tracker to AWS using Terraform for infrastructure and GitHub Actions for CI/CD.

---

## 1. Target Architecture

| Component | AWS Service | Notes |
|-----------|-------------|-------|
| FastAPI backend | ECS Fargate (behind an Application Load Balancer) | Container image stored in ECR. Auto scaled and logs shipped to CloudWatch. |
| PostgreSQL database | Amazon RDS | Single-AZ for MVP, provisioned inside private subnets. |
| Frontend (Next.js) | S3 static hosting + CloudFront CDN *(or ECS container if you prefer SSR)* | This guide assumes static hosting; the provided Dockerfile still supports containerized runtime for flexibility. |
| Object storage | S3 receipts bucket | Stores uploaded receipt images. |
| Secrets | AWS Systems Manager Parameter Store (SecureString) | Referenced from ECS task definitions. |
| Observability | CloudWatch Logs + standard AWS metrics | Container logs available under `/aws/ecs/<cluster>`. |

All resources live inside a dedicated VPC with public subnets (for ALB/NAT) and private subnets (for ECS/RDS). Terraform automates the network layout, security groups, ECS, RDS, S3, and IAM roles.

---

## 2. Prerequisites

1. **AWS account + IAM user/role** with permissions for VPC, ECS, IAM, RDS, S3, CloudWatch, Parameter Store, and CloudFront.
2. **Tools installed locally or in CI**: `awscli v2`, `terraform >= 1.5`, `docker`, `npm`, and `python3`.
3. **Container Registry**: Terraform creates ECR repositories, but you must authenticate (`aws ecr get-login-password`) before pushing images.
4. **Secrets in Parameter Store**: create SecureString parameters for each sensitive env (JWT secret, WhatsApp tokens, parser API key, etc.). Example:
   ```bash
   aws ssm put-parameter \
     --name "/waexpense/prod/JWT_SECRET_KEY" \
     --type "SecureString" \
     --value "super-secret" \
     --overwrite
   ```
   Repeat for every key listed in `backend/.env`.

---

## 3. Infrastructure as Code

The Terraform stack lives in `deploy/aws/terraform`. It provisions:

- VPC, subnets, NAT, and security groups.
- ECS cluster + Fargate service for the backend API.
- RDS PostgreSQL instance (single AZ).
- S3 buckets for the static frontend and receipt storage.
- ECR repositories for backend & frontend images.
- CloudWatch log groups.

### Usage

```bash
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

Key outputs:

- `alb_dns_name`: public URL for the API.
- `frontend_bucket`: S3 bucket to upload the Next.js build artifacts.
- `receipts_bucket`: bucket for receipt uploads.
- `ecr_backend_repo` / `ecr_frontend_repo`: URIs to push Docker images.

---

## 4. Application Packaging

Two Dockerfiles were added:

- `backend/Dockerfile`: builds the FastAPI service.
- `frontend/nextjs-app/Dockerfile`: builds the production-ready Next.js app (useful for SSR deployments or preview environments).

For the recommended S3 + CloudFront flow, run:

```bash
cd frontend/nextjs-app
npm ci
npm run build
npm run export        # outputs to out/
aws s3 sync out/ s3://<frontend_bucket>/ --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

(Terraform can optionally create the CloudFront distribution; adjust the module when ready.)

---

## 5. CI/CD Automation

Two GitHub Actions workflows (see `.github/workflows`) automate deployments:

1. **`deploy-backend.yml`**
   - Triggers on pushes to `main` touching `backend/**`.
   - Builds and pushes the backend image to ECR.
   - Updates the running ECS service to pull the new tag (via `aws ecs update-service --force-new-deployment`).

2. **`deploy-frontend.yml`**
   - Triggers on pushes to `main` touching `frontend/**`.
   - Builds the Next.js app, syncs the static export to the frontend S3 bucket, and optionally invalidates CloudFront.

Configure repository secrets (Settings → Secrets and variables → Actions):

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | IAM credentials used by GitHub Actions. |
| `AWS_REGION` | Target region (e.g., `us-east-1`). |
| `ECR_BACKEND_REPO` | Output from Terraform. |
| `ECR_FRONTEND_REPO` | Output from Terraform. |
| `FRONTEND_BUCKET` | Output from Terraform. |
| `CLOUDFRONT_DISTRIBUTION_ID` *(optional)* | If using CloudFront. |

> For Terraform deployments from CI, add an additional workflow that runs `terraform plan/apply` with remote state (e.g., S3 backend) and uses an assumed IAM role. That workflow is not included here because many teams prefer to run infrastructure changes manually.

---

## 6. Deployment Flow Summary

1. **Provision infra**: run Terraform once per environment (dev/stage/prod).
2. **Seed parameters**: store all secrets in SSM Parameter Store and note their ARNs for Terraform variables.
3. **Build & push images**: let GitHub Actions or your build server push to the Terraform-created ECR repositories.
4. **Deploy backend**: ECS picks up the new image tag and refreshes containers.
5. **Deploy frontend**: export the Next.js build to S3 and invalidate CDN caches.
6. **Rotate secrets**: update SSM parameters and redeploy ECS to pick up new values.

Following this process ensures deployments are reproducible, reviewable, and require no manual clicking in the AWS console.
