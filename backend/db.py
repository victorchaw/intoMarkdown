from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DB_PATH = Path(__file__).parent.parent / "converter.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text, unique=True, nullable=False)
    folder_name = Column(String(500), nullable=False)
    output_name = Column(String(500), nullable=True)
    pdf_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="discovered")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("BookFile", back_populates="book", cascade="all, delete-orphan")


class BookFile(Base):
    __tablename__ = "book_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    filename = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=True)
    included = Column(Boolean, nullable=False, default=True)
    skip_reason = Column(String(100), nullable=True)

    book = relationship("Book", back_populates="files")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
