output "bucket_criado" {
  value = module.novamente_storage.bucket_name
}

output "oci_namespace" {
  value = module.novamente_storage.namespace
}

output "vm_public_ip" {
  value = module.novamente_compute.public_ip
}

output "url_streamlit" {
  value = "http://${module.novamente_compute.public_ip}:8501"
}
