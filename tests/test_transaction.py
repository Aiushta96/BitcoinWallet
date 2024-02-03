import uuid
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import ANY

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from core import constants
from runner.setup import init_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(init_app())


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def user(self) -> dict[str, Any]:
        return {
            "username": self.faker.word(),
            "password": self.faker.word()
        }

    def unknown_id(self) -> uuid:
        return self.faker.uuid4()


def create_user(client: TestClient) -> uuid:
    user = Fake().user()
    response = client.post("/users", json=user)
    return response.json()["user"]["API_key"]


def create_wallet(client: TestClient, API_key: uuid) -> uuid:
    response = client.post("/wallets", json={"API_key": API_key})
    return response.json()["wallet"]["address"]


def test_should_create_transaction_same_user(client: TestClient) -> None:
    API_key = create_user(client)
    wallet_from = create_wallet(client, API_key)
    wallet_to = create_wallet(client, API_key)
    response = client.post("/transactions",
                           json={"API_key": API_key, "wallet_from": wallet_from, "wallet_to": wallet_to,
                                 "amount_in_satoshis": 100})
    assert response.status_code == 201
    assert response.json() == {}


def test_should_create_transaction_different_user(client: TestClient) -> None:
    API_key1 = create_user(client)
    wallet_from = create_wallet(client, API_key1)
    API_key2 = create_user(client)
    wallet_to = create_wallet(client, API_key2)
    response = client.post("/transactions",
                           json={"API_key": API_key1, "wallet_from": wallet_from, "wallet_to": wallet_to,
                                 "amount_in_satoshis": 100})
    assert response.status_code == 201
    assert response.json() == {}


def test_should_not_create(client: TestClient) -> None:
    API_key = Fake().unknown_id()
    wallet_from = Fake().unknown_id()
    wallet_to = Fake().unknown_id()

    response = client.post("/transactions", json={"API_key": API_key, "wallet_from": wallet_from, "wallet_to": wallet_to,
                                 "amount_in_satoshis": 100})
    assert response.status_code == 404
    assert response.json() == {'message': 'Wallet does not exist.'}
