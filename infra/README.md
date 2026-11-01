# Infraestrutura de Armazenamento (OCI Object Storage)

Este diretório contém os manuais de configuração necessários para estabelecer a comunicação do backend do **NovaMente** com o serviço de Object Storage da Oracle Cloud Infrastructure, suportando tanto o desenvolvimento isolado quanto a homologação em nuvem.

---

## Visão Geral da Infraestrutura

O módulo de persistência (`src/storage.py`) foi projetado para funcionar de forma híbrida e transparente. Através das variáveis de ambiente contidas no arquivo `.env`, o SDK da OCI sabe se deve redirecionar as chamadas de API para um container Docker local ou para os servidores reais da Oracle Cloud.

Os guias detalhados de configuração estão divididos em dois cenários e localizados na pasta `docs/`:

*   [docs/LOCAL_GUIDE.md](./docs/LOCAL_GUIDE.md): Manual focado na emulação local do Object Storage via Docker Compose. Ideal para desenvolvimento offline, novos integrantes da equipe ou testes rápidos sem consumo de recursos externos.
*   [docs/REMOTE_MANUAL_GUIDE.md](./docs/REMOTE_MANUAL_GUIDE.md): Manual focado no provisionamento manual do bucket gratuito (Always Free) diretamente no console web da OCI e na geração das chaves de API reais de acesso.

---

## Arquivos de Configuração Envolvidos

Para garantir o funcionamento correto de qualquer um dos ambientes escolhidos, o desenvolvedor deve se atentar aos seguintes pontos de ancoragem locais:

1.  **Pasta `~/.oci/`**: Diretório oculto na raiz do usuário do sistema operacional que armazena as chaves RSA (`oci_api_key.pem`) e as assinaturas de requisição do SDK.
2.  **Arquivo `~/.oci/config`**: Arquivo de mapeamento contendo os identificadores exclusivos (OCIDs), região padrão e o caminho local da chave privada.
3.  **Arquivo `.env`**: Arquivo na raiz do projeto que dita o comportamento dinâmico do código por meio de propriedades como `BUCKET_NAME` e `OCI_ENDPOINT`.

---

## Validação do Módulo de Storage

Independentemente de estar rodando o emulador local ou a nuvem real da OCI, o comportamento das funções de upload, listagem e download integradas pode ser validado imediatamente executando o conjunto de testes unitários:

```bash
python3 -m unittest src/test_storage.py
```
