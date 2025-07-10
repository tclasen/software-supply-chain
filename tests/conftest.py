from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from software_supply_chain.web import app as web_app


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(web_app) as _client:
        yield _client
