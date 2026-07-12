import os
import shutil
from typing import BinaryIO

class StorageService:
    def upload_file(self, file_obj: BinaryIO, filename: str, content_type: str) -> str:
        raise NotImplementedError

    def download_file(self, file_key: str, destination_path: str) -> bool:
        raise NotImplementedError
        
    def get_file_url(self, file_key: str) -> str:
        raise NotImplementedError

    def delete_file(self, file_key: str) -> bool:
        raise NotImplementedError

class LocalStorageBackend(StorageService):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_obj: BinaryIO, filename: str, content_type: str = None) -> str:
        # Mock S3 key generation
        file_key = f"local-bucket/{filename}"
        local_path = os.path.join(self.base_dir, filename)
        
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        return file_key

    def download_file(self, file_key: str, destination_path: str) -> bool:
        filename = file_key.split("/")[-1]
        local_path = os.path.join(self.base_dir, filename)
        
        if not os.path.exists(local_path):
            return False
            
        shutil.copy(local_path, destination_path)
        return True

    def get_file_url(self, file_key: str) -> str:
        return f"file://{os.path.abspath(self.base_dir)}/{file_key.split('/')[-1]}"

    def delete_file(self, file_key: str) -> bool:
        filename = file_key.split("/")[-1]
        local_path = os.path.join(self.base_dir, filename)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                return True
            except Exception as e:
                print(f"[LocalStorageBackend] Error removing file {local_path}: {e}")
                return False
        return False

# Factory method to return the right backend based on environment
def get_storage_service() -> StorageService:
    provider = os.environ.get("STORAGE_PROVIDER", "local")
    if provider == "s3":
        # return S3StorageBackend()  # To be implemented
        pass
    return LocalStorageBackend()

storage_service = get_storage_service()
