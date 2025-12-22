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

---

## 7. Step-by-Step Deployment (First Time)

### 1) Configure AWS CLI
```bash
aws configure
aws sts get-caller-identity
```

### 2) Create SSM Parameters (Secrets)
Create SecureString parameters for every value in `backend/.env`:
```bash
aws ssm put-parameter --name "/waexpense/dev/JWT_SECRET_KEY" --type "SecureString" --value "..." --overwrite
```
Repeat for all secrets and note the ARNs.

### 3) Configure Terraform
```bash
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars`:
- Fill `aws_region`, `environment`, and DB credentials.
- Add `secret_env_parameters` with the SSM ARNs.
- (Optional) enable HTTPS and access logs if you have an ACM cert.

### 4) Provision Infrastructure
```bash
terraform init
terraform plan
terraform apply
```
Capture outputs: `alb_dns_name`, `ecr_backend_repo`, `frontend_bucket`.

### 5) Build + Push Backend Image
```bash
cd ../../..
BACKEND_REPO=<ecr_backend_repo_from_tf_output>
docker build -f backend/Dockerfile -t $BACKEND_REPO:v1 .
docker tag $BACKEND_REPO:v1 $BACKEND_REPO:latest
docker push $BACKEND_REPO:v1
docker push $BACKEND_REPO:latest
```

### 6) Deploy Backend to ECS
```bash
aws ecs update-service \
  --cluster waexpense-dev-cluster \
  --service waexpense-dev-svc \
  --force-new-deployment \
  --region us-east-1
```

### 7) Build + Export Frontend
```bash
cd frontend/nextjs-app
export NEXT_PUBLIC_API_BASE=http://<alb_dns_name>
npm ci
npm run build
npm run export
```

### 8) Upload Frontend to S3
```bash
aws s3 sync frontend/nextjs-app/out/ s3://<frontend_bucket>/ --delete
```

### 9) Validate
```bash
curl http://<alb_dns_name>/health
```
Open the S3 website endpoint (or CloudFront URL) and verify login works.

---

## 8. Troubleshooting Notes (From This Deployment)

### Terraform + AWS Access
- **STS `SignatureDoesNotMatch`**: AWS credentials invalid or wrong region; re-run `aws configure` and verify `aws sts get-caller-identity` works.
- **S3/DNS errors (`no such host`)**: local DNS/network issue; fix connectivity, then `terraform state push errored.tfstate`.
- **DynamoDB lock error**: lock table must have partition key `LockID` (string). Recreate the table with correct schema.
- **ECR repo already exists**: import existing repos into state:  
  `terraform import aws_ecr_repository.backend waexpense-dev-backend`  
  `terraform import aws_ecr_repository.frontend waexpense-dev-frontend`
- **RDS engine version unavailable**: use a supported version in your region (e.g., `15.3` in us-east-1).

### ECS + IAM / Secrets
- **SSM AccessDenied during task start**: ECS uses the **execution role** to fetch secrets at startup. Grant `ssm:GetParameters` to the execution role (not just the task role).
- **Missing env var (e.g., `JWT_ALGORITHM`)**: SSM parameter names are case-sensitive; ensure your secret key name is uppercase and matches the env var.
- **`psycopg2` missing**: add `psycopg2-binary` to `backend/requirements.txt`, rebuild and redeploy.

### Docker Build/Push
- **Docker build fails to find `backend/app`**: run `docker build` from repo root so `backend/` is in context.
- **`app.db` not found during build**: removed from Dockerfile since DB file isn’t tracked.
- **Push fails with broken pipe**: network/proxy issue; retry or use another network/CI to push.
- **`latest` tag missing**: tag `latest` in workflow so ECS pulls latest by default.

### Frontend (Next.js → S3)
- **`npm run export` missing**: add `"export": "next export"` to `package.json`.
- **GitHub Actions cache error**: commit `frontend/nextjs-app/package-lock.json` or remove cache step.
- **S3 403 AccessDenied**: disable block public access for bucket and add a public read bucket policy.
- **S3 404 NoSuchKey on `/login`**: S3 doesn’t rewrite routes; use trailing slash or add `next.config.js` with `output: "export"` and `trailingSlash: true`, then re-export.
- **Sync error “Unknown options: /”**: `FRONTEND_BUCKET` secret empty; add guard and set secret.

### HTTPS + Webhook
- **WhatsApp webhook verification fails**: requires HTTPS; ALB HTTP URL won’t pass. Use CloudFront default HTTPS domain or a custom domain + ACM cert.
- **CloudFront default HTTPS**: set ALB as origin, allow all methods, caching disabled, use `https://<cloudfront-domain>/webhook`.
