from pathlib import Path
from typing import BinaryIO, Optional
from .base import StorageProvider


class FileSystemStorage(StorageProvider):

    def __init__(self, base_path: str, base_url: str):
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip("/")

    def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        subdir: Optional[str] = None
    ) -> str:

        directory = self.base_path / (subdir or "")
        directory.mkdir(parents=True, exist_ok=True)

        filepath = directory / filename

        with open(filepath, "wb") as f:
            f.write(file.read())

        relative = filepath.relative_to(self.base_path)

        return f"{self.base_url}/uploads/{relative}"

    def delete(self, file_path: str):

        path = self.base_path / file_path

        if path.exists():
            path.unlink()

