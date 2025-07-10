from fastapi import status
from fastapi.testclient import TestClient


def test_index(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert "Dependencies" in response.text
