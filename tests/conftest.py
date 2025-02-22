import pytest

from app.db import SessionLocal, Base, engine


# This fixture provides a fresh database session for each test function
@pytest.fixture(scope='function')
def db_session():
    # Create the tables for testing
    Base.metadata.create_all(bind=engine)

    # Create a new session
    db = SessionLocal()
    yield db

    # Rollback the transaction after each test to keep database state clean
    db.rollback()
    db.close()

    # Drop the tables to clean up after the test
    Base.metadata.drop_all(bind=engine)


import asyncio
import pytest


@pytest.fixture(autouse=True)
def set_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
