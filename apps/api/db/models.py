from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    artist: Mapped[str] = mapped_column(Text)
    album: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lyrics: Mapped[list["Lyric"]] = relationship(back_populates="track")


class Lyric(Base):
    __tablename__ = "lyrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"))
    text: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    track: Mapped["Track"] = relationship(back_populates="lyrics")
