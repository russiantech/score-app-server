# 

from app.core.config import get_app_config
from .filesystem import FileSystemStorage
from .s3 import S3Storage

settings = get_app_config()

class StorageManager:

    def __init__(self):

        config = settings.hosting_config.content_delivery

        if config.type == "filesystem":

            self.driver = FileSystemStorage(
                base_path=config.filesystem_base_path,
                base_url=settings.hosting_config.api_url
            )

        elif config.type == "s3api":

            self.driver = S3Storage(config.s3api)

        else:
            raise ValueError("Unsupported storage provider")

    def upload(self, *args, **kwargs):

        return self.driver.upload(*args, **kwargs)

    def delete(self, *args, **kwargs):

        return self.driver.delete(*args, **kwargs)

