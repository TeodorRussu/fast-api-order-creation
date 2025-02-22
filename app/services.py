import uuid
from datetime import datetime, timezone

from app.db import get_db
from app.exceptions import OrderPlacementException, OrderPersistingException
from app.models import OrderEntity, OrderStatus
from app.schemas import CreateOrderModel, CreateOrderResponseModel
from app.stock_exchange import place_order, OrderPlacementError
from app.types import Order


def create_order(model: CreateOrderModel):
    with next(get_db()) as db:
        order_id = str(uuid.uuid4())
        order_entity_initiated = create_order_entity(model, order_id, OrderStatus.INITIATED)
        order_domain = map_entity_to_order(order_entity_initiated)
        try:
            # Step 1: Persist the initial order with 'initiated' status
            persist_order_to_db(db, order_entity_initiated)

            # Step 2: Attempt to place the order at the stock exchange
            place_order(order_domain)

            # Step 3: If successful, create a new record with 'completed' status
            order_entity_completed = create_order_entity(model, order_id, OrderStatus.COMPLETED)
            persist_order_to_db(db, order_entity_completed)

        except OrderPlacementError as exception:
            print(f"Error creating order at stock exchange: {exception}")
            # Step 4: If failed, create a new record with 'exchange order failed' status
            order_entity_failed = create_order_entity(model, order_id, OrderStatus.EXCHANGE_CREATION_FAILED)
            persist_order_to_db(db, order_entity_failed)
            raise OrderPlacementException(f"Order placement failed: {exception}")

        except OrderPersistingException as exception:
            print(f"Error persisting the order to the database: {exception}")
            # Step 4: If the database persisting failed, create a new record with 'database persisting failed' status
            order_entity_failed = create_order_entity(model, order_id, OrderStatus.DATABASE_PERSISTENCE_FAILED)
            persist_order_to_db(db, order_entity_failed)
            raise OrderPlacementException(f"Database persistence failed: {exception}")

        order_response = map_order_to_response(order_domain)
        return order_response


def persist_order_to_db(db, order_entity):
    db.add(order_entity)
    db.commit()
    db.refresh(order_entity)


def map_entity_to_order(order_entity: OrderEntity) -> Order:
    """
    Converts an OrderEntity (DB model) to an Order (domain model)
    so it can be passed to the place_order function.
    """
    return Order(
        id=order_entity.id,
        created_at=order_entity.created_at,
        type=order_entity.type,
        side=order_entity.side,
        instrument=order_entity.instrument,
        limit_price=order_entity.limit_price,
        quantity=order_entity.quantity,
    )


def map_order_to_response(order: Order) -> CreateOrderResponseModel:
    """
    Converts an Order (domain model) to CreateOrderResponseModel
    so it can be returned as a response to the client.
    """
    return CreateOrderResponseModel(
        id=order.id_,
        created_at=order.created_at,
        type=order.type_,
        side=order.side,
        instrument=order.instrument,
        limit_price=order.limit_price,
        quantity=order.quantity,
    )


def create_order_entity(model: CreateOrderModel, order_id: str, status: OrderStatus) -> OrderEntity:
    """
    Converts the incoming CreateOrderModel to an OrderEntity (DB model).
    Set the status dynamically based on the process stage.
    """
    return OrderEntity(
        id=order_id,
        created_at=datetime.now(timezone.utc),
        type=model.type_.value,
        side=model.side.value,
        instrument=model.instrument,
        limit_price=model.limit_price,
        quantity=model.quantity,
        status=status,  # Set status dynamically
    )
