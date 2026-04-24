# Scoring Methodology — WellnessOps

## Overview

The scoring system quantifies the practitioner's diagnostic observations into a 100-point scale. The system generates scores;the practitioner always has final override authority.

---

## Core Audit Scoring

10 categories x 10 points each = 100 total.

### Categories and Scoring Criteria

**1. Setup vs. Goals (setup_vs_goals)**
Does how the client is actually living match what they say they want?
- 10: Environment perfectly reflects stated goals. Systems in place. No contradictions.
- 7: Mostly aligned but 1-2 clear gaps between intention and reality.
- 4: Significant disconnect. Client says one thing but environment says another.
- 1: Complete misalignment. The environment is actively working against every stated goal.

**2. Intention in Space and Habits (intention)**
Are things where they are on purpose or by default?
- 10: Every placement, habit, and system is deliberately chosen.
- 7: Clear intention in main areas, some default patterns in secondary spaces.
- 4: Most of the space evolved by accident. Little evidence of intentional design.
- 1: Nothing is intentional. The space is pure accumulated default.

**3. The Hidden Spaces (hidden_spaces)**
Fridge, closets, drawers, cabinets. What is behind the closed doors?
- 10: Hidden spaces are as organized and intentional as visible ones.
- 7: Some organization, some chaos. Effort is present but inconsistent.
- 4: Hidden spaces are where the real story lives. Significantly worse than visible areas.
- 1: Hidden spaces reveal a level of overwhelm the client may not be acknowledging.

**4. Kitchen Flow and Food System (kitchen_flow)**
Is there a system or is it chaos dressed up as cooking?
- 10: Clear food system. Kitchen supports the meals actually being made. Fridge is intentional.
- 7: Some system present. Fridge has good ingredients but no plan connecting them.
- 4: Reactive eating. No meal planning. Kitchen not set up for actual cooking habits.
- 1: No food system at all. Evidence of significant decision fatigue around eating.

**5. Natural Elements and Biophilic Design (natural_elements)**
Light, plants, air, water, connection to nature inside the home.
- 10: Strong biophilic presence. Natural light managed well. Plants thriving. Air quality considered.
- 7: Some natural elements present but not fully integrated. Decent natural light.
- 4: Minimal connection to nature. Few or no plants. Natural light blocked or ignored.
- 1: Complete disconnection from natural environment. No greenery, poor air, sealed off from daylight.

**6. Sleep Environment (sleep_environment)**
Temperature, light, sound, humidity, what is visible from the bed.
- 10: Sleep environment is optimized. Temperature controlled, blackout capability, no work visible, humidity managed, intentional nightstand.
- 7: Good foundation with 1-2 issues (e.g., humidity high, phone on nightstand).
- 4: Multiple sleep disruptors present. Work visible from bed, poor light control, no temperature management.
- 1: Sleep environment is actively hostile. Every factor is working against restorative sleep.

**7. Movement Integration (movement)**
Is movement built into the architecture of the day?
- 10: Movement is woven into daily routines and the environment supports it. Standing options, walkable layout, exercise equipment accessible.
- 7: Some movement infrastructure. Client exercises but it is separate from daily life, not integrated.
- 4: Sedentary default. Environment encourages sitting. Movement requires separate effort.
- 1: Environment actively discourages movement. No infrastructure, no integration, sedentary by design.

**8. Sensory Environment (sensory)**
What is the nervous system absorbing all day?
- 10: Sensory environment is intentionally curated. Sound, scent, texture, visual field all considered.
- 7: Some sensory awareness. A few intentional choices but also some unnoticed irritants.
- 4: Sensory environment is mostly accidental. Background noise, harsh lighting, visual clutter unaddressed.
- 1: Sensory overload or sensory deprivation. The nervous system is under constant unacknowledged stress.

**9. Financial Alignment (financial_alignment)**
Does the money trail match the stated priorities? (Advanced clients only)
- 10: Spending perfectly reflects values and goals. No contradictions between budget and priorities.
- 7: Mostly aligned with 1-2 spending categories that contradict stated goals.
- 4: Significant misalignment. Money flows to things that do not serve the client's wellness goals.
- 1: Complete financial disconnect from stated priorities.
- N/A: Client has not opted into financial audit.

**10. Wearable Data vs. Environment (wearable_data)**
Does the data explain the environment or vice versa? (If applicable)
- 10: Wearable data confirms environment is supporting health metrics. Sleep scores, HRV, stress all trending positive.
- 7: Mostly positive data with 1-2 metrics that the environment might be affecting negatively.
- 4: Data shows clear negative patterns that correlate with environmental observations.
- 1: Wearable data reveals significant health impact from environmental factors.
- N/A: Client does not use a wearable.

---

## Extended Audit Categories

When extended categories are included, all 15 categories are scored 1-10 and the overall score is calculated as: (sum of all applicable scores / max possible) x 100.

**11. Ergonomics and Physical Setup (ergonomics)**
Is the body being supported or slowly damaged?

**12. Art and Aesthetic Environment (art_aesthetic)**
What is the visual intelligence of the space?

**13. Library and Learning Environment (library_learning)**
What does the reading life communicate?

**14. Vehicle Environment (vehicle)**
What does the car say about the mobile life?

**15. Workspace Assessment (workspace)**
Where eight or more hours a day are spent.

---

## Overall Score Calculation

**Core Audit (10 categories):**
Sum of all applicable category scores. Categories marked N/A are excluded and the denominator adjusts. Formula: `(sum of scores / (count of applicable categories * 10)) * 100`, rounded to nearest integer.

**Extended Audit (15 categories):**
Same formula with all 15 categories in the pool.

---

## AI Score Generation Process

1. Collect all observations for the session, grouped by category.
2. For each category, retrieve relevant chunks from all 7 knowledge domains.
3. Send category observations + knowledge context + scoring criteria to Claude Opus.
4. Claude generates: score (1-10), status label, what_observed summary, why_it_matters (backed by knowledge base), how_to_close_gap (prioritized recommendations).
5. System also matches relevant products (Domain 3) and partners (Domain 7) to each category.
6. All scores presented tothe practitioner for review and override before report generation.

---

## Practitioner Override Protocol

- The practitioner can change any score and must provide override notes explaining her reasoning.
- The AI-generated score is preserved in `ai_generated_score` for calibration tracking.
- Over time, the delta between AI scores andthe practitioner overrides is used to improve the scoring prompts.
