from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Integer

from fastapi import UploadFile, File, Query, Depends, HTTPException, FastAPI
from pydantic import BaseModel, Field
from typing import Annotated

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
    sku: str
    name: str
    brand: str
    color: str | None = None
    size: str | None = None
    mrp: int
    price: int
    quantity: int

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
            status_code=400, detail="Invalid file type. Please upload a CSV file.")
    file_content = await file.read()
    summary = parse_and_store_csv(db, file_content)
    return summary


@app.get("/products", response_model=list[ProductBase])
def get_products(db=Depends(get_db)):
    products = db.query(Product).all()
    return products


class ProductFilter(BaseModel):
    brand: str = Field(None, description="Filter by brand")
    color: str = Field(None, description="Filter by color")
    min_price: int = Field(None, ge=0, description="Minimum price")
    max_price: int = Field(None, ge=0, description="Maximum price")


@app.get("/products/search", response_model=list[ProductBase])
def search_products(filter_query: Annotated[ProductFilter, Query()], db=Depends(get_db)):
    products = get_searched_products(filter_query)
    return products


def parse_and_store_csv(db, file_content: bytes):
    pass


def get_searched_products(filter_query: ProductFilter, db):
    query = db.query(Product)
    if filter_query.brand:
        query = query.filter(Product.brand == filter_query.brand)
    if filter_query.color:
        query = query.filter(Product.color == filter_query.color)
    if filter_query.min_price is not None:
        query = query.filter(Product.price >= filter_query.min_price)
    if filter_query.max_price is not None:
        query = query.filter(Product.price <= filter_query.max_price)
    return query.all()
