from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
<<<<<<< HEAD
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker
=======
from sqlalchemy.orm import declarative_base, sessionmaker
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
from datetime import datetime


DATABASE_URL = "sqlite:///./rag_data.db" 
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
<<<<<<< HEAD
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
=======
    id = Column(Integer, primary_key=True, index=True)
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False) 
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db   
    finally:
        db.close()