from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Allergen(Base):
    __tablename__ = "allergen"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)