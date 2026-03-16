from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Cuisine(Base):
    __tablename__ = "cuisine"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)