# Manual de Configuração do Ambiente Remoto (OCI Object Storage Always Free)

Siga os passos abaixo para configurar manualmente o seu ambiente de desenvolvimento local para apontar diretamente para a nuvem real da Oracle Cloud Infrastructure.

---

## 1. Criar o Bucket no Console da OCI

1. Acesse o Console da OCI e navegue até **Armazenamento (Storage)** > **Buckets**.
2. Certifique-se de selecionar o seu compartimento raiz (`root`) no menu lateral esquerdo.
3. Clique em **Criar Bucket (Create Bucket)**.
4. Defina o nome como `novamente-bucket-prod` e mantenha a camada de armazenamento em **Standard**.
5. Clique em **Criar (Create)**.

---

## 2. Gerar as Chaves de API Reais na OCI

1. No Console da OCI, clique no ícone do seu **Perfil (Avatar)** no canto superior direito e selecione **Configurações do Usuário (User Settings)**.
2. No menu lateral esquerdo, sob a seção *Recursos (Resources)*, clique em **Chaves de API (API Keys)**.
3. Clique em **Adicionar Chave de API (Add API Key)**.
4. Selecione **Gerar Par de Chaves de API (Generate API Key Pair)**.
5. Clique em **Baixar Chave Privada (Download Private Key)** para salvar o arquivo `.pem`.
6. Clique em **Adicionar (Add)**.

---

## 3. Configurar as Credenciais Reais na Máquina Local

**Passo 3.1:** Crie a pasta oculta `.oci` no seu diretório home:
```bash
mkdir -p ~/.oci
```

**Passo 3.2:** Mova o arquivo da chave privada que você baixou do navegador para dentro da pasta criada:
```bash
mv ~/Downloads/*.pem ~/.oci/oci_api_key.pem
```

**Passo 3.3:** Crie ou edite o arquivo de configuração da OCI:
```bash
nano ~/.oci/config
```

**Passo 3.4:** Cole o bloco gerado na tela do console da OCI (Configuration File Preview), configurando o caminho correto da chave privada na propriedade `key_file`:
```ini
[DEFAULT]
user=ocid1.user.oc1..seu_ocid_real
fingerprint=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99:00
tenancy=ocid1.tenancy.oc1..seu_ocid_da_conta
region=sa-saopaulo-1
key_file=~/.oci/oci_api_key.pem
```

---

## 4. Configurar o Arquivo de Ambiente (.env)

Adicione estas variáveis ao seu arquivo `.env` na raiz do seu projeto. Certifique-se de manter desativada a variável `OCI_ENDPOINT` para não usar o emulador local:

```env
# OCI_ENDPOINT=
BUCKET_NAME="novamente-bucket-prod"
OCI_NAMESPACE=""
OCI_CONFIG_FILE="~/.oci/config"
OCI_PROFILE="DEFAULT"
```

---

## 5. Executar os Testes na Nuvem

```bash
python3 -m unittest src/test_storage.py
```
