import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ProductOptionCreate(BaseModel):
    name: str
    price: Decimal | None = None
    description: str | None = None
    is_default: bool = False


class ProductOptionResponse(ProductOptionCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    slug: str
    category: str | None = None
    description: str | None = None
    short_desc: str | None = None
    price: Decimal | None = None
    price_currency: str = "USD"
    price_notes: str | None = None
    unit: str | None = None
    specs: dict | None = None
    features: list[str] | None = None
    image_urls: list[str] | None = None
    video_url: str | None = None
    document_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    short_desc: str | None = None
    price: Decimal | None = None
    price_notes: str | None = None
    specs: dict | None = None
    features: list[str] | None = None
    image_urls: list[str] | None = None
    is_active: bool | None = None
    in_stock: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    slug: str
    category: str | None
    description: str | None
    short_desc: str | None
    price: Decimal | None
    price_currency: str
    price_notes: str | None
    unit: str | None
    specs: dict | None
    features: list | None
    image_urls: list | None
    video_url: str | None
    document_url: str | None
    is_active: bool
    in_stock: bool
    display_order: int
    options: list[ProductOptionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
