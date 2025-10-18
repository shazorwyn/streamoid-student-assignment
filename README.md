# Streamoid Product Management Backend

A FastAPI backend service for uploading, validating, storing, and filtering product data from CSV files.

## Features

1. CSV Upload & Validation
    1. Upload CSV files containing product data.
    2. Validate each row:
        - Required fields: sku, name, brand, mrp, price.
        - Price ≤ MRP.
        - Quantity ≥ 0.
        - Avoid duplicate SKUs.
2. Database Storage in SQLite.
3. List Products
    - Paginated retrieval of all products: /products.
4. Search / Filter Products
    - Filter by brand, color, or price range: /products/search.
    - Supports partial string matching for brand and color.
    - Supports pagination.
5. Clear Database ***(Only for testing)***
    - Delete all products with confirmation: /products/clear?confirm=true.

## Tech Stack
- Python 3.12.4
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Project Structure

```
project/
│
├─ app/
│  ├─ main.py          # FastAPI application with endpoints
│  ├─ models.py        # SQLAlchemy & Pydantic models
│  ├─ database.py      # Database setup and session
│  └─ utils.py         # CSV parsing and search utility functions
│
├─ Pipfile
├─ Pipfile.lock
```
## Setup Instructions
1. Clone the repository
```
git clone <repo-url>
cd project
```
2. Install dependencies
```
pip install pipenv
pipenv install
pipenv shell
```
3. Run the FastAPI server
```
uvicorn app.main:app --reload
```
The API will be accessible at ```http://127.0.0.1:8000```.

4. API Documentation (Swagger UI)

Visit: ```http://127.0.0.1:8000/docs``` or Redoc: ```http://127.0.0.1:8000/redoc```

## API Endpoints
### 1. Upload CSV

#### POST ```/upload```

- Description: Upload a CSV file of products.
- Form Field: file (CSV file)
- Response:
```
{
  "stored": 10,
  "failed": [
    {"row": 3, "error": "Duplicate SKU TSHIRT-RED-001 already exists."},
    {"row": 5, "error": ["Price must be less than or equal to MRP"]}
  ]
}
```
### 2. List Products

#### GET ```/products?page=1&limit=10```

- Description: Retrieve paginated products.
- Query Parameters:
    - ```page``` (default=1)
    - ```limit``` (default=10, max=100)
- Response:
```
[
  {
    "sku": "TSHIRT-RED-001",
    "name": "Classic Cotton T-Shirt",
    "brand": "StreamThreads",
    "color": "Red",
    "size": "M",
    "mrp": 799,
    "price": 499,
    "quantity": 20
  },
  ...
]
```
### 3. Search / Filter Products

#### GET ```/products/search?brand=StreamThreads&color=Red&min_price=400&max_price=800&page=1&limit=10```

- **Description:** Filter products by brand, color, and price range. Supports partial matches.
- Query Parameters:
    - brand (optional)
    - color (optional)
    - min_price (optional)
    - max_price (optional)
    - page (default=1)
    - limit (default=10, max=100)
    - Response:
```
[
  {
    "sku": "TSHIRT-RED-001",
    "name": "Classic Cotton T-Shirt",
    "brand": "StreamThreads",
    "color": "Red",
    "size": "M",
    "mrp": 799,
    "price": 499,
    "quantity": 20
  }
]
```
### 4. Clear Database

#### DELETE ```/products/clear?confirm=true```

Description: Delete all products in the database. Requires confirm=true.
Response:
```
{
  "message": "All products cleared. Total rows deleted: 42"
}
```
If confirm is false or missing:
```
{
  "message": "Deletion not confirmed. Please set confirm=true to clear the database."
}
```
## Testing via CLI

### Upload CSV:
```
curl -X POST "http://127.0.0.1:8000/upload" -F "file=@products.csv"
```

### List products:
```
curl "http://127.0.0.1:8000/products?page=1&limit=5"
```

### Search products:
```
curl "http://127.0.0.1:8000/products/search?brand=StreamThreads&min_price=500"
```

### Clear database:
```
curl -X DELETE "http://127.0.0.1:8000/products/clear?confirm=true"
```

## Notes

- CSV file must have headers: ```sku,name,brand,color,size,mrp,price,quantity```.
- Validation errors are reported per row and do not block other valid rows.
- Pagination is implemented with page and limit query parameters for both listing and search endpoints.
