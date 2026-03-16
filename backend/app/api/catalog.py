import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product, ProductOption
from app.schemas.catalog import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.get("/{company_id}", response_model=list[ProductResponse])
async def list_products(
    company_id: uuid.UUID,
    category: str | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.company_id == company_id)
    if active_only:
        query = query.where(Product.is_active.is_(True))
    if category:
        query = query.where(Product.category == category)
    query = query.order_by(Product.display_order, Product.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}/{product_id}", response_model=ProductResponse)
async def get_product(
    company_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.company_id == company_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/{company_id}", response_model=ProductResponse, status_code=201)
async def create_product(
    company_id: uuid.UUID,
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    product = Product(company_id=company_id, **data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.patch("/{company_id}/{product_id}", response_model=ProductResponse)
async def update_product(
    company_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.company_id == company_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product
