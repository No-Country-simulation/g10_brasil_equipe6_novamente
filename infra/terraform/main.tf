module "novamente_storage" {
  source         = "./modules/object_storage"
  compartment_id = var.compartment_id
  bucket_name    = var.bucket_name
  namespace      = var.namespace
  storage_tier   = "Standard"
}

module "novamente_compute" {
  source             = "./modules/compute"
  compartment_id     = var.compartment_id
  subnet_id          = var.existing_subnet_id
  ssh_public_key     = file(pathexpand(var.ssh_public_key_path))
  env_file_content   = file(pathexpand(var.env_file_path))
  oci_config_content = file(pathexpand(var.oci_config_path))
  oci_key_content    = file(pathexpand(var.oci_key_path))
}
