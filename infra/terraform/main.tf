module "novamente_storage" {
  source = "./modules/object_storage"

  compartment_id = var.compartment_id
  bucket_name    = var.bucket_name
  storage_tier   = "Standard"
}

module "novamente_network" {
  source = "./modules/network"

  compartment_id = var.compartment_id
}

module "novamente_compute" {
  source = "./modules/compute"

  compartment_id = var.compartment_id
  subnet_id      = module.novamente_network.subnet_id
  ssh_public_key = file(pathexpand(var.ssh_public_key_path))
}
