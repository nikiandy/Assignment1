import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient

# same db as the api uses
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "inventory_db"
COLLECTION_NAME = "products"


# read csv and convert each row to a dict
def load_csv_to_json(csv_path: str) -> list[dict]:
    products = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = {
                "ProductID": int(row["ProductID"]),
                "Name": row["Name"],
                "UnitPrice": float(row["UnitPrice"]),
                "StockQuantity": int(row["StockQuantity"]),
                "Description": row["Description"],
            }
            products.append(product)
    return products


# clear collection, insert all products, add index on ProductID
def load_into_mongodb(products: list[dict]) -> None:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    collection.delete_many({})
    collection.insert_many(products)
    collection.create_index("ProductID", unique=True)

    print(f"Successfully loaded {len(products)} products into MongoDB.")
    client.close()


# find csv in project root and load it
def main():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "products.csv"
    )

    if not os.path.exists(csv_path):
        print(f"Error: products.csv not found at {csv_path}")
        sys.exit(1)

    products = load_csv_to_json(csv_path)
    load_into_mongodb(products)


if __name__ == "__main__":
    main()
