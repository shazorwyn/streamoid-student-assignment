from typing import Optional

from sqlalchemy import String, Column, Integer

from pydantic import BaseModel, Field, model_validator

from .database import Base


class Product(Base):
    __tablename__ = "products"
    sku = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    color = Column(String)
    size = Column(String)
    mrp = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer)


class ProductBase(BaseModel):
    sku: str = Field(...)
    name: str = Field(...)
    brand: str = Field(...)
    color: str = Field(None)
    size: str = Field(None)
    mrp: int = Field(ge=0)
    price: int = Field(ge=0)
    quantity: int = Field(None, ge=0)

    @model_validator(mode='after')
    def price_less_than_mrp(self) -> 'ProductBase':
        if self.price > self.mrp:
            raise ValueError('Price must be less than or equal to MRP')
        return self

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    brand: Optional[str] = Field(None, description="Filter by brand")
    color: Optional[str] = Field(None, description="Filter by color")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price")


class UploadSummary(BaseModel):
    stored: int
    failed: list[dict]

