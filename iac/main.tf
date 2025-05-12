# Configuración del proveedor de AWS
provider "aws" {
  region = var.aws_region
}

# Bloque de Terraform para especificar la versión del proveedor
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Recurso de S3 para almacenar los datos
resource "aws_s3_bucket" "data_bucket" {
  bucket = var.bucket_name
}

# Bloquear el acceso público al bucket de S3
resource "aws_s3_bucket_public_access_block" "data_bucket_block" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Base de datos de Glue para el catálogo
resource "aws_glue_catalog_database" "catalog_db" {
  name = var.database_name
}

# Trabajo de Glue para transformar los datos
resource "aws_glue_job" "transform_data" {
  name     = "transform_data_glue"
  role_arn = aws_iam_role.glue_role.arn  # Referenciamos el rol IAM aquí

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/glue_jobs/transform_data_glue.py"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET_NAME" = var.bucket_name
  }
}

# Trabajo de Glue para catalogar los datos
resource "aws_glue_job" "catalog_data" {
  name     = "catalog_data_glue"
  role_arn = aws_iam_role.glue_role.arn  # Referenciamos el rol IAM aquí

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/glue_jobs/catalog_data_glue.py"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET_NAME"    = var.bucket_name
    "--DATABASE_NAME"  = aws_glue_catalog_database.catalog_db.name
    "--IAM_ROLE"       = aws_iam_role.glue_role.arn
  }
}

# Grupo de trabajo opcional de Athena para realizar consultas
resource "aws_athena_workgroup" "main" {
  name = "main"

  configuration {
    result_configuration {
      output_location = "s3://${var.bucket_name}/athena/"
    }
  }
}
