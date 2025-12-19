terraform {
  backend "s3" {
    bucket         = "waexpense-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "waexpense-terraform-locks"
    encrypt        = true
  }
}
