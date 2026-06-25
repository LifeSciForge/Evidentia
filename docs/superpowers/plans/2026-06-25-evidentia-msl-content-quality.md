# Evidentia — MSL Content Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Fix three pre-existing content/MSL-fit issues found in user testing: (#3) replace commercial market metrics with sourced scientific ones, (#4) make talking points drug-specific and evidence-grounded, (#6) give the Competitive Landscape a real side-by-side comparison.

**Architecture:** Each item touches schema (hold the data) + agent (produce it, sourced) + UI (render it), guarded by the Stage-5 characterization net (`tests/test_render_smoke.py`). The provenance rule from Stage 2 still holds: **source URLs come only from real retrieval, never the LLM.**

**Honest scope note:** prompt + schema + UI changes make the output *structurally* right and much more specific. Final *content* quality (e.g. whether the LLM cites the exact PFS number) depends on the live model + retrieval and will need a validation run + possible prompt iteration — that's expected, not a defect of this plan.

**Tech Stack:** Python, Streamlit, pytest. Branch `stage6-content` (on `stage5-refactor`).

---

## Task 1 — #3: Scientific at-a-glance metrics (UI + provenance)

**Files:** `src/ui/app.py` (at-a-glance band ~363–413); `src/agents/gtm_agents/market_research_agent.py` (patient-population source).

> Decision: REMOVE TAM/SAM/SOM (commercial GTM leftovers). Replace the 3 at-a-glance cards with MSL-relevant scientific metrics the agents already gather.

- [ ] **Step 1:** In `display_msl_results`'s at-a-glance band, change the 3 metric cards from `patient_population / tam / sam` to:
  - **Eligible patients** — `state.market_data.patient_population` (value) + `chip_for(state, "market.patient_population")` (keep). Honest "—" when None.
  - **Pivotal trials** — `len(state.market_data.clinical_trials or [])` (a count of retrieved trials). No chip needed (it's a count of retrieved items); subtitle "from ClinicalTrials.gov".
  - **Key publications** — `len(state.market_data.key_publications or [])`. Subtitle "from PubMed".
  Remove the `market.tam` / `market.sam` cards entirely.
- [ ] **Step 2:** In `market_research_agent`, ensure `state.sources["market.patient_population"]` is set to a real `verified_source`/`web_source` when the population came from epidemiology/PubMed (it has a url) — so the patients chip is truthful. If population is unavailable, leave the existing `unavailable` source (the card shows "—").
- [ ] **Step 3:** Update `tests/test_render_smoke.py`'s populated state if it asserted on tam/sam (it shouldn't — it just renders). Run safety net + full suite green. Add a small test that the band renders trials/pubs counts without raising for a state with clinical_trials/key_publications lists.
- [ ] **Step 4:** Commit `feat(ui): scientific at-a-glance metrics (patients/trials/pubs), drop commercial TAM/SAM`.

---

## Task 2 — #6: Competitive comparison table (schema + agent + UI)

**Files:** `src/schema/gtm_state.py` (CompetitorData), `src/agents/gtm_agents/competitor_analysis_agent.py`, `src/service/validators/json_validator.py` (CompetitorResponse), `src/ui/sections/competitive.py`.

> The panel must let an MSL *compare*. Build a table: our drug (anchor column) vs each competitor across the dimensions that matter for a brief.

- [ ] **Step 1 (schema):** Add structured comparative fields to `CompetitorData` (Optional, default None/empty): `mechanism: str`, `efficacy: str` (e.g. "PFS 5.6 mo (CodeBreaK 200)"), `key_safety: str` (key AEs), `primary_endpoint: str`, `dosing: str`, `approval_status: str`. Keep existing fields. Also add an anchor `our_drug_row` concept: a parallel set of these dimensions for the subject drug (store on `CompetitorAnalysisData`, e.g. `subject_comparison: Dict[str, str]`).
- [ ] **Step 2 (validation):** extend `CompetitorResponse` (json_validator) with the new permissive fields so validated output carries them.
- [ ] **Step 3 (agent):** update the competitor prompt (now a template in `src/prompts/competitor_analysis.txt`) to ask for, per competitor AND for the subject drug, the six comparison dimensions above — grounded in the retrieved web/trial data, concise (a phrase each, with a trial name where known). Keep the "no fabrication" fallback: if unknown, the field is empty (UI shows "—"), never invented. Map the parsed fields into `CompetitorData` + `subject_comparison`.
- [ ] **Step 4 (UI):** in `sections/competitive.py`, render a **comparison table**: rows = dimensions (Mechanism, Efficacy, Key safety, Endpoint, Dosing, Status), columns = [Subject drug] + top competitors. Empty cells render "—". Keep the existing gaps/opportunities content below the table. Direction-C styling (reuse existing CSS classes/`metric` look).
- [ ] **Step 5:** Run safety net (the competitive smoke test must still pass) + full suite. Add a render test for the table with a populated `CompetitorAnalysisData` (≥1 competitor + subject_comparison). Commit per sub-step where practical; at minimum `feat: competitive comparison table (schema+agent+ui)`.

---

## Task 3 — #4: Talking-points specificity (agent + UI)

**Files:** `src/prompts/messaging_positioning.txt` (+ other messaging templates), `src/agents/gtm_agents/messaging_agent.py`, `src/schema/gtm_state.py` (pillar evidence), `src/ui/sections/talking_points.py`.

> Replace vague filler with drug-specific, evidence-grounded points, each tied to a real source; fix the contradictory "select a physician" line.

- [ ] **Step 1 (prompt):** tighten the messaging positioning/pillars prompt to REQUIRE: name the specific mechanism (e.g. "KRAS G12C inhibition"), reference specific trials by name/NCT and publications by PMID, include concrete figures where available, and BAN vague phrasing ("a distinct mechanism", "a clinically validated pathway"). Instruct: every pillar's `evidence` must reference a real retrieved trial/publication; if none supports a claim, omit the claim rather than inventing.
- [ ] **Step 2 (provenance):** ensure each pillar/differentiator can carry a source URL drawn from the retrieved trials/pubs (NCT/PMID canonical URLs from Stage 2 tools) — NOT from LLM text. Add an optional `source_url`/`source_label` to the pillar evidence structure if not present.
- [ ] **Step 3 (UI):** in `sections/talking_points.py`, render a `source_chip` next to each pillar/differentiator when a source exists. Fix the "Select a physician in the sidebar…" line so it's not shown *above contradictory generic content*: when no KOL is selected, show a clear header like "General positioning (select a physician for KOL-tailored points)" — one coherent message, not a mixed signal.
- [ ] **Step 4:** safety net (talking_points smoke test) + full suite green. Commit `feat: drug-specific, sourced talking points; clearer no-KOL state`.

---

## Task 4 — Verification (human checkpoint)
- [ ] Run the app; generate the `sotorasib` brief. Confirm: at-a-glance shows patients/trials/pubs (no $0 TAM); talking points are specific to sotorasib with source chips; Competitive panel shows a real comparison table; nothing regressed elsewhere.
- [ ] Controller shows the user; explicit approval. Note any content that still reads generic (may need a prompt iteration pass).

---

## Self-Review
**Spec coverage:** #3 scientific metrics (T1) · #6 comparison table (T2) · #4 specificity + sources + fixed no-KOL state (T3). ✓ (#2 Discovery reframe intentionally deferred.)
**Risk:** all UI changes guarded by the characterization net; agent changes keep the no-fabrication fallbacks (empty→"—", never invented); provenance URLs only from real retrieval.
**Honesty:** structural quality is guaranteed by schema/UI/prompt; semantic quality (exact figures) needs a live validation run — flagged in Task 4.
