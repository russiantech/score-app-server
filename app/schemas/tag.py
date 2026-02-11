from pydantic import BaseModel, ConfigDict
from uuid import UUID

class TagBase(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True
    is_featured: bool = False
    display_order: int = 0
    parent_id: UUID | None = None
    
class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    pass

class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)  #  Pydantic V2
    id: UUID
    slug: str
    description: str | None = None
    is_active: bool
    is_featured: bool
    display_order: int
    parent_id: UUID | None = None
    click_count: int