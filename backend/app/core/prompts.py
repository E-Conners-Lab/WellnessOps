"""
Field Companion structured prompt definitions.
Defines all room sections and prompts used in Mode 1 (structured intake).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    key: str
    room_area: str
    text: str
    sort_order: int


@dataclass(frozen=True)
class RoomSection:
    room_area: str
    label: str
    tier: str  # "core" or "extended"
    prompts: tuple[Prompt, ...]


# Core audit sections (always shown)
ENTRY = RoomSection(
    room_area="entry",
    label="Entry and Curb Appeal",
    tier="core",
    prompts=(
        Prompt("entry_first_impression", "entry", "What is your first impression walking up to the home?", 0),
        Prompt("entry_communication", "entry", "What does the entry communicate before you step inside?", 1),
        Prompt("entry_threshold", "entry", "Is there intention at the threshold or does the outside not match the inside?", 2),
    ),
)

LIVING = RoomSection(
    room_area="living",
    label="Living Spaces",
    tier="core",
    prompts=(
        Prompt("living_dominant_feeling", "living", "What is the dominant feeling in the main living area?", 0),
        Prompt("living_natural_light", "living", "Is there natural light and how is it managed?", 1),
        Prompt("living_art_objects", "living", "What art or objects are displayed and what do they communicate?", 2),
        Prompt("living_biophilic", "living", "Is there biophilic presence? Plants, natural materials, water elements?", 3),
        Prompt("living_sensory", "living", "What is the sensory environment? Sound, smell, temperature, texture?", 4),
        Prompt("living_ergonomics", "living", "Is the furniture ergonomic or is discomfort being normalized?", 5),
        Prompt("living_seating", "living", "What does the seating arrangement communicate about how this person lives?", 6),
    ),
)

KITCHEN = RoomSection(
    room_area="kitchen",
    label="Kitchen",
    tier="core",
    prompts=(
        Prompt("kitchen_fridge", "kitchen", "Open the fridge. Describe what you see.", 0),
        Prompt("kitchen_food_system", "kitchen", "Is there a food system or is it reactive and random?", 1),
        Prompt("kitchen_setup", "kitchen", "Is the kitchen set up for the meals this person actually eats?", 2),
        Prompt("kitchen_eating_location", "kitchen", "Where do they eat? At a table, at a barstool, standing over the sink?", 3),
        Prompt("kitchen_meal_planning", "kitchen", "Is there evidence of meal planning or evidence of decision fatigue?", 4),
        Prompt("kitchen_pantry", "kitchen", "What does the pantry or cabinet situation look like?", 5),
    ),
)

HIDDEN = RoomSection(
    room_area="hidden_spaces",
    label="Hidden Spaces",
    tier="core",
    prompts=(
        Prompt("hidden_closet", "hidden_spaces", "Open a closet. What does it tell you?", 0),
        Prompt("hidden_junk_drawer", "hidden_spaces", "What is the state of the junk drawer?", 1),
        Prompt("hidden_under_sink", "hidden_spaces", "What is in the cabinet under the sink?", 2),
        Prompt("hidden_unseen", "hidden_spaces", "What is hiding that the client has stopped seeing?", 3),
    ),
)

BEDROOM = RoomSection(
    room_area="bedroom",
    label="Bedroom",
    tier="core",
    prompts=(
        Prompt("bedroom_visible_from_bed", "bedroom", "What is visible from the bed?", 0),
        Prompt("bedroom_nightstand", "bedroom", "What is on the nightstand and is it intentional?", 1),
        Prompt("bedroom_light", "bedroom", "What is the light situation? Natural, artificial, blackout capability?", 2),
        Prompt("bedroom_temp_humidity", "bedroom", "What is the temperature and humidity? (Measure if possible)", 3),
        Prompt("bedroom_work_visible", "bedroom", "Is there work material visible from the sleep position?", 4),
        Prompt("bedroom_last_sight", "bedroom", "What is the last thing their eyes see before sleep?", 5),
    ),
)

WORKSPACE = RoomSection(
    room_area="workspace",
    label="Workspace",
    tier="core",
    prompts=(
        Prompt("workspace_dedicated", "workspace", "Is this a dedicated workspace or a borrowed corner?", 0),
        Prompt("workspace_lighting", "workspace", "What is the lighting situation?", 1),
        Prompt("workspace_chair", "workspace", "Is the chair ergonomic?", 2),
        Prompt("workspace_sightline", "workspace", "What is in the sightline during work hours?", 3),
        Prompt("workspace_separation", "workspace", "Is there separation between work space and rest space?", 4),
    ),
)

CLIENT_QUESTIONS = RoomSection(
    room_area="client_responses",
    label="Client Questions",
    tier="core",
    prompts=(
        Prompt("client_primary_concern", "client_responses", "What is the client's stated primary concern?", 0),
        Prompt("client_already_tried", "client_responses", "What have they already tried?", 1),
        Prompt("client_ideal_life", "client_responses", "What does their ideal daily life look like?", 2),
        Prompt("client_answer_patterns", "client_responses", "What patterns did you notice in how they answered questions?", 3),
        Prompt("client_between_lines", "client_responses", "What did they say between the lines?", 4),
    ),
)

# Extended audit sections (tier 2/3 only)
EXTENDED = RoomSection(
    room_area="extended",
    label="Extended Audit Areas",
    tier="extended",
    prompts=(
        Prompt("extended_books", "extended", "Books and library: what is being read or displayed?", 0),
        Prompt("extended_art", "extended", "Art: is there art and was it chosen with intention?", 1),
        Prompt("extended_vehicle", "extended", "Vehicle: describe the state of the car.", 2),
        Prompt("extended_office", "extended", "Office (if separate from home): describe the work environment.", 3),
    ),
)

WEARABLE = RoomSection(
    room_area="wearable",
    label="Wearable Data",
    tier="core",
    prompts=(
        Prompt("wearable_device", "wearable", "What device are they using?", 0),
        Prompt("wearable_sleep", "wearable", "What are their current sleep scores?", 1),
        Prompt("wearable_hrv", "wearable", "What is their HRV trend?", 2),
        Prompt("wearable_stress", "wearable", "What is their stress or body battery reading?", 3),
        Prompt("wearable_patterns", "wearable", "What patterns stand out in the data?", 4),
    ),
)

FINANCIAL = RoomSection(
    room_area="financial",
    label="Financial Alignment",
    tier="extended",
    prompts=(
        Prompt("financial_statements", "financial", "Has the client shared bank statements or spending data?", 0),
        Prompt("financial_top_categories", "financial", "What categories are they spending most on?", 1),
        Prompt("financial_alignment", "financial", "Does the spending reflect the stated priorities?", 2),
        Prompt("financial_contradictions", "financial", "Where is money going that contradicts the goals?", 3),
    ),
)

# All sections in default display order
ALL_SECTIONS: tuple[RoomSection, ...] = (
    ENTRY, LIVING, KITCHEN, HIDDEN, BEDROOM, WORKSPACE,
    CLIENT_QUESTIONS, EXTENDED, WEARABLE, FINANCIAL,
)

CORE_SECTIONS: tuple[RoomSection, ...] = tuple(
    s for s in ALL_SECTIONS if s.tier == "core"
)

# Lookup maps
PROMPT_BY_KEY: dict[str, Prompt] = {}
SECTION_BY_ROOM: dict[str, RoomSection] = {}
for section in ALL_SECTIONS:
    SECTION_BY_ROOM[section.room_area] = section
    for prompt in section.prompts:
        PROMPT_BY_KEY[prompt.key] = prompt


def get_sections_for_tier(tier: str) -> list[RoomSection]:
    """Return sections applicable to the given audit tier."""
    if tier == "extended":
        return list(ALL_SECTIONS)
    return list(CORE_SECTIONS)


def get_total_prompts_for_tier(tier: str) -> int:
    """Return total prompt count for a given tier."""
    return sum(len(s.prompts) for s in get_sections_for_tier(tier))
