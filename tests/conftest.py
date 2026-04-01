import os

import mongomock
import pytest

os.environ["TESTING"] = "1"


# runs before every test swaps real db for mongomock
@pytest.fixture(autouse=True)
def mock_mongodb(monkeypatch):
    client = mongomock.MongoClient()
    db = client["inventory_db"]
    collection = db["products"]

    # some sample data for the tests
    sample_products = [
        {
            "ProductID": 1001,
            "Name": "NVIDIA RTX 4090",
            "UnitPrice": 1599.99,
            "StockQuantity": 12,
            "Description": "High-end GPU",
        },
        {
            "ProductID": 1002,
            "Name": "AMD Ryzen 9 7950X",
            "UnitPrice": 549.00,
            "StockQuantity": 25,
            "Description": "16-core processor",
        },
        {
            "ProductID": 1003,
            "Name": "Samsung 990 Pro 2TB",
            "UnitPrice": 179.99,
            "StockQuantity": 40,
            "Description": "NVMe SSD",
        },
    ]
    collection.insert_many(sample_products)

    # point get_db at our fake collection
    def mock_get_db():
        return collection

    from app import main as app_module
    monkeypatch.setattr(app_module, "get_db", mock_get_db)

    yield collection
