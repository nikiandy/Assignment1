Inventory Management API - Endpoints Reference
==============================================

Base URL: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

ENDPOINTS:
---------

1. GET /getSingleProduct
   Parameters: product_id (int, required) - Product ID number
   Returns: Single product details in JSON

2. GET /getAll
   Parameters: None
   Returns: All inventory in JSON format

3. POST /addNew
   Body (JSON): ProductID (int), Name (str), UnitPrice (float), StockQuantity (int), Description (str)
   Returns: Confirmation message

4. DELETE /deleteOne
   Parameters: product_id (int, required) - Product ID to delete
   Returns: Confirmation message

5. GET /startsWith
   Parameters: letter (str, required) - Single letter (e.g. "s")
   Returns: Products whose names start with the letter

6. GET /paginate
   Parameters: start_id (int), end_id (int) - Product ID range
   Returns: Batch of up to 10 products in range

7. GET /convert
   Parameters: product_id (int, required) - Product ID
   Returns: Price in EUR (uses live exchange rate API)

8. GET /metrics
   Parameters: None
   Returns: Prometheus metrics for API monitoring

FastAPI Documentation: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
