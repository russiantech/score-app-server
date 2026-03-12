import hashlib
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile, HTTPException, status

from app.core.config import get_app_config
from app.utils.files.helpers import clean_filename, validate_file_type
from app.utils.files.processors import process_image

settings = get_app_config()

def upload_file(
    file: UploadFile,
    upload_subdir: str = "uploads",
    dimensions: tuple | None = None
):
    """
    Universal upload service.

    Supports:
    - images
    - videos
    - documents

    """
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    if not validate_file_type(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )

    media_root = Path(settings.general_config.media_location)
    upload_dir = (media_root / upload_subdir).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = clean_filename(file.filename)
    name, ext = Path(original_filename).stem, Path(original_filename).suffix

    contents = file.file.read()

    file_hash = hashlib.md5(contents).hexdigest()

    unique_name = f"{name[:40]}_{file_hash[:8]}{ext.lower()}"
    save_path = upload_dir / unique_name

    if save_path.exists():
        return {
            "file_name": unique_name,
            "url": f"{settings.general_config.media_location}/{upload_subdir}/{unique_name}"
        }

    try:

        if file.content_type.startswith("image/"):

            processed = process_image(contents, dimensions)

            with open(save_path, "wb") as f:
                f.write(processed)

        else:

            with open(save_path, "wb") as f:
                f.write(contents)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

    return {
        "file_name": unique_name,
        "url": f"{settings.general_config.media_location}/{upload_subdir}/{unique_name}",
        "size": len(contents),
        "type": file.content_type
    }

