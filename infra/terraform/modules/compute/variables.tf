variable "compartment_id" { type = string }
variable "subnet_id" { type = string }
variable "ssh_public_key" { type = string }

variable "env_file_content" {
  type      = string
  sensitive = true
}

variable "oci_config_content" {
  type      = string
  sensitive = true
}

variable "oci_key_content" {
  type      = string
  sensitive = true
}

variable "project_name" {
  type    = string
  default = "novamente"
}
