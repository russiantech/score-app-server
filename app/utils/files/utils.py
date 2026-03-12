import hashlib
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile


def generate_unique_filename(filename: str, content: bytes) -> str:

    name = Path(filename).stem
    ext = Path(filename).suffix.lower()

    file_hash = hashlib.md5(content).hexdigest()[:8]

    return f"{name[:50]}_{file_hash}{ext}"


def validate_file(
    file: UploadFile,
    allowed_types: list[str],
    max_size_mb: int
) -> Tuple[bytes, str]:

    content = file.file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > max_size_mb:
        raise ValueError(f"File exceeds {max_size_mb}MB limit")

    if file.content_type not in allowed_types:
        raise ValueError(f"Invalid file type: {file.content_type}")

    return content, file.content_type

