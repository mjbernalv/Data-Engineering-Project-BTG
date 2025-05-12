output "s3_bucket_name" {
  value = aws_s3_bucket.data_bucket.id
}

output "glue_role_arn" {
  value = aws_iam_role.glue_role.arn
}

output "glue_database" {
  value = aws_glue_catalog_database.catalog_db.name
}
