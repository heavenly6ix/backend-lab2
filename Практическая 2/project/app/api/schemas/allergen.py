from pydantic import BaseModel, ConfigDict


class AllergenCreate(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")


class AllergenUpdate(BaseModel):
    name: str | None = None

    model_config = ConfigDict(extra="forbid")


class AllergenRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
