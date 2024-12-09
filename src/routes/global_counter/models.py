from sqlalchemy import Column, Integer, BigInteger
from src.database import Base

class Counter(Base):
    __tablename__ = "counter"

    id = Column(Integer, primary_key=True, index=True)
    current_counter = Column(BigInteger, index=False, default=0)