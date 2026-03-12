from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

# from app.database import get_db
from app.services.file_service import upload_file
from app.utils.responses import api_response
# from app.utils.api_response import api_response

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...)
):

    result = upload_file(
        file=file,
        upload_subdir="images",
        dimensions=(600, 600)
    )

    return api_response(
        success=True,
        message="Image uploaded successfully",
        data=result
    )




# for 2nd pattern implimentation - extended for external file uploads.
from fastapi import APIRouter, UploadFile
from app.services.storage.media import MediaService
media_service = MediaService()

@router.post("/upload")
async def upload_file(file: UploadFile):

    result = await media_service.upload_file(
        file,
        subdir="students"
    )

    return result