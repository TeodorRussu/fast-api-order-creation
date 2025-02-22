from unittest import mock

import pytest

from app.exceptions import OrderPlacementException
from app.models import OrderEntity, OrderStatus
from app.schemas import CreateOrderModel
from app.services import create_order


# Mock the `place_order` function in `stock_exchange`
@pytest.fixture
def mock_place_order():
    with mock.patch('app.stock_exchange.place_order') as mock_place:
        yield mock_place


# Mock random.random() to return a value >= 0.9 (so that it triggers the exception), simulating exchange create failure
@pytest.fixture
def mock_random():
    with mock.patch('random.random', return_value=0.9):
        yield


def test_create_order_when_place_order_fails(mock_place_order, db_session, mock_random):
    """
    Test scenario:
    - first database insert -> success
    - exchange order create -> fail:
    - second database insert(with status EXCHANGE_CREATION_FAILED) -> success:

    expected to have in the db:
    - 1 record with status INITIATED
    - 1 record with status EXCHANGE_CREATION_FAILED
    """
    model = CreateOrderModel(
        type='limit',
        side='buy',
        instrument='AAPL12345678',
        limit_price=150.0,
        quantity=10
    )

    with pytest.raises(OrderPlacementException):  # Ensure the exception is raised
        create_order(model)

    order_entities = db_session.query(OrderEntity).all()
    assert len(order_entities) == 2  # Two records: initiated and exchange failed

    initiated_order = next(order for order in order_entities if order.status == OrderStatus.INITIATED)
    failed_order = next(order for order in order_entities if order.status == OrderStatus.EXCHANGE_CREATION_FAILED)

    assert initiated_order.status == OrderStatus.INITIATED
    assert failed_order.status == OrderStatus.EXCHANGE_CREATION_FAILED

    """
    Another test case that can be implemented
    
    Test scenario:
    - first database insert -> success
    - exchange order create -> fail:
    - second database insert(with status EXCHANGE_CREATION_FAILED) -> fail:

    expected to have in the db:
    - 1 record with status INITIATED
    """
