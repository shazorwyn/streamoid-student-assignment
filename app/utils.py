import csv

from io import StringIO

from typing import Any, Dict, List

from pydantic import ValidationError

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import Product, ProductBase, ProductFilter


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
