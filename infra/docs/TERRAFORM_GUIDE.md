# Guia de Provisionamento de Infraestrutura via Terraform (OCI Object Storage e Compute)

Execute os comandos abaixo no terminal a partir da raiz do seu projeto para formatar, validar e provisionar o bucket e a instância computacional (VM) na nuvem da Oracle Cloud Infrastructure utilizando a estrutura modular do Terraform.

---

## 1. Requisitos Prévios

Certifique-se de possuir:
* Terraform instalado (versão `>= 1.16.0`).
* Credenciais reais da OCI configuradas em `~/.oci/config` apontando para a região `sa-saopaulo-1` (siga os passos de configuração de chaves de API descritos em [REMOTE_MANUAL_GUIDE.md](./REMOTE_MANUAL_GUIDE.md)).
* O OCID do compartimento de destino, o Object Storage Namespace da Tenancy e o OCID de uma Subnet pública existente na VCN.
* O par de chaves SSH local (`~/.ssh/id_ed25519.pub`) e o arquivo `.env` na raiz do projeto.

---

## 2. Configurar as Variáveis do Ambiente

Garanta a existência da chave SSH local, acesse o diretório do Terraform e gere o arquivo `terraform.tfvars` com os identificadores reais do ambiente:

```bash
# Gera a chave SSH local caso ainda não exista
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

cd infra/terraform

cat <<EOF > terraform.tfvars
compartment_id     = "ocid1.compartment.oc1..seu_ocid_do_compartimento_aqui"
region             = "sa-saopaulo-1"
bucket_name        = "novamente-bucket-prod"
namespace          = "seu_object_storage_namespace_aqui"
existing_subnet_id = "ocid1.subnet.oc1.sa-saopaulo-1..seu_ocid_da_subnet_publica_aqui"
EOF
```

---

## 3. Inicializar, Formatar e Validar

Execute os comandos abaixo para baixar o provedor oficial da Oracle (`oracle/oci`), registrar os módulos locais (`object_storage` e `compute`), padronizar a formatação dos arquivos `.tf` e validar a sintaxe da configuração:

```bash
# Baixa os provedores e inicializa os módulos
terraform init

# Formata recursivamente todos os arquivos de configuração do Terraform
terraform fmt -recursive

# Valida a sintaxe e a consistência interna dos módulos
terraform validate
```

---

## 4. Planejar e Provisionar a Infraestrutura

Visualize o plano de execução antes de aplicar as mudanças e crie os recursos na nuvem:

```bash
# Exibe o plano detalhado do que será criado na OCI (Bucket e VM)
terraform plan

# Provisiona os recursos automaticamente na nuvem
terraform apply -auto-approve
```

*(Nota: Caso o bucket já exista na conta OCI e você deseje apenas vinculá-lo ao gerenciamento do Terraform sem recriar, execute antes do `apply`: `terraform import module.novamente_storage.oci_objectstorage_bucket.this n/<seu_namespace>/b/novamente-bucket-prod`)*

---

## 5. Inspecionar e Derrubar o Ambiente

Para consultar os valores gerados após o deploy (como o IP público da VM), remover os recursos provisionados na nuvem e apagar os arquivos locais de estado e cache:

```bash
# Exibe as saídas (outputs) dos módulos provisionados
terraform output

# Destrói os recursos provisionados na OCI
terraform destroy -auto-approve

# Remove os arquivos de estado, cache de provedores e variáveis locais
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* terraform.tfvars
```
