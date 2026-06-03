"""
report_generator.py — Generate a branded PDF call analysis report.
Usage:
    from report_generator import generate_pdf
    pdf_bytes = generate_pdf(analysis, contact, events)
"""

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageTemplate,
    Paragraph, Spacer, Table, TableStyle
)

# ---------------------------------------------------------------------------
# Brand tokens
# ---------------------------------------------------------------------------
INK        = colors.HexColor("#0d1b2a")
INK_2      = colors.HexColor("#132236")
SURFACE    = colors.HexColor("#172840")
BRASS      = colors.HexColor("#b6862c")
BRASS_SOFT = colors.HexColor("#cba14a")
IVORY      = colors.HexColor("#f0ece4")
MUTED      = colors.HexColor("#8a9eb5")
GREEN      = colors.HexColor("#3faa78")
AMBER      = colors.HexColor("#d9982e")
RED        = colors.HexColor("#d95f5c")
BLUE       = colors.HexColor("#4f8fd4")
WHITE      = colors.white
PAGE_W, PAGE_H = A4

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def _styles():
    base = getSampleStyleSheet()

    def s(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "h1": s("h1", fontSize=22, textColor=IVORY, fontName="Helvetica-Bold",
                leading=28, spaceAfter=4),
        "h2": s("h2", fontSize=13, textColor=BRASS_SOFT, fontName="Helvetica-Bold",
                leading=18, spaceBefore=18, spaceAfter=6),
        "h3": s("h3", fontSize=10, textColor=IVORY, fontName="Helvetica-Bold",
                leading=14, spaceBefore=10, spaceAfter=4),
        "body": s("body", fontSize=9.5, textColor=IVORY, fontName="Helvetica",
                  leading=15, spaceAfter=6),
        "body_muted": s("body_muted", fontSize=9, textColor=MUTED,
                        fontName="Helvetica", leading=14, spaceAfter=4),
        "label": s("label", fontSize=7.5, textColor=BRASS, fontName="Helvetica-Bold",
                   leading=10, spaceAfter=3, wordWrap="CJK",
                   textTransform="uppercase", charSpace=1.2),
        "bullet": s("bullet", fontSize=9.5, textColor=IVORY, fontName="Helvetica",
                    leading=15, spaceAfter=5, leftIndent=14, firstLineIndent=-14),
        "email": s("email", fontSize=9, textColor=colors.HexColor("#c8d8e8"),
                   fontName="Courier", leading=14, spaceAfter=4),
        "tag": s("tag", fontSize=8, textColor=BRASS_SOFT, fontName="Helvetica-Bold",
                 leading=11, spaceAfter=3, textTransform="uppercase", charSpace=1),
    }


# ---------------------------------------------------------------------------
# Page template: dark background + brass header bar
# ---------------------------------------------------------------------------
class _DarkPage:
    def __init__(self, doc):
        self.doc = doc

    def __call__(self, canvas, doc):
        canvas.saveState()
        # Full-page dark background
        canvas.setFillColor(INK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Header bar
        bar_h = 14 * mm
        canvas.setFillColor(INK_2)
        canvas.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, fill=1, stroke=0)

        # Brass left accent in header
        canvas.setFillColor(BRASS)
        canvas.rect(0, PAGE_H - bar_h, 4, bar_h, fill=1, stroke=0)

        # Brand name in header
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(IVORY)
        canvas.drawString(12 * mm, PAGE_H - bar_h + 4 * mm, "MERIDIAN AI OPS")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(12 * mm, PAGE_H - bar_h + 1.5 * mm, "C1 Insurance Group  ·  Confidential")

        # Page number (right side of header)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_W - 12 * mm, PAGE_H - bar_h + 2.5 * mm,
                               f"Page {doc.page}")

        # Footer
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        ts = datetime.now(timezone.utc).strftime("%B %d, %Y  %H:%M UTC")
        canvas.drawString(12 * mm, 8 * mm, f"Generated {ts}")
        canvas.drawRightString(PAGE_W - 12 * mm, 8 * mm,
                               "Internal use only — do not distribute")

        # Thin brass rule above footer
        canvas.setStrokeColor(BRASS)
        canvas.setLineWidth(0.5)
        canvas.line(12 * mm, 13 * mm, PAGE_W - 12 * mm, 13 * mm)

        canvas.restoreState()


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------
def _hr(c=BRASS, w=0.5, space_before=4, space_after=12):
    return HRFlowable(width="100%", thickness=w, color=c,
                      spaceBefore=space_before, spaceAfter=space_after)


def _tile_table(tiles, styles):
    """Render a row of info tiles: [(label, value), ...]"""
    n = len(tiles)
    col_w = (PAGE_W - 28 * mm) / n
    header_row = [Paragraph(lbl, styles["label"]) for lbl, _ in tiles]
    value_row  = [Paragraph(str(val or "Not recorded"), styles["h3"]) for _, val in tiles]
    tbl = Table([header_row, value_row], colWidths=[col_w] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [SURFACE, SURFACE]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, BRASS),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6]),
    ]))
    return tbl


def _urgency_bar(score: int, tier: str, reason: str, styles):
    colour = RED if score >= 8 else AMBER if score >= 5 else GREEN
    bar_w  = PAGE_W - 28 * mm
    filled = bar_w * (score / 10)

    elems = [Paragraph(styles["label"].name, styles["label"])]
    elems = [Paragraph("Urgency", styles["label"])]

    score_style = ParagraphStyle("score_s", parent=styles["h1"],
                                 textColor=colour, fontSize=16)
    elems.append(Paragraph(f"{tier} Priority &nbsp;&nbsp; {score} / 10", score_style))
    elems.append(Spacer(1, 4))

    # Visual bar using a 1-row table
    bar_table = Table([[""]], colWidths=[filled], rowHeights=[6])
    bar_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colour),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("ROUNDEDCORNERS", [3]),
    ]))
    track_table = Table([[bar_table]], colWidths=[bar_w], rowHeights=[6])
    track_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#1c3050")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ("ROUNDEDCORNERS", [3]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elems.append(track_table)
    elems.append(Spacer(1, 6))
    elems.append(Paragraph(reason, styles["body_muted"]))
    return elems


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def generate_pdf(analysis: dict, contact: dict | None, events: list[dict]) -> bytes:
    buf    = io.BytesIO()
    styles = _styles()

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=22 * mm, bottomMargin=20 * mm,
    )

    header_h = 14 * mm
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        PAGE_W - doc.leftMargin - doc.rightMargin,
        PAGE_H - doc.bottomMargin - header_h - 6 * mm,
        id="main",
    )
    pt = PageTemplate(id="dark", frames=[frame], onPage=_DarkPage(doc))
    doc.addPageTemplates([pt])

    story = []
    name     = analysis.get("client_name", "Unknown Client")
    location = analysis.get("property_location", "")
    closing  = analysis.get("closing_date", "")
    carriers = ", ".join(analysis.get("current_carriers", [])) or "Not recorded"
    urg      = analysis.get("urgency", {})
    score    = int(urg.get("score", 0) or 0)
    tier     = "High" if score >= 8 else "Medium" if score >= 5 else "Low"

    # ── Title ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Call Analysis Report", styles["h1"]))
    story.append(_hr())

    # ── Client summary tiles ───────────────────────────────────────────
    story.append(Paragraph("Client Summary", styles["h2"]))
    tiles = [
        ("Client", name),
        ("Property", location or "Not recorded"),
        ("Closing Date", closing if closing not in ("unknown", "") else "Not applicable"),
        ("Current Carriers", carriers),
    ]
    story.append(_tile_table(tiles, styles))
    story.append(Spacer(1, 8))

    # Contact row
    if contact:
        story.append(Paragraph("Contact Record", styles["label"]))
        story.append(Paragraph(
            f"{contact.get('name','')} &nbsp;·&nbsp; "
            f"{contact.get('phone','')} &nbsp;·&nbsp; "
            f"{contact.get('email','')}",
            styles["body_muted"],
        ))
        story.append(Spacer(1, 4))

    # ── Urgency ────────────────────────────────────────────────────────
    story.append(Paragraph("Urgency Assessment", styles["h2"]))
    reason = urg.get("reason", "")
    story.extend(_urgency_bar(score, tier, reason, styles))
    story.append(Spacer(1, 4))

    # ── Coverage interests ─────────────────────────────────────────────
    interests = analysis.get("coverage_interests", [])
    if interests:
        story.append(Paragraph("Coverage Interests", styles["h2"]))
        story.append(Paragraph(
            "  ·  ".join(i.title() for i in interests),
            styles["body"],
        ))

    # ── Revenue opportunities ──────────────────────────────────────────
    flags = analysis.get("crosssell_flags", [])
    if flags:
        story.append(Paragraph("Revenue Opportunities", styles["h2"]))
        for flag in flags:
            direction = ("C1 → MyUtilities" if flag.get("direction") == "c1_to_myutils"
                         else "MyUtilities → C1")
            story.append(Paragraph(direction, styles["tag"]))
            story.append(Paragraph(flag.get("reason", ""), styles["body"]))
            story.append(Paragraph(
                f"Recommended Action: {flag.get('suggested_action','')}",
                styles["body_muted"],
            ))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Revenue Opportunities", styles["h2"]))
        story.append(Paragraph("No cross-sell opportunities identified in this call.",
                               styles["body_muted"]))

    # ── Action plan ────────────────────────────────────────────────────
    actions = analysis.get("advisor_actions", [])
    if actions:
        story.append(Paragraph("Action Plan", styles["h2"]))
        for i, step in enumerate(actions, 1):
            story.append(Paragraph(f"{i}.  {step}", styles["bullet"]))
        story.append(Spacer(1, 4))

    # ── Draft email ────────────────────────────────────────────────────
    draft = analysis.get("draft_email", {})
    if draft:
        story.append(Paragraph("Draft Follow-up Email", styles["h2"]))
        to_addr = (contact or {}).get("email", "[client email needed]")
        story.append(Paragraph(
            f"<b>To:</b> {to_addr}   <b>Subject:</b> {draft.get('subject','')}",
            styles["body_muted"],
        ))
        story.append(Spacer(1, 4))
        for line in draft.get("body", "").splitlines():
            story.append(Paragraph(line if line.strip() else "&nbsp;", styles["email"]))
        story.append(Spacer(1, 6))

    # ── Automated actions ──────────────────────────────────────────────
    if events:
        story.append(Paragraph("Automated Actions", styles["h2"]))
        TYPE_LABEL = {
            "CREATE_CRM_LEAD":     "CRM Lead Created",
            "CREATE_ADVISOR_TASK": "Advisor Task Created",
            "SEND_EMAIL":          "Follow-up Email Ready",
            "SEND_SMS":            "SMS Queued",
            "MYUTILITIES_HANDOFF": "MyUtilities Referral Sent",
        }
        for ev in events:
            etype   = ev.get("eventType", "")
            payload = ev.get("payload", {})
            label   = TYPE_LABEL.get(etype, etype)
            target  = ev.get("targetSystem", "")
            story.append(Paragraph(
                f"<font color='#3faa78'>&#10003;</font> "
                f"<b>{label}</b> &nbsp;→ {target}",
                styles["body"],
            ))
            # One key detail per event type
            detail = ""
            if etype == "CREATE_CRM_LEAD":
                detail = (f"Pipeline: {payload.get('pipeline','')} · "
                          f"Stage: {payload.get('deal_stage','')} · "
                          f"Urgency: {payload.get('urgency_score','')}/10")
            elif etype == "CREATE_ADVISOR_TASK":
                detail = (f"Priority: {payload.get('priority','')} · "
                          f"Due: {payload.get('due_date','')}")
            elif etype == "SEND_EMAIL":
                detail = f"To: {payload.get('to_email','')} · Subject: {payload.get('subject','')}"
            elif etype == "SEND_SMS":
                detail = f"To: {payload.get('to_phone','')}"
            elif etype == "MYUTILITIES_HANDOFF":
                detail = (f"Needs: {', '.join(payload.get('utility_needs',[]))} · "
                          f"SLA: {payload.get('sla_minutes','')} min")
            if detail:
                story.append(Paragraph(detail, styles["body_muted"]))
            story.append(Spacer(1, 3))

    doc.build(story)
    return buf.getvalue()
