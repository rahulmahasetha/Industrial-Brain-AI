"""
PDF utility class for generating professional industrial documents.
FreshFlow Beverages Pvt. Ltd. - branded base class.
"""
from fpdf import FPDF
from dataset_gen.config import COMPANY, PLANT_NAME, DOC_PREFIX, ADDRESS, ISO_CERT


class IndustrialPDF(FPDF):
    """Base PDF class with FreshFlow company header/footer and helper methods."""

    def __init__(self, doc_title="", doc_number="", orientation="P"):
        super().__init__(orientation=orientation, unit="mm", format="A4")
        self.doc_title = doc_title
        self.doc_number = doc_number
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(0, 102, 0)   # FreshFlow green
        self.cell(90, 5, COMPANY, ln=False, align="L")
        if self.doc_number:
            self.set_text_color(80, 80, 80)
            self.cell(0, 5, f"Doc No: {self.doc_number}", ln=True, align="R")
        else:
            self.ln(5)
        self.set_draw_color(0, 140, 40)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(0, 140, 40)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, f"CONFIDENTIAL - For internal use only | {COMPANY} | {ADDRESS[:60]}",
                  ln=False, align="L")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", ln=True, align="R")

    def add_title_page(self, title, subtitle="", equip_id="", revision="Rev 1.0", doc_type="Document"):
        """Add a professional title page."""
        self.add_page()
        self.ln(30)
        # Company name
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(0, 120, 40)
        self.cell(0, 12, COMPANY, ln=True, align="C")
        self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, PLANT_NAME, ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, f"FSSAI: {__import__('dataset_gen.config', fromlist=['FSSAI_NO']).FSSAI_NO} | {ISO_CERT}", ln=True, align="C")
        self.ln(12)
        # Document type badge
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(0, 140, 40)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {doc_type.upper()}  ", ln=True, align="C", fill=True)
        self.ln(5)
        # Title
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 10, title, align="C")
        self.ln(3)
        if subtitle:
            self.set_font("Helvetica", "", 12)
            self.set_text_color(60, 60, 60)
            self.cell(0, 7, subtitle, ln=True, align="C")
            self.ln(2)
        if equip_id:
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(0, 120, 40)
            self.cell(0, 7, f"Equipment ID: {equip_id}", ln=True, align="C")
        self.ln(15)
        # Metadata box
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(235, 248, 235)
        x = 35
        w = 140
        meta = [
            f"Document Number: {self.doc_number}",
            f"Revision: {revision}",
            f"Classification: CONFIDENTIAL - INTERNAL USE ONLY",
            f"Prepared by: Engineering / QA Department",
            f"Approved by: Plant Manager",
        ]
        for m in meta:
            self.set_x(x)
            self.cell(w, 8, m, ln=True, fill=True, align="C", border=1)

    def add_section_title(self, number, title):
        self.ln(5)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 100, 30)
        self.cell(0, 8, f"{number}. {title}", ln=True)
        self.set_draw_color(0, 140, 40)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 130, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def add_subsection_title(self, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 80, 30)
        self.cell(0, 6, title, ln=True)
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def add_body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def add_warning_box(self, text, level="WARNING"):
        """Add a coloured warning/caution/note box."""
        colors = {
            "DANGER":   (200, 0, 0),
            "WARNING":  (180, 100, 0),
            "CAUTION":  (150, 120, 0),
            "NOTE":     (0, 80, 150),
        }
        r, g, b = colors.get(level, (100, 100, 100))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  ! {level}", ln=True, fill=True)
        self.set_fill_color(255, 248, 230)
        self.set_text_color(30, 30, 30)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def add_bullet_list(self, items):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        for item in items:
            self.set_x(10)
            self.cell(8, 5, "-", ln=False)
            self.multi_cell(0, 5, str(item))
        self.ln(2)

    def add_numbered_list(self, items):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        for i, item in enumerate(items, 1):
            self.set_x(10)
            self.set_font("Helvetica", "B", 10)
            self.cell(10, 5, f"{i}.", ln=False)
            self.set_font("Helvetica", "", 10)
            self.multi_cell(0, 5, str(item))
        self.ln(2)

    def add_table(self, headers, rows, col_widths=None):
        if not col_widths:
            n = len(headers)
            available = 190
            col_widths = [available // n] * n
            col_widths[-1] = available - sum(col_widths[:-1])

        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 110, 35)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, str(h)[:40], border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        fill = False
        for row in rows:
            if self.get_y() > 260:
                self.add_page()
                self.set_font("Helvetica", "B", 9)
                self.set_fill_color(0, 110, 35)
                self.set_text_color(255, 255, 255)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 7, str(h)[:40], border=1, fill=True, align="C")
                self.ln()
                self.set_font("Helvetica", "", 9)
                self.set_text_color(30, 30, 30)
                fill = False
            self.set_fill_color(235, 248, 235) if fill else self.set_fill_color(255, 255, 255)
            for i, cell_text in enumerate(row):
                self.cell(col_widths[i], 6, str(cell_text)[:55], border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(3)

    def add_key_value_table(self, data_dict, title=None):
        if title:
            self.add_subsection_title(title)
        headers = ["Parameter", "Value"]
        rows = [[k, str(v)] for k, v in data_dict.items()]
        self.add_table(headers, rows, col_widths=[70, 120])

    def save(self, filepath):
        self.alias_nb_pages()
        self.output(filepath)
