# Configuración del proveedor de AWS
provider "aws" {
  region = var.aws_region
}

# Crear el bucket de S3 para almacenar los datos
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

# Base de datos de AWS Glue
resource "aws_glue_catalog_database" "catalog_db" {
  name = var.database_name
}

# Base de datos de Lake Formation (integrada con Glue)
resource "aws_lakeformation_database" "lake_db" {
  name       = var.database_name
  catalog_id = aws_glue_catalog_database.catalog_db.catalog_id
}

# Trabajo de Glue para transformar los datos
resource "aws_glue_job" "transform_data" {
  name     = "transform_data_glue"
  role_arn = aws_iam_role.glue_role.arn

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
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/glue_jobs/catalog_data_glue.py"
    python_version  = "3"
  }

  default_arguments = {
    "--BUCKET_NAME"   = var.bucket_name
    "--DATABASE_NAME" = var.database_name  # Usamos la variable aquí
    "--IAM_ROLE"      = aws_iam_role.glue_role.arn
  }
}

# Permisos de Lake Formation sobre la base de datos
resource "aws_lakeformation_permissions" "lake_permissions" {
  principal = aws_iam_role.glue_role.arn  # El rol de Glue tiene acceso

  database {
    catalog_id = aws_glue_catalog_database.catalog_db.catalog_id
    name       = var.database_name
  }

  permissions = [
    "SELECT",
    "DESCRIBE",
    "ALTER",
    "CREATE_TABLE"
  ]
}

# Permisos de Lake Formation sobre la ubicación en S3
resource "aws_lakeformation_permissions" "s3_permissions" {
  principal = aws_iam_role.glue_role.arn

  data_location {
    catalog_id   = aws_glue_catalog_database.catalog_db.catalog_id
    resource_arn = "arn:aws:s3:::${var.bucket_name}/staged/"
  }

  permissions = [
    "DESCRIBE",
    "READ"
  ]
}

# Configurar grupo de trabajo de Athena
resource "aws_athena_workgroup" "main" {
  name = "main"

  configuration {
    result_configuration {
      output_location = "s3://${var.bucket_name}/athena/"
    }
  }
}
