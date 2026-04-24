"""
Auto-referral matching service (Phase 6).
Matches low-scoring categories to relevant products and partners.
Included automatically in report generation.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.partner import Partner
from app.db.models.product import Product
from app.db.models.score import CategoryScore

logger = structlog.stdlib.get_logger()

# Maps scoring categories to product/partner categories
CATEGORY_TO_PRODUCT_CATEGORIES: dict[str, list[str]] = {
    "kitchen_flow": ["food", "organization", "supplements"],
    "sleep_environment": ["sleep", "lighting", "air_quality"],
    "natural_elements": ["biophilic", "air_quality", "lighting"],
    "movement": ["movement", "ergonomics"],
    "sensory": ["sensory", "air_quality", "lighting"],
    "hidden_spaces": ["organization"],
    "setup_vs_goals": ["organization"],
    "intention": [],
    "financial_alignment": [],
    "wearable_data": [],
    "ergonomics": ["ergonomics", "movement"],
    "art_aesthetic": ["biophilic", "sensory"],
    "library_learning": [],
    "vehicle": [],
    "workspace": ["ergonomics", "lighting"],
}

CATEGORY_TO_PARTNER_CATEGORIES: dict[str, list[str]] = {
    "kitchen_flow": ["chef", "nutritionist"],
    "sleep_environment": ["sleep_specialist", "functional_medicine"],
    "natural_elements": ["plants", "lighting", "smart_home"],
    "movement": ["trainer", "therapist"],
    "sensory": ["therapist", "acupuncture"],
    "hidden_spaces": ["organizer"],
    "setup_vs_goals": ["organizer", "therapist"],
    "intention": ["therapist"],
    "financial_alignment": [],
    "wearable_data": ["functional_medicine"],
    "ergonomics": ["ergonomics", "therapist"],
    "art_aesthetic": ["cleaning"],
    "library_learning": [],
    "vehicle": ["cleaning"],
    "workspace": ["ergonomics", "smart_home"],
}


async def match_referrals(
    db: AsyncSession,
    scores: list[CategoryScore],
    max_products_per_category: int = 3,
    max_partners_per_category: int = 2,
) -> dict:
    """Match low-scoring categories to relevant products and partners.

    Returns:
        {
            "product_matches": {category_key: [ProductResponse, ...]},
            "partner_matches": {category_key: [PartnerResponse, ...]},
        }
    """
    # Focus on categories scoring 7 or below (room for improvement)
    gap_categories = [s for s in scores if s.score <= 7]

    product_matches: dict[str, list[dict]] = {}
    partner_matches: dict[str, list[dict]] = {}

    for score in gap_categories:
        cat_key = score.category_key

        # Match products
        product_cats = CATEGORY_TO_PRODUCT_CATEGORIES.get(cat_key, [])
        if product_cats:
            result = await db.execute(
                select(Product)
                .where(
                    Product.is_active.is_(True),
                    Product.is_recommended.is_(True),
                    Product.category.in_(product_cats),
                )
                .order_by(Product.name)
                .limit(max_products_per_category)
            )
            products = result.scalars().all()
            if products:
                product_matches[cat_key] = [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "brand": p.brand,
                        "category": p.category,
                        "price_range": p.price_range,
                        "why_recommended": p.why_recommended,
                    }
                    for p in products
                ]

        # Match partners
        partner_cats = CATEGORY_TO_PARTNER_CATEGORIES.get(cat_key, [])
        if partner_cats:
            result = await db.execute(
                select(Partner)
                .where(
                    Partner.is_active.is_(True),
                    Partner.category.in_(partner_cats),
                )
                .order_by(Partner.name)
                .limit(max_partners_per_category)
            )
            partners = result.scalars().all()
            if partners:
                partner_matches[cat_key] = [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "business_name": p.business_name,
                        "category": p.category,
                        "location": p.location,
                        "why_recommended": p.why_recommended,
                    }
                    for p in partners
                ]

    logger.info(
        "referrals_matched",
        product_categories=len(product_matches),
        partner_categories=len(partner_matches),
    )

    return {
        "product_matches": product_matches,
        "partner_matches": partner_matches,
    }
