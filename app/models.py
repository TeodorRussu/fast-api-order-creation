from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Float, Enum as SQLAlchemyEnum
from sqlalchemy.schema import PrimaryKeyConstraint

from app.db import Base


class OrderStatus(Enum):
    INITIATED = "initiated"
    COMPLETED = "completed"
    EXCHANGE_CREATION_FAILED = "exchange_creation_failed"
    DATABASE_PERSISTENCE_FAILED = "database_persistence_failed"


class OrderEntity(Base):
    __tablename__ = 'orders'  # Name of the table in the database

    id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    type = Column(String, nullable=False)
    side = Column(String, nullable=False)
    instrument = Column(String, nullable=False)
    limit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    status = Column(SQLAlchemyEnum(OrderStatus, name="order_status_enum"), nullable=False)

    # Define the composite primary key (id + status)
    __table_args__ = (
        PrimaryKeyConstraint('id', 'status', name='pk_order_id_status'),
    )
