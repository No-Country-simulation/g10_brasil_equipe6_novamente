resource "oci_objectstorage_bucket" "this" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = var.namespace
  storage_tier   = var.storage_tier
  access_type    = "NoPublicAccess"
}
