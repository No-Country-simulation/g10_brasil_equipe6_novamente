variable "compartment_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-sanjose-1"
}

variable "bucket_name" {
  type    = string
  default = "novamente-bucket-prod"
}

variable "oci_config_profile" {
  type    = string
  default = "DEFAULT"
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}
