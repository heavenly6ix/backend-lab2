from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipe.id"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    measurement: Mapped[int] = mapped_column(Integer, nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients",)
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_ingredients",)

    @property
    def name(self) -> str:
        return self.ingredient.name

    @property
    def ingredient_name(self) -> str:
        return self.ingredient.name