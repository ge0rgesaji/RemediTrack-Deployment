output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "DNS name of the Load Balancer"
}

output "ec2_public_ip" {
  value       = aws_instance.web.public_ip
  description = "Public IP of the EC2 instance (if applicable)"
}

output "bastion_public_ip" {
  value       = aws_instance.bastion.public_ip
  description = "Public IP of the Bastion Host"
}

output "rds_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "Endpoint of the RDS instance"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.assets.id
  description = "Name of the S3 bucket"
}
