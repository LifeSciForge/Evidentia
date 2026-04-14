"""
PDF Brief Generator — Evidentia MSL Intelligence Platform
Generates a professional pre-call brief using ReportLab.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#003366")
ACCENT = colors.HexColor("#0066CC")
GREEN = colors.HexColor("#00A86B")
LIGHT_GREY = colors.HexColor("#F5F5F5")
MID_GREY = colors.HexColor("#666666")
BORDER = colors.HexColor("#E0E0E0")
WHITE = colors.white

# Page margins (portrait A4)
LEFT_M = 18 * mm
RIGHT_M = 18 * mm
TOP_M = 16 * mm
BOTTOM_M = 16 * mm


# ── Style sheet ───────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def ps(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "drug": ps("drug",
                   fontName="Helvetica-Bold", fontSize=20,
                   textColor=NAVY, spaceAfter=2),
        "indication": ps("indication",
                         fontName="Helvetica", fontSize=11,
                         textColor=ACCENT, spaceAfter=4),
        "meta": ps("meta",
                   fontName="Helvetica", fontSize=9,
                   textColor=MID_GREY, spaceAfter=2),
        "section": ps("section",
                      fontName="Helvetica-Bold", fontSize=12,
                      textColor=NAVY, spaceBefore=10, spaceAfter=4),
        "subsection": ps("subsection",
                         fontName="Helvetica-Bold", fontSize=10,
                         textColor=ACCENT, spaceBefore=6, spaceAfter=3),
        "body": ps("body",
                   fontName="Helvetica", fontSize=9,
                   textColor=colors.HexColor("#333333"),
                   leading=14, spaceAfter=3),
        "bullet": ps("bullet",
                     fontName="Helvetica", fontSize=9,
                     textColor=colors.HexColor("#333333"),
                     leftIndent=12, bulletIndent=0,
                     leading=14, spaceAfter=2),
        "caption": ps("caption",
                      fontName="Helvetica-Oblique", fontSize=8,
                      textColor=MID_GREY, spaceAfter=2),
        "footer": ps("footer",
                     fontName="Helvetica", fontSize=8,
                     textColor=MID_GREY, alignment=TA_CENTER),
        "label": ps("label",
                    fontName="Helvetica-Bold", fontSize=8,
                    textColor=MID_GREY, spaceAfter=1),
        "green_bullet": ps("green_bullet",
                           fontName="Helvetica", fontSize=9,
                           textColor=GREEN,
                           leftIndent=12, leading=14, spaceAfter=2),
    }


# ── Helper builders ───────────────────────────────────────────────────────────

def _rule(styles: dict) -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6)


def _section_heading(title: str, styles: dict) -> list:
    return [
        Spacer(1, 4 * mm),
        Paragraph(title.upper(), styles["section"]),
        HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=4),
    ]


def _bullet_items(items: List[str], styles: dict, style_key: str = "bullet") -> list:
    """Convert a list of strings to bullet Paragraph objects."""
    out = []
    for item in items:
        text = str(item).strip()
        if text:
            out.append(Paragraph(f"• {text}", styles[style_key]))
    return out or [Paragraph("No data available.", styles["caption"])]


def _safe_str(val: Any, fallback: str = "—") -> str:
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback


# ── Section renderers ─────────────────────────────────────────────────────────

def _build_header(state, drug_name: str, physician: str, hospital: str,
                  styles: dict) -> list:
    """Evidentia brand header + brief metadata."""
    # Brand bar (navy table row spanning full width)
    brand_data = [["EVIDENTIA  ·  Clinical Pre-Call Intelligence Brief  ·  For MSL Use Only"]]
    brand_table = Table(brand_data, colWidths=["100%"])
    brand_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))

    indication = _safe_str(getattr(state, "indication", None))
    generated = datetime.now().strftime("%d %b %Y, %H:%M")
    physician_line = physician or "—"
    hospital_line = hospital or "—"

    meta_rows = [
        ["Drug / Indication",
         f"{drug_name}  ·  {indication}"],
        ["Physician", physician_line],
        ["Institution", hospital_line],
        ["Generated", generated],
    ]

    W = 174 * mm  # usable width at 18mm margins on A4 (210 - 36)
    meta_table = Table(meta_rows, colWidths=[35 * mm, W - 35 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MID_GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, BORDER),
    ]))

    return [brand_table, Spacer(1, 4 * mm), meta_table, Spacer(1, 4 * mm)]


def _build_talking_points(state, styles: dict) -> list:
    """MSL Talking Points — KOL-specific if available."""
    story = _section_heading("MSL Talking Points", styles)

    tp = getattr(state, "msl_talking_points", None)
    md = getattr(state, "messaging_data", None)

    if tp:
        # Conversation opener
        opener = _safe_str(getattr(tp, "conversation_opener", None))
        if opener and opener != "—":
            story.append(Paragraph("Conversation Opener", styles["subsection"]))
            story.append(Paragraph(opener, styles["body"]))

        # Three clinical pillars
        pillars = getattr(tp, "three_pillars", []) or []
        if pillars:
            story.append(Paragraph("Three Clinical Pillars", styles["subsection"]))
            for i, p in enumerate(pillars[:3], 1):
                title = _safe_str(getattr(p, "pillar_title", None))
                point = _safe_str(getattr(p, "msl_talking_point", None))
                ev = getattr(p, "evidence", None)
                data_pt = _safe_str(getattr(ev, "key_data_point", None)) if ev else "—"
                story.append(Paragraph(f"{i}. {title}", styles["label"]))
                if point and point != "—":
                    story.append(Paragraph(point, styles["bullet"]))
                if data_pt and data_pt != "—":
                    story.append(Paragraph(f"Evidence: {data_pt}", styles["caption"]))

        # Key differentiators
        diffs = getattr(tp, "key_differentiators", []) or []
        if diffs:
            story.append(Paragraph("Key Differentiators", styles["subsection"]))
            for d in diffs[:4]:
                adv = _safe_str(getattr(d, "advantage", None))
                msl_pt = _safe_str(getattr(d, "msl_talking_point", None))
                if adv != "—":
                    story.append(Paragraph(f"• {adv}", styles["green_bullet"]))
                if msl_pt != "—":
                    story.append(Paragraph(msl_pt, styles["caption"]))

    elif md:
        # Fallback: generic positioning
        pos = _safe_str(getattr(md, "positioning_statement", None))
        if pos != "—":
            story.append(Paragraph("Positioning Statement", styles["subsection"]))
            story.append(Paragraph(pos, styles["body"]))

        pillars = getattr(md, "messaging_pillars", []) or []
        if pillars:
            story.append(Paragraph("Messaging Pillars", styles["subsection"]))
            story.extend(_bullet_items(pillars, styles, "green_bullet"))

        diffs = getattr(md, "key_differentiators", []) or []
        if diffs:
            story.append(Paragraph("Key Differentiators", styles["subsection"]))
            story.extend(_bullet_items(diffs, styles, "bullet"))
    else:
        story.append(Paragraph("Talking points not yet generated.", styles["caption"]))

    return story


def _build_discovery_questions(state, styles: dict) -> list:
    """Tiered discovery questions."""
    drug = _safe_str(getattr(state, "drug_name", None), "this drug")
    indication = _safe_str(getattr(state, "indication", None), "target indication")

    story = _section_heading("Discovery Questions", styles)
    story.append(Paragraph(
        "Use these questions to understand the physician's practice and patient population fit.",
        styles["caption"]
    ))

    tiers = [
        ("Tier 1 — Must Ask  (every call)", [
            f"How many of your {indication} patients have PD-L1 negative tumours or have developed resistance to standard IO?",
            "What is your current approach for patients who have failed checkpoint inhibitors?",
            f"Are you currently enrolling patients in any {indication} clinical trials?",
        ]),
        ("Tier 2 — Context-Dependent", [
            f"What data would you need to see before considering {drug} for your patients?",
            "How do you currently sequence therapies after first-line progression?",
            "What does your multidisciplinary team discussion look like for complex cases?",
        ]),
        ("Tier 3 — Nice to Have", [
            "Are your patients asking about newer agents or trial options?",
            "What are the main barriers to trying a new therapy in this setting?",
            "How do you handle reimbursement conversations with patients about newer agents?",
        ]),
    ]

    for tier_label, questions in tiers:
        story.append(Paragraph(tier_label, styles["subsection"]))
        story.extend(_bullet_items(questions, styles, "bullet"))

    return story


def _build_objections(state, styles: dict) -> list:
    """Anticipated objections & MSL responses."""
    story = _section_heading("Objections & Responses", styles)

    tp = getattr(state, "msl_talking_points", None)
    md = getattr(state, "messaging_data", None)

    objections = []

    if tp and getattr(tp, "anticipated_objections", None):
        for obj in tp.anticipated_objections[:5]:
            objections.append({
                "q": _safe_str(getattr(obj, "objection", None)),
                "why": _safe_str(getattr(obj, "why_they_ask", None)),
                "r": _safe_str(getattr(obj, "msl_response", None)),
                "ev": _safe_str(getattr(obj, "evidence_response", None)),
            })
    elif md and getattr(md, "common_objections", None):
        for q, r in (getattr(md, "common_objections", {}) or {}).items():
            objections.append({"q": str(q), "why": "", "r": str(r), "ev": ""})

    if not objections:
        story.append(Paragraph("No objection data available.", styles["caption"]))
        return story

    W = 174 * mm
    for obj in objections:
        q_para = Paragraph(f"Q: {obj['q']}", styles["label"])
        r_text = obj["r"] if obj["r"] != "—" else "See MSL training materials."
        r_para = Paragraph(f"Response: {r_text}", styles["body"])
        parts = [q_para, r_para]
        if obj["ev"] and obj["ev"] != "—":
            parts.append(Paragraph(f"Evidence: {obj['ev']}", styles["caption"]))

        row_table = Table([[parts]], colWidths=[W])
        row_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(KeepTogether([row_table, Spacer(1, 3 * mm)]))

    return story


def _build_clinical_evidence(state, styles: dict) -> list:
    """Clinical trial summary + key publications."""
    story = _section_heading("Clinical Evidence", styles)

    md = getattr(state, "market_data", None)
    if not md:
        story.append(Paragraph("No clinical data available.", styles["caption"]))
        return story

    # Market stats row
    tam = f"${md.tam_estimate:,.0f}M" if md.tam_estimate else "N/A"
    pop = f"{md.patient_population:,}" if md.patient_population else "N/A"
    trials_n = str(len(md.clinical_trials)) if md.clinical_trials else "0"

    stat_data = [
        ["Active Trials", "Target Market (TAM)", "Patient Population"],
        [trials_n, tam, pop],
    ]
    stat_table = Table(stat_data, colWidths=[58 * mm, 58 * mm, 58 * mm])
    stat_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), MID_GREY),
        ("TEXTCOLOR", (0, 1), (-1, 1), NAVY),
        ("FONTSIZE", (0, 1), (-1, 1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 4 * mm))

    # Top 5 trials
    trials = (md.clinical_trials or [])[:5]
    if trials:
        story.append(Paragraph("Active Clinical Trials", styles["subsection"]))
        trial_header = [["NCT ID", "Phase", "Status", "Enrolled"]]
        trial_rows = []
        for t in trials:
            trial_rows.append([
                _safe_str(t.get("nct_id")),
                _safe_str(t.get("phase")),
                _safe_str(t.get("status")),
                _safe_str(t.get("enrollment")),
            ])
        trial_data = trial_header + trial_rows
        t_widths = [40 * mm, 25 * mm, 70 * mm, 39 * mm]
        trial_table = Table(trial_data, colWidths=t_widths)
        trial_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(trial_table)
        story.append(Spacer(1, 3 * mm))

    # Key publications
    pubs = (md.key_publications or [])[:5]
    if pubs:
        story.append(Paragraph("Key Publications", styles["subsection"]))
        for pub in pubs:
            title = _safe_str(pub.get("title"))
            journal = _safe_str(pub.get("journal"), "")
            year = _safe_str(pub.get("year"), "")
            pmid = pub.get("pmid")
            line = title
            if journal or year:
                line += f"  ·  {journal}" if journal else ""
                line += f" ({year})" if year else ""
            if pmid:
                line += f"  ·  PMID {pmid}"
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    return story


def _build_competitive_position(state, styles: dict) -> list:
    """Competitive positioning — affirmative framing."""
    story = _section_heading("Competitive Position", styles)

    cd = getattr(state, "competitor_data", None)
    md = getattr(state, "messaging_data", None)
    drug = _safe_str(getattr(state, "drug_name", None), "this drug")

    # Affirmative bridge statements
    vs_statements = []
    if md and getattr(md, "competitive_vs_statements", None):
        vs_statements = list(md.competitive_vs_statements or [])

    if vs_statements:
        story.append(Paragraph("Affirmative Positioning Statements", styles["subsection"]))
        story.append(Paragraph(
            f"Use these when a colleague raises an established competitor. "
            f"Acknowledge their point, then pivot to {drug}'s unique value.",
            styles["caption"]
        ))
        story.extend(_bullet_items(vs_statements, styles, "green_bullet"))
        story.append(Spacer(1, 3 * mm))

    # Competitor summary table
    competitors = (getattr(cd, "competitors", []) or [])[:3] if cd else []
    if competitors:
        story.append(Paragraph("Competitor Overview", styles["subsection"]))
        header = [["Competitor", "Est. Share", "Key Differentiator"]]
        rows = []
        for c in competitors:
            share = f"{c.market_share:.1f}%" if c.market_share else "N/A"
            diff = (c.key_differentiators[:1] or ["—"])[0]
            rows.append([
                _safe_str(c.competitor_name),
                share,
                _safe_str(diff),
            ])
        t_widths = [55 * mm, 30 * mm, 89 * mm]
        comp_table = Table(header + rows, colWidths=t_widths)
        comp_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(comp_table)

    if not vs_statements and not competitors:
        story.append(Paragraph("No competitive data available.", styles["caption"]))

    return story


def _build_footer(styles: dict) -> list:
    generated = datetime.now().strftime("%d %b %Y %H:%M")
    return [
        Spacer(1, 6 * mm),
        HRFlowable(width="100%", thickness=0.5, color=BORDER),
        Paragraph(
            f"Generated by Evidentia MSL Intelligence Platform  ·  {generated}  ·  CONFIDENTIAL — FOR MSL USE ONLY",
            styles["footer"]
        ),
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_brief_pdf(
    state: Any,
    drug_name: str,
    hospital: str = "",
    physician: str = "",
) -> bytes:
    """
    Generate a PDF pre-call brief from a populated GTMState.

    Args:
        state:      GTMState instance with agent outputs populated.
        drug_name:  Drug name (displayed in header).
        hospital:   Physician's institution (optional).
        physician:  Physician name (optional).

    Returns:
        PDF file as bytes, ready for st.download_button().
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=LEFT_M,
        rightMargin=RIGHT_M,
        topMargin=TOP_M,
        bottomMargin=BOTTOM_M,
        title=f"Evidentia Brief — {drug_name}",
        author="Evidentia MSL Intelligence Platform",
    )

    styles = _build_styles()
    story: list = []

    story.extend(_build_header(state, drug_name, physician, hospital, styles))
    story.extend(_build_talking_points(state, styles))
    story.extend(_build_discovery_questions(state, styles))
    story.extend(_build_objections(state, styles))
    story.extend(_build_clinical_evidence(state, styles))
    story.extend(_build_competitive_position(state, styles))
    story.extend(_build_footer(styles))

    doc.build(story)
    return buf.getvalue()
