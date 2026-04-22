output "schedule_bucket_name" {
  description = "S3 bucket storing the schedule CSV."
  value       = aws_s3_bucket.schedule_data.bucket
}

output "schedule_object_key" {
  description = "S3 object key for the schedule CSV."
  value       = aws_s3_object.schedule_csv.key
}
