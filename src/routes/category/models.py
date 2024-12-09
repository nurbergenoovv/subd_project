from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    tickets = relationship("Ticket", back_populates="category", cascade="all, delete-orphan")
    users = relationship("User", back_populates="category", cascade="all, delete-orphan")