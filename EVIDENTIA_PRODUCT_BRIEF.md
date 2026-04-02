# Evidentia — Product Brief
## AI-Native Closed-Loop MSL Intelligence Platform

---

## The Problem

Pharma companies deploy Medical Science Liaisons at $200K–$300K loaded annual cost per person. A company with 150 MSLs spends **$30M–$45M per year** on this team.

The function is genuinely valuable: MSL pre-launch scientific engagement with KOLs produces **1.5x treatment adoption** in the first 6 months post-launch and **40% faster adoption trajectories**. When an MSL has a quality interaction with a Key Opinion Leader, it influences prescribing across that KOL's institution and network for over 2 years (Veeva Pulse, 2023–2024).

**But the system leaks value at every step:**

| Problem | Data Point | Source |
|---------|-----------|--------|
| Pre-call prep takes 45+ min per meeting | MSLs manually assemble KOL profiles from disconnected systems | Industry practitioners; H1 internal data |
| Post-call insights are never captured | Only 4 of ~500 MSL Society attendees had a documented post-call process | MSL Society Conference |
| Coverage gaps go unnoticed | 30% of global KOLs have zero recorded MSL interactions | Veeva Pulse 2023 |
| Measurement doesn't measure anything | Only 3% rate their MSL KPI systems "very effective" | Global Survey, 1,023 MA professionals, 2024 |
| Scientific content sits unused | ~80% of approved content is rarely or never used in field meetings | Veeva Pulse 2025 |
| MSLs under pressure without tools | 95% face increased pressure to gather actionable insights | THE MSL Journal |

**The CRM gap:** Veeva CRM — used by 80% of global biopharma — tracks activity counts: calls made, emails sent. It cannot tell you whether those interactions were scientifically substantive, which KOLs are being missed, or what unmet needs are emerging across the territory. It was built for sales, not medical.

**The total cost of this dysfunction:** For a 150-MSL organization, manual pre-call prep alone costs approximately **$2.88M/year** in loaded labor time. That excludes the harder-to-quantify cost of insights never captured, strategy never informed, and coverage gaps in the 30% of KOLs who should be engaged but aren't.

---

## The Solution

Evidentia is an AI-native closed-loop MSL intelligence platform. Four integrated workflows:

### 1. Pre-Call Brief Generation (90 seconds → 10 minutes to review)
Select a KOL and drug. Evidentia generates a 10-tab intelligence package:
- **KOL Profile**: research focus, publication count, trial PI roles, influence tier, prior interaction history
- **Clinical Evidence**: top 5 most relevant publications ranked by RAG retrieval (not just 20 chronological results)
- **Competitive Position**: competitor data grounded in FDA approval records, not LLM imagination
- **Payer Intelligence**: HTA status, QALY threshold, reimbursement barriers
- **Talking Points + Objection Responses**: specific to this KOL's research focus and known positions
- **Discovery Questions**: based on the KOL's published data gaps and therapeutic area focus

Every data point shows its source: FDA-verified (green), web-sourced (yellow), or AI-estimated (orange — verify before use).

### 2. Post-Call Insight Capture (2 minutes)
MSL enters freeform field notes after a meeting. Evidentia extracts 1–10 structured insights automatically:
- **10 categories**: unmet medical need, competitive intelligence, data gap, safety signal, prescribing barrier, payer barrier, clinical question, publication request, trial interest, KOL sentiment
- MSL reviews, edits, confirms
- Safety signals auto-trigger an escalation email draft to Medical Affairs
- Insights stored persistently for trend analysis

### 3. Engagement Quality Tracking (automated)
After each interaction, Evidentia computes a quality score (0–10) across four dimensions:
- Scientific depth, KOL engagement, actionability, relationship advancement
- Coverage dashboard: which Tier 1 KOLs haven't been contacted in 45+ days
- Quality trend: is this MSL's interaction quality improving over time?
- Network map: who does this KOL influence (co-authors, co-PIs, institutional colleagues)?

### 4. Territory Intelligence Synthesis (on-demand, <60 seconds)
Aggregates 90 days of field insights across all MSLs in a territory:
- Top 3 unmet medical needs with KOL quotes
- Competitive signals and new mentions in the last 30 days
- Content gaps: what KOLs are asking for that doesn't exist in the approved content library
- Medical strategy recommendations with rationale and owner assignment
- Safety signal escalation tracker

---

## Differentiation

| Capability | **Evidentia** | Veeva CRM | Sorcero | H1 | TikaMobile |
|-----------|--------------|-----------|---------|----|----|
| Pre-call KOL briefs | AI-native, 90s, KOL-specific | Manual prep, no AI | Enterprise-only | Data only | Not a brief tool |
| Post-call insight capture | Structured, AI-extracted, 10 categories | Freeform text field | Partial (note analytics) | No | Basic CRM notes |
| Interaction quality scoring | Yes, 0–10 scientific quality | Activity count only | No | No | No |
| Territory insight synthesis | Yes, on-demand, <60s | No | Partial (expensive) | No | No |
| Clinical evidence RAG | Yes (PubMed + ClinTrials + FDA) | No | No | Publication data | No |
| Competitor data grounding | FDA-verified + confidence badges | No | No | Publication data | No |
| Persistent memory across sessions | Yes (SQLite + ChromaDB) | Yes (Salesforce) | Yes | Yes | Yes |
| MSL-specific UX | Built for MSLs | Built for sales | Complex/enterprise | Data portal | Mobile-first |
| **Pricing** | **SMB/Mid-market** | Enterprise $$$ | Enterprise $$$$ | Data platform $$$ | SMB $ |

**The key differentiator:** Evidentia is the only tool that closes the loop from brief generation → post-call capture → team-wide intelligence → medical strategy. Every other tool solves one of these problems. None solve all four together.

---

## Customer ROI

### Time Savings
```
150 MSLs
× 4 HCP interactions/week
× 40 minutes saved per meeting (45 min → 5 min review)
= 400 hours/week recovered
= 1,600 hours/month
× $150/hour loaded labor cost
= $240,000/month saved
= $2.88M/year
```

### Coverage Improvement
Closing the 30% Tier 1 KOL coverage gap = more pre-launch scientific engagement = higher adoption trajectory.

For a drug with $200M peak sales:
- MSL pre-launch engagement → 1.5x adoption in first 6 months (Veeva Pulse 2023)
- 50% improvement in Tier 1 coverage = conservative 0.3x additional adoption uplift
- On $200M drug: **$60M additional revenue** attributable to scientific engagement quality
- MSL tool cost: $360K–$720K/year for a 50–100 MSL team

**The ROI closes in the first month.** This is why VP Medical Affairs signs, not IT.

---

## Target Customer

### Primary Buyer
**VP Medical Affairs** or **Chief Medical Officer** at pharmaceutical/biotech companies with 50–500 MSLs.

**Ideal company profile:**
- Revenue: $500M–$5B (mid-size pharma, large biotech)
- MSL headcount: 50–300 (scaling or mature field medical program)
- **High-priority pain signal:** Drug launch in the next 12–24 months OR poor insight capture feedback from field team leadership
- Tech stack: Veeva CRM (Evidentia is additive, not a replacement)
- Geography: US-first, then EU4/UK

**Secondary buyer:** Director of Field Medical Excellence / Director of MSL Operations. They own the measurement problem most acutely — they're the ones being asked to prove MSL ROI with tools that only measure call volume.

**Field champion:** Individual MSLs. They experience the 45-minute prep pain daily and will advocate for a tool that reduces it to 5 minutes.

### Therapeutic Area Focus (Initial)
- Oncology (largest MSL teams, most complex science, most active KOL landscape)
- Rare disease (high per-patient value, smaller but critical KOL universe)
- Specialty cardiology / neurology (secondary)

---

## Pilot Design

### Structure
**90-day paid pilot at a single therapeutic area with 10 MSLs.**

### Pricing
- Pilot: **$15,000 flat** (covers setup, onboarding, 90-day access, weekly check-ins)
- Scale pricing: **$500–$800/MSL/month** depending on feature tier
- Enterprise: custom contract with Veeva API integration + SSO + dedicated support

### Minimum viable annual deal
50 MSLs × $600/month = **$360,000 ARR** per customer

### Target Year 1
5 pilot customers → 3 convert to annual at 50–100 MSLs = **$1.08M–$2.16M ARR** by end of Year 1

### Pilot Success Criteria (Measured from Day 1)

| Metric | Baseline (Week 1) | Target (Week 12) |
|--------|------------------|-----------------|
| Pre-call brief prep time | ~45 min (self-reported) | <10 min |
| Post-call insight capture rate | <20% of calls | >80% of calls |
| Tier 1 KOL coverage gap | Measured at start | Reduced by 50% |
| MSL NPS | Baseline measured | >8/10 |

### Pilot Deliverable to Medical Affairs Leadership
At 90 days: a territory intelligence report showing emerging unmet needs, competitive signals, and medical strategy recommendations — built from the pilot team's actual field insights. This is the "wow moment" that converts pilots to annual contracts.

---

## Why Now

1. **AI timing:** Claude Sonnet 4 + LangGraph enable multi-agent orchestration that was impractical 18 months ago. The underlying tech is mature enough for production.

2. **Market timing:** Pharma's AI investment in commercial is maturing. Medical Affairs AI is 2–3 years behind commercial AI adoption — the window to establish category leadership is open now.

3. **Competitor timing:** Sorcero and H1 are enterprise-only, $500K+ contracts. TikaMobile is a CRM, not an intelligence platform. Veeva is a data company, not an AI company. The mid-market (50–300 MSL teams) is underserved.

4. **Regulatory pressure:** FDA and EMA increasingly require evidence of MSL interaction quality and scientific exchange integrity. Companies need audit trails. Evidentia's data confidence badges and audit logging are features that compliance teams will request.

---

## Current State

**Evidentia v1.0 is live** at `evidentia-production-73a5.up.railway.app`.

Tech stack: Python 3.11, LangGraph 1.1.3, Claude Sonnet 4, Streamlit 1.55.0, FastAPI 0.135.1.

**v2.0 adds** (8-week build plan, see `EVIDENTIA_V2_ARCHITECTURE.md`):
- Persistent memory: SQLite + ChromaDB (SKILL_06)
- KOL-specific profiling with RAG-grounded evidence (SKILL_01)
- Post-call structured insight capture (SKILL_02)
- Engagement quality scoring + coverage gap detection (SKILL_03)
- Territory-wide intelligence dashboard (SKILL_04)
- Production-grade reliability: Pydantic validation, retry logic, caching (SKILL_05)

**v2.0 is pilot-ready.** v2.1 adds OAuth2/SSO, Veeva API integration, and mobile app (React Native).

---

## One-Paragraph Pitch

> Evidentia is the AI platform Medical Affairs teams need but pharma's CRM vendors were never built to deliver. While Veeva counts calls and H1 indexes publications, Evidentia closes the loop: it generates a KOL-specific, FDA-grounded pre-call brief in 90 seconds, extracts structured insights from field notes in 2 minutes, scores interaction quality automatically, and synthesizes territory-wide intelligence that tells your Head of Medical Affairs what KOLs across your NSCLC territory are really saying about unmet needs — right now, not in next quarter's advisory board. For a 150-MSL team, that's $2.88M/year recovered in prep time alone, before you count the revenue impact of higher-quality scientific engagement on treatment adoption.
