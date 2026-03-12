import re
from fastapi import UploadFile

VALID_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime"
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def clean_filename(filename: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    cleaned = cleaned.replace(" ", "_")
    cleaned = cleaned.replace("-", "_")
    return cleaned


def validate_file_type(file: UploadFile) -> bool:
    allowed = (
        ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOCUMENT_TYPES
    )
    return file.content_type in allowed
