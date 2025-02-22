from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Float

from app.db import Base


class OrderEntity(Base):
    __tablename__ = 'orders'  # Name of the table in the database

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    type = Column(String, nullable=False)
    side = Column(String, nullable=False)
    instrument = Column(String, nullable=False)
    limit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)

