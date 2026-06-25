# Evidentia Stage 2 — Trustworthy Data (Provenance) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make every displayed figure either carry a real, clickable source or show an honest "unavailable" state — and stop the agents from emitting fabricated numbers (the `$0` / `Competitor 1 / $50k / 30%` / `$75M` problems). Source URLs come only from real retrieval; the LLM is never asked for a URL.

**Architecture:** A small provenance vocabulary (`Source`, `SourcedValue`) in the schema, plus a **side map** `GTMState.sources: Dict[str, Source]` keyed by stable ids (e.g. `"market.patient_population"`). Agents populate this map from real retrieval results and stop inventing fallback numbers. Tool functions return canonical URLs (ClinicalTrials/PubMed) and real web URLs (Tavily); `fda_tools` is finally wired for verified facts. The UI reads the value field as today AND looks up `sources.get(key)` to render a chip; a missing/`unavailable` source with a 0/None value renders an honest empty state instead of a fake number.

**Why a side map (refines the spec):** the spec described wrapping fields in `SourcedValue`. Wrapping every numeric field would break ~30 display functions that read `state.market_data.tam_estimate` directly. The side map gives the identical user-visible result (value + chip, or honest-empty) with minimal disruption. `SourcedValue` is still used where a value and its inputs travel together — the modeled market figure.

**Tech Stack:** Python, dataclasses, pytest. Builds on Stage 0 harness + Stage 1 `source_chip` component.

**Branch:** `stage2-provenance` (stacked on `stage1-visual`).

---

## Provenance contract (used throughout)

- Tiers: `"verified"` (FDA / PubMed / ClinicalTrials / SEER), `"web"` (Tavily result, domain shown), `"filing"` (company filing), `"modeled"` (computed from sourced inputs), `"unavailable"` (no source → honest empty).
- **Hard rule (tested):** `Source.url` is only ever set from a real retrieval result object. No prompt asks the LLM for a URL; any URL-looking string in LLM output is ignored for sourcing.
- Stable source-map keys: `market.patient_population`, `market.tam`, `market.sam`, `market.market_figure`, `payer.hta_status`, `payer.pricing_ceiling`, `competitor.<name>.market_share`, `competitor.<name>.pricing`. (Keys are documented in Task 1.)

---

## File Structure

- Modify `src/schema/gtm_state.py` — add `Source`, `SourcedValue`, helper constructors; add `sources: Dict[str, Source]` to `GTMState`.
- Modify `src/service/tools/clinical_trials_tools.py`, `pubmed_tools.py`, `tavily_tools.py` — return canonical / real URLs.
- Modify `src/service/tools/fda_tools.py` usage — call it from `competitor_analysis_agent` / `market_research_agent` for verified facts (the module already exists; it is currently never imported).
- Modify the 6 agents in `src/agents/gtm_agents/` — populate `state.sources`, remove fabricated fallback values, build the modeled market figure; make ICP + synthesis validate JSON like the others.
- Modify `src/ui/app.py` + `src/ui/components.py` — render chips from `state.sources`; honest empty states.
- Create tests under `tests/` for each.

---

## Task 1: Provenance types + state field (TDD)

**Files:** Create `tests/test_provenance.py`; Modify `src/schema/gtm_state.py`.

- [ ] **Step 1: Failing test** — Create `tests/test_provenance.py`:

```python
from src.schema.gtm_state import Source, SourcedValue, unavailable, web_source, verified_source, modeled, GTMState


def test_unavailable_has_no_url_and_unavailable_tier():
    s = unavailable("No public figure")
    assert s.tier == "unavailable"
    assert s.url is None


def test_web_source_keeps_real_url_and_domain_label():
    s = web_source("https://www.drugs.com/price-guide/lumakras")
    assert s.tier == "web"
    assert s.url == "https://www.drugs.com/price-guide/lumakras"
    assert "drugs.com" in s.label


def test_verified_source_sets_verified_tier():
    s = verified_source("ClinicalTrials.gov", "https://clinicaltrials.gov/study/NCT04685135")
    assert s.tier == "verified"
    assert s.url.endswith("NCT04685135")


def test_modeled_carries_inputs_and_no_url():
    patients = SourcedValue(value=13000, display="~13,000", source=verified_source("SEER", "https://seer.cancer.gov"))
    sv = modeled(value=1_600_000_000, display="$1.2–1.8B", inputs=[patients])
    assert sv.source.tier == "modeled"
    assert sv.source.url is None
    assert sv.modeled_from and sv.modeled_from[0].value == 13000


def test_gtmstate_has_sources_map_default_empty():
    st = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
    assert st.sources == {}
```

- [ ] **Step 2: Run → fail** — `pytest tests/test_provenance.py -v` → ImportError.

- [ ] **Step 3: Implement** — Add to `src/schema/gtm_state.py` (near the top, after imports):

```python
from urllib.parse import urlparse

@dataclass
class Source:
    tier: str               # verified | web | filing | modeled | unavailable
    label: str
    url: Optional[str] = None
    note: Optional[str] = None

@dataclass
class SourcedValue:
    value: Any
    source: Source
    display: Optional[str] = None
    modeled_from: List["SourcedValue"] = field(default_factory=list)

def unavailable(note: str = "Unavailable") -> Source:
    return Source(tier="unavailable", label="Unavailable", url=None, note=note)

def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return url

def web_source(url: str, note: Optional[str] = None) -> Source:
    return Source(tier="web", label=_domain(url), url=url, note=note)

def verified_source(label: str, url: Optional[str] = None, note: Optional[str] = None) -> Source:
    return Source(tier="verified", label=label, url=url, note=note)

def filing_source(label: str, url: Optional[str] = None, note: Optional[str] = None) -> Source:
    return Source(tier="filing", label=label, url=url, note=note)

def modeled(value: Any, display: str, inputs: List[SourcedValue]) -> SourcedValue:
    return SourcedValue(value=value, display=display,
                        source=Source(tier="modeled", label="Modeled from sourced inputs", url=None),
                        modeled_from=list(inputs))
```

Add to the `GTMState` dataclass body: `sources: Dict[str, "Source"] = field(default_factory=dict)`.

- [ ] **Step 4: Run → pass** — `pytest tests/test_provenance.py -v` → 5 passed. Then `pytest -q` → all green.

- [ ] **Step 5: Commit** — `git commit -m "feat(schema): add provenance types + GTMState.sources map"`

---

## Task 2: Canonical URLs from ClinicalTrials + PubMed (TDD)

**Files:** Create `tests/test_tool_urls.py`; Modify `clinical_trials_tools.py`, `pubmed_tools.py`.

> **Implementer:** read both tool files first. Each returns dicts per trial/publication. Add a canonical `url` to each record without changing existing keys.

- [ ] **Step 1: Failing test** — Create `tests/test_tool_urls.py`:

```python
from src.service.tools.clinical_trials_tools import nct_url
from src.service.tools.pubmed_tools import pmid_url


def test_nct_url():
    assert nct_url("NCT04685135") == "https://clinicaltrials.gov/study/NCT04685135"


def test_pmid_url():
    assert pmid_url("36546659") == "https://pubmed.ncbi.nlm.nih.gov/36546659/"
```

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement** — add `nct_url(nct_id)` to `clinical_trials_tools.py` and `pmid_url(pmid)` to `pubmed_tools.py` (pure string builders). Then, where each tool builds its per-record dicts, set `record["url"] = nct_url(...)` / `pmid_url(...)`. Keep all existing keys.

- [ ] **Step 4: Run → pass; `pytest -q` green.**

- [ ] **Step 5: Commit** — `git commit -m "feat(tools): canonical ClinicalTrials/PubMed URLs on records"`

---

## Task 3: Real Tavily URLs + wire FDA verified facts (TDD)

**Files:** Modify `tavily_tools.py`, `fda_tools.py`; Create `tests/test_tavily_urls.py`.

> **Implementer:** Tavily's client returns a dict with an `answer` AND a `results` list, each result having a `url`. Today only `answer` is used. Capture the top result url + domain and return them alongside `answer` (new keys; don't remove `answer`). For `fda_tools`, expose a convenience function that returns a verified `Source` for a drug approval (using the existing FDA client), with the openFDA/label URL.

- [ ] **Step 1: Failing test** — `tests/test_tavily_urls.py` asserts that the tavily wrapper return dict includes `top_url` and `top_domain` when results exist, and `top_url=None` when results are empty (use a fake/mock client response — do NOT hit the network).

- [ ] **Step 2–4:** implement, run red→green, `pytest -q` green.

- [ ] **Step 5: Commit** — `git commit -m "feat(tools): capture real Tavily source URLs + FDA verified-source helper"`

---

## Task 4: Consistent JSON validation in ICP + Synthesis (TDD)

**Files:** Modify `icp_definition_agent.py`, `synthesis_agent.py`; add `tests/test_agent_validation.py`.

> **Implementer:** the other four agents use `extract_json_from_text` + `validate_with_pydantic(raw, SomeResponse)`. ICP and synthesis use bare `extract_json_from_text` with no schema. Add Pydantic response schemas for them in `src/service/validators/json_validator.py` (mirror the existing ones) and route both agents through `validate_with_pydantic`, falling back to their default-data path on `not result.valid`.

- [ ] Steps: write a test that malformed JSON for these two agents yields the fallback path (mock the LLM to return junk; assert no exception and a default-shaped result); implement; red→green; commit `fix(agents): validate ICP + synthesis JSON like the others`.

---

## Task 5: Stop fabrication + populate sources + modeled market figure (TDD)

**Files:** Modify all six agents in `src/agents/gtm_agents/`; add `tests/test_no_fabrication.py`.

> **Implementer:** this is the core of Stage 2. Read each agent's `get_default_*` function and its success path. Work one agent at a time, committing per agent.

For EACH agent:
- **Success path:** when a real value is extracted, also record its provenance in `state.sources[key]` using the right constructor — `web_source(top_url)` for Tavily-derived facts, `verified_source(...)` for FDA/PubMed/ClinicalTrials-derived facts. Use the documented stable keys (Task 1).
- **Failure/fallback path:** REMOVE invented numbers. Specifically:
  - `competitor_analysis_agent.get_default_competitor_data`: no `"Competitor 1" / market_share 30.0 / pricing 50000`. Return an empty competitor list and set `state.sources["competitor.*"] = unavailable(...)`.
  - `market_research_agent.get_default_market_data`: keep `None`/`0` value but mark `state.sources["market.patient_population"]=unavailable(...)`, etc. — the UI will show an honest empty state, not a `$0` headline.
  - `icp_definition_agent` ($75M/$25M) and `synthesis_agent` ($40–60k): replace hardcoded figures with `unavailable` provenance (no fabricated number presented as fact).
- **Market figure:** in `market_research_agent`, prefer a real published source (Tavily/filing). If absent, build a `modeled(...)` SourcedValue from sourced inputs (patients × price × penetration); if inputs themselves are unavailable, mark the market figure `unavailable`. Never a bare LLM number.

- [ ] **Tests (`tests/test_no_fabrication.py`):**
  - Mock each agent's LLM to FAIL/return junk; assert the result contains NO fabricated sentinel values (`"Competitor 1"`, `50000`, `75000000`, `40000`), and that `state.sources` marks the relevant keys `unavailable`.
  - Assert no `Source.url` is ever set to a value that came from LLM text (feed the LLM a fake URL in its output; assert it does not appear as a source url).
- [ ] Implement per agent, red→green, commit per agent (e.g. `fix(competitor): no fabricated fallback; real provenance`).

---

## Task 6: UI renders chips + honest empty states

**Files:** Modify `src/ui/app.py`, `src/ui/components.py`.

> **Implementer:** read the At-a-glance band + metric rendering added in Stage 1, and `glance_lead_points`.

- [ ] **Step 1:** add a helper `chip_for(state, key)` in `app.py` that returns `source_chip_html(...)` from `state.sources.get(key)` (tier/label/url), or `""` if absent.
- [ ] **Step 2:** in the At-a-glance band and any metric that has a stable source key, pass `source_html=chip_for(state, key)` into `metric_card`. When the value is `None`/`0` AND the source is `unavailable`/absent, render the honest empty state (the metric shows "—" with an `unavailable` chip, NOT `$0`).
- [ ] **Step 3:** verify with a constructed `GTMState` that has `sources` populated (unit-render test in `tests/test_components.py` or a small `app` helper test): a verified key renders a green chip; an absent key renders empty; a 0-value+unavailable renders "—".
- [ ] **Step 4:** `pytest -q` green. Commit `feat(ui): render provenance chips + honest empty states`.

---

## Task 7: Integration + visual verification (human checkpoint)

- [ ] Run the app locally (`.venv_py310/bin/streamlit run streamlit_app.py`), generate the `sotorasib` brief, and confirm: real figures now carry chips (verified/web), the market figure shows either a sourced number or a "Modeled" range with linked inputs, and anything unsourced shows an honest empty state — **no `$0` / `0 patients` headline numbers, no invented competitor**.
- [ ] Controller shows the user; get explicit approval before Stage 2 is complete.

---

## Self-Review

**Spec coverage:** provenance model (T1) · tool URLs incl. FDA wired (T2,T3) · stop fabrication + modeled figure (T5) · consistent validation (T4) · UI chips + honest empty states (T6) · no-LLM-URL rule tested (T5) · all-six-agents-validate (T4). ✓
**Placeholder scan:** new types are complete code; agent/tool/UI edits are directive against a large existing codebase with one complete example + explicit value lists + "read current code first." ✓
**Type consistency:** `Source`/`SourcedValue`/`unavailable`/`web_source`/`verified_source`/`modeled` defined in T1 and used identically in T5/T6; `state.sources` keys documented in T1 and reused in T5/T6; `source_chip_html` (Stage 1) consumed in T6. ✓
**Design note for reviewer:** provenance via side map `state.sources` (not field-wrapping) — least-breaking; flagged for your approval.
