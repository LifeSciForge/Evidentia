# Evidentia Stage 1 — Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reskin the results view to the approved "Direction C" look (soft neutrals + indigo accent), add a reusable source-chip component and an "At a glance" summary band, and restructure the results tabs (7→6, Export as a header button) — UI layer only, no agent/tool logic changes.

**Architecture:** Presentational logic lives in `src/ui/components.py` as **pure `*_html(...) -> str` builder functions** (unit-testable) wrapped by thin Streamlit `st.markdown` callers. `src/ui/app.py` consumes them: a new Direction-C CSS theme block, an `at a glance` band in `display_msl_results()`, and a restructured 6-tab layout. No backend/provenance data exists yet (that is Stage 2) — chips render from whatever real links already exist (trial NCT, publication PMID) and degrade gracefully otherwise.

**Tech Stack:** Streamlit, Python, pytest. Builds on Stage 0's test harness (`tests/`, `pytest.ini`, `conftest.py`).

**Branch:** `stage1-visual` (stacked on `stage0-foundation`).

---

## Design tokens (Direction C — use these exact values)

```
--ev-bg: #f7f8fb;        /* page background        */
--ev-surface: #ffffff;   /* cards                  */
--ev-border: #ececf3;    /* card / divider borders */
--ev-text: #1a1d29;      /* primary text           */
--ev-muted: #6b7280;     /* secondary text         */
--ev-accent: #5b5bd6;    /* indigo accent          */
--ev-verified: #1aa564;  /* green  — authoritative source */
--ev-web: #4b4bc7;       /* blue   — web source           */
--ev-filing: #c2741b;    /* amber  — filing / modeled     */
--ev-unavailable: #9aa0ad;/* gray  — no source / empty     */
```

Chip background tints: verified `#e9f7f0`, web `#eef0fe`, filing `#fff3e9`, unavailable `#f1f2f5`.

---

## File Structure

- Modify `src/ui/components.py` — add `source_chip_html` / `source_chip`, rewrite `metric_card` as `metric_card_html` + wrapper, restyle the two Plotly charts to the palette.
- Create `tests/test_components.py` — unit tests for the html builders.
- Modify `src/ui/app.py` — replace the global CSS palette with Direction-C tokens; add the "At a glance" band in `display_msl_results()`; restructure tabs 7→6 (merge "Final Brief" into a lead "Pre-Call Brief", move "Download" to a header Export button); remove the duplicated "no data" guard.
- Create `tests/test_at_a_glance.py` — unit tests for the pure content-selection helper.

---

## Task 1: Source-chip component (TDD)

**Files:**
- Create: `tests/test_components.py`
- Modify: `src/ui/components.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_components.py`:

```python
from src.ui.components import source_chip_html


def test_verified_tier_renders_link_with_label_and_class():
    html = source_chip_html("verified", "ClinicalTrials.gov", url="https://clinicaltrials.gov/study/NCT04685135")
    assert "ev-chip-verified" in html
    assert "ClinicalTrials.gov" in html
    assert 'href="https://clinicaltrials.gov/study/NCT04685135"' in html
    assert "<a " in html  # has url -> anchor


def test_unavailable_tier_renders_span_without_link():
    html = source_chip_html("unavailable", "Unavailable")
    assert "ev-chip-unavailable" in html
    assert "<a " not in html  # no url -> span, not a link


def test_label_is_html_escaped():
    html = source_chip_html("web", '<script>alert(1)</script>', url="https://x.test")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_unknown_tier_falls_back_to_unavailable_class():
    html = source_chip_html("bogus", "X")
    assert "ev-chip-unavailable" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_components.py -v`
Expected: FAIL with `ImportError: cannot import name 'source_chip_html'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/ui/components.py` (top: `import html as _html`; keep existing `import streamlit as st`):

```python
import html as _html

_CHIP_TIERS = {"verified", "web", "filing", "modeled", "unavailable"}


def source_chip_html(tier: str, label: str, url: str | None = None, note: str | None = None) -> str:
    """Build a provenance chip as an HTML string.

    tier: one of verified | web | filing | modeled | unavailable (unknown -> unavailable).
    Renders an <a> when a url is given, otherwise a <span>. All text is HTML-escaped.
    """
    safe_tier = tier if tier in _CHIP_TIERS else "unavailable"
    cls = f"ev-chip ev-chip-{safe_tier}"
    safe_label = _html.escape(label or "")
    title = f' title="{_html.escape(note)}"' if note else ""
    if url:
        safe_url = _html.escape(url, quote=True)
        return (
            f'<a class="{cls}" href="{safe_url}" target="_blank" '
            f'rel="noopener noreferrer"{title}>{safe_label} ↗</a>'
        )
    return f'<span class="{cls}"{title}>{safe_label}</span>'


def source_chip(tier: str, label: str, url: str | None = None, note: str | None = None) -> None:
    """Render a provenance chip inline."""
    st.markdown(source_chip_html(tier, label, url=url, note=note), unsafe_allow_html=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_components.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/test_components.py src/ui/components.py
git commit -m "feat(ui): add source_chip provenance component (Direction C)"
```

---

## Task 2: Metric card + chart restyle (TDD for the card)

**Files:**
- Modify: `src/ui/components.py`
- Modify: `tests/test_components.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_components.py`:

```python
from src.ui.components import metric_card_html


def test_metric_card_shows_label_value_and_no_gradient():
    html = metric_card_html("Addressable patients", "~13,000")
    assert "Addressable patients" in html
    assert "~13,000" in html
    assert "linear-gradient" not in html  # retired the purple gradient
    assert "ev-metric-card" in html


def test_metric_card_embeds_optional_source_chip():
    chip = source_chip_html("verified", "SEER/NCI", url="https://seer.cancer.gov")
    html = metric_card_html("Addressable patients", "~13,000", source_html=chip)
    assert "ev-chip-verified" in html
    assert "SEER/NCI" in html
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_components.py -v`
Expected: FAIL with `ImportError: cannot import name 'metric_card_html'`

- [ ] **Step 3: Replace `metric_card` with a pure builder + wrapper**

In `src/ui/components.py`, replace the existing `metric_card(...)` function with:

```python
def metric_card_html(title: str, value: str, subtitle: str = "", source_html: str = "") -> str:
    """Direction C metric card (no gradient). Optionally embeds a source chip."""
    safe_title = _html.escape(title or "")
    safe_value = _html.escape(str(value))
    safe_sub = _html.escape(subtitle or "")
    sub = f'<div class="ev-metric-sub">{safe_sub}</div>' if safe_sub else ""
    chip = f'<div class="ev-metric-chip">{source_html}</div>' if source_html else ""
    return (
        f'<div class="ev-metric-card">'
        f'<div class="ev-metric-label">{safe_title}</div>'
        f'<div class="ev-metric-value">{safe_value}</div>'
        f'{chip}{sub}</div>'
    )


def metric_card(title: str, value: str, subtitle: str = "", icon: str = "", source_html: str = "") -> None:
    """Render a metric card. `icon` kept for backward compatibility (prefixed to title)."""
    title_text = f"{icon} {title}".strip() if icon else title
    st.markdown(metric_card_html(title_text, value, subtitle=subtitle, source_html=source_html),
                unsafe_allow_html=True)
```

- [ ] **Step 4: Restyle the two charts to the palette**

In `src/ui/components.py`, update `market_sizing_waterfall` and `competitor_positioning_scatter`: set the marker/line colors and `fig.update_layout` to the Direction C palette — accent `#5b5bd6`, positive `#1aa564`, loss `#c2741b`; `paper_bgcolor="#ffffff"`, `plot_bgcolor="#ffffff"`, font `family="Inter", color="#1a1d29"`. Keep the function signatures and return values unchanged.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_components.py -v`
Expected: PASS (6 passed total in this file).

- [ ] **Step 6: Commit**

```bash
git add src/ui/components.py tests/test_components.py
git commit -m "feat(ui): Direction C metric card (no gradient) + chart restyle"
```

---

## Task 3: Direction C CSS theme in app.py

**Files:**
- Modify: `src/ui/app.py`

> **Implementer:** read the current global `st.markdown("""<style> ... </style>""")` block (starts near line 52) and the `.ev-*` rules below it before editing. This task re-skins; it does not change structure.

- [ ] **Step 1: Introduce the design tokens + chip styles**

At the very top of the existing global `<style>` block (right after `<style>`), add a `:root` token block and the chip rules:

```css
:root{
  --ev-bg:#f7f8fb; --ev-surface:#ffffff; --ev-border:#ececf3;
  --ev-text:#1a1d29; --ev-muted:#6b7280; --ev-accent:#5b5bd6;
  --ev-verified:#1aa564; --ev-web:#4b4bc7; --ev-filing:#c2741b; --ev-unavailable:#9aa0ad;
}
.ev-chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;
  padding:4px 9px;border-radius:999px;text-decoration:none;border:1px solid transparent;}
.ev-chip-verified{background:#e9f7f0;color:var(--ev-verified);}
.ev-chip-web{background:#eef0fe;color:var(--ev-web);}
.ev-chip-filing{background:#fff3e9;color:var(--ev-filing);}
.ev-chip-modeled{background:#fff3e9;color:var(--ev-filing);}
.ev-chip-unavailable{background:#f1f2f5;color:var(--ev-unavailable);}
.ev-metric-card{background:var(--ev-surface);border:1px solid var(--ev-border);border-radius:14px;
  padding:16px;box-shadow:0 1px 3px rgba(20,20,50,.05);}
.ev-metric-label{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--ev-muted);}
.ev-metric-value{font-size:24px;font-weight:700;color:var(--ev-text);margin:4px 0 8px;}
.ev-metric-chip{margin-bottom:6px;} .ev-metric-sub{font-size:12px;color:var(--ev-muted);}
.ev-glance{margin:8px 0 4px;} .ev-glance-row{display:flex;gap:14px;flex-wrap:wrap;}
.ev-glance-row > div{flex:1;min-width:180px;}
.ev-glance-box{background:var(--ev-surface);border:1px solid var(--ev-border);border-radius:12px;padding:13px;}
.ev-glance-h{font-size:11px;font-weight:700;color:var(--ev-accent);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px;}
.ev-glance-box p{font-size:13px;color:#3f4654;margin:0;line-height:1.5;}
```

- [ ] **Step 2: Repoint the existing palette to Direction C**

In the same `<style>` block, change the navy-based values to the new palette: brand/title and accents `#003366` → `var(--ev-accent)` (`#5b5bd6`); meta-value color `#003366` → `var(--ev-text)`; keep the existing layout/spacing. Update the page background to `--ev-bg` via `section[data-testid="stMain"]{background:var(--ev-bg);}`. Do not change non-color structural rules.

- [ ] **Step 3: Verify the app module imports and the CSS contains the tokens**

Run: `ANTHROPIC_API_KEY=test-key TAVILY_API_KEY=test-key python -c "import ast; ast.parse(open('src/ui/app.py').read()); print('syntax ok')"`
Expected: `syntax ok`
Run: `grep -c -- "--ev-accent" src/ui/app.py`
Expected: a count ≥ 2 (token defined and referenced).
Run: `pytest -q`
Expected: all green (no behavior regressions).

- [ ] **Step 4: Commit**

```bash
git add src/ui/app.py
git commit -m "feat(ui): apply Direction C palette + chip/metric/glance styles"
```

---

## Task 4: "At a glance" band (TDD for content selection)

**Files:**
- Create: `tests/test_at_a_glance.py`
- Modify: `src/ui/app.py`

> **Implementer:** first read `src/schema/gtm_state.py` for the real field names on `GTMState`, `MarketResearchData`, `MSLTalkingPoints`, and `MessagingData`, and skim `display_talking_points_section` / `display_objection_handling_section` in `app.py` to see how they already pull a lead talking point and a top objection. Reuse those access patterns. The helper must be defensive (return `None` when data is absent) so it never raises.

- [ ] **Step 1: Write the failing test**

Create `tests/test_at_a_glance.py`:

```python
from types import SimpleNamespace
from src.ui.app import glance_lead_points


def test_returns_none_fields_when_state_empty(demo_state):
    lead, objection = glance_lead_points(demo_state)
    assert lead is None or isinstance(lead, str)
    assert objection is None or isinstance(objection, str)


def test_picks_strings_when_present():
    state = SimpleNamespace(
        msl_talking_points=SimpleNamespace(talking_points=["Lead point about efficacy"]),
        messaging_data=SimpleNamespace(positioning_statement="pos"),
        objections=[{"objection": "OS not significant", "response": "reframe"}],
    )
    lead, objection = glance_lead_points(state)
    assert isinstance(lead, str) and lead
    assert isinstance(objection, str) and objection
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_at_a_glance.py -v`
Expected: FAIL with `ImportError: cannot import name 'glance_lead_points'`

- [ ] **Step 3: Implement the defensive helper**

Add `glance_lead_points(state)` to `src/ui/app.py` near `display_msl_results`. It returns `(lead_point, likely_objection)` as `Optional[str]`, reading whatever fields exist (use the real field names found above; the test above shows the expected duck-typed shape). Use `getattr(..., None)` and guard every access; never raise.

- [ ] **Step 4: Render the band in `display_msl_results()`**

After the metadata strip and before `tabs = st.tabs([...])`, render an "At a glance" section: a row of up to three `metric_card`s built from `state.market_data` (e.g. patients, cost, market — show only those present), then a two-box row using `.ev-glance-box` for "Lead talking point" and "Likely objection" from `glance_lead_points(state)`. Skip any sub-part whose data is `None` (honest empty — no placeholder text).

- [ ] **Step 5: Run tests + syntax**

Run: `pytest tests/test_at_a_glance.py -v` → PASS.
Run: `pytest -q` → all green.

- [ ] **Step 6: Commit**

```bash
git add tests/test_at_a_glance.py src/ui/app.py
git commit -m "feat(ui): add At a glance summary band"
```

---

## Task 5: Tab restructure (7→6) + Export header button + dedup guard

**Files:**
- Modify: `src/ui/app.py`

> **Implementer:** read `display_msl_results` (≈ line 647), `display_final_brief_section` (≈ 1825), and `display_download_section` (≈ 2208) before editing.

- [ ] **Step 1: Remove the duplicated "no data" guard**

In `display_msl_results`, the identical "No data found" `if not state.market_data ...` block appears twice in a row (≈ lines 651–660 and 663–672). Delete the second copy; keep one.

- [ ] **Step 2: Restructure the tabs**

Change the `st.tabs([...])` list from the current 7 to these 6, in order:
`["Pre-Call Brief", "Talking Points", "Objections & Questions", "Discovery Questions", "Clinical Evidence", "Competitive Position"]`.
Wire `tabs[0]` (Pre-Call Brief) to call `display_final_brief_section(state)` (the merged brief). Map the remaining tabs to their existing section functions in the new order. Remove the separate "Download Brief" tab.

- [ ] **Step 3: Add an Export button to the header**

In the header/metadata area of `display_msl_results` (where the meta strip renders), add a right-aligned Export control that invokes the existing download logic from `display_download_section(state)`. Reuse that function's PDF/download code — do not duplicate it; if needed, extract its button into a small helper called from both places, or call `display_download_section(state)` inside a right-aligned column. Keep behavior identical.

- [ ] **Step 4: Verify**

Run: `ANTHROPIC_API_KEY=test-key TAVILY_API_KEY=test-key python -c "import ast; ast.parse(open('src/ui/app.py').read()); print('syntax ok')"` → `syntax ok`
Run: `pytest -q` → all green.
Run: `grep -c 'st.tabs' src/ui/app.py` → 1 (still one tab container).

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py
git commit -m "feat(ui): 6-tab call-flow layout, merged Pre-Call Brief, header Export"
```

---

## Task 6: Visual verification (human checkpoint)

**Files:** none (verification only)

- [ ] **Step 1: Launch the app locally and capture the results view**

Run the app with the local `.env` (real keys present) and generate the demo brief (`sotorasib` / `KRAS G12C NSCLC`). Confirm visually: Direction C palette applied, "At a glance" band shows metrics + lead point + objection, 6 tabs in order, Export button in the header, no purple gradient, source chips appear where real links exist. Capture a screenshot.

- [ ] **Step 2: Controller presents to the user for sign-off**

The controller (not a subagent) shows the screenshot to the user and gets explicit visual approval before Stage 1 is considered complete. Fix any visual issues the user raises, then re-verify.

---

## Self-Review

**Spec coverage (Stage 1):**
- Direction C styling, retire purple gradient → Tasks 2 + 3. ✓
- Source-chip component → Task 1. ✓
- "At a glance" band → Task 4. ✓
- 6-tab call-flow layout, merge Final Brief, Export header button, dedup guard → Task 5. ✓
- Honest empty states (UI groundwork: skip absent sub-parts, no placeholders) → Task 4 step 4. ✓
- Render smoke tests for source_chip + metric card → Tasks 1, 2. ✓

**Placeholder scan:** New component/helper code is complete; app.py edits are directive (modifying a 2,288-line existing file) and explicitly instruct the implementer to read the current code first — appropriate for in-file edits, not placeholders. ✓

**Type consistency:** `source_chip_html(tier,label,url,note)` defined Task 1, consumed in `metric_card_html(..., source_html=...)` Task 2 and the band Task 4. `metric_card_html`/`metric_card` signatures consistent. `glance_lead_points(state) -> (Optional[str], Optional[str])` defined Task 4, used in the band. ✓

**Note:** Provenance chips render truthfully only after Stage 2 supplies `Source` data; in Stage 1 they appear where real links already exist and the component degrades gracefully otherwise — consistent with the spec.
