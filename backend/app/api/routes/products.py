"""Product management routes. Auth required (SEC-02)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.common import APIResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.get("")
async def list_products(
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    query = select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    if category:
        query = query.where(Product.category == category)
    result = await db.execute(query)
    return APIResponse(
        data=[ProductResponse.model_validate(p).model_dump() for p in result.scalars().all()]
    )


@router.post("", status_code=201)
async def create_product(
    body: ProductCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    product = Product(**body.model_dump())
    db.add(product)
    await db.flush()
    return APIResponse(data=ProductResponse.model_validate(product).model_dump())


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.flush()
    return APIResponse(data=ProductResponse.model_validate(product).model_dump())


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    await db.flush()
    return APIResponse(data={"message": "Product deactivated"})
