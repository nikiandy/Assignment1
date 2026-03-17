# tests for the api endpoints
import pytest
from fastapi.testclient import TestClient

from app.main import app


# client to hit the api in tests
@pytest.fixture
def api_client():
    return TestClient(app)


# get product by id
def test_get_single_product(api_client):
    response = api_client.get("/getSingleProduct?product_id=1001")
    assert response.status_code == 200
    data = response.json()
    assert data["ProductID"] == 1001
    assert "Name" in data
    assert "UnitPrice" in data


# 404 error when product doesnt exist
def test_get_single_product_not_found(api_client):
    response = api_client.get("/getSingleProduct?product_id=99999")
    assert response.status_code == 404


# get all products
def test_get_all(api_client):
    response = api_client.get("/getAll")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# add new product then clean up
def test_add_new(api_client):
    new_product = {
        "ProductID": 9999,
        "Name": "Test Product",
        "UnitPrice": 99.99,
        "StockQuantity": 10,
        "Description": "Test description for unit test",
    }
    response = api_client.post("/addNew", json=new_product)
    assert response.status_code == 200
    data = response.json()
    assert "Product added successfully" in data["message"]
    api_client.delete("/deleteOne?product_id=9999")


# add product, delete it, check success
def test_delete_one(api_client):
    new_product = {
        "ProductID": 9998,
        "Name": "To Delete",
        "UnitPrice": 1.00,
        "StockQuantity": 1,
        "Description": "Will be deleted",
    }
    api_client.post("/addNew", json=new_product)

    response = api_client.delete("/deleteOne?product_id=9998")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()


# 404 error when deleting non existent product
def test_delete_one_not_found(api_client):
    response = api_client.delete("/deleteOne?product_id=99999")
    assert response.status_code == 404


# filter by first letter of name
def test_starts_with(api_client):
    response = api_client.get("/startsWith?letter=s")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for product in data:
        assert product["Name"][0].upper() == "S"


# get products in id range
def test_paginate(api_client):
    response = api_client.get("/paginate?start_id=1001&end_id=1050")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


# mock the exchange rate api so test doesnt call it
def test_convert(api_client):
    from unittest.mock import MagicMock, patch
    mock_response = MagicMock()
    mock_response.json.return_value = {"rates": {"EUR": 0.92}}
    mock_response.raise_for_status = MagicMock()

    async def mock_get(*args, **kwargs):
        return mock_response

    mock_client = MagicMock()
    mock_client.get = mock_get

    class AsyncContextManager:
        async def __aenter__(self):
            return mock_client
        async def __aexit__(self, *args):
            pass

    with patch("app.main.httpx.AsyncClient", return_value=AsyncContextManager()):
        response = api_client.get("/convert?product_id=1001")
    assert response.status_code == 200
    data = response.json()
    assert "PriceUSD" in data
    assert "PriceEUR" in data
    assert "ExchangeRate" in data


# prometheus metrics should be there
def test_metrics_endpoint(api_client):
    response = api_client.get("/metrics")
    assert response.status_code == 200
    assert "inventory_api" in response.text or "python_" in response.text
