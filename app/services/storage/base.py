from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class StorageProvider(ABC):

    @abstractmethod
    def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        subdir: Optional[str] = None
    ) -> str:
        """
        Upload file and return public URL
        """
        pass

    @abstractmethod
    def delete(self, file_path: str) -> None:
        pass

