from fastapi import FastAPI, HTTPException

from app import services
from app.db import create_tables
from app.schemas import CreateOrderResponseModel, CreateOrderModel

app = FastAPI()
create_tables()


@app.post(
    "/orders",
    status_code=201,
    response_model=CreateOrderResponseModel,
    response_model_by_alias=True,
)
async def create_order(model: CreateOrderModel):
    try:
        order_response = services.create_order(model=model)
        return order_response

    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while placing the order")
