from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import String, Text, Integer, CheckConstraint
from sqlalchemy import ForeignKey
from .recipe_allergen import recipe_allergens

from .base import Base

class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    cooking_time: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    cuisine_id: Mapped[int] = mapped_column(ForeignKey("cuisine.id"), nullable=False)

    allergens: Mapped[list["Allergen"]] = relationship(secondary=recipe_allergens,back_populates="recipes",)
    cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes",)
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe",cascade="all, delete-orphan",)
    
    # __table_args__ = (
    #     CheckConstraint(
    #         "difficulty >= 1 AND difficulty <= 5", name="check_difficulty_range"
    #     ),
    # )

    def __repr__(self):
        return f"Recipe(id={self.id}, title={self.title})"
