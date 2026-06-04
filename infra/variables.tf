variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name for tagging"
  default     = "remeditrack"
}

variable "db_password" {
  description = "Password for RDS PostgreSQL"
  sensitive   = true
}

variable "key_name" {
  description = "Name of the AWS Key Pair to use for SSH access"
}
