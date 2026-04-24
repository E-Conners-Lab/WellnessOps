# Field Companion Prompt Sequences — WellnessOps

## Overview

These are the structured prompts used in Mode 1 (Field Companion). They guidethe practitioner room by room through her observation framework so nothing gets missed. Each prompt accepts text input, photo uploads, or a skip action.

The UI should present these one at a time on mobile with clear progress indication.

---

## Room: Entry and Curb Appeal

| Key | Prompt |
|---|---|
| entry_first_impression | What is your first impression walking up to the home? |
| entry_communication | What does the entry communicate before you step inside? |
| entry_threshold | Is there intention at the threshold or does the outside not match the inside? |

---

## Room: Living Spaces

| Key | Prompt |
|---|---|
| living_dominant_feeling | What is the dominant feeling in the main living area? |
| living_natural_light | Is there natural light and how is it managed? |
| living_art_objects | What art or objects are displayed and what do they communicate? |
| living_biophilic | Is there biophilic presence? Plants, natural materials, water elements? |
| living_sensory | What is the sensory environment? Sound, smell, temperature, texture? |
| living_ergonomics | Is the furniture ergonomic or is discomfort being normalized? |
| living_seating | What does the seating arrangement communicate about how this person lives? |

---

## Room: Kitchen

| Key | Prompt |
|---|---|
| kitchen_fridge | Open the fridge. Describe what you see. |
| kitchen_food_system | Is there a food system or is it reactive and random? |
| kitchen_setup | Is the kitchen set up for the meals this person actually eats? |
| kitchen_eating_location | Where do they eat? At a table, at a barstool, standing over the sink? |
| kitchen_meal_planning | Is there evidence of meal planning or evidence of decision fatigue? |
| kitchen_pantry | What does the pantry or cabinet situation look like? |

---

## Room: Hidden Spaces

| Key | Prompt |
|---|---|
| hidden_closet | Open a closet. What does it tell you? |
| hidden_junk_drawer | What is the state of the junk drawer? |
| hidden_under_sink | What is in the cabinet under the sink? |
| hidden_unseen | What is hiding that the client has stopped seeing? |

---

## Room: Bedroom

| Key | Prompt |
|---|---|
| bedroom_visible_from_bed | What is visible from the bed? |
| bedroom_nightstand | What is on the nightstand and is it intentional? |
| bedroom_light | What is the light situation? Natural, artificial, blackout capability? |
| bedroom_temp_humidity | What is the temperature and humidity? (Measure if possible) |
| bedroom_work_visible | Is there work material visible from the sleep position? |
| bedroom_last_sight | What is the last thing their eyes see before sleep? |

---

## Room: Workspace

| Key | Prompt |
|---|---|
| workspace_dedicated | Is this a dedicated workspace or a borrowed corner? |
| workspace_lighting | What is the lighting situation? |
| workspace_chair | Is the chair ergonomic? |
| workspace_sightline | What is in the sightline during work hours? |
| workspace_separation | Is there separation between work space and rest space? |

---

## Extended Audit Areas (Tier Two and Three)

| Key | Prompt |
|---|---|
| extended_books | Books and library: what is being read or displayed? |
| extended_art | Art: is there art and was it chosen with intention? |
| extended_vehicle | Vehicle: describe the state of the car. |
| extended_office | Office (if separate from home): describe the work environment. |

---

## Wearable Data (if client has wearables)

| Key | Prompt |
|---|---|
| wearable_device | What device are they using? |
| wearable_sleep | What are their current sleep scores? |
| wearable_hrv | What is their HRV trend? |
| wearable_stress | What is their stress or body battery reading? |
| wearable_patterns | What patterns stand out in the data? |

---

## Financial Alignment (advanced clients only)

| Key | Prompt |
|---|---|
| financial_statements | Has the client shared bank statements or spending data? |
| financial_top_categories | What categories are they spending most on? |
| financial_alignment | Does the spending reflect the stated priorities? |
| financial_contradictions | Where is money going that contradicts the goals? |

---

## Client Questions and Responses

| Key | Prompt |
|---|---|
| client_primary_concern | What is the client's stated primary concern? |
| client_already_tried | What have they already tried? |
| client_ideal_life | What does their ideal daily life look like? |
| client_answer_patterns | What patterns did you notice in how they answered questions? |
| client_between_lines | What did they say between the lines? |

---

## Implementation Notes

- Each room section is collapsible/expandable in the UI.
- Progress bar shows completion across all sections.
- "Skip" button available on every prompt (some rooms may not apply).
- Photo upload button on every prompt.
- Text input auto-saves on blur or after 2 seconds of inactivity.
- Session state persists in the database, not client-side storage (SEC-01).
- Room order can be customized per session (the practitioner may not walk through in this exact order).
