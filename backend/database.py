"""
database.py
-----------
SQLite database setup using SQLAlchemy.
Stores user listening history and ratings for the collaborative model.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/melodix.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserRating(Base):
    __tablename__ = "user_ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    song_id = Column(String, index=True)
    rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class ListeningHistory(Base):
    __tablename__ = "listening_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    song_id = Column(String, index=True)
    listened_at = Column(DateTime, default=datetime.utcnow)
    play_count = Column(Integer, default=1)


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
