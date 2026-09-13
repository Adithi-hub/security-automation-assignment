variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "app_image" {
  description = "Container image for the application"
  type        = string
}

variable "secret_arn" {
  description = "ARN of the AWS Secrets Manager secret containing application secrets"
  type        = string
  sensitive   = true
}
variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  sensitive   = true
}