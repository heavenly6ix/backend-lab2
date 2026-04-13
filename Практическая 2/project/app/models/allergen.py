from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .recipe_allergen import recipe_allergens

from .base import Base

class Allergen(Base):
    __tablename__ = "allergen"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(secondary=recipe_allergens,back_populates="allergens",)