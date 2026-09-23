from pydantic import BaseModel, ConfigDict

class ItemIn(BaseModel):
    id: str
    name: str

class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    version: int

class ItemUpdate(BaseModel):
    name: str