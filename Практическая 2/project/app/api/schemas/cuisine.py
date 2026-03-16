from pydantic import BaseModel, ConfigDict


class CuisineCreate(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")


class CuisineUpdate(BaseModel):
    name: str | None = None

    model_config = ConfigDict(extra="forbid")


class CuisineRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
