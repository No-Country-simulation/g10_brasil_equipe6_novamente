"""Object Storage da OCI (somente funções, via oci-sdk)."""
import mimetypes
import os
import shutil
from functools import lru_cache
from pathlib import Path

import oci

DEFAULT_CHROMA_DIR = ".data/chroma"
DEFAULT_BACKUP_KEY = "backups/chroma_db.zip"


@lru_cache(maxsize=1)
def _client() -> oci.object_storage.ObjectStorageClient:
    """Retorna o cliente autenticado do Object Storage."""
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", "~/.oci/config"),
        profile_name=os.getenv("OCI_PROFILE", "DEFAULT"),
    )
    oci.config.validate_config(config)

    # Se a variável OCI_ENDPOINT estiver definida (ex: http://localhost:12000),
    # o SDK usará o emulador em vez da nuvem real.
    endpoint = os.getenv("OCI_ENDPOINT")

    return oci.object_storage.ObjectStorageClient(config, service_endpoint=endpoint)


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


def backup_directory(
    dir_path: str | Path | None = None,
    remote_key: str = DEFAULT_BACKUP_KEY,
) -> str:
    """Compacta o diretório local do ChromaDB em .zip e envia para o bucket da OCI."""
    target_dir = Path(
        dir_path or os.getenv("CHROMA_PERSIST_DIRECTORY", DEFAULT_CHROMA_DIR)
    )
    if not target_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {target_dir}")

    zip_path = Path(shutil.make_archive("temp_dir_backup", "zip", root_dir=target_dir))
    try:
        return upload_file(zip_path, key=remote_key)
    finally:
        if zip_path.exists():
            zip_path.unlink()


def restore_directory(
    remote_key: str = DEFAULT_BACKUP_KEY,
    extract_dir: str | Path | None = None,
) -> None:
    """Baixa um arquivo .zip do bucket da OCI e extrai no diretório local do ChromaDB."""
    target_dir = Path(
        extract_dir or os.getenv("CHROMA_PERSIST_DIRECTORY", DEFAULT_CHROMA_DIR)
    )
    temp_zip = Path("temp_dir_restore.zip")
    try:
        temp_zip.write_bytes(download_bytes(remote_key))
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(temp_zip), extract_dir=str(target_dir), format="zip")
    finally:
        if temp_zip.exists():
            temp_zip.unlink()
