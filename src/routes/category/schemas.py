from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name: str

class CategoryUpdate(BaseModel):
    name: str

class CategoryOutput(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryWithQueue(BaseModel):
    id: int
    name: str
    queue: int
    class Config:
        from_attributes = True