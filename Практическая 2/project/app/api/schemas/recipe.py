from pydantic import BaseModel, ConfigDict, Field


class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    quantity: int = Field(gt=0)
    measurement: int

    model_config = ConfigDict(extra="forbid")


class RecipeCuisineRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RecipeAllergenRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientRead(BaseModel):
    id: int
    name: str
    quantity: int = Field(gt=0)
    measurement: int

    model_config = ConfigDict(from_attributes=True)


class RecipeCreate(BaseModel):
    title: str
    description: str
    cooking_time: int = Field(alias="cook_time", gt=0)
    difficulty: int = Field(default=1, ge=1, le=5)
    cuisine_id: int
    allergen_ids: list[int] = Field(default_factory=list)
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class RecipeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    cooking_time: int | None = Field(default=None, alias="cook_time", gt=0)
    difficulty: int | None = Field(default=None, ge=1, le=5)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class RecipeRead(BaseModel):
    id: int
    title: str
    description: str
    cooking_time: int = Field(alias="cook_time")
    difficulty: int
    cuisine: RecipeCuisineRead | None = None
    allergens: list[RecipeAllergenRead] = Field(default_factory=list)
    ingredients: list[RecipeIngredientRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
