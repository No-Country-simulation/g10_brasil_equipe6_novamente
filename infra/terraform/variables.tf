variable "compartment_id" {
  description = "OCID do compartimento (ou tenancy OCID para o root)"
  type        = string
}

variable "region" {
  description = "Região da OCI"
  type        = string
  default     = "us-sanjose-1"
}

variable "bucket_name" {
  description = "Nome do bucket de produção do projeto"
  type        = string
  default     = "novamente-bucket-prod"
}

variable "oci_config_profile" {
  description = "Perfil utilizado no arquivo ~/.oci/config"
  type        = string
  default     = "DEFAULT"
}
