from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Cuisine(Base):
    __tablename__ = "cuisine"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="cuisine",)