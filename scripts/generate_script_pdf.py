#!/usr/bin/env python3
"""Convert presentation_script_and_queries.md to a styled PDF."""

import re
from fpdf import FPDF

INPUT_MD = "/Users/rahulmahaseth/.gemini/antigravity-ide/brain/d7783efb-c28c-477f-a681-2ed89c95fbee/presentation_script_and_queries.md"
OUTPUT_PDF = "/Users/rahulmahaseth/Desktop/Industrial Brain AI/Presentation_Script_and_Queries.pdf"

# ─── Read markdown ───
with open(INPUT_MD, "r", encoding="utf-8") as f:
    raw = f.read()

# ─── Strip HTML span tags but keep their text ───
def strip_spans(text):
    return re.sub(r'<span[^>]*>(.*?)</span>', r'\1', text)

raw = strip_spans(raw)

# ─── Replace Unicode with ASCII-safe equivalents ───
def ascii_safe(text):
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
        '\u2192': '->', '\u2190': '<-', '\u00e2': 'a', '\u2019': "'",
        '\u2715': 'x', '\u2713': 'v', '\u2610': '[ ]', '\u2611': '[x]',
        '\u25b8': '>', '\u25b6': '>', '\u25ba': '>',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining non-latin1 chars
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text

raw = ascii_safe(raw)

# ─── PDF Setup ───
class StyledPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Industrial Brain AI - Presentation Script & Demo Guide", align="C")
        self.ln(4)
        self.set_draw_color(0, 180, 140)
        self.set_line_width(0.5)
        self.line(10, 14, 200, 14)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Rahul Mahaseth  |  Page {self.page_no()}/{{nb}}", align="C")

pdf = StyledPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# ─── Parse and render ───
lines = raw.split("\n")

for line in lines:
    stripped = line.strip()

    if not stripped:
        pdf.ln(3)
        continue

    # --- Horizontal rule ---
    if stripped.startswith("---"):
        pdf.ln(4)
        pdf.set_draw_color(0, 180, 140)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)
        continue

    # --- H1 ---
    if stripped.startswith("# ") and not stripped.startswith("## "):
        title = stripped[2:].strip()
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(15, 50, 120)
        pdf.multi_cell(0, 10, title)
        pdf.set_draw_color(0, 180, 140)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y() + 1, 80, pdf.get_y() + 1)
        pdf.ln(6)
        continue

    # --- H2 ---
    if stripped.startswith("## "):
        title = stripped[3:].strip()
        # Remove emoji
        title = re.sub(r'^[🎯📋🔍⚡🤖]\s*', '', title)
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(5, 120, 90)
        pdf.multi_cell(0, 9, title)
        pdf.ln(3)
        continue

    # --- H3 ---
    if stripped.startswith("### "):
        title = stripped[4:].strip()
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(180, 100, 0)
        pdf.multi_cell(0, 8, title)
        pdf.ln(2)
        continue

    # --- Bullet points ---
    if stripped.startswith("* ") or stripped.startswith("- "):
        bullet_text = stripped[2:].strip()
        # Clean markdown formatting
        bullet_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', bullet_text)  # bold
        bullet_text = re.sub(r'\*([^*]+)\*', r'\1', bullet_text)      # italic
        bullet_text = bullet_text.strip('"').strip("*")

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(60, 60, 60)

        # Bullet marker
        x = pdf.get_x()
        pdf.set_x(14)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 160, 120)
        pdf.cell(6, 6, "-")  # bullet dot
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(170, 6, bullet_text)
        pdf.ln(1)
        continue

    # --- Regular paragraph ---
    # Clean markdown
    text = stripped
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # bold markers
    text = re.sub(r'\*([^*]+)\*', r'\1', text)       # italic markers
    text = re.sub(r'^\(Action:.*?\)\s*', '', text)   # action notes

    if text.startswith('"') or text.startswith('"'):
        # Script quote — styled differently
        text = text.strip('"').strip('"').strip('"')
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(50, 50, 80)
        # Add a left border effect
        y_before = pdf.get_y()
        pdf.set_x(16)
        pdf.multi_cell(174, 6, f'"{text}"')
        y_after = pdf.get_y()
        # Draw left accent bar
        pdf.set_draw_color(0, 160, 120)
        pdf.set_line_width(1.2)
        pdf.line(13, y_before, 13, y_after)
        pdf.ln(2)
    elif "(Action:" in stripped:
        # Action instruction
        action_text = re.search(r'\(Action:([^)]+)\)', stripped)
        if action_text:
            pdf.set_font("Helvetica", "BI", 10)
            pdf.set_text_color(130, 50, 200)
            pdf.set_x(14)
            pdf.multi_cell(176, 6, f"Action: {action_text.group(1).strip()}")
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)

# ─── Save ───
pdf.output(OUTPUT_PDF)
print(f"✅ PDF saved to {OUTPUT_PDF}")
