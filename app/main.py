from io import StringIO
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, Column, String, Integer

import csv

from fastapi import Query, UploadFile, File, Depends, HTTPException, FastAPI
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Annotated, Any, List, Dict, Optional

# Database setup
DATABASE_URL = "sqlite:///./streamoid.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    sku = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    color = Column(String)
    size = Column(String)
    mrp = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)


Base.metadata.create_all(bind=engine)

# Dependency to get DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models


class ProductBase(BaseModel):
    sku: str = Field(...)
    name: str = Field(...)
    brand: str = Field(...)
    color: str = Field(None)
    size: str = Field(None)
    mrp: int = Field(ge=0)
    price: int = Field(ge=0)
    quantity: int = Field(ge=0)

    @model_validator(mode='after')
    def price_less_than_mrp(self) -> 'ProductBase':
        if self.price > self.mrp:
            raise ValueError('Price must be less than or equal to MRP')
        return self

    class Config:
        from_attributes = True


class UploadSummary(BaseModel):
    stored: int
    failed: list[dict]


# FastAPI app setup
app = FastAPI()


@app.post("/upload", response_model=UploadSummary)
async def upload_products(file: UploadFile = File(...), db=Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a CSV file."
        )

    file_content = await file.read()
    summary = parse_and_store_csv(file_content, db)
    return summary


@app.get("/products", response_model=list[ProductBase])
def get_products(db=Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    offset = (page-1)*limit
    products = db.query(Product).offset(offset).limit(limit).all()
    return products


class ProductFilter(BaseModel):
    brand: Optional[str] = Field(None, description="Filter by brand")
    color: Optional[str] = Field(None, description="Filter by color")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price")


@app.get("/products/search", response_model=list[ProductBase])
def search_products(filter_query: Annotated[ProductFilter, Depends()], db=Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    products = get_searched_products(filter_query, db, page, limit)
    return products


def parse_and_store_csv(file_content: bytes, db: Session) -> dict:
    file_content_str = file_content.decode("utf-8")
    csv_file = StringIO(file_content_str)
    reader = csv.DictReader(csv_file)

    valid_products_to_add: List[Product] = []
    failed_rows: List[Dict[str, Any]] = []

    csv_rows = list(reader)
    csv_skus = [row.get("sku") for row in csv_rows if row.get("sku")]

    existing_skus = {sku for (sku,) in db.query(
        Product.sku).filter(Product.sku.in_(csv_skus)).all()}

    # Validation
    for row_num, row_data in enumerate(csv_rows, start=2):
        try:
            product_data = ProductBase(**row_data)
            if (product_data.sku in existing_skus):
                failed_rows.append({
                    "row": row_num,
                    "error": f"Duplicate SKU {product_data.sku} already exists."
                })
                continue
            db_product = Product(**product_data.model_dump())
            valid_products_to_add.append(db_product)
        except ValidationError as e:
            failed_rows.append({
                "row": row_num,
                "error": [err['msg'] for err in e.errors()]
            })
        except Exception as e:
            failed_rows.append({"row": row_num, "error": str(e)})

    # Storing in database
    stored_count = 0
    if valid_products_to_add:
        try:
            db.add_all(valid_products_to_add)
            db.commit()
            stored_count = len(valid_products_to_add)
        except IntegrityError as e:
            db.rollback()
            failed_rows.append({
                "error":   "Database Integrity check",
                "details": str(e)
            })
        except Exception as e:
            db.rollback()
            failed_rows.append({
                "error": "A database error occured",
                "details": str(e)
            })

    return {"stored": stored_count, "failed": failed_rows}


def get_searched_products(filter_query: ProductFilter, db, page, limit):
    query = db.query(Product)
    offset = (page-1)*limit
    if filter_query.brand:
        query = query.filter(Product.brand.ilike(f"%{filter_query.brand}%"))
    if filter_query.color:
        query = query.filter(Product.color.ilike(f"%{filter_query.color}%"))
    if filter_query.min_price is not None:
        query = query.filter(Product.price >= filter_query.min_price)
    if filter_query.max_price is not None:
        query = query.filter(Product.price <= filter_query.max_price)
    return query.offset(offset).limit(limit).all()
