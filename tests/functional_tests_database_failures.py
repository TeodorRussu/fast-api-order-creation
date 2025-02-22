from unittest import mock

import pytest

from app.exceptions import OrderPlacementException, OrderPersistingException
from app.models import OrderEntity, OrderStatus
from app.schemas import CreateOrderModel
from app.services import create_order, persist_order_to_db


# Mock the `persist_order_to_db` function in `services`
@pytest.fixture
def mock_persist_order():
    with mock.patch('app.services.persist_order_to_db') as mock_persist:
        yield mock_persist


def test_create_order_when_db_persist_fails(mock_persist_order, db_session):
    """
    Test scenario:
    - first database insert -> fail
    - second database insert(with status DATABASE_PERSISTENCE_FAILED) -> success:

    expected records in the db:
    - 1 record with status DATABASE_PERSISTENCE_FAILED
    """
    # Arrange
    model = CreateOrderModel(
        type='limit',
        side='buy',
        instrument='AAPL12345678',
        limit_price=150.0,
        quantity=10
    )

    # Store the original persist function
    original_persist = persist_order_to_db

    # Define a side effect to fail on the first call but work on subsequent ones
    def side_effect_persist(*args, **kwargs):
        if not hasattr(side_effect_persist, "first_call"):
            side_effect_persist.first_call = True
            raise OrderPersistingException("DB Insert Failed")  # Simulate DB failure
        return original_persist(*args, **kwargs)  # Call the real function afterward

    mock_persist_order.side_effect = side_effect_persist

    # Act
    with pytest.raises(OrderPlacementException):  # Ensure the exception is raised
        create_order(model)

    # Assert
    order_entities = db_session.query(OrderEntity).all()

    # Only one record should be created with status DATABASE_PERSISTENCE_FAILED
    assert len(order_entities) == 1

    failed_order = order_entities[0]
    assert failed_order.status == OrderStatus.DATABASE_PERSISTENCE_FAILED


def test_create_order_when_second_db_persist_fails(mock_persist_order, db_session):
    """
    Test scenario:
    - first database insert -> success
    - exchange order create -> success:
    - second database insert -> failed:
    - third database insert(with status DATABASE_PERSISTENCE_FAILED) -> success:

    expected to have in the db:
    - 1 record with status INITIATED
    - 1 record with status DATABASE_PERSISTENCE_FAILED
    """
    # Arrange
    model = CreateOrderModel(
        type='limit',
        side='buy',
        instrument='AAPL12345678',
        limit_price=150.0,
        quantity=10
    )

    # Step 1: First DB insert succeeds, second one fails
    persist_call_counter = 0

    def side_effect_persist(*args, **kwargs):
        nonlocal persist_call_counter
        persist_call_counter += 1
        if persist_call_counter == 2:  # Fail on second persist attempt
            raise OrderPersistingException("DB Insert Failed")
        return persist_order_to_db(*args, **kwargs)  # Call original function otherwise

    mock_persist_order.side_effect = side_effect_persist

    # Act
    with pytest.raises(OrderPlacementException):  # Ensure the exception is raised
        create_order(model)

    # Assert
    order_entities = db_session.query(OrderEntity).all()

    # We expect two records in the DB: INITIATED and DATABASE_PERSISTENCE_FAILED
    assert len(order_entities) == 2

    initiated_order = next(order for order in order_entities if order.status == OrderStatus.INITIATED)
    failed_order = next(order for order in order_entities if order.status == OrderStatus.DATABASE_PERSISTENCE_FAILED)

    assert initiated_order.status == OrderStatus.INITIATED
    assert failed_order.status == OrderStatus.DATABASE_PERSISTENCE_FAILED


def test_create_order_when_first_db_persist_fails(mock_persist_order, db_session):
    """
    Test scenario:
    - first database insert -> failure
    - exchange order create -> skipped:
    - second database insert -> skipped:
    - second database insert(with status DATABASE_PERSISTENCE_FAILED) -> failure:

    expected to have in the db:
    - no records in the db
    """
    # Arrange
    model = CreateOrderModel(
        type='limit',
        side='buy',
        instrument='AAPL12345678',
        limit_price=150.0,
        quantity=10
    )

    # Mock `persist_order_to_db` to fail on the first call, succeed on the second
    mock_persist_order.side_effect = [OrderPersistingException("DB Insert Failed"), None]

    # Act
    with pytest.raises(OrderPlacementException):  # Ensure the exception is raised
        create_order(model)

    # Assert
    order_entities = db_session.query(OrderEntity).all()

    # Expect NO records in the database
    assert len(order_entities) == 0
