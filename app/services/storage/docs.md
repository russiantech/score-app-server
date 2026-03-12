Your current configuration system is **already very well architected** (Pydantic models + loader + env/YAML merging). The right way to build a **professional reusable upload system** on top of it is to follow the same pattern you used for **mail, redis, payments, etc.**:

**Key idea:**
Create a **Storage/Media Service Layer** driven entirely by `ContentDeliveryConfig`.

So instead of a single `uploader()` function tied to filesystem + cv2, we build a **pluggable storage driver architecture**.

This gives you:

• filesystem uploads
• S3 uploads
• Cloudinary uploads
• automatic validation
• configurable file types
• configurable size limits
• reusable service for any module
• clean separation of concerns

Exactly like your **PaymentsConfig provider pattern.**

---

# 1. Architecture (Production Grade)

Recommended structure:

```
app/
 ├── services/
 │    └── storage/
 │         ├── base.py
 │         ├── filesystem.py
 │         ├── s3.py
 │         ├── cloudinary.py
 │         └── manager.py
 │
 ├── utils/
 │    └── file_utils.py
 │
 ├── core/
 │    └── config/
 │
 └── api/
```

---

# 2. Base Storage Interface

`services/storage/base.py`

```python
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
```

This ensures every storage backend **behaves the same**.

---

# 3. File Validation Utility

`utils/file_utils.py`

```python
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
```

Reusable everywhere.

---

# 4. Filesystem Storage Driver

`services/storage/filesystem.py`

```python
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
```

---

# 5. S3 Storage Driver

`services/storage/s3.py`

```python
import boto3
from .base import StorageProvider


class S3Storage(StorageProvider):

    def __init__(self, config):

        self.bucket = config.bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    def upload(self, file, filename, content_type, subdir=None):

        key = f"{subdir}/{filename}" if subdir else filename

        self.client.upload_fileobj(
            file,
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type}
        )

        return f"{self.client.meta.endpoint_url}/{self.bucket}/{key}"

    def delete(self, file_path):

        self.client.delete_object(
            Bucket=self.bucket,
            Key=file_path
        )
```

---

# 6. Storage Manager (Key Part)

This uses your **config loader**.

`services/storage/manager.py`

```python
from app.core.config import settings
from .filesystem import FileSystemStorage
from .s3 import S3Storage


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
```

---

# 7. Upload Service (Your New Reusable Layer)

`services/media_service.py`

```python
from fastapi import UploadFile
from app.services.storage.manager import StorageManager
from app.utils.file_utils import validate_file, generate_unique_filename
from app.core.config import settings


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
```

---

# 8. API Usage

Example endpoint:

```python
from fastapi import APIRouter, UploadFile
from app.services.media_service import MediaService

router = APIRouter()
media_service = MediaService()


@router.post("/upload")
async def upload_file(file: UploadFile):

    result = await media_service.upload_file(
        file,
        subdir="students"
    )

    return result
```

---

# 9. Result

Your system now supports:

### Automatic validation from config

```
APP_MAX_FILE_SIZE_MB=100
APP_ALLOWED_FILE_TYPES=image/jpeg,image/png,application/pdf
```

---

### Storage switching

```
APP_CONTENT_DELIVERY_TYPE=filesystem
```

or

```
APP_CONTENT_DELIVERY_TYPE=s3api
```

No code change needed.

---

### Reusable anywhere

```
await media_service.upload_file(file, "products")
await media_service.upload_file(file, "students")
await media_service.upload_file(file, "course_materials")
```

---

# 10. Compared to your current Flask uploader

Your Flask function mixes:

• validation
• storage logic
• hashing
• image processing
• DB logic

The architecture above **separates all responsibilities cleanly.**

---

# 11. Optional Advanced Features

Easy to add later:

### image resizing pipeline

```
services/media_processors/
```

### async background processing

Celery / Redis queue.

### antivirus scanning

ClamAV integration.

### presigned uploads (for S3)

Direct browser upload.

---

# 12. If you'd like

I can also show you **how to upgrade this into a full production Media Pipeline** like:

Netflix / Shopify / large SaaS systems use:

* versioned images
* automatic thumbnails
* CDN integration
* image optimization
* async video transcoding

It fits **perfectly with the config system you built.**
