import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_FONT_REGISTERED = False


def _register_fonts() -> None:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    pdfmetrics.registerFont(TTFont("DejaVuSans", os.path.join(_FONTS_DIR, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf")))
    _FONT_REGISTERED = True


def text_to_pdf(text: str, title: str = "") -> io.BytesIO:
    _register_fonts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    title_style = ParagraphStyle(
        "Title",
        fontName="DejaVuSans-Bold",
        fontSize=14,
        leading=18,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontName="DejaVuSans",
        fontSize=9,
        leading=12,
        textColor=(0.5, 0.5, 0.5),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="DejaVuSans",
        fontSize=11,
        leading=16,
        spaceAfter=8,
        wordWrap="CJK",
    )
    code_style = ParagraphStyle(
        "Code",
        fontName="DejaVuSans",
        fontSize=9,
        leading=13,
        leftIndent=8,
        spaceAfter=8,
        backColor=(0.95, 0.95, 0.95),
        wordWrap="CJK",
    )

    story = []

    if title:
        story.append(Paragraph(_escape(title), title_style))
    story.append(
        Paragraph(
            f"Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            meta_style,
        )
    )
    story.append(Spacer(1, 4 * mm))

    in_code_block = False
    code_lines: list[str] = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            code_text = "<br/>".join(_escape(l) for l in code_lines)
            story.append(Paragraph(code_text, code_style))
            code_lines = []

    for line in text.splitlines():
        if line.startswith("```"):
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_code()
            story.append(Spacer(1, 3 * mm))
            continue

        flush_code()

        if line.startswith("### "):
            story.append(
                Paragraph(
                    _escape(line[4:]),
                    ParagraphStyle("H3", fontName="DejaVuSans-Bold", fontSize=11, leading=15, spaceAfter=4),
                )
            )
        elif line.startswith("## "):
            story.append(
                Paragraph(
                    _escape(line[3:]),
                    ParagraphStyle("H2", fontName="DejaVuSans-Bold", fontSize=12, leading=16, spaceAfter=5),
                )
            )
        elif line.startswith("# "):
            story.append(
                Paragraph(
                    _escape(line[2:]),
                    ParagraphStyle("H1", fontName="DejaVuSans-Bold", fontSize=13, leading=17, spaceAfter=6),
                )
            )
        else:
            story.append(Paragraph(_escape(line), body_style))

    flush_code()
    if in_code_block and code_lines:
        flush_code()

    doc.build(story)
    buf.seek(0)
    return buf


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
