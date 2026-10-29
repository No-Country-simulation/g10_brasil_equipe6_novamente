# Guia de Configuração do Ambiente Local (OCI Object Storage Emulator)

Execute os comandos abaixo no terminal a partir da raiz do seu projeto para configurar o ambiente e rodar os testes.

---

## 1. Subir o Emulador Local

```bash
docker compose -f infra/docker-compose.yml up -d
```

---

## 2. Configurar as Credenciais Fictícias da OCI (Passo a Passo)

O SDK da OCI exige uma estrutura de arquivos de configuração e chaves válidas na máquina local, mesmo utilizando um emulador. Siga os passos abaixo para criar essa estrutura:

**Passo 2.1:** Crie a pasta oculta `.oci` no diretório home do seu usuário:
```bash
mkdir -p ~/.oci
```

**Passo 2.2:** Gere uma chave privada RSA válida no formato PEM exigido pelo SDK dentro dessa pasta:
```bash
openssl genrsa -out ~/.oci/oci_api_key.pem 2000
```

**Passo 2.3:** Crie e abra o arquivo de configuração no editor do terminal:
```bash
nano ~/.oci/config
```

**Passo 2.4:** Copie o bloco de texto abaixo, cole dentro do editor de texto que se abriu no terminal e salve o arquivo (no Nano, aperte `Ctrl + O` seguido de `Enter` para salvar, e `Ctrl + X` para sair):
```ini
[DEFAULT]
user=ocid1.user.oc1..ficticio
fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..ficticio
region=us-ashburn-1
```

---

## 3. Configurar o Arquivo de Ambiente (.env)

Adicione estas variáveis ao seu arquivo `.env` na raiz do projeto:

```env
OCI_ENDPOINT="http://localhost:12000"
OCI_NAMESPACE="namespace_ficticio"
BUCKET_NAME="seu_bucket_de_testes"
OCI_CONFIG_FILE="~/.oci/config"
OCI_PROFILE="DEFAULT"
```

---

## 4. Executar os Testes

```bash
python3 -m unittest src/test_storage.py
```

---

## 5. Derrubar o Ambiente

```bash
docker compose -f infra/docker-compose.yml down
```
