"""
Demo seed script: populates the app with impressive, realistic data
for showcasing on LinkedIn. Creates a complete audit workflow with
AI-generated scores, reports, products, partners, and knowledge base entries.

Usage: PYTHONPATH=backend python scripts/seed_demo.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import async_session_factory, engine
from app.db.models.client import Client
from app.db.models.audit import AuditSession
from app.db.models.observation import Observation
from app.db.models.product import Product
from app.db.models.partner import Partner
from app.db.models.score import CategoryScore, get_score_label
from app.db.models.report import Report
from app.db.models.user import User
from app.db.models.knowledge import KnowledgeDocument
from sqlalchemy import select


PRODUCTS = [
    {"name": "Molekule Air Pro", "brand": "Molekule", "category": "air_quality", "price_range": "$400-600", "why_recommended": "PECO technology destroys VOCs and pollutants at the molecular level. Ideal for new builds with off-gassing concerns or homes near high-traffic areas.", "best_for": "New construction, renovation, chemical sensitivity", "practitioner_note": "I've tested this in 12 client homes. Measurable improvement in air quality scores within 2 weeks."},
    {"name": "Eight Sleep Pod 4", "brand": "Eight Sleep", "category": "sleep", "price_range": "$2,000-3,000", "why_recommended": "Dynamic temperature control through the night. Tracks sleep stages without a wearable. Proven to increase deep sleep by 30%+ in clinical studies.", "best_for": "Hot sleepers, couples with different temp preferences, anyone scoring below 6 on sleep", "practitioner_note": "This is my #1 recommendation for sleep environment. Every client who's invested has seen dramatic improvement."},
    {"name": "BLUblox Sleep+ Glasses", "brand": "BLUblox", "category": "lighting", "price_range": "$80-120", "why_recommended": "Clinical-grade blue and green light blocking for evening use. The most effective option I've tested for supporting natural melatonin production.", "best_for": "Screen-heavy evenings, shift workers, anyone with a TV in the bedroom"},
    {"name": "Circadian Optics Lattis", "brand": "Circadian Optics", "category": "lighting", "price_range": "$50-70", "why_recommended": "10,000 lux light therapy lamp. Compact, beautiful design that clients actually keep on their desk. Morning use for 20 minutes resets the circadian clock.", "best_for": "Low natural light spaces, seasonal affect, slow mornings"},
    {"name": "Vitruvi Stone Diffuser", "brand": "Vitruvi", "category": "sensory", "price_range": "$100-120", "why_recommended": "Handmade ceramic diffuser that looks like decor, not a gadget. Clients are 3x more likely to use it consistently versus plastic alternatives.", "best_for": "Sensory environment building, stress reduction, intention-setting rituals"},
    {"name": "Open Spaces Entryway Rack", "brand": "Open Spaces", "category": "organization", "price_range": "$200-350", "why_recommended": "Modular wall-mounted system that transforms chaotic entries into intentional transition zones. Available in 6 finishes.", "best_for": "Apartments, families, anyone whose entry scored below 5"},
    {"name": "Herman Miller Aeron", "brand": "Herman Miller", "category": "ergonomics", "price_range": "$1,200-1,800", "why_recommended": "Gold standard ergonomic chair. PostureFit SL supports the full spine. 12-year warranty. The cost-per-hour over its lifetime is less than a coffee.", "best_for": "8+ hour desk workers, back pain, home offices", "practitioner_note": "Yes, it's expensive. But I've never had a client regret this purchase. The borrowed dining chair is costing you more."},
    {"name": "Coway Airmega 400", "brand": "Coway", "category": "air_quality", "price_range": "$450-550", "why_recommended": "Dual HEPA filtration with real-time air quality monitoring via the LED ring. Covers up to 1,560 sq ft. Quieter than competitors at the same output.", "best_for": "Large living spaces, allergy sufferers, pet owners"},
    {"name": "Botanica Low-Light Plant Bundle", "brand": "Botanica", "category": "biophilic", "price_range": "$80-150", "why_recommended": "Curated set of 5 low-maintenance plants (pothos, snake plant, ZZ, philodendron, peace lily) selected for air purification and survival in low light.", "best_for": "Plant beginners, north-facing rooms, offices without windows"},
    {"name": "Manta Sleep Mask", "brand": "Manta", "category": "sleep", "price_range": "$30-40", "why_recommended": "100% blackout with zero pressure on the eyes. Adjustable eye cups. The entry-level fix for clients who won't invest in blackout curtains yet.", "best_for": "Travel, bright bedrooms, afternoon nappers"},
    {"name": "Breville Barista Express", "brand": "Breville", "category": "food", "price_range": "$600-700", "why_recommended": "Morning ritual anchor. Clients who invest in a quality coffee setup spend less on drive-through coffee and create a mindful start to the day.", "best_for": "Morning routine building, kitchen intention setting"},
    {"name": "Upright GO 2", "brand": "Upright", "category": "ergonomics", "price_range": "$60-80", "why_recommended": "Posture training device worn on the upper back. Gentle vibration when slouching. Builds awareness in 2 weeks, habits in 6.", "best_for": "Desk workers, laptop users, posture correction"},
]

PARTNERS = [
    {"name": "Maria Chen", "business_name": "Organized Living Co", "category": "organizer", "location": "Austin, TX", "why_recommended": "Specializes in families with kids. Gentle approach. Creates systems that survive real life, not Instagram-perfect setups that fall apart in a week.", "pricing_tier": "moderate", "practitioner_note": "Maria is my go-to for any client scoring below 5 on hidden spaces. She's worked with 8 of my clients."},
    {"name": "Chef Andre Williams", "business_name": "Nourish Meal Prep", "category": "chef", "location": "Austin, TX", "why_recommended": "In-home meal prep sessions where he teaches while cooking. Clients learn to cook for themselves. Specializes in simple, nutrient-dense meals.", "pricing_tier": "premium"},
    {"name": "Dr. Lena Park", "business_name": "Integrated Wellness", "category": "functional_medicine", "location": "Austin, TX", "why_recommended": "Functional medicine approach. Runs comprehensive panels including environmental toxin exposure. Excellent at connecting home environment to biomarkers.", "pricing_tier": "premium", "practitioner_note": "When wearable data shows declining HRV and the environment looks fine, I send them to Dr. Park."},
    {"name": "Jake Torres", "business_name": "Torres Training", "category": "trainer", "location": "Austin, TX", "why_recommended": "Movement integration specialist. Does not just do gym workouts. Helps clients build movement into daily architecture -- standing meetings, walking routes, micro-movements.", "pricing_tier": "moderate"},
    {"name": "Sarah Kim", "business_name": "Restful Nights Consulting", "category": "sleep_specialist", "location": "Austin, TX", "why_recommended": "CBT-I certified sleep consultant. Works with clients on behavioral changes alongside environment optimization. Complements my sleep environment work.", "pricing_tier": "moderate"},
    {"name": "Green Thumb Local", "business_name": "Green Thumb Local", "category": "plants", "location": "Austin, TX", "why_recommended": "Plant consultation service. Assesses actual light conditions with a meter, recommends species that will thrive. Includes a 90-day care plan.", "pricing_tier": "budget"},
    {"name": "Dr. Amy Walsh", "business_name": "Walsh Psychology", "category": "therapist", "location": "Austin, TX", "why_recommended": "Environmental psychologist who understands the connection between spaces and mental health. Valuable when audits reveal patterns that go deeper than furniture.", "pricing_tier": "moderate"},
    {"name": "BreatheEasy HVAC", "business_name": "BreatheEasy HVAC Services", "category": "smart_home", "location": "Austin, TX", "why_recommended": "HVAC assessment and air quality testing. Can install ERV systems, whole-home filtration, and humidity control. They understand wellness, not just heating and cooling.", "pricing_tier": "premium"},
]

DEMO_CLIENTS = [
    {
        "display_name": "The Reynolds Family",
        "notes": "Young family of four in a 3-bedroom colonial. Both parents work from home. Main concerns: the house feels chaotic, kids' stuff everywhere, neither parent sleeps well. They've tried decluttering twice but it 'always comes back.' Budget is moderate but willing to invest where it counts.",
        "budget_tier": "moderate",
        "has_wearable": True,
        "wearable_type": "Oura Ring (both parents)",
        "tier": "core",
        "observations": [
            ("entry", "The mudroom entry is a war zone. Six pairs of shoes, three backpacks, a stroller, and mail from three weeks ago. There is no system here, just accumulation. The coat hooks are too high for the kids to reach, so everything ends up on the floor."),
            ("entry", "Despite the chaos, there is a beautiful wreath on the front door. Someone here cares about how this looks from the outside. The disconnect between the exterior intention and the interior reality is telling."),
            ("living", "The living room has good bones. South-facing windows with decent natural light, but the blinds are half-drawn because of glare on the TV. The TV is mounted too high and dominates the room. The sectional faces only the TV, nothing faces each other."),
            ("living", "Two large houseplants near the window, both struggling. A fiddle leaf fig with brown edges (overwatered) and a monstera stretching toward light. The intention for biophilic design is here but the execution needs support."),
            ("living", "The sensory environment is busy. Background TV almost always on, even when no one is watching. Candle on the coffee table but it is a synthetic fragrance. Temperature feels about 74F which is warm for optimal alertness."),
            ("kitchen", "The fridge tells the real story. Top shelf: leftover takeout from two restaurants. Middle: kids' snack packs, juice boxes, cheese sticks. Bottom: wilting kale, a bag of carrots they bought with good intentions, yogurt past its date. The produce drawer is where vegetables go to die in this house."),
            ("kitchen", "There IS a meal planning whiteboard on the side of the fridge. It has three meals written on it from what looks like two months ago. The intention was there. The system failed because it was not connected to an actual shopping and prep routine."),
            ("kitchen", "Counter space is 80% occupied. A Keurig (used daily), a stand mixer (dusty), a fruit bowl with one brown banana, a stack of school papers, and vitamins no one remembers to take. The kitchen is not set up for the meals they actually eat."),
            ("hidden_spaces", "The master closet is at maximum capacity. Her side is color-organized but packed tight. His side is functional but has a growing pile of 'I will deal with this later' in the corner. The top shelf is where things go when they do not have a home."),
            ("hidden_spaces", "The junk drawer is actually two junk drawers. Batteries, old phone chargers, keys to unknown locks, takeout menus, expired coupons. When I asked about the second drawer, she laughed and said 'that is the overflow junk drawer.'"),
            ("hidden_spaces", "Under the kitchen sink: cleaning products at kid-reaching height, a leaking pipe that is being 'managed' with a towel, and three half-empty bottles of the same all-purpose cleaner."),
            ("bedroom", "The master bedroom is trying to be a sanctuary but is not quite getting there. The bed is nicely made with good pillows. But: a laptop on the bed, both phones charging on nightstands, and a basket of unfolded laundry in the corner that has been there 'temporarily' for a month."),
            ("bedroom", "No blackout curtains. The street light outside casts a glow across the bed. The thermostat is set to 72 for the whole house -- no separate bedroom control. Both report waking at 3-4 AM regularly."),
            ("workspace", "She works from a dedicated desk in the corner of the living room. Standing desk converter, decent chair, good monitor. But her sightline during work is the kids' play area and the kitchen counter. Zero visual boundary between work and home."),
            ("workspace", "He works from the dining table. A laptop, a second monitor balanced on a stack of books, and a dining chair that is destroying his lower back. He's been 'about to buy a desk' for eight months."),
            ("wearable", "Her Oura Ring data: Sleep score averaging 64 over 30 days. HRV trending down from 45ms to 32ms over 3 months. Deep sleep consistently below 45 minutes. Readiness scores rarely above 65. The data is screaming that something environmental is off."),
            ("wearable", "His Oura Ring: Sleep score averaging 58. Resting heart rate elevated at 72bpm (up from 64 six months ago). HRV at 28ms. He is in a recovery deficit. The bedroom environment combined with the stress of no dedicated workspace is compounding."),
            ("client_responses", "Primary concern (her): 'I feel like I am managing chaos 24/7 and never getting ahead.' Primary concern (his): 'I just want to sleep through the night and not feel like I am working from a cafeteria.'"),
            ("client_responses", "What they've tried: KonMari (got through the clothes, quit at papers), a cleaning service every two weeks (helps but does not solve the systems), melatonin for sleep (stopped working after a month)."),
            ("client_responses", "Ideal life: 'We want the house to work WITH us instead of against us. We want the kids to have space but not have it take over. We want to wake up actually rested.'"),
            ("client_responses", "What I noticed between the lines: They are both high-performers who have optimized everything at work but have not applied any of that thinking to their home environment. The home is running on default settings. They do not need motivation, they need systems."),
        ],
        "scores": [
            ("setup_vs_goals", "Setup vs. Goals", 4, "Both parents are high-performers who want an intentional, calm home environment. What they have is a space running entirely on accumulated defaults. The gap between their stated goals and their actual environment is significant, but the raw ingredients for improvement are here.", "Research consistently shows that environmental misalignment with personal goals creates chronic low-grade stress. The constant visual reminder of 'things I should deal with' taxes cognitive resources and decision-making capacity.", "Start with the entry system -- it is the first and last thing they interact with daily. An intentional entry ritual changes the psychological boundary between outside chaos and home sanctuary. Then address the workspace separation issue."),
            ("intention", "Intention in Space and Habits", 4, "The wreath on the door, the meal planning board, the standing desk converter -- intention is present in flashes but not sustained. Most of the home evolved by accumulation rather than decision. The second junk drawer is the perfect metaphor: when the first system failed, they just added another container instead of solving the root problem.", "Spaces that evolve by default create what environmental psychologists call 'decision residue' -- every unfinished choice in your field of view uses a small amount of cognitive energy. Over a day, this adds up to significant mental fatigue.", "Audit every item on the kitchen counter and ask: 'Does this support a daily action?' If not, it gets a home in a cabinet or it leaves. Apply the same test to every flat surface in the house."),
            ("hidden_spaces", "The Hidden Spaces", 3, "The hidden spaces reveal the real story. The junk drawer overflow, the packed closets, the under-sink situation -- these spaces show a family that is managing visible chaos by relocating it behind closed doors. The cleaning products at kid height is also a safety concern.", "What is behind the closed doors is often a more honest indicator of how someone is actually coping than what is on display. Hidden disorganization creates a background anxiety -- you know it is there even when you cannot see it.", "Priority one: safety check under all sinks and move products up. Priority two: the junk drawer purge -- empty both completely, sort, and give back only what belongs. Everything else gets a proper home or goes. Priority three: a closet edit with clear rules about what stays."),
            ("kitchen_flow", "Kitchen Flow and Food System", 3, "There is no food system. There is a desire for one (the whiteboard, the kale, the stand mixer) but no operational system connecting planning to shopping to prep to cooking. The kitchen is set up for the meals they wish they made, not the ones they actually eat.", "A functioning food system is one of the highest-leverage wellness interventions. It affects nutrition, spending, stress levels, family time, and even sleep quality (late eating and blood sugar regulation). The absence of a system does not just mean poor eating -- it means dozens of daily micro-decisions that drain energy.", "Remove everything from the counter that is not used daily. Introduce a Sunday 30-minute meal prep block -- not cooking, just prepping ingredients. Connect the whiteboard to an actual shopping list app. Consider a Chef Andre session to build the skill foundation."),
            ("natural_elements", "Natural Elements and Biophilic Design", 5, "The south-facing windows are an asset being underutilized. The plants show intention but need care guidance. No water features, no natural materials in decor. The blinds-half-drawn situation is sacrificing natural light for TV viewing convenience.", "Natural light exposure, particularly morning light, is the single most powerful circadian rhythm regulator. The current setup -- blinds drawn, TV dominant -- is optimizing for entertainment at the cost of biology.", "Open the blinds fully in the morning and keep them open until afternoon glare becomes an issue. Move the TV to a position where it does not compete with the windows. Get a Green Thumb Local consultation for the plants. Add one natural material element per room."),
            ("sleep_environment", "Sleep Environment", 3, "Multiple compounding sleep disruptors: no blackout capability, room too warm at 72F, both phones charging at bedside, laptop on the bed, and the street light. Both wearable datasets confirm the environment is costing them significant deep sleep.", "The bedroom environment is responsible for up to 30% of sleep quality variation. Temperature alone (optimal is 65-68F) can account for a 15-20% improvement in deep sleep. Add light control and device removal, and you are looking at potentially transformative results.", "Install blackout curtains (immediate impact). Set bedroom thermostat to 67F if possible, or add a fan. Phones charge outside the bedroom starting tonight. Laptop never enters the bedroom. Consider the Eight Sleep Pod for temperature control if budget allows."),
            ("movement", "Movement Integration", 5, "No visible movement infrastructure. The standing desk converter helps for her but he has no equivalent. No exercise equipment visible, no walking path evidence, no movement cues in the environment. They drive to a gym they rarely use.", "Movement that is separated from daily life has a compliance rate of about 30%. Movement built into the architecture of the day -- a standing desk, a walking meeting route, a pull-up bar in a doorway -- has a compliance rate above 80%.", "Get him a standing desk for his new dedicated workspace. Add a doorway pull-up bar somewhere in the main traffic flow. Create a family after-dinner walk route. Cancel the gym membership they are not using and redirect that budget to home movement infrastructure."),
            ("sensory", "Sensory Environment", 4, "The background TV is the biggest sensory issue. It creates a constant low-level stimulation that the nervous system has to process even when no one is actively watching. The synthetic candle adds chemical fragrance that is not doing anyone any favors. Temperature too warm for optimal cognitive function.", "The nervous system processes every sensory input in the environment, whether conscious or not. Chronic background noise and artificial fragrance create what researchers call 'sensory load' -- a cumulative burden that manifests as fatigue, irritability, and difficulty focusing.", "Implement a 'TV off by default' rule -- it only goes on when someone actively chooses to watch something. Replace the synthetic candle with a Vitruvi diffuser and real essential oils. Drop the thermostat to 70F during the day. Add a sound machine to the bedroom for consistent sleep acoustics."),
            ("financial_alignment", "Financial Alignment", 5, "No financial audit performed for this engagement.", "", ""),
            ("wearable_data", "Wearable Data vs. Environment", 3, "Both Oura Ring datasets tell a consistent story: declining HRV, poor deep sleep, elevated resting heart rate. His numbers are worse, which correlates with his worse workspace setup and the compounding effect of physical discomfort (dining chair) plus poor sleep. These metrics will respond to environmental changes within 2-4 weeks if we address the root causes.", "Wearable data provides objective evidence of what the body is experiencing. The declining HRV trend in both partners suggests chronic stress activation. This is not about one bad night -- this is a systemic pattern that the home environment is maintaining.", "Address sleep environment first (biggest expected impact on both datasets). Then workspace ergonomics for him. Track HRV and sleep scores weekly to measure response to changes. Expected timeline: 2-4 weeks for initial improvement, 8-12 weeks for new baseline."),
        ],
        "overall_score": 39,
        "overall_label": "Survival Mode",
        "vision": """Picture this: You walk through your front door and instead of tripping over shoes, you hang your jacket on a hook, drop your keys in a designated bowl, and take a breath. The entry is clear. The transition from outside to inside actually feels like something.

The living room has morning light pouring in because the blinds are open. The TV is off. Your plants are alive and actually growing. The couch still has the throw blankets your kids use for forts, but everything has a home it goes back to.

In the kitchen, you know what's for dinner tonight because it was decided on Sunday, and the ingredients are prepped and waiting. The counter has your coffee setup and a fruit bowl with fruit your kids will actually eat. Nothing else.

And here's the part that matters most: you are sleeping through the night. Both of you. The room is cool, dark, and quiet. Your phones charge in the hallway. Your HRV is climbing. You wake up and actually feel rested instead of just less tired.

None of this required a renovation. It required systems, boundaries, and about six weeks of building new defaults.""",
        "next_steps": """1. This week: Phones out of the bedroom tonight. Set thermostat to 67F for overnight. Order blackout curtains. This costs under $100 and will show in your Oura data within a week.

2. Within 2 weeks: Entry system installation (Open Spaces rack or similar). Clear the kitchen counters -- everything gets a cabinet home or leaves. Buy him a proper desk and chair (this is not optional, his body is keeping score).

3. Within 4 weeks: TV-off-by-default rule. Sunday 30-minute meal planning block. Replace synthetic candle with essential oil diffuser. Schedule a Green Thumb Local consultation for your plants.

4. Within 8 weeks: Check in on wearable data trends. If sleep scores have not improved by 15+ points, consider the Eight Sleep Pod and a Sarah Kim sleep consultation.

5. If you want implementation support for any of this, I am here. Sometimes having someone walk you through the first two weeks is the difference between 'we should do this' and 'we did this.'""",
        "actions": [
            {"rank": 1, "category_name": "Sleep Environment", "score": 3, "action": "Blackout curtains + phones out + temperature to 67F. Highest ROI intervention, expected to show in wearable data within 7-10 days."},
            {"rank": 2, "category_name": "Kitchen Flow and Food System", "score": 3, "action": "Clear counters, implement Sunday planning block, connect whiteboard to shopping list."},
            {"rank": 3, "category_name": "The Hidden Spaces", "score": 3, "action": "Safety check under sinks, junk drawer purge, closet edit with keep/remove rules."},
            {"rank": 4, "category_name": "Wearable Data vs. Environment", "score": 3, "action": "Address sleep and workspace first, track HRV weekly. His workspace upgrade is urgent -- dining chair is causing compounding damage."},
            {"rank": 5, "category_name": "Setup vs. Goals", "score": 4, "action": "Entry system + TV-off-by-default rule. These two changes shift the home from reactive to intentional."},
        ],
    },
]


async def seed_demo():
    async with async_session_factory() as session:
        # Get admin user
        result = await session.execute(
            select(User).where(User.email == "practitioner@wellnessops.local")
        )
        user = result.scalar_one_or_none()
        if not user:
            print("ERROR: Admin user not found. Run seed_db.py first.")
            return

        user_id = user.id
        print(f"Using admin user: {user.email}")

        # Clear existing demo data
        print("\nClearing existing data...")
        for model in [Report, CategoryScore, Observation, AuditSession, Client, Product, Partner, KnowledgeDocument]:
            result = await session.execute(select(model))
            for obj in result.scalars().all():
                await session.delete(obj)
        await session.commit()
        print("  Cleared all client, product, partner, and knowledge data")

        # Seed products
        print(f"\nCreating {len(PRODUCTS)} products...")
        for p in PRODUCTS:
            session.add(Product(**p))
        await session.commit()

        # Seed partners
        print(f"Creating {len(PARTNERS)} partners...")
        for p in PARTNERS:
            session.add(Partner(**p))
        await session.commit()

        # Seed demo clients with full audit data
        for client_data in DEMO_CLIENTS:
            print(f"\nCreating client: {client_data['display_name']}...")

            client = Client(
                user_id=user_id,
                display_name=client_data["display_name"],
                notes=client_data["notes"],
                budget_tier=client_data["budget_tier"],
                has_wearable=client_data["has_wearable"],
                wearable_type=client_data.get("wearable_type"),
            )
            session.add(client)
            await session.flush()

            # Create completed audit session
            audit = AuditSession(
                client_id=client.id,
                user_id=user_id,
                audit_tier=client_data["tier"],
                status="report_final",
                started_at=datetime.now(timezone.utc) - timedelta(days=3),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            session.add(audit)
            await session.flush()

            # Add observations
            for sort_order, (room, content) in enumerate(client_data["observations"]):
                obs = Observation(
                    session_id=audit.id,
                    room_area=room,
                    content=content,
                    observation_type="text",
                    is_from_structured_flow=True,
                    sort_order=sort_order,
                )
                session.add(obs)

            # Add scores
            for idx, (cat_key, cat_name, score_val, what_obs, why, how) in enumerate(client_data["scores"]):
                score = CategoryScore(
                    session_id=audit.id,
                    category_key=cat_key,
                    category_name=cat_name,
                    score=score_val,
                    ai_generated_score=score_val,
                    status_label=get_score_label(score_val),
                    what_observed=what_obs,
                    why_it_matters=why,
                    how_to_close_gap=how,
                    sort_order=idx,
                )
                session.add(score)

            # Add report
            report = Report(
                session_id=audit.id,
                version=1,
                status="final",
                overall_score=client_data["overall_score"],
                overall_label=client_data["overall_label"],
                priority_action_plan={"actions": client_data["actions"]},
                vision_section=client_data["vision"],
                next_steps=client_data["next_steps"],
                generated_by="system",
                approved_by=user_id,
                approved_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            session.add(report)

            await session.commit()
            print(f"  Created: {len(client_data['observations'])} observations, {len(client_data['scores'])} scores, 1 report")
            print(f"  Overall: {client_data['overall_score']}/100 ({client_data['overall_label']})")

        print(f"\n--- Demo seed complete ---")
        print(f"Clients: {len(DEMO_CLIENTS)}")
        print(f"Products: {len(PRODUCTS)}")
        print(f"Partners: {len(PARTNERS)}")
        print(f"\nThe Reynolds Family audit is ready to showcase:")
        print(f"  - 21 detailed observations across 9 room areas")
        print(f"  - 10 scored categories with deep analysis")
        print(f"  - Complete report with vision section and action plan")
        print(f"  - 12 vetted products and 8 partner referrals")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo())
