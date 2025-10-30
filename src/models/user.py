from sqlalchemy import Column, Integer, String
from src.db.config import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True)
    email = Column(String(50), index=True, unique=True)