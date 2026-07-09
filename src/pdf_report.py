# -*- coding: utf-8 -*-
"""Lightweight Markdown-to-PDF renderer for notification attachments."""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path
from typing import Iterable, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


logger = logging.getLogger(__name__)


_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\u2600-\u27bf"
    "]+",
    flags=re.UNICODE,
)


def _candidate_fonts() -> Iterable[Path]:
    candidates = [
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ]
    return candidates


def _register_report_font() -> str:
    for font_path in _candidate_fonts():
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("ReportFont", str(font_path)))
            logger.info("PDF report font registered: %s", font_path)
            return "ReportFont"
        except Exception as exc:
            logger.debug("PDF report font registration failed for %s: %s", font_path, exc)
    logger.warning("No Unicode TTF font found for PDF report; falling back to Helvetica")
    return "Helvetica"


def _clean_inline(text: object) -> str:
    cleaned = str(text or "")
    cleaned = _EMOJI_RE.sub("", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = cleaned.replace("<br>", "\n").replace("<br/>", "\n")
    return cleaned.strip()


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    safe = html.escape(_clean_inline(text)).replace("\n", "<br/>")
    return Paragraph(safe or "&nbsp;", style)


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and "|" in stripped.strip("|")


def _parse_table_row(line: str) -> List[str]:
    return [_clean_inline(cell) for cell in line.strip().strip("|").split("|")]


def _consume_table(lines: List[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not _is_table_row(line):
            break
        if not _is_table_separator(line):
            rows.append(_parse_table_row(line))
        index += 1
    return rows, index


def markdown_to_pdf_file(markdown_text: str, output_path: str) -> Optional[str]:
    """Render Markdown text into a readable PDF file.

    The renderer intentionally supports a small Markdown subset used by reports:
    headings, bullets, blockquotes, basic paragraphs, and pipe tables.
    """
    try:
        font_name = _register_report_font()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        base_styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            "ReportNormal",
            parent=base_styles["Normal"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=4,
            wordWrap="CJK",
        )
        h1 = ParagraphStyle(
            "ReportH1",
            parent=normal,
            fontSize=16,
            leading=21,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=10,
            spaceAfter=8,
        )
        h2 = ParagraphStyle(
            "ReportH2",
            parent=normal,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=6,
        )
        h3 = ParagraphStyle(
            "ReportH3",
            parent=normal,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#334155"),
            spaceBefore=6,
            spaceAfter=4,
        )
        quote = ParagraphStyle(
            "ReportQuote",
            parent=normal,
            leftIndent=8,
            textColor=colors.HexColor("#475569"),
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.5,
            borderPadding=5,
            backColor=colors.HexColor("#f8fafc"),
        )
        footer_style = ParagraphStyle(
            "ReportFooter",
            parent=normal,
            fontSize=8,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_CENTER,
        )

        story = []
        lines = markdown_text.splitlines()
        index = 0
        while index < len(lines):
            raw = lines[index].rstrip()
            stripped = raw.strip()
            if not stripped:
                story.append(Spacer(1, 2 * mm))
                index += 1
                continue
            if stripped == "---":
                story.append(Spacer(1, 4 * mm))
                index += 1
                continue
            if stripped.startswith("# "):
                story.append(_paragraph(stripped[2:], h1))
            elif stripped.startswith("## "):
                story.append(_paragraph(stripped[3:], h2))
            elif stripped.startswith("### "):
                story.append(_paragraph(stripped[4:], h3))
            elif stripped.startswith(">"):
                story.append(_paragraph(stripped.lstrip("> ").strip(), quote))
            elif _is_table_row(stripped):
                rows, next_index = _consume_table(lines, index)
                if rows:
                    max_cols = max(len(row) for row in rows)
                    normalized = [row + [""] * (max_cols - len(row)) for row in rows]
                    data = [[_paragraph(cell, normal) for cell in row] for row in normalized]
                    table = Table(data, repeatRows=1 if len(data) > 1 else 0)
                    table.setStyle(
                        TableStyle(
                            [
                                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )
                    story.append(table)
                    story.append(Spacer(1, 3 * mm))
                index = next_index
                continue
            elif stripped.startswith(("- ", "* ")):
                story.append(_paragraph("• " + stripped[2:], normal))
            else:
                story.append(_paragraph(stripped, normal))
            index += 1

        if not story:
            story.append(_paragraph("No report content.", normal))

        def _draw_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont(font_name if font_name != "Helvetica" else "Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748b"))
            canvas.drawCentredString(A4[0] / 2, 10 * mm, f"Page {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=16 * mm,
        )
        doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
        return str(path)
    except Exception as exc:
        logger.exception("Markdown to PDF conversion failed: %s", exc)
        return None
