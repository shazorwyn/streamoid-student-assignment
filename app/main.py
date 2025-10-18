from fastapi import Query, UploadFile, File, Depends, HTTPException, FastAPI

from typing import Annotated

from .database import get_db
from .models import Product, ProductBase, ProductFilter, UploadSummary
from .utils import parse_and_store_csv, get_searched_products

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


@app.get("/products/search", response_model=list[ProductBase])
def search_products(filter_query: Annotated[ProductFilter, Depends()], db=Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    products = get_searched_products(filter_query, db, page, limit)
    return products


@app.delete("/products/clear")
def clear_products(confirm: bool = Query(False, description="set true for confirm deletion(testing only)"), db=Depends(get_db)):
    if not confirm:
        return {"message": "Deletion not confirmed. Please set confirm=true to clear the database."}

    deleted_count = db.query(Product).delete()
    db.commit()
    return {"message": f"All products cleared. Total rows deleted: {deleted_count}"}
