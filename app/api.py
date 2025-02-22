import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, condecimal, conint, constr, root_validator
from sqlalchemy.orm import Session

from app.db import engine, Base, get_db, create_tables
from app.models import OrderEntity
from app.types import Order, OrderSide, OrderType

app = FastAPI()
create_tables()


class CreateOrderModel(BaseModel):
    type_: OrderType = Field(..., alias="type")
    side: OrderSide
    instrument: constr(min_length=12, max_length=12)
    limit_price: Optional[condecimal(decimal_places=2)]
    quantity: conint(gt=0)

    @root_validator
    def validator(cls, values: dict):
        if values.get("type_") == "market" and values.get("limit_price"):
            raise ValueError(
                "Providing a `limit_price` is prohibited for type `market`"
            )

        if values.get("type_") == "limit" and not values.get("limit_price"):
            raise ValueError("Attribute `limit_price` is required for type `limit`")

        return values


class CreateOrderResponseModel(BaseModel):
    id: str


@app.post(
    "/orders",
    status_code=201,
    response_model=CreateOrderResponseModel,
    response_model_by_alias=True,
)
async def create_order(model: CreateOrderModel, db: Session = Depends(get_db)):
    order_id = str(uuid.uuid4())
    try:
        order = OrderEntity(
            id=order_id,
            created_at=datetime.now(),
            type=model.type_.value,
            side=model.side.value,
            instrument=model.instrument,
            limit_price=model.limit_price,
            quantity=model.quantity,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        order_response = CreateOrderResponseModel(
            id=order.id,
        )
        return order_response

    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while placing the order")
