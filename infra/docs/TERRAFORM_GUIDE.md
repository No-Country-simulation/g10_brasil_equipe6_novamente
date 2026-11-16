# Guia de Provisionamento de Infraestrutura via Terraform (OCI Object Storage)

Execute os comandos abaixo no terminal a partir da raiz do seu projeto para formatar, validar e provisionar o bucket na nuvem da Oracle Cloud Infrastructure utilizando a estrutura modular do Terraform.

---

## 1. Requisitos Prévios

Certifique-se de possuir:
* Terraform instalado (versão `>= 1.16.0`).
* Credenciais reais da OCI configuradas em `~/.oci/config` (siga os passos de configuração de chaves de API descritos em [REMOTE_MANUAL_GUIDE.md](./REMOTE_MANUAL_GUIDE.md)).

---

## 2. Configurar as Variáveis do Ambiente

Acesse o diretório do Terraform e gere o arquivo `terraform.tfvars` preenchendo automaticamente o identificador do seu compartimento raiz (`tenancy`) a partir das suas credenciais locais:

```bash
cd infra/terraform

cat <<EOF > terraform.tfvars
compartment_id = "\$(grep '^tenancy=' ~/.oci/config | cut -d'=' -f2)"
region         = "us-sanjose-1"
bucket_name    = "novamente-bucket-prod"
EOF
```

---

## 3. Inicializar, Formatar e Validar

Execute os comandos abaixo para baixar o provedor oficial da Oracle (`oracle/oci`), registrar os módulos locais, padronizar a formatação dos arquivos `.tf` e validar a sintaxe da configuração:

```bash
# Baixa os provedores e inicializa os módulos
terraform init

# Formata recursivamente todos os arquivos de configuração do Terraform
terraform fmt -recursive

# Valida a sintaxe e a consistência interna dos módulos
terraform validate
```

---

## 4. Planejar e Provisionar o Bucket

Visualize o plano de execução antes de aplicar as mudanças e crie o recurso na nuvem:

```bash
# Exibe o plano detalhado do que será criado na OCI
terraform plan

# Provisiona o bucket automaticamente na nuvem
terraform apply -auto-approve
```

*(Nota: Caso o bucket já exista na sua conta OCI e você deseje apenas vinculá-lo ao gerenciamento do Terraform sem recriar, execute antes do `apply`: `terraform import module.novamente_storage.oci_objectstorage_bucket.this n/<seu_namespace>/b/novamente-bucket-prod`)*

---

## 5. Inspecionar e Derrubar o Ambiente

Para consultar os valores gerados após o deploy, remover o bucket provisionado na nuvem e apagar os arquivos locais de estado e cache:

```bash
# Exibe as saídas (outputs) do módulo provisionado
terraform output

# Destrói os recursos provisionados na OCI
terraform destroy -auto-approve

# Remove os arquivos de estado, cache de provedores e variáveis locais
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* terraform.tfvars
```
