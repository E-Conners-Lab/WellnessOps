"""Partner management routes. Auth required (SEC-02)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.partner import Partner
from app.db.models.user import User
from app.schemas.common import APIResponse
from app.schemas.partner import PartnerCreate, PartnerResponse, PartnerUpdate

router = APIRouter()


@router.get("")
async def list_partners(
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    query = select(Partner).where(Partner.is_active.is_(True)).order_by(Partner.name)
    if category:
        query = query.where(Partner.category == category)
    result = await db.execute(query)
    return APIResponse(
        data=[PartnerResponse.model_validate(p).model_dump() for p in result.scalars().all()]
    )


@router.post("", status_code=201)
async def create_partner(
    body: PartnerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    partner = Partner(**body.model_dump())
    db.add(partner)
    await db.flush()
    return APIResponse(data=PartnerResponse.model_validate(partner).model_dump())


@router.put("/{partner_id}")
async def update_partner(
    partner_id: UUID,
    body: PartnerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
    await db.flush()
    return APIResponse(data=PartnerResponse.model_validate(partner).model_dump())


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    partner.is_active = False
    await db.flush()
    return APIResponse(data={"message": "Partner deactivated"})
