import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db

DEFAULT_TEST_DATABASE_URL = "postgresql://tasklane:tasklane@localhost:5433/tasklane_test"


def assert_safe_test_database(url: str) -> None:
    """Refuse to run unless the database name ends with `_test`.

    The fixtures below create and drop every table on each test, so pointing
    them at a development or production database would destroy its data.
    """
    name = make_url(url).database or ""
    if not name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run tests: database {name!r} does not end with '_test'. "
            "Set TEST_DATABASE_URL to a dedicated test database."
        )


# Tests use their own variable on purpose. DATABASE_URL is the application's
# database (development, or production when running migrations), and the
# fixtures drop all tables on teardown.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
assert_safe_test_database(TEST_DATABASE_URL)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
