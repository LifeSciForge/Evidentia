# SKILL_09 — UI/UX Standards for Evidentia

**Source:** [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
**Applies to:** All Streamlit UI pages in `src/ui/app.py` and `pages/`

---

## Search Command

The ui-ux-pro-max skill provides a searchable database for design decisions.
If the skill is installed locally:

```bash
# Get design system for a specific domain
python3 skills/ui-ux-pro-max/scripts/search.py "pharma MSL dashboard" --design-system

# Get UX guidelines
python3 skills/ui-ux-pro-max/scripts/search.py "data table clinical" --domain ux

# Get color palette for healthcare SaaS
python3 skills/ui-ux-pro-max/scripts/search.py "healthcare enterprise SaaS" --domain color

# Get chart recommendations
python3 skills/ui-ux-pro-max/scripts/search.py "KOL engagement trend line" --domain chart
```

---

## Priority Rules for Evidentia UI

### CRITICAL — Accessibility

- **Contrast:** All body text ≥ 4.5:1, secondary text ≥ 3:1 in both light and dark mode
- **Focus states:** All interactive elements must have visible keyboard focus indicators
- **Alt text:** Every non-decorative image and icon must have a label
- **Never use colour alone** to convey information (e.g. confidence badges must also use icons or text)

### CRITICAL — Touch & Interaction (for future mobile)

- Minimum touch targets: 44×44px
- Button spacing: ≥ 8px between adjacent tap targets
- Loading feedback: show spinner within 150ms of any action that takes >500ms

### HIGH — Streamlit-Specific Layout Rules

```python
# Always set page config at top of every page:
st.set_page_config(
    page_title="Evidentia | MSL Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

- Use `st.columns()` for side-by-side metrics, not nested `st.container()`
- Use `st.tabs()` for multi-section content (the 10-tab brief pattern is correct)
- Use `st.expander()` for secondary information that clutters the primary view
- Never use horizontal scroll — all content must fit within the viewport width

### HIGH — Data Confidence Badges

Every AI-generated data point must show its source. Use consistent colours:

```python
# In src/ui/components.py
def confidence_badge(level: str) -> str:
    badges = {
        "FDA-verified":   "🟢 FDA-verified",
        "Tavily-sourced": "🟡 Web-sourced",
        "LLM-estimated":  "🟠 AI-estimated — verify before use",
    }
    return badges.get(level, "⚪ Unknown source")
```

Never display competitor pricing, market share, or clinical trial data without a badge.

### HIGH — Navigation & Page Structure

The 5-page Evidentia layout:
```
01_Brief_Generator.py     → Primary page (most used, load first)
02_Post_Call_Capture.py   → Secondary action
03_KOL_Engagement.py      → Manager / team view
04_Field_Intelligence.py  → Medical Affairs leadership view
05_Settings.py            → Authentication + configuration
```

- Page names in sidebar must be ≤ 30 characters
- Active page indicator must be visible
- Back navigation must be predictable (Streamlit handles this via multipage)

### MEDIUM — Typography & Colour

Evidentia colour palette (from `generate_pdf.py`, keep consistent across UI):

| Token | Hex | Use |
|-------|-----|-----|
| `NAVY` | `#0A2342` | Section headers, primary text |
| `BLUE` | `#0055B8` | Buttons, links, active states |
| `LIGHT_BLUE` | `#E8F0FB` | Card backgrounds, highlights |
| `TEAL` | `#00818A` | Success states, confirmed insights |
| `ORANGE` | `#E87722` | AI-estimated badges, warnings |
| `RED` | `#C0392B` | Safety signal alerts, errors |

Apply in Streamlit with CSS injection:
```python
st.markdown("""
<style>
.insight-card { background: #E8F0FB; border-left: 4px solid #0055B8; padding: 1rem; }
.safety-alert { background: #FDECEA; border-left: 4px solid #C0392B; padding: 1rem; }
.confirmed-badge { color: #00818A; font-weight: 600; }
</style>
""", unsafe_allow_html=True)
```

### MEDIUM — Forms & User Feedback

Post-call capture form rules:
- Every input field must have a visible label (not just placeholder)
- Required fields marked with `*`
- Show word count for field notes textarea (target: 50–500 words)
- Disable submit button while LLM is processing (show spinner)
- On successful insight extraction: show green confirmation toast
- On safety signal detected: show red alert immediately, above other insights

### MEDIUM — Charts & Data Visualisation

Recommended chart types for Evidentia (from ui-ux-pro-max chart database):

| Data | Chart Type | Library |
|------|-----------|---------|
| Quality score over time | Line chart | Plotly |
| Insight category distribution | Horizontal bar | Plotly |
| KOL coverage heatmap | Heatmap | Plotly |
| Territory unmet needs frequency | Bar chart (sorted desc) | Plotly |
| Content usage rate | Gauge (0–100%) | Plotly |

Chart standards:
- All charts must be responsive (`use_container_width=True`)
- All charts must include axis labels and a title
- Colour-blind safe palette: avoid red/green only; use blue/orange or add patterns
- Tooltips must show exact values on hover

---

## Pre-Delivery UI Checklist

Before shipping any new UI page or component:

- [ ] All text passes 4.5:1 contrast ratio
- [ ] Page loads without horizontal scroll at 1280px wide
- [ ] All data confidence badges present on AI-generated numbers
- [ ] Safety signals shown in red, above other content
- [ ] All form fields have visible labels
- [ ] Submit/action buttons disabled during processing
- [ ] Loading spinner appears within 150ms of user action
- [ ] All charts have titles, axis labels, and tooltips
- [ ] Page works with empty state (no KOL selected, no insights yet)
- [ ] `st.set_page_config()` called at top of page file

---

## Evidentia UI Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Bare numbers without source | Add `confidence_badge()` |
| Colour-only status indicators | Add icon + text label |
| Long unstructured LLM text dump | Use `st.expander()` + structured bullets |
| Full JSON shown in UI | Format with `st.json()` in an expander only for debug |
| Missing empty state | Add `if not data: st.info("No data yet — generate a brief first.")` |
| Blocking UI during 90s brief generation | Use `st.status()` streaming updates per agent |
