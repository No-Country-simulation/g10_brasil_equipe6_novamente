output "bucket_name" {
  description = "Nome do bucket provisionado"
  value       = oci_objectstorage_bucket.this.name
}

output "namespace" {
  description = "Namespace do Object Storage"
  value       = oci_objectstorage_bucket.this.namespace
}
