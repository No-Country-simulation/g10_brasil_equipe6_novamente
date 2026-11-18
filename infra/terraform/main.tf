terraform {
  required_version = ">= 1.16.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 9.13.0"
    }
  }
}

provider "oci" {
  region              = var.region
  config_file_profile = var.oci_config_profile
}

module "novamente_storage" {
  source = "./modules/object_storage"

  compartment_id = var.compartment_id
  bucket_name    = var.bucket_name
  storage_tier   = "Standard"
}
