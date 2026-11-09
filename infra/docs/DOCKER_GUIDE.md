# Guia de Configuração e Execução via Docker (Ambiente Multicamadas)

Execute os comandos abaixo no terminal a partir da raiz do seu projeto para compilar a imagem de produção e inicializar o container da aplicação utilizando a estrutura multi-stage otimizada.

---

## 1. Requisitos Prévios

Certifique-se de possuir o arquivo de variáveis de ambiente `.env` configurado na raiz do repositório contendo as chaves de acesso necessárias.

---

## 2. Construir a Imagem Docker (Build)

Execute o comando de compilação utilizando a flag de limpeza de cache para garantir o isolamento total das dependências declaradas no arquivo de pacotes:

```bash
docker build --no-cache -t novamente-app:latest .
```

---

## 3. Inicializar o Container

Suba o serviço vinculando a porta padrão do Streamlit à sua máquina local e injetando as definições de ambiente mapeadas no arquivo oculto:

```bash
docker run -d -p 8501:8501 --env-file .env --name novamente-container novamente-app:latest
```

---

## 4. Verificar o Status da Aplicação

Monitore a saída de terminal e os logs internos para certificar que o servidor de rotas web iniciou corretamente sem falhas de runtime:

```bash
docker logs novamente-container
```

A aplicação estará disponível para acesso no navegador através do endereço:
* http://localhost:8501

---

## 5. Derrubar e Apagar o Ambiente Completo

Para encerrar as atividades, remover o contêiner e limpar a imagem gerada do armazenamento local da máquina, execute a sequência de comandos abaixo:

```bash
# Para e remove o contêiner em execução
docker rm -f novamente-container

# Remove a imagem criada para o aplicativo
docker rmi novamente-app:latest

# Limpa camadas órfãs remanescentes dos processos de build
docker image prune -f # Esse comando é perigoso, tome cuidado antes de executá-lo
```
