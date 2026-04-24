"""
Seed script: populate the app with 4 clients, observations, products, and partners
for end-to-end testing.

Usage: PYTHONPATH=backend python scripts/seed_test_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import async_session_factory, engine
from app.db.models.client import Client
from app.db.models.audit import AuditSession
from app.db.models.observation import Observation
from app.db.models.product import Product
from app.db.models.partner import Partner
from app.db.models.user import User
from sqlalchemy import select


# --- Test Data ---

CLIENTS = [
    {
        "display_name": "Sarah Mitchell",
        "notes": "First-time client. Lives alone in a 2BR apartment. Works from home in tech. Mentioned feeling 'stuck' but could not articulate why.",
        "budget_tier": "moderate",
        "has_wearable": True,
        "wearable_type": "Oura Ring",
        "pii_consent": False,
    },
    {
        "display_name": "The Andersons",
        "notes": "Young couple, both remote workers. Recently moved into a new build. Concerned about air quality and sleep. Very motivated.",
        "budget_tier": "premium",
        "has_wearable": True,
        "wearable_type": "Apple Watch",
        "financial_audit_consent": True,
        "pii_consent": False,
    },
    {
        "display_name": "Client-2024-007",
        "notes": "Single parent, two kids under 10. Townhome. Primary concern is feeling overwhelmed by clutter. Budget conscious but willing to invest in the kitchen.",
        "budget_tier": "budget",
        "has_wearable": False,
        "pii_consent": False,
    },
    {
        "display_name": "Marcus Reed",
        "notes": "Executive, high-rise condo. Travels frequently. Wants the space to feel like a retreat when he is home. Already invested in good furniture.",
        "budget_tier": "premium",
        "has_wearable": True,
        "wearable_type": "Whoop",
        "pii_consent": False,
    },
]

# Observations per client (client_index -> list of (room, content) tuples)
CLIENT_OBSERVATIONS = {
    0: [  # Sarah Mitchell
        ("entry", "Small apartment building hallway. Her door has a nice welcome mat but the entry is cluttered with shoes and mail."),
        ("living", "Main living area has decent natural light from one large window. Blinds are half-closed. A few plants but they are struggling. The couch faces a TV mounted too high."),
        ("living", "The art on the walls looks like it came with the apartment. Nothing personal. The space feels temporary even though she has lived here three years."),
        ("kitchen", "Fridge is about 60% condiments and takeout leftovers. Fresh produce drawer has some wilted greens. There is a nice knife set that looks unused."),
        ("kitchen", "No meal planning evidence. Takeout menus on the counter. The pantry has good intentions -- quinoa, lentils, spices -- but no system connecting them to actual meals."),
        ("hidden_spaces", "The hall closet is packed floor to ceiling. She admitted she has not opened some boxes since moving in. Under the bathroom sink is a mess of products, many expired."),
        ("bedroom", "Phone charges on the nightstand directly visible from the pillow. No blackout curtains. The bedroom also serves as overflow storage -- boxes stacked in the corner."),
        ("bedroom", "Temperature feels warm. No fan or AC visible. She mentioned waking up at 3am regularly."),
        ("workspace", "Works from the dining table. No proper chair -- using a wooden dining chair for 8+ hours. Laptop, no external monitor. Sightline is the kitchen counter."),
        ("client_responses", "Primary concern: 'I feel stuck and I do not know why.' Already tried: decluttering YouTube videos, bought organizing bins that are still in the closet. Ideal life: 'I want to come home and feel calm, not overwhelmed.'"),
        ("wearable", "Oura Ring data: Sleep score averaging 62. HRV trending down over 3 months. Readiness scores rarely above 70. REM sleep consistently low."),
    ],
    1: [  # The Andersons
        ("entry", "Beautiful new build. Entry is intentional -- shoe rack, key hooks, mirror. They have clearly thought about this space."),
        ("living", "Open concept. Lots of natural light. Biophilic design is strong -- large fiddle leaf fig, pothos on shelves. The sensory environment is good except for a subtle chemical smell from new materials."),
        ("living", "Furniture is ergonomic and intentional. Seating arrangement encourages conversation. Art is personal -- travel photos and a few original pieces."),
        ("kitchen", "Fridge is well-organized. Meal prep containers visible. Fresh produce, organized condiments. They have a whiteboard meal planner on the fridge."),
        ("kitchen", "The kitchen is set up for cooking. Good lighting, proper tools, spice rack organized. They eat at the dining table together."),
        ("hidden_spaces", "Closets are organized with matching bins and labels. Under-sink area is clean with a caddy system. The one junk drawer is minimal and functional."),
        ("bedroom", "Blackout curtains installed. Temperature controlled at 67F. No work visible. White noise machine. Nightstands have books, not phones. Phone charges in the hallway."),
        ("workspace", "Two dedicated desks in a shared office room. Standing desk converters. Ergonomic chairs. Good task lighting. Clear separation from living space."),
        ("wearable", "Apple Watch data: Sleep scores averaging 82. HRV stable and trending up. Activity rings consistently closed. Stress levels low."),
        ("financial", "Spending analysis shows 35% on housing, 15% on food (mostly groceries, minimal dining out), 10% on wellness (gym, supplements, air filters). Strong alignment with stated values."),
        ("client_responses", "Primary concern: 'The new build smell and whether our air quality is affecting us.' Already tried: opened windows, bought an air purifier for the bedroom. Ideal life: 'We want to know we are not poisoning ourselves with our own home.'"),
    ],
    2: [  # Client-2024-007
        ("entry", "Townhome entry doubles as a mudroom. Kid shoes, backpacks, and coats everywhere. No system for managing the daily drop zone."),
        ("living", "Living room is dominated by kids' toys. Very little natural light -- blinds closed to reduce glare on the TV. No plants. The couch has seen better days."),
        ("living", "The space feels chaotic but there is love here. Family photos on every surface. The sensory environment is loud -- TV usually on in the background."),
        ("kitchen", "Fridge has kids' snacks, juice boxes, some produce. Evidence of trying -- a meal planning printout on the fridge from 2 months ago, mostly unchecked."),
        ("kitchen", "Counter is cluttered. No clear workspace for cooking. Dishes in the sink. The pantry is overstocked with duplicates -- three boxes of the same cereal."),
        ("hidden_spaces", "Every closet is at capacity. The junk drawer does not close. Under the kitchen sink has cleaning products at kid-reaching height. Storage unit mentioned but not visited in months."),
        ("bedroom", "Her bedroom is the only semi-organized space. But work laptop is on the bed. Nightstand has a pile of parenting books and an empty water glass. No curtains."),
        ("workspace", "Works at the kitchen counter after kids go to bed. No dedicated space. Uses a barstool. Back pain mentioned."),
        ("client_responses", "Primary concern: 'I am drowning in stuff and I can not keep up.' Already tried: Marie Kondo book, hiring a cleaning service (too expensive to maintain). Ideal life: 'A home where I do not feel guilty about the mess every single day.'"),
    ],
    3: [  # Marcus Reed
        ("entry", "High-rise condo, 15th floor. Entry is sleek -- marble floor, minimal decor. A console table with a nice bowl for keys. Very intentional."),
        ("living", "Floor-to-ceiling windows with a city view. Automated blinds. The furniture is high-end and comfortable. Art is curated -- two original pieces and a photography collection."),
        ("living", "The space is beautiful but feels like a hotel. There is nothing personal beyond the art. No plants, no books visible, no evidence of hobbies. It is designed for looking at, not living in."),
        ("kitchen", "Fridge is nearly empty -- sparkling water, protein shakes, some condiments. He admitted to eating most meals out or ordering in. The kitchen looks unused."),
        ("kitchen", "Top-of-the-line appliances that have barely been touched. No cooking tools in the drawers. The dishwasher had two glasses in it."),
        ("hidden_spaces", "Closet is impeccably organized -- clearly a professional closet system. Under the bathroom sink is minimal and clean. No junk drawer (he said he does not believe in them)."),
        ("bedroom", "Motorized blackout shades. High-thread-count sheets. Temperature controlled. BUT -- his phone and two work monitors are visible from the bed. The bedroom doubles as a secondary office."),
        ("bedroom", "Despite the perfect setup, he reports poor sleep. Whoop data confirms it."),
        ("workspace", "Primary workspace is a dedicated room with a standing desk, three monitors, and an ergonomic chair. The problem is the second setup in the bedroom."),
        ("wearable", "Whoop data: Sleep performance averaging 55%. HRV dropping over 6 months. Strain scores high but recovery scores low. Classic overtraining pattern."),
        ("client_responses", "Primary concern: 'I have spent a lot of money on this place and I still do not sleep well.' Already tried: new mattress ($$), sleep supplements, cold plunge. Ideal life: 'I want to come home from a trip and actually recover instead of just continuing the grind.'"),
    ],
}

PRODUCTS = [
    {"name": "Molekule Air Pro", "brand": "Molekule", "category": "air_quality", "price_range": "$400-600", "why_recommended": "PECO technology destroys VOCs and pollutants at molecular level. Ideal for new builds with off-gassing concerns.", "best_for": "New construction, renovation, chemical sensitivity"},
    {"name": "Purple Harmony Pillow", "brand": "Purple", "category": "sleep", "price_range": "$150-180", "why_recommended": "Grid technology adapts to head position. Good for clients who sleep hot.", "best_for": "Hot sleepers, neck pain"},
    {"name": "BLUblox Sleep+ Glasses", "brand": "BLUblox", "category": "lighting", "price_range": "$80-120", "why_recommended": "Blocks blue and green light after sunset. Clinical-grade lens tinting.", "best_for": "Screen-heavy evenings, shift workers"},
    {"name": "Circadian Optics Light Therapy Lamp", "brand": "Circadian Optics", "category": "lighting", "price_range": "$40-60", "why_recommended": "10000 lux for morning light exposure. Compact enough for any desk.", "best_for": "Low natural light, seasonal affect, slow mornings"},
    {"name": "Melitta Pour-Over System", "brand": "Melitta", "category": "food", "price_range": "$15-25", "why_recommended": "Simple ritual that replaces reactive morning habits with intentional ones.", "best_for": "Morning routine building, mindfulness practice"},
    {"name": "Open Spaces Entryway System", "brand": "Open Spaces", "category": "organization", "price_range": "$200-400", "why_recommended": "Modular wall-mounted system that creates an intentional entry ritual.", "best_for": "Small entries, families, apartment dwellers"},
    {"name": "Herman Miller Aeron Chair", "brand": "Herman Miller", "category": "ergonomics", "price_range": "$1200-1800", "why_recommended": "Gold standard ergonomic chair. PostureFit SL supports the full spine.", "best_for": "8+ hour desk workers, back pain"},
    {"name": "Coway Airmega 400", "brand": "Coway", "category": "air_quality", "price_range": "$450-550", "why_recommended": "Dual filtration with real-time air quality monitoring. Covers up to 1560 sq ft.", "best_for": "Large rooms, allergy sufferers"},
    {"name": "The Upright Go 2", "brand": "Upright", "category": "ergonomics", "price_range": "$60-80", "why_recommended": "Posture training device. Gentle vibration when slouching. Builds awareness.", "best_for": "Desk workers, posture correction"},
    {"name": "Botanica Air Purifying Plants Bundle", "brand": "Botanica", "category": "biophilic", "price_range": "$80-150", "why_recommended": "Curated low-maintenance plants (pothos, snake plant, ZZ) that improve air quality and add life to spaces.", "best_for": "Beginners, low light spaces"},
]

PARTNERS = [
    {"name": "Maria Chen", "business_name": "Organized Living Co", "category": "organizer", "location": "Nashville, TN", "why_recommended": "Specializes in families with kids. Gentle approach, not judgy. Creates systems that survive real life.", "pricing_tier": "moderate"},
    {"name": "Chef Andre Williams", "business_name": "Nourish Meal Prep", "category": "chef", "location": "Nashville, TN", "why_recommended": "Does weekly meal prep sessions in-home. Teaches while cooking. Clients learn to cook for themselves.", "pricing_tier": "premium"},
    {"name": "Dr. Lena Park", "business_name": "Integrated Wellness", "category": "functional_medicine", "location": "Nashville, TN", "why_recommended": "Functional medicine approach. Runs comprehensive panels. Good at connecting environmental factors to biomarkers.", "pricing_tier": "premium"},
    {"name": "Jake Torres", "business_name": "Torres Training", "category": "trainer", "location": "Nashville, TN", "why_recommended": "Focus on movement integration, not just gym workouts. Helps clients build movement into daily routines.", "pricing_tier": "moderate"},
    {"name": "Sarah Kim", "business_name": "Restful Nights Sleep Consulting", "category": "sleep_specialist", "location": "Nashville, TN", "why_recommended": "CBT-I certified. Works with clients on sleep hygiene, environment optimization, and behavioral changes.", "pricing_tier": "moderate"},
    {"name": "Green Thumb Nashville", "business_name": "Green Thumb Nashville", "category": "plants", "location": "Nashville, TN", "why_recommended": "Plant consultation service. Assesses light conditions and recommends appropriate species. Includes maintenance plan.", "pricing_tier": "budget"},
    {"name": "Dr. Amy Walsh", "category": "therapist", "location": "Nashville, TN", "why_recommended": "Specializes in environmental psychology and the connection between living spaces and mental health.", "pricing_tier": "moderate"},
    {"name": "BreatheEasy HVAC", "business_name": "BreatheEasy HVAC Services", "category": "smart_home", "location": "Nashville, TN", "why_recommended": "HVAC assessment and air quality testing. Can install ERV systems and whole-home filtration.", "pricing_tier": "premium"},
]


async def seed():
    # Get admin user
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "practitioner@wellnessops.local")
        )
        user = result.scalar_one_or_none()
        if not user:
            print("ERROR: Admin user not found. Run seed_db.py first.")
            return

        user_id = user.id
        print(f"Using admin user: {user.email} (id: {user_id})")

        # Create products
        print("\nCreating products...")
        for p in PRODUCTS:
            product = Product(**p)
            session.add(product)
        await session.commit()
        print(f"  Created {len(PRODUCTS)} products")

        # Create partners
        print("\nCreating partners...")
        for p in PARTNERS:
            partner = Partner(**p)
            session.add(partner)
        await session.commit()
        print(f"  Created {len(PARTNERS)} partners")

        # Create clients with sessions and observations
        for i, client_data in enumerate(CLIENTS):
            print(f"\nCreating client: {client_data['display_name']}...")
            client = Client(user_id=user_id, **client_data)
            session.add(client)
            await session.flush()

            # Create audit session
            tier = "extended" if i == 1 else "core"
            audit = AuditSession(
                client_id=client.id,
                user_id=user_id,
                audit_tier=tier,
                status="observations_complete",
            )
            session.add(audit)
            await session.flush()

            # Add observations
            observations = CLIENT_OBSERVATIONS.get(i, [])
            for sort_order, (room, content) in enumerate(observations):
                obs = Observation(
                    session_id=audit.id,
                    room_area=room,
                    content=content,
                    observation_type="text",
                    is_from_structured_flow=False,
                    sort_order=sort_order,
                )
                session.add(obs)

            await session.commit()
            print(f"  Created session ({tier}) with {len(observations)} observations")

        print("\n--- Seed complete ---")
        print(f"Clients: {len(CLIENTS)}")
        print(f"Products: {len(PRODUCTS)}")
        print(f"Partners: {len(PARTNERS)}")
        print("\nYou can now log in and:")
        print("  1. Go to each client's session")
        print("  2. Click 'Generate Scores' on the scores page")
        print("  3. Generate a report and approve it")
        print("  4. Check the dashboard for calibration data")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
