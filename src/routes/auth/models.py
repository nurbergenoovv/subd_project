from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base
from src.routes.category.models import Category

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    window = Column(Integer, default=0, nullable=True)
    is_admin = Column(Boolean, default=False)
    token = Column(String, unique=True, index=True, nullable=True)
    reset_token = Column(String, unique=True, index=True, nullable=True)
    category_id = Column(Integer, ForeignKey(Category.id), default=None, nullable=True)

    category = relationship("Category", back_populates="users") 
    tickets = relationship("Ticket", back_populates="user")