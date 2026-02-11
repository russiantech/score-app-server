from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from .user import UserRead

class StudentBase(BaseModel):
    dob: date | None = None

class StudentCreate(StudentBase):
    user_id: UUID

class StudentUpdate(StudentBase):
    pass

class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)  #  Pydantic V2
    id: UUID
    user: UserRead
