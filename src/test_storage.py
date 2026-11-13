"""Script de testes para validacao das funcoes do OCI Object Storage na nuvem real."""
import shutil
import unittest
from pathlib import Path
from dotenv import load_dotenv
from oci.exceptions import ServiceError

from src.storage import (
    _client, _namespace, _bucket,
    upload_bytes, upload_file, download_bytes, list_keys, delete_key,
    backup_directory, restore_directory
)

load_dotenv()


class TestObjectStorage(unittest.TestCase):
    """Classe de testes integrados para o ciclo de vida do OCI Object Storage."""

    @classmethod
    def setUpClass(cls) -> None:
        """Garante a infraestrutura inicial verificando se o bucket existe na OCI."""
        client = _client()
        namespace = _namespace()
        bucket_name = _bucket()
        try:
            client.get_bucket(namespace, bucket_name)
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

        if local_file.exists():
            local_file.unlink()

    def test_directory_backup_and_restore(self) -> None:
        """Testa a compactacao, envio, download e extracao do diretorio vetorial."""
        source_dir = Path(".data/chroma_test_source")
        restore_dir = Path(".data/chroma_test_restore")
        remote_backup_key = "backups/test_chroma_db.zip"

        source_dir.mkdir(parents=True, exist_ok=True)
        sample_file = source_dir / "chroma.sqlite3"
        sample_content = "dados_simulados_do_indice_vetorial"
        sample_file.write_text(sample_content, encoding="utf-8")

        try:
            uploaded_key = backup_directory(dir_path=source_dir, remote_key=remote_backup_key)
            self.assertEqual(uploaded_key, remote_backup_key)
            self.assertIn(remote_backup_key, list_keys(prefix="backups/"))

            restore_directory(remote_key=remote_backup_key, extract_dir=restore_dir)
            restored_file = restore_dir / "chroma.sqlite3"

            self.assertTrue(restored_file.exists())
            self.assertEqual(restored_file.read_text(encoding="utf-8"), sample_content)
        finally:
            delete_key(remote_backup_key)
            if source_dir.exists():
                shutil.rmtree(source_dir)
            if restore_dir.exists():
                shutil.rmtree(restore_dir)


if __name__ == "__main__":
    unittest.main()
