from fastapi import UploadFile
from app.services.storage.manager import StorageManager
from app.utils.files.utils import validate_file, generate_unique_filename
from app.core.config import get_app_config

settings = get_app_config()

class MediaService:

    def __init__(self):
        self.storage = StorageManager()

    async def upload_file(self, file: UploadFile, subdir: str = "general"):

        config = settings.hosting_config.content_delivery

        content, content_type = validate_file(
            file,
            config.allowed_file_types,
            config.max_file_size_mb
        )

        filename = generate_unique_filename(file.filename, content)

        from io import BytesIO

        url = self.storage.upload(
            file=BytesIO(content),
            filename=filename,
            content_type=content_type,
            subdir=subdir
        )

        return {
            "filename": filename,
            "url": url,
            "content_type": content_type,
            "size": len(content)
        }
