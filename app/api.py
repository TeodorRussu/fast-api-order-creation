from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field, condecimal, conint, constr, root_validator

from app.types import Order, OrderSide, OrderType

app = FastAPI()


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


class CreateOrderResponseModel(Order):
    pass


@app.post(
    "/orders",
    status_code=201,
    response_model=CreateOrderResponseModel,
    response_model_by_alias=True,
)
async def create_order(model: CreateOrderModel):
    # TODO: Add your implementation here
    raise NotImplementedError()
