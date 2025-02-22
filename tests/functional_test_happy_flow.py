from unittest import mock

import pytest

from app.models import OrderEntity, OrderStatus
from app.schemas import CreateOrderModel
from app.services import create_order


# Mock the `place_order` function in `stock_exchange`
@pytest.fixture
def mock_place_order():
    with mock.patch('app.stock_exchange.place_order') as mock_place:
        yield mock_place


def test__happy_flow__records_are_created_in_the_database_initiated_and_completed(mock_place_order, db_session):
    """
    on happy flow, the database should end up with 2 records with the same id, and the following statuses:
    INITIATED
    COMPLETED
    that means place order to exchange successfully executed
    """
    # Arrange
    model = CreateOrderModel(
        type='limit',  # Example type
        side='buy',  # Example side
        instrument='AAPL12345678',  # Example instrument
        limit_price=150.0,  # Example limit price
        quantity=10  # Example quantity
    )

    order_response = create_order(model)  # Call the service function

    # Check that two orders are created with the same order_id
    order_entities = db_session.query(OrderEntity).filter(OrderEntity.id == order_response.id_).all()

    assert len(order_entities) == 2  # Should be 2 records (initiated and completed)

    initiated_order = next(order for order in order_entities if order.status == OrderStatus.INITIATED)
    completed_order = next(order for order in order_entities if order.status == OrderStatus.COMPLETED)

    assert initiated_order.status == OrderStatus.INITIATED
    assert completed_order.status == OrderStatus.COMPLETED

    assert order_response.id_ == initiated_order.id
    assert order_response.type_ == model.type_
    assert order_response.side == model.side
    assert order_response.instrument == model.instrument
    assert order_response.limit_price == model.limit_price
    assert order_response.quantity == model.quantity
