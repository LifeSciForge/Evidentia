"""
Generate Evidentia product document as PDF.
Run: python3 generate_pdf.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import ListFlowable, ListItem
from datetime import datetime

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0A2342")
BLUE       = colors.HexColor("#0055B8")
LIGHT_BLUE = colors.HexColor("#E8F0FB")
TEAL       = colors.HexColor("#00818A")
DARK_GRAY  = colors.HexColor("#2D2D2D")
MID_GRAY   = colors.HexColor("#555555")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
BORDER_GRAY= colors.HexColor("#CCCCCC")
WHITE      = colors.white
GREEN      = colors.HexColor("#1A7A4A")
AMBER      = colors.HexColor("#B05E00")
RED        = colors.HexColor("#C0392B")

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm


def build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=36,
        textColor=WHITE,
        spaceAfter=6,
        leading=42,
        alignment=TA_LEFT,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=15,
        textColor=colors.HexColor("#B8CCE8"),
        spaceAfter=4,
        leading=20,
        alignment=TA_LEFT,
    )
    styles["cover_tagline"] = ParagraphStyle(
        "cover_tagline",
        fontName="Helvetica-Oblique",
        fontSize=12,
        textColor=colors.HexColor("#D0E4FF"),
        spaceAfter=0,
        leading=16,
        alignment=TA_LEFT,
    )
    styles["section_heading"] = ParagraphStyle(
        "section_heading",
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=NAVY,
        spaceBefore=20,
        spaceAfter=8,
        leading=22,
        borderPad=4,
    )
    styles["sub_heading"] = ParagraphStyle(
        "sub_heading",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BLUE,
        spaceBefore=14,
        spaceAfter=5,
        leading=16,
    )
    styles["sub_sub_heading"] = ParagraphStyle(
        "sub_sub_heading",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=TEAL,
        spaceBefore=10,
        spaceAfter=4,
        leading=14,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=6,
        leading=15,
        alignment=TA_JUSTIFY,
    )
    styles["body_bold"] = ParagraphStyle(
        "body_bold",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=4,
        leading=15,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=4,
        leading=14,
        leftIndent=14,
        bulletIndent=4,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=12,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_GRAY,
        leading=13,
        alignment=TA_LEFT,
    )
    styles["table_cell_bold"] = ParagraphStyle(
        "table_cell_bold",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=DARK_GRAY,
        leading=13,
    )
    styles["callout"] = ParagraphStyle(
        "callout",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=NAVY,
        spaceAfter=4,
        leading=15,
        alignment=TA_CENTER,
    )
    styles["callout_sub"] = ParagraphStyle(
        "callout_sub",
        fontName="Helvetica",
        fontSize=9,
        textColor=MID_GRAY,
        spaceAfter=2,
        leading=12,
        alignment=TA_CENTER,
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        fontName="Helvetica",
        fontSize=8,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
    )
    styles["pitch"] = ParagraphStyle(
        "pitch",
        fontName="Helvetica-Oblique",
        fontSize=11,
        textColor=NAVY,
        spaceAfter=6,
        leading=17,
        alignment=TA_JUSTIFY,
        leftIndent=10,
        rightIndent=10,
    )
    return styles


# ── Helper flowables ──────────────────────────────────────────────────────────

def divider(color=BLUE, thickness=1.5, space_before=4, space_after=10):
    return [
        Spacer(1, space_before),
        HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=space_after),
    ]


def section_title(text, styles):
    parts = [Spacer(1, 4)]
    parts += divider(NAVY, thickness=2.5, space_before=2, space_after=6)
    parts.append(Paragraph(text, styles["section_heading"]))
    parts += divider(BLUE, thickness=0.8, space_before=0, space_after=8)
    return parts


def callout_box(stats, styles, bg=LIGHT_BLUE, border=BLUE):
    """Render a row of stat boxes."""
    col_w = (PAGE_W - 2 * MARGIN) / len(stats)
    data = [[
        [Paragraph(s["value"], styles["callout"]),
         Paragraph(s["label"], styles["callout_sub"]),
         Paragraph(s.get("source", ""), styles["callout_sub"])]
        for s in stats
    ]]
    # Flatten each cell into a single column of paragraphs
    table_data = [[
        [Paragraph(s["value"], styles["callout"]),
         Paragraph(s["label"], styles["callout_sub"]),
         Paragraph(s.get("source", ""), styles["callout_sub"])]
        for s in stats
    ]]
    col_widths = [col_w] * len(stats)

    # Build using nested Paragraph lists in cells
    row = []
    for s in stats:
        cell = [
            Paragraph(s["value"], styles["callout"]),
            Paragraph(s["label"], styles["callout_sub"]),
        ]
        if s.get("source"):
            cell.append(Paragraph(s["source"], styles["callout_sub"]))
        row.append(cell)

    t = Table([row], colWidths=col_widths, rowHeights=None)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX",        (0, 0), (-1, -1), 1.2, border),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, border),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def comparison_table(headers, rows, styles, col_widths=None):
    usable_w = PAGE_W - 2 * MARGIN
    if col_widths is None:
        col_widths = [usable_w / len(headers)] * len(headers)

    header_row = [Paragraph(h, styles["table_header"]) for h in headers]
    table_rows = [header_row]
    for i, row in enumerate(rows):
        tr = []
        for j, cell in enumerate(row):
            s = styles["table_cell_bold"] if j == 0 else styles["table_cell"]
            tr.append(Paragraph(str(cell), s))
        table_rows.append(tr)

    t = Table(table_rows, colWidths=col_widths, repeatRows=1)
    row_colors = []
    for i in range(1, len(table_rows)):
        bg = LIGHT_GRAY if i % 2 == 0 else WHITE
        row_colors.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.8, BORDER_GRAY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ] + row_colors))
    return t


def highlight_box(text, styles, bg=LIGHT_BLUE, border=BLUE):
    t = Table([[Paragraph(text, styles["body"])]], colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.2, border),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return t


def bullet_list(items, styles):
    return [Paragraph(f"• &nbsp; {item}", styles["bullet"]) for item in items]


# ── Cover page ────────────────────────────────────────────────────────────────

def cover_page(styles):
    story = []

    # Full-width navy banner via a wide table
    banner_text = [
        Spacer(1, 2.5 * cm),
        Paragraph("EVIDENTIA", styles["cover_title"]),
        Paragraph("AI-Native Closed-Loop MSL Intelligence Platform", styles["cover_sub"]),
        Spacer(1, 0.4 * cm),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4A90D9"), spaceAfter=10),
        Paragraph(
            "Transforming Medical Science Liaisons from reactive briefers into<br/>"
            "strategic intelligence engines — before, during, and after every KOL interaction.",
            styles["cover_tagline"]
        ),
        Spacer(1, 2.0 * cm),
    ]

    banner = Table(
        [[banner_text]],
        colWidths=[PAGE_W - 2 * MARGIN]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("LEFTPADDING",   (0, 0), (-1, -1), 28),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 28),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.8 * cm))

    # Key stats row
    stat_box = callout_box([
        {"value": "90 sec", "label": "Pre-Call Brief", "source": "vs 45+ min manual"},
        {"value": "1.5×",   "label": "Treatment Adoption", "source": "Veeva Pulse 2023"},
        {"value": "$2.88M", "label": "Annual Savings", "source": "Per 150-MSL team"},
        {"value": "4×",     "label": "KOL Impact", "source": "vs sales reps"},
    ], styles)
    story.append(stat_box)
    story.append(Spacer(1, 0.8 * cm))

    # Meta row
    meta_style = ParagraphStyle("meta", fontName="Helvetica", fontSize=9,
                                textColor=MID_GRAY, alignment=TA_LEFT)
    meta = Table([[
        Paragraph("Evidentia v2.0 — Enterprise Platform", meta_style),
        Paragraph(f"March 2026  |  Confidential", meta_style),
    ]], colWidths=[(PAGE_W - 2 * MARGIN) / 2] * 2)
    meta.setStyle(TableStyle([
        ("ALIGN",  (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta)
    story.append(PageBreak())
    return story


# ── Section 1: What is Evidentia ─────────────────────────────────────────────

def section_what(styles):
    story = []
    story += section_title("1.  What is Evidentia?", styles)

    story.append(Paragraph(
        "Evidentia is an AI-native, closed-loop intelligence platform purpose-built for Medical "
        "Science Liaisons (MSLs) at pharmaceutical and biotech companies. It replaces 45+ minutes "
        "of fragmented manual research with a 90-second, evidence-grounded pre-call brief — and "
        "then closes the loop by capturing structured insights after every KOL interaction, scoring "
        "engagement quality, and synthesising territory-wide intelligence for medical affairs strategy.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Who are MSLs?", styles["sub_heading"]))
    story.append(Paragraph(
        "Medical Science Liaisons are field-based scientific experts (PhD / PharmD / MD) who serve "
        "as the non-promotional bridge between pharmaceutical companies and the medical community. "
        "They engage Key Opinion Leaders (KOLs) — leading physicians, clinical researchers, and "
        "payer decision-makers — through bilateral scientific exchange: discussing clinical trial "
        "data, mechanisms of action, real-world evidence, and unmet medical needs. Unlike sales "
        "representatives, MSLs do not promote products; they educate and gather field intelligence.",
        styles["body"]
    ))

    story.append(Paragraph("The Four Workflows", styles["sub_heading"]))

    workflows = [
        ("1", "Pre-Call Brief Generation",
         "Select a KOL and a drug. Evidentia queries ClinicalTrials.gov, PubMed, the FDA OpenFDA "
         "database, and real-time web sources, then uses a 7-agent LangGraph pipeline to synthesise "
         "a 10-tab intelligence package in under 90 seconds. The brief is KOL-specific — it knows "
         "Dr Smith's research focus, publication history, trial PI roles, and influence tier before "
         "the MSL walks into the room."),
        ("2", "Post-Call Insight Capture",
         "After the meeting, the MSL enters freeform field notes. An AI extraction agent classifies "
         "and structures 1–10 insights per call across 10 clinical categories: unmet medical need, "
         "competitive intelligence, data gap, safety signal, prescribing barrier, payer barrier, "
         "clinical question, publication request, trial interest, and KOL sentiment. Safety signals "
         "auto-trigger a compliant escalation email to Medical Affairs."),
        ("3", "Engagement Quality Tracking",
         "Every interaction receives a scientific engagement quality score from 0 to 10, assessed "
         "across four dimensions: scientific depth, KOL engagement, actionability, and relationship "
         "advancement. Coverage dashboards surface Tier 1 KOLs who have not been contacted within "
         "45 days — the 30% coverage gap Veeva Pulse identifies as the industry's largest strategic blind spot."),
        ("4", "Territory Intelligence Synthesis",
         "On demand, Evidentia aggregates 90 days of post-call insights across all MSLs in a "
         "territory. An LLM synthesis agent clusters emerging unmet needs, competitive signals, "
         "content gaps, and safety patterns into a structured medical affairs strategy report — "
         "delivered in under 60 seconds, not next quarter's advisory board."),
    ]

    for num, title, desc in workflows:
        box_content = [
            [
                Paragraph(num, ParagraphStyle("wf_num", fontName="Helvetica-Bold",
                                              fontSize=20, textColor=WHITE, alignment=TA_CENTER)),
                [Paragraph(title, styles["sub_sub_heading"]),
                 Paragraph(desc, styles["body"])]
            ]
        ]
        t = Table(box_content, colWidths=[1.1 * cm, PAGE_W - 2 * MARGIN - 1.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), BLUE),
            ("BACKGROUND",    (1, 0), (1, 0), LIGHT_BLUE),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (0, 0), 4),
            ("RIGHTPADDING",  (0, 0), (0, 0), 4),
            ("LEFTPADDING",   (1, 0), (1, 0), 12),
            ("RIGHTPADDING",  (1, 0), (1, 0), 12),
            ("BOX",           (0, 0), (-1, -1), 0.8, BORDER_GRAY),
        ]))
        story.append(KeepTogether([t, Spacer(1, 8)]))

    story.append(Paragraph("Technical Foundation", styles["sub_heading"]))
    story.append(Paragraph(
        "Evidentia is built on LangGraph 1.1.3 (multi-agent orchestration), Claude Sonnet 4 "
        "(Anthropic), Streamlit (web UI), SQLite + ChromaDB (persistent memory), and a hybrid "
        "BM25 + vector retrieval pipeline for grounded clinical evidence. All competitor and "
        "market data is labelled with its data source — FDA-verified, PubMed-cited, web-sourced, "
        "or AI-estimated — so MSLs always know what they can rely on in front of a KOL.",
        styles["body"]
    ))

    story.append(PageBreak())
    return story


# ── Section 2: Problem it solves ─────────────────────────────────────────────

def section_problem(styles):
    story = []
    story += section_title("2.  The Problem Evidentia Solves", styles)

    story.append(Paragraph(
        "The MSL function is one of the highest-ROI investments in pharmaceutical commercial "
        "strategy — when it works. MSL pre-launch scientific engagement with KOLs produces 1.5× "
        "treatment adoption in the first six months post-launch. KOLs who spend more time with "
        "MSLs are 2–4× more likely to change treatment patterns and influence their peer networks. "
        "Yet the tools available to MSLs were built for sales representatives — not for scientific "
        "intelligence work.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    # Problem data table
    prob_headers = ["Problem", "Evidence", "Source"]
    prob_rows = [
        ["Pre-call prep takes 45+ minutes per meeting",
         "MSLs manually assemble KOL profiles from disconnected PubMed, CRM, and web sources",
         "H1 / Industry practitioners"],
        ["Post-call insights are never captured",
         "Only 4 of ~500 MSL Society conference attendees had a documented post-call process",
         "MSL Society Conference"],
        ["30% of KOLs have zero MSL contact",
         "Massive strategic coverage gaps go unnoticed by field managers",
         "Veeva Pulse 2023"],
        ["Measurement systems don't measure impact",
         "Only 3% of organisations rate MSL KPI systems 'very effective'; 67% say 'difficult'",
         "Global Survey, 1,023 MA professionals"],
        ["80% of approved content is never used",
         "Content teams produce materials that MSLs never deploy in field meetings",
         "Veeva Pulse 2025"],
        ["Insights never reach medical strategy",
         "95% of MSLs face pressure to gather actionable insights but lack structured tools",
         "THE MSL Journal"],
        ["CRM built for sales, not science",
         "Veeva CRM counts calls. It cannot measure scientific depth, coverage quality, or emerging KOL sentiment",
         "Industry consensus"],
    ]
    col_w = PAGE_W - 2 * MARGIN
    story.append(comparison_table(
        prob_headers, prob_rows, styles,
        col_widths=[col_w * 0.30, col_w * 0.45, col_w * 0.25]
    ))
    story.append(Spacer(1, 12))

    story.append(highlight_box(
        "<b>The compounding cost:</b> A 150-MSL organisation spends $30M–$45M per year on the "
        "function. If 45 minutes of prep time per call is wasted, if 30% of Tier 1 KOLs are never "
        "engaged, and if every post-call insight disappears into a CRM text box — the strategic "
        "return on that $30M investment is a fraction of what it could be.",
        styles, bg=colors.HexColor("#FFF3CD"), border=colors.HexColor("#D4A017")
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Why existing tools don't solve it", styles["sub_heading"]))
    comp_headers = ["Tool", "What It Does", "What It Misses"]
    comp_rows = [
        ["Veeva CRM",    "Tracks MSL activity counts (calls, emails)",        "Scientific quality, KOL coverage gaps, insight capture"],
        ["H1 / HCP Universe", "Daily-updated HCP publication + trial data",   "No workflow integration; brief generation; post-call capture"],
        ["Sorcero",      "Language intelligence for medical affairs text",     "Enterprise-only ($500K+); no pre-call brief; no quality scoring"],
        ["TikaMobile",   "MSL-first mobile CRM",                              "Activity management, not intelligence platform"],
        ["IQVIA OCE",    "CRM + commercial analytics",                        "Built for commercial; limited medical affairs intelligence"],
        ["<b>Evidentia</b>", "<b>Closed-loop: brief → capture → score → synthesise</b>", "<b>Nothing — this is the gap it fills</b>"],
    ]
    col_w = PAGE_W - 2 * MARGIN
    story.append(comparison_table(
        comp_headers, comp_rows, styles,
        col_widths=[col_w * 0.20, col_w * 0.42, col_w * 0.38]
    ))

    story.append(PageBreak())
    return story


# ── Section 3: ROI ────────────────────────────────────────────────────────────

def section_roi(styles):
    story = []
    story += section_title("3.  ROI for Pharma and Biotech", styles)

    story.append(Paragraph(
        "Evidentia's return on investment operates across three value layers: direct labour cost "
        "savings, revenue impact from improved KOL engagement quality, and risk reduction from "
        "better compliance and audit readiness. Each layer is independently quantifiable.",
        styles["body"]
    ))

    # ── Layer 1 ──
    story.append(Paragraph("Layer 1 — Direct Labour Cost Savings", styles["sub_heading"]))
    story.append(Paragraph(
        "Pre-call brief preparation is the most immediately measurable cost. Industry data from "
        "H1 and MSL practitioners confirms the current baseline at 45 minutes per KOL meeting. "
        "Evidentia reduces this to under 10 minutes of brief review, saving 35+ minutes per call.",
        styles["body"]
    ))

    calc_data = [
        ["Variable", "Value", "Notes"],
        ["MSL headcount",                "150",        "Typical mid-size pharma MSL team"],
        ["KOL interactions / MSL / week", "4",         "Industry benchmark; ~20/month"],
        ["Pre-call prep time saved",      "35 min",    "45 min manual → <10 min review"],
        ["Hours saved per week",          "350 hrs",   "150 × 4 × 35 min"],
        ["Hours saved per month",         "1,400 hrs", "350 × 4 weeks"],
        ["Loaded labour cost per hour",   "$150",      "MSL salary + benefits + overhead"],
        ["<b>Monthly savings</b>",        "<b>$210,000</b>", ""],
        ["<b>Annual savings</b>",         "<b>$2.52M</b>",   "Prep time alone"],
    ]
    col_w = PAGE_W - 2 * MARGIN
    t = Table(calc_data, colWidths=[col_w * 0.42, col_w * 0.25, col_w * 0.33])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#D4EDDA")),
        ("BACKGROUND",    (0, -2), (-1, -2), colors.HexColor("#D4EDDA")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -3), [WHITE, LIGHT_GRAY]),
        ("BOX",           (0, 0), (-1, -1), 0.8, BORDER_GRAY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Add CRM logging efficiency (AI-assisted note capture reduces logging time by ~8 minutes "
        "per call) and the total direct labour saving rises to approximately <b>$2.88M per year</b> "
        "for a 150-MSL team — before counting any revenue impact.",
        styles["body"]
    ))

    # ── Layer 2 ──
    story.append(Paragraph("Layer 2 — Revenue Impact from MSL Engagement Quality", styles["sub_heading"]))
    story.append(Paragraph(
        "This is the larger — and more strategically important — value layer. Veeva Pulse analysis "
        "of real-world CRM data from 80%+ of global biopharma field teams establishes a direct "
        "causal link between MSL scientific engagement quality and drug adoption outcomes.",
        styles["body"]
    ))

    rev_stats = [
        {"value": "1.5×", "label": "Treatment adoption\nin first 6 months", "source": "Veeva Pulse 2023"},
        {"value": "40%",  "label": "Faster adoption\nwith pre-launch investment", "source": "Veeva Pulse Q2 2024"},
        {"value": "2×+",  "label": "Adoption from\ncontent-driven engagement", "source": "Veeva Pulse 2025"},
        {"value": "4×",   "label": "Early-career HCP\nadoption post-engagement", "source": "Veeva Pulse 2024"},
    ]
    story.append(callout_box(rev_stats, styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Translating engagement improvement into revenue requires conservative assumptions. "
        "Consider a drug with $200M peak annual sales:",
        styles["body"]
    ))

    rev_data = [
        ["Scenario", "Assumption", "Revenue Impact"],
        ["Close the 30% Tier 1 KOL coverage gap",
         "30% of highest-influence KOLs currently receive zero MSL contact. "
         "Engaging them raises adoption by a conservative 0.3× uplift on top of baseline.",
         "$60M additional\nannual revenue"],
        ["Improve interaction quality score by 2 pts (e.g. 5→7/10)",
         "Higher-quality scientific exchange correlates with stronger KOL advocacy and faster adoption. "
         "A 2-point quality lift → ~10% adoption improvement.",
         "$20M additional\nannual revenue"],
        ["Content-driven engagement in 50% more meetings",
         "Currently <50% of meetings use approved content. Closing to 75% usage, given the 2× adoption "
         "data, adds a meaningful incremental lift.",
         "$15–30M additional\nannual revenue"],
    ]
    col_w = PAGE_W - 2 * MARGIN
    story.append(comparison_table(
        rev_data[0], rev_data[1:], styles,
        col_widths=[col_w * 0.27, col_w * 0.47, col_w * 0.26]
    ))
    story.append(Spacer(1, 8))

    story.append(highlight_box(
        "<b>Conservative total revenue impact:</b> On a single $200M peak-sales drug, "
        "improving MSL coverage and engagement quality through Evidentia could unlock "
        "<b>$75M–$110M in additional cumulative revenue</b> over the product's key growth years. "
        "The annual Evidentia licence fee for a 150-MSL team ($1.35M at $750/MSL/month) "
        "represents a <b>55–80× return</b> on investment.",
        styles, bg=colors.HexColor("#D4EDDA"), border=GREEN
    ))
    story.append(Spacer(1, 10))

    # ── Layer 3 ──
    story.append(Paragraph("Layer 3 — Risk Reduction and Compliance Value", styles["sub_heading"]))
    for item in [
        "<b>Audit trail compliance:</b> All AI-generated outputs are logged with user ID, timestamp, and data source. Pharma companies face increasing regulatory scrutiny on AI-assisted HCP engagement activities. Evidentia's provenance logging reduces audit risk.",
        "<b>Safety signal escalation:</b> Adverse event observations from field interactions are automatically flagged and escalation emails are drafted, reducing pharmacovigilance response lag.",
        "<b>Data confidence transparency:</b> Every data point displayed to an MSL carries its source label (FDA-verified / PubMed-cited / web-sourced / AI-estimated). MSLs never present unverified numbers to KOLs as facts.",
        "<b>Insight capture standardisation:</b> Structured post-call intelligence reduces reliance on individual MSL memory and creates an institutional knowledge base that survives team turnover.",
    ]:
        story.append(Paragraph("• &nbsp;" + item, styles["bullet"]))
        story.append(Spacer(1, 3))

    # ── ROI Summary ──
    story.append(Paragraph("ROI Summary", styles["sub_heading"]))
    roi_box = callout_box([
        {"value": "$2.88M", "label": "Direct labour\nsavings / year", "source": "150-MSL team"},
        {"value": "$75M+",  "label": "Revenue uplift\npotential", "source": "Single $200M drug"},
        {"value": "55–80×", "label": "Return on\nEvidentia licence", "source": "Conservative estimate"},
        {"value": "<1 mo",  "label": "Payback\nperiod", "source": "Labour savings alone"},
    ], styles, bg=colors.HexColor("#D4EDDA"), border=GREEN)
    story.append(roi_box)

    story.append(PageBreak())
    return story


# ── Section 4: Future use cases ──────────────────────────────────────────────

def section_usecases(styles):
    story = []
    story += section_title("4.  Future Use Cases and Extensions", styles)

    story.append(Paragraph(
        "Evidentia's core architecture — a LangGraph multi-agent pipeline, persistent SQLite + "
        "ChromaDB memory, structured field intelligence capture, and Claude Sonnet synthesis — "
        "is a platform, not a point solution. The following use cases are natural extensions that "
        "build directly on the existing codebase without requiring architectural changes.",
        styles["body"]
    ))

    use_cases = [
        {
            "num": "01",
            "title": "Market Access MSL Intelligence",
            "timeline": "Buildable in 4–6 weeks",
            "desc": (
                "A rapidly growing sub-speciality: dedicated Market Access MSLs who engage payer "
                "decision-makers (formulary committees, HTA reviewers, managed care medical directors) "
                "rather than clinical KOLs. The same pre-call brief and insight capture workflows apply, "
                "with the payer intelligence agent promoted to primary status and extended with: NICE / "
                "EMA / ICER decision database integration, QALY modelling context, formulary tier history "
                "per insurer, and prior authorisation criteria by drug class. Current extension point: "
                "the existing PayerIntelligenceAgent in the pipeline."
            ),
            "impact": "Direct contribution to formulary placement — one positive P&T committee outcome can be worth $50M+ in annual revenue.",
        },
        {
            "num": "02",
            "title": "Congress Intelligence Platform",
            "timeline": "Buildable in 3–4 weeks",
            "desc": (
                "Major congresses (ASCO, ESMO, ASH, AHA, NEJM Oncology) generate hundreds of abstracts "
                "in 48 hours. MSL teams currently read manually or miss competitive data entirely. "
                "Evidentia's RAG pipeline ingests congress abstract feeds (via Tavily or direct API), "
                "classifies them by therapeutic area and relevance, and generates: competitive threat "
                "alerts ('Competitor X just presented Phase 3 data that changes the NSCLC conversation'), "
                "KOL presentation trackers ('Dr Smith presented a poster — here's what she said'), "
                "and rapid-response talking point updates for the field team within hours of data release."
            ),
            "impact": "MSL teams that proactively engage with congress data achieve 40% faster treatment adoption (Veeva Pulse 2024).",
        },
        {
            "num": "03",
            "title": "Investigator-Initiated Trial (IIT) Pipeline",
            "timeline": "Buildable in 6–8 weeks",
            "desc": (
                "IITs — studies sponsored and run by KOLs using company drugs — are a critical channel "
                "for generating real-world evidence and deepening KOL relationships. The workflow is: "
                "identify KOLs with research interests aligned to data gaps (from field insights), "
                "generate an IIT concept proposal tailored to the KOL's methodology and patient population, "
                "track proposal status through scientific review, and update the KOL engagement plan "
                "based on IIT milestones. Evidentia has all the data it needs (KOL profiles, field insights, "
                "competitor data gaps) to automate the identification and concept generation steps."
            ),
            "impact": "IITs generate peer-reviewed RWE that supports label expansions, payer submissions, and guideline inclusion.",
        },
        {
            "num": "04",
            "title": "Medical Education Content Generation",
            "timeline": "Buildable in 4–5 weeks",
            "desc": (
                "80% of approved scientific content is never used in field meetings (Veeva Pulse 2025). "
                "The field intelligence dashboard (SKILL_04) already identifies content gaps — what KOLs "
                "are asking for that the approved content library doesn't contain. The extension: "
                "automatically generate first-draft scientific slide decks, publication reprints, "
                "plain-language summaries, and annotated bibliography documents based on the detected "
                "content gaps, using Claude to synthesise from the RAG clinical evidence pipeline. "
                "All outputs go through standard medical, legal, regulatory (MLR) review before use."
            ),
            "impact": "Content-driven engagement doubles treatment adoption. Closing the 80% content usage gap is a direct revenue driver.",
        },
        {
            "num": "05",
            "title": "Competitive Intelligence Early Warning System",
            "timeline": "Buildable in 3–4 weeks",
            "desc": (
                "Running field_synthesis_agent on a daily schedule (rather than on-demand) against "
                "competitive intelligence insights creates a near-real-time early warning system. "
                "When MSLs start reporting a new competitor name, a new clinical result being discussed, "
                "or a shift in KOL prescribing sentiment, the system detects the pattern before it "
                "surfaces in formal competitive intelligence reports. Integrated with Slack or email: "
                "'3 MSLs in the NE territory mentioned Competitor X's new dosing data this week — "
                "here is what they said and recommended response messaging.'"
            ),
            "impact": "Weeks-earlier detection of competitive threats enables faster MSL response, counter-data preparation, and label update acceleration.",
        },
        {
            "num": "06",
            "title": "Digital Opinion Leader (DOL) Engagement",
            "timeline": "Buildable in 5–6 weeks",
            "desc": (
                "Veeva Pulse identifies early-career HCPs who are digitally active as 4× more likely "
                "to adopt new treatments post-MSL engagement. Evidentia can be extended to identify and "
                "profile Digital Opinion Leaders — physicians with significant social media / online "
                "publishing presence (Twitter/X, ResearchGate, LinkedIn) who influence their peers "
                "digitally rather than through traditional congress presentations. The KOL profiling "
                "agent (SKILL_01) already queries Tavily for social media activity; formalising this "
                "into a DOL tier and engagement plan is a natural extension."
            ),
            "impact": "Early-career HCPs drive disproportionate long-term adoption. DOL programmes are emerging as a top medical affairs priority for 2026.",
        },
        {
            "num": "07",
            "title": "Clinical Trial Site Identification and Activation",
            "timeline": "Buildable in 8–10 weeks",
            "desc": (
                "For drugs in late Phase 2 / Phase 3, MSLs play a critical role in identifying "
                "investigator sites and facilitating site activation. Evidentia already queries "
                "ClinicalTrials.gov for KOL PI roles. The extension: a site identification workflow "
                "that scores potential sites by: prior trial experience, patient volume (from "
                "ClinicalTrials enrollment data), KOL tier, geographic coverage, and protocol fit. "
                "Generates a ranked shortlist with engagement plans for each site PI, dramatically "
                "reducing the time from protocol finalisation to first patient enrolled."
            ),
            "impact": "Each day of trial acceleration is worth $1M+ for drugs with peak sales >$1B. Site identification and activation is consistently cited as the #1 cause of trial delay.",
        },
        {
            "num": "08",
            "title": "MSL Onboarding and Training Accelerator",
            "timeline": "Buildable in 3–4 weeks",
            "desc": (
                "New MSLs typically take 6–12 months to reach full productivity. They must learn the "
                "therapeutic area science, the competitive landscape, the key KOLs, and the company's "
                "data in parallel while starting field engagement. Evidentia's brief generation and "
                "territory intelligence features can be repackaged as a structured onboarding curriculum: "
                "automatically generate therapeutic area primers, KOL landscape maps, and competitive "
                "positioning guides from the same data sources used for field briefs. New MSLs reach "
                "field-ready proficiency in weeks rather than months."
            ),
            "impact": "Reducing MSL ramp time from 9 months to 3 months on a $200K+ loaded hire is worth $100K+ per new MSL in productivity recovery.",
        },
    ]

    for uc in use_cases:
        num_para = Paragraph(uc["num"], ParagraphStyle(
            "uc_num", fontName="Helvetica-Bold", fontSize=14,
            textColor=WHITE, alignment=TA_CENTER))
        title_para = Paragraph(uc["title"], styles["sub_sub_heading"])
        timeline_para = Paragraph(
            f"⏱  {uc['timeline']}",
            ParagraphStyle("timeline", fontName="Helvetica-Oblique", fontSize=9,
                           textColor=TEAL, spaceAfter=4)
        )
        desc_para = Paragraph(uc["desc"], styles["body"])
        impact_para = Paragraph(
            f"<b>Revenue / Impact:</b> {uc['impact']}",
            ParagraphStyle("impact", fontName="Helvetica", fontSize=9,
                           textColor=DARK_GRAY, leading=13,
                           backColor=colors.HexColor("#F0F8F0"),
                           leftIndent=6, rightIndent=6)
        )

        inner = Table(
            [[title_para], [timeline_para], [desc_para], [impact_para]],
            colWidths=[PAGE_W - 2 * MARGIN - 1.6 * cm]
        )
        inner.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))

        row = Table(
            [[[num_para], inner]],
            colWidths=[1.2 * cm, PAGE_W - 2 * MARGIN - 1.6 * cm]
        )
        row.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), NAVY),
            ("BACKGROUND",    (1, 0), (1, 0), WHITE),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (0, 0), 14),
            ("LEFTPADDING",   (0, 0), (0, 0), 2),
            ("RIGHTPADDING",  (0, 0), (0, 0), 2),
            ("BOX",           (0, 0), (-1, -1), 0.8, BORDER_GRAY),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ]))
        story.append(KeepTogether([row, Spacer(1, 10)]))

    story.append(PageBreak())
    return story


# ── Section 5: Closing ────────────────────────────────────────────────────────

def section_closing(styles):
    story = []
    story += section_title("5.  Summary and Next Steps", styles)

    story.append(Paragraph(
        "Evidentia occupies a gap in the medical affairs technology market that no existing vendor "
        "has filled: a closed-loop, AI-native intelligence platform that works before, during, and "
        "after every MSL-KOL interaction — at mid-market pricing accessible to any pharma or biotech "
        "company with 50+ MSLs.",
        styles["body"]
    ))
    story.append(Spacer(1, 8))

    summary_data = [
        ["Dimension", "Evidentia v2.0"],
        ["Core value",         "90-second KOL-specific briefs + post-call insight capture + territory intelligence"],
        ["Target buyer",       "VP Medical Affairs / CMO at pharma/biotech with 50–500 MSLs"],
        ["Key differentiator", "Only platform that closes the full loop: brief → capture → score → synthesise"],
        ["Direct ROI",         "$2.88M/year labour savings for 150-MSL team"],
        ["Revenue impact",     "$75M+ uplift potential on a single $200M peak-sales drug"],
        ["Pilot structure",    "90-day, 10-MSL pilot at $15,000 flat; conversion to $500–800/MSL/month"],
        ["Technology",         "LangGraph + Claude Sonnet 4 + SQLite + ChromaDB; live on Railway.app"],
        ["Status",             "v1.0 live; v2.0 built over 8 weeks per published architecture plan"],
        ["Future platform",    "8 use case extensions identified; all buildable on existing architecture"],
    ]
    col_w = PAGE_W - 2 * MARGIN
    t = Table(summary_data, colWidths=[col_w * 0.28, col_w * 0.72])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0, 1), (0, -1), BLUE),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("BOX",           (0, 0), (-1, -1), 0.8, BORDER_GRAY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Pitch box
    story.append(highlight_box(
        "<b>One-paragraph pitch:</b><br/><br/>"
        "Evidentia is the AI platform Medical Affairs teams need but pharma's CRM vendors were "
        "never built to deliver. While Veeva counts calls and H1 indexes publications, Evidentia "
        "closes the loop: it generates a KOL-specific, FDA-grounded pre-call brief in 90 seconds, "
        "extracts structured insights from field notes in 2 minutes, scores interaction quality "
        "automatically, and synthesises territory-wide intelligence that tells your Head of Medical "
        "Affairs what KOLs across your NSCLC territory are really saying about unmet needs — right "
        "now, not in next quarter's advisory board. For a 150-MSL team, that is $2.88M per year "
        "recovered in prep time alone, before counting the revenue impact of higher-quality "
        "scientific engagement on treatment adoption.",
        styles, bg=LIGHT_BLUE, border=BLUE
    ))
    story.append(Spacer(1, 14))

    # Footer note
    story.append(Paragraph(
        f"Document prepared: {datetime.now().strftime('%B %Y')}  |  Evidentia v2.0  |  Confidential",
        styles["footer"]
    ))
    return story


# ── Page number footer ────────────────────────────────────────────────────────

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(MARGIN, 1.2 * cm, "Evidentia — AI-Native MSL Intelligence Platform")
    canvas.drawRightString(PAGE_W - MARGIN, 1.2 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.55 * cm, PAGE_W - MARGIN, 1.55 * cm)
    canvas.restoreState()


# ── Main ──────────────────────────────────────────────────────────────────────

def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.8 * cm,
        bottomMargin=2.0 * cm,
        title="Evidentia — AI-Native MSL Intelligence Platform",
        author="Evidentia Team",
        subject="Product Brief and ROI Analysis",
    )

    styles = build_styles()

    story = []
    story += cover_page(styles)
    story += section_what(styles)
    story += section_problem(styles)
    story += section_roi(styles)
    story += section_usecases(styles)
    story += section_closing(styles)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    build_pdf("Evidentia_Platform_Document.pdf")
