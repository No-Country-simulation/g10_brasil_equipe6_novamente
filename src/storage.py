"""Object Storage da OCI (somente funções, via oci-sdk)."""
import mimetypes
import os
from functools import lru_cache
from pathlib import Path

import oci


@lru_cache(maxsize=1)
def _client() -> oci.object_storage.ObjectStorageClient:
    """Retorna o cliente autenticado do Object Storage."""
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", "~/.oci/config"),
        profile_name=os.getenv("OCI_PROFILE", "DEFAULT"),
    )
    oci.config.validate_config(config)  # erro claro se a configuração estiver incompleta
    return oci.object_storage.ObjectStorageClient(config)


@lru_cache(maxsize=1)
def _namespace() -> str:
    """Retorna o namespace da OCI via env ou API."""
    return os.getenv("OCI_NAMESPACE") or _client().get_namespace().data


def _bucket() -> str:
    """Retorna o nome do bucket obtido via variável de ambiente."""
    return os.environ["BUCKET_NAME"]


def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    """Envia dados em formato de bytes diretamente para o bucket."""
    _client().put_object(_namespace(), _bucket(), key, data, content_type=content_type)


def upload_file(path: str | Path, key: str | None = None) -> str:
    """Envia um arquivo local para o bucket definindo o content-type."""
    path = Path(path)
    key = key or path.name
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    upload_bytes(key, path.read_bytes(), content_type)
    return key


def download_bytes(key: str) -> bytes:
    """Baixa o conteúdo de um objeto do bucket em formato de bytes."""
    return _client().get_object(_namespace(), _bucket(), key).data.content


def list_keys(prefix: str = "") -> list[str]:
    """Lista as chaves dos objetos presentes no bucket filtrando por prefixo."""
    keys, start = [], None
    while True:
        resp = _client().list_objects(_namespace(), _bucket(), prefix=prefix, start=start)
        keys += [o.name for o in resp.data.objects]
        start = resp.data.next_start_with
        if not start:
            return keys


def delete_key(key: str) -> None:
    """Remove um objeto do bucket a partir de sua chave."""
    _client().delete_object(_namespace(), _bucket(), key)
