"""PDF-Export des aktuellen Plans (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

from mtr_evaluation import Analysis, Settings, edge_table, grade_label, kosten, verdict_optimal

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis, settings: Settings) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Greedy und Tausch: Leitungsnetz"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        _s(f"{a.inst.n} Standorte, {a.inst.m} mögliche Leitungen, Seed {settings.seed}, Nabe {'ja' if settings.nabe else 'nein'}, {grade_label(settings.grad)}."),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.multi_cell(0, 5, _s(verdict_optimal(a, settings.grad)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s(f"Greedy-Baum: {', '.join(a.inst.label(e) for e in a.tree) or '-'}  (Kosten {kosten(a.cost) if a.cost is not None else '-'})"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    widths = (16, 36, 24, 90)
    heads = ("Schritt", "Leitung", "Kosten", "Entscheidung")
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(heads, widths):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for row in edge_table(a):
        for key, w in zip(heads, widths):
            pdf.cell(w, 5.5, _s(row[key]), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: greedy-austausch-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
