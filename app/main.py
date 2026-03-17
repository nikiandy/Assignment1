# inventory api - main file
from contextlib import asynccontextmanager
import os
import time

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from pymongo import MongoClient
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# db connection settings
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "inventory_db"
COLLECTION_NAME = "products"


# pydantic models for request validation
class Product(BaseModel):
    ProductID: int = Field(..., gt=0)
    Name: str = Field(..., min_length=1, max_length=500)
    UnitPrice: float = Field(..., gt=0, le=1000000)
    StockQuantity: int = Field(..., ge=0, le=100000)
    Description: str = Field(..., min_length=1, max_length=2000)


class ProductCreate(BaseModel):
    ProductID: int = Field(..., gt=0)
    Name: str = Field(..., min_length=1, max_length=500)
    UnitPrice: float = Field(..., gt=0, le=1000000)
    StockQuantity: int = Field(..., ge=0, le=100000)
    Description: str = Field(..., min_length=1, max_length=2000)


# returns the products collection from mongodb
def get_db():
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME][COLLECTION_NAME]


# for monitoring - tracks requests and how long they take
REQUEST_COUNT = Counter(
    "inventory_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "inventory_api_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Inventory Management API",
    description="Complete API for product inventory management",
    version="1.0.0",
    lifespan=lifespan,
)


# middleware to record each request for prometheus
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path or "unknown"
    method = request.method
    status = str(response.status_code)
    REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
    return response


# prometheus scrapes this for metrics
@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# fetch one product by id
@app.get("/getSingleProduct")
def get_single_product(product_id: int = Query(..., gt=0)):
    db = get_db()
    product = db.find_one({"ProductID": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["_id"] = str(product["_id"])
    return product


# get all products in the db
@app.get("/getAll")
def get_all():
    db = get_db()
    products = list(db.find({}))
    for p in products:
        p["_id"] = str(p["_id"])
    return products


# add a new product, checks id is unique first
@app.post("/addNew")
def add_new(product: ProductCreate):
    db = get_db()
    if db.find_one({"ProductID": product.ProductID}):
        raise HTTPException(status_code=400, detail="Product ID already exists")
    doc = product.model_dump()
    db.insert_one(doc.copy())
    return {"message": "Product added successfully", "product": doc}


# delete product by id
@app.delete("/deleteOne")
def delete_one(product_id: int = Query(..., gt=0)):
    db = get_db()
    result = db.delete_one({"ProductID": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


# find products whose name starts with given letter
@app.get("/startsWith")
def starts_with(
    letter: str = Query(..., min_length=1, max_length=1)
):
    letter = letter.upper()
    db = get_db()
    products = list(db.find({"Name": {"$regex": f"^{letter}", "$options": "i"}}))
    for p in products:
        p["_id"] = str(p["_id"])
    return products


# get up to 10 products in id range, sorted by id
@app.get("/paginate")
def paginate(
    start_id: int = Query(..., gt=0),
    end_id: int = Query(..., gt=0),
):
    if start_id > end_id:
        raise HTTPException(
            status_code=400, detail="start_id must be less than or equal to end_id"
        )
    db = get_db()
    products = list(
        db.find(
            {"ProductID": {"$gte": start_id, "$lte": end_id}}
        ).sort("ProductID", 1).limit(10)
    )
    for p in products:
        p["_id"] = str(p["_id"])
    return products


# convert product price from usd to eur using live rate
@app.get("/convert")
async def convert(
    product_id: int = Query(..., gt=0)
):
    db = get_db()
    product = db.find_one({"ProductID": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # get usd to eur rate from frankfurter api
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.frankfurter.dev/v1/latest",
                params={"base": "USD", "symbols": "EUR"},
            )
            response.raise_for_status()
            data = response.json()
            rate = data["rates"]["EUR"]
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch exchange rate: {str(e)}"
            )

    # convert and round to 2 decimals
    price_usd = product["UnitPrice"]
    price_eur = round(price_usd * rate, 2)

    return {
        "ProductID": product_id,
        "Name": product["Name"],
        "PriceUSD": price_usd,
        "PriceEUR": price_eur,
        "ExchangeRate": rate,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
