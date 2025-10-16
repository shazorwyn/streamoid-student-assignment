from fastapi import FastAPI
from pydantic import BaseModel

# Database setup
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
