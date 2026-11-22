data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "this" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  display_name        = "${var.project_name}-vm"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }


  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(<<-EOF
      #!/bin/bash
      set -e

      apt-get update -y
      apt-get install -y docker.io git iptables-persistent
      systemctl enable --now docker
      usermod -aG docker ubuntu
      iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
      netfilter-persistent save

      mkdir -p /root/.oci
      cat << 'OCICONF' > /root/.oci/config
${var.oci_config_content}
OCICONF

      cat << 'OCIKEY' > /root/.oci/oci_api_key.pem
${var.oci_key_content}
OCIKEY
      chmod 600 /root/.oci/oci_api_key.pem
      sed -i 's|key_file=.*|key_file=/root/.oci/oci_api_key.pem|g' /root/.oci/config

      cd /opt
      git clone https://github.com
      cd g10_brasil_equipe6_novamente

      cat << 'ENVFILE' > .env
${var.env_file_content}
ENVFILE

      docker build -t novamente-api:latest .
      docker run -d \
        -p 8000:8000 \
        --env-file .env \
        -v /root/.oci:/root/.oci:ro \
        --restart unless-stopped \
        --name novamente-container \
        novamente-api:latest
    EOF
    )
  }
}
