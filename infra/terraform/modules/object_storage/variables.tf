variable "compartment_id" {
  description = "OCID do compartimento onde o bucket será criado"
  type        = string
}

variable "bucket_name" {
  description = "Nome do bucket no OCI Object Storage"
  type        = string
}

variable "storage_tier" {
  description = "Camada de armazenamento (Standard para Always Free)"
  type        = string
  default     = "Standard"
}
