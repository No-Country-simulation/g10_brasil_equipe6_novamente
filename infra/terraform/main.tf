module "novamente_storage" {
  source = "./modules/object_storage"

  compartment_id = var.compartment_id
  bucket_name    = var.bucket_name
  storage_tier   = "Standard"
}
