from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import relationship
from src.database import Base

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    fromm = Column(Time, nullable=False)
    to = Column(Time, nullable=False)