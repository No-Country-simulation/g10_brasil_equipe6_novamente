variable "compartment_id" { type = string }
variable "region" {
  type    = string
  default = "sa-saopaulo-1"
}
variable "bucket_name" {
  type    = string
  default = "novamente-bucket-prod"
}
variable "namespace" {
  type = string
}
variable "existing_subnet_id" {
  description = "OCID da Subnet pública da VCN Hackathon"
  type        = string
}
variable "oci_config_profile" {
  type    = string
  default = "DEFAULT"
}
variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}
variable "env_file_path" {
  type    = string
  default = "../../.env"
}
variable "oci_config_path" {
  type    = string
  default = "~/.oci/config"
}
variable "oci_key_path" {
  type    = string
  default = "~/.oci/oci_api_key.pem"
}
