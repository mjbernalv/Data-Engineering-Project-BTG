variable "aws_region" {
  default = "us-east-2" # cambiar a region de aws real
}

variable "bucket_name" {
  default = "your_bucket_name" # cambiar por nombre del bucket real
}

variable "database_name" {
  description = "El nombre de la base de datos en AWS Glue"
  type        = string
}
