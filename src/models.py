from sqlalchemy import Column, Integer
from src.database import Base

class GlobalTicketCounter(Base):
    __tablename__ = "global_ticket_counter"
    id = Column(Integer, primary_key=True, index=True, default=1)
    counter = Column(Integer, default=0)

