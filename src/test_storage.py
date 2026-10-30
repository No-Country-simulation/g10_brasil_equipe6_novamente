"""Script de testes para validacao das funcoes do OCI Object Storage via emulador."""
import unittest
from pathlib import Path
from dotenv import load_dotenv
from oci.object_storage.models import CreateBucketDetails
from oci.exceptions import ServiceError

from src.storage import (
    _client, _namespace, _bucket,
    upload_bytes, upload_file, download_bytes, list_keys, delete_key
)

load_dotenv()


class TestObjectStorage(unittest.TestCase):
    """Classe de testes integrados para o ciclo de vida do OCI Object Storage."""

    @classmethod
    def setUpClass(cls) -> None:
        """Garante a infraestrutura inicial criando o bucket necessario dentro do emulador local."""
        client = _client()
        namespace = _namespace()
        bucket_name = _bucket()
        try:
            details = CreateBucketDetails(name=bucket_name, compartment_id=namespace)
            client.create_bucket(namespace, details)
        except ServiceError as e:
            if e.status != 409 and "BucketAlreadyExists" not in str(e):
                raise e

    def test_object_storage_lifecycle(self) -> None:
        """Executa o ciclo completo de testes integrados das operacoes do Object Storage."""
        bytes_object_name = "teste_bytes.txt"
        original_bytes_content = b"Ola, este e um teste de bytes usando o emulador OCI!"
        upload_bytes(bytes_object_name, original_bytes_content, content_type="text/plain")

        local_file = Path("arquivo_local_teste.txt")
        local_file.write_text("Conteúdo de um arquivo de texto físico local.", encoding="utf-8")

        file_object_name = upload_file(local_file)

        keys = list_keys()
        self.assertIn(bytes_object_name, keys)
        self.assertIn(file_object_name, keys)

        downloaded_content = download_bytes(bytes_object_name)
        self.assertEqual(downloaded_content, original_bytes_content)

        delete_key(bytes_object_name)
        delete_key(file_object_name)

        final_keys = list_keys()
        self.assertEqual(len(final_keys), 0)

        if local_file.exists():
            local_file.unlink()


if __name__ == "__main__":
    unittest.main()
