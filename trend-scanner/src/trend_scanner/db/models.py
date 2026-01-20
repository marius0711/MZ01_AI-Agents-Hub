from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawItem(Base):
    __tablename__ = "raw_items"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_platform_external_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    platform: Mapped[str] = mapped_column(String(32), default="reddit")
    external_id: Mapped[str] = mapped_column(String(64))  # reddit submission id

    subreddit: Mapped[str] = mapped_column(String(128))
    author: Mapped[str] = mapped_column(String(128), default="")

    title: Mapped[str] = mapped_column(String(512))
    body: Mapped[str] = mapped_column(Text, default="")

    score: Mapped[int] = mapped_column(Integer, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, default=0)

    url: Mapped[str] = mapped_column(String(1024), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pulled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
