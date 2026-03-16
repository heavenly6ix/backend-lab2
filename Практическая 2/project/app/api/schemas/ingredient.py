from pydantic import BaseModel, ConfigDict


class IngredientCreate(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")


class IngredientUpdate(BaseModel):
    name: str | None = None

    model_config = ConfigDict(extra="forbid")


class IngredientRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
