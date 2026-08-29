"""
Export — generazione di riepiloghi condivisibili (testo pronto per
WhatsApp/Telegram e PDF) per destinazioni singole e viaggi combinati.

Deliberatamente separato da trip_presentation.py: quel modulo sa come
descrivere un itinerario in linguaggio naturale (spiegazioni, timeline), ma
non si occupa di destinazioni singole né di produrre file scaricabili. Questo
modulo consuma le stesse funzioni di formattazione (mai le duplica) e
aggiunge solo il layer di "pacchettizzazione" in testo/PDF.

Il PDF è generato con reportlab se disponibile; se non lo è (o se qualcosa
va storto nella generazione), build_pdf_bytes restituisce None e chi chiama
mostra semplicemente il testo, che resta sempre disponibile e copiabile —
l'export testuale non dipende mai da reportlab. Nessuna delle due modalità
richiede una connessione di rete: tutto gira sui dati già calcolati da
recommender.py/trip_builder.py.
"""

from __future__ import annotations

import re
from typing import Any

from trip_presentation import export_trip_as_text, format_cost_scenarios_lines
from utils import budget_warning_for_range, format_price_range

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False

# Stessi colori del brand usati in app.py (inject_css): qui duplicati come
# costanti perché export.py non dipende da Streamlit e non può leggere il
# CSS dell'app — è l'unico posto dove questi valori esadecimali vivono
# fuori da app.py, tenerli allineati a mano se il brand cambia.
_PDF_ACCENT = colors.HexColor("#0EA5A0") if _REPORTLAB_AVAILABLE else None
_PDF_ACCENT_DARK = colors.HexColor("#0B7A75") if _REPORTLAB_AVAILABLE else None
_PDF_MUTED = colors.HexColor("#64748B") if _REPORTLAB_AVAILABLE else None
_PDF_TEXT = colors.HexColor("#0F172A") if _REPORTLAB_AVAILABLE else None

# Righe che nei testi generati da trip_presentation.py/export.py sono sempre
# titoli di sezione puri (nessun dato, solo un'etichetta) — riconosciute per
# corrispondenza esatta, non indovinate: sono le uniche stringhe che questo
# modulo stesso produce con questo scopo, quindi l'elenco resta corto e
# affidabile invece di un'euristica fragile sul testo.
_PDF_SECTION_HEADERS = {
    "🗓️ ITINERARIO",
    "⭐ ESPERIENZE WOW",
    "Dettaglio (scenario medio):",
}
_PDF_FOOTER_MARKER = "— Generato con TravelMatch ✈️"

# I 3 marcatori dello scenario di costo (vedi utils.cost_scenarios) vengono
# ricolorati invece di essere lasciati come emoji semaforo: stesso
# significato (economico/medio/comodo), leggibile anche senza glifi emoji.
_PDF_SCENARIO_COLOR_HEX = {
    "🟢 Economico:": "#166534",
    "🟡 Medio:": "#92620A",
    "🔴 Comodo:": "#991B1B",
}

# reportlab usa i 14 font PDF di base (Helvetica ecc.), che non contengono
# glifi emoji: mostrarli così com'è produce quadratini vuoti ("tofu"), tutto
# tranne che "piacevole da leggere". Li rimuoviamo dal testo mostrato nel PDF
# — l'informazione (numeri, parole) resta identica, sparisce solo la
# decorazione grafica che comunque non sarebbe stata visibile correttamente.
# Il testo per WhatsApp/Telegram (export_trip_as_text, non questo) non è
# toccato: lì gli stessi font non c'entrano, l'emoji resta.
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"  # bandiere
    "\U0001F300-\U0001FAFF"  # pittogrammi/emoji moderni
    "\U00002600-\U000027BF"  # simboli varie + dingbat (es. ✈ ☀ ❤)
    "\U00002B00-\U00002BFF"  # frecce/simboli varie (es. ⭐)
    "\U0000FE0F"              # variation selector-16 (presentazione emoji)
    "\U0000200D"              # zero-width joiner
    "]+"
)

# Caratteri tipografici usati nel testo che, pur non essendo emoji, non sono
# comunque coperti dai font di base di reportlab (verificato di persona
# guardando l'output: "↳" risultava un quadratino) — sostituiti con
# l'equivalente più vicino già usato altrove nel testo e già leggibile.
_PDF_CHAR_REPLACEMENTS = {"↳": "→"}


def _pdf_display_text(line: str) -> str:
    """Il testo di una riga così come va disegnato nel PDF: stesso
    contenuto informativo della riga originale, ripulito dai soli caratteri
    che i font PDF di reportlab non sanno disegnare."""
    text = line
    for char, replacement in _PDF_CHAR_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    text = _EMOJI_PATTERN.sub("", text)
    return " ".join(text.split())


def export_destination_as_text(row: Any, budget_max: float | None = None) -> str:
    """Riepilogo testuale di una destinazione singola, nello stesso stile
    "pronto da incollare" dell'export dei viaggi combinati (vedi
    trip_presentation.export_trip_as_text)."""
    lines = [
        f"📍 {row['name']}, {row['country']}",
        f"Match: {row['match_score']:.0f}%",
        "",
        row.get("explanation", ""),
        "",
        f"🗓️ Durata consigliata: {row['days_min']}-{row['days_max']} giorni",
        "",
        f"💰 COSTO STIMATO / PERSONA: {format_price_range(row['total_cost_min'], row['total_cost_max'])}",
    ]
    lines.extend(format_cost_scenarios_lines(row["total_cost_min"], row["total_cost_max"]))
    warning = budget_warning_for_range(row["total_cost_min"], row["total_cost_max"], budget_max)
    if warning:
        lines.append("")
        lines.append(warning)

    wow = list(row.get("wow_experiences", []))[:3]
    if wow:
        lines.append("")
        lines.append("⭐ ESPERIENZE WOW")
        lines.extend(f"- {w}" for w in wow)

    lines.append("")
    lines.append("— Generato con TravelMatch ✈️")
    return "\n".join(lines)


def export_trip_as_text_with_budget(trip: dict[str, Any], budget_max: float | None = None) -> str:
    """Wrapper su trip_presentation.export_trip_as_text che aggiunge, se
    pertinente, l'avviso di sforamento budget subito dopo il costo stimato —
    tenuto qui (non dentro trip_presentation) perché la soglia di budget è
    una preferenza dell'utente, non una proprietà del viaggio in sé."""
    text = export_trip_as_text(trip)
    warning = budget_warning_for_range(trip["total_cost_min"], trip["total_cost_max"], budget_max)
    if not warning:
        return text
    marker = f"💰 COSTO STIMATO / PERSONA: {format_price_range(trip['total_cost_min'], trip['total_cost_max'])}"
    return text.replace(marker, f"{marker}\n{warning}", 1)


def _escape_pdf_text(line: str) -> str:
    return line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pdf_bytes(title: str, body_text: str) -> bytes | None:
    """PDF ordinato e piacevole da leggere a partire dal testo già
    formattato — stesso identico contenuto dell'export testo (nessuna
    informazione cambia, cambia solo come viene disegnata): titoli di
    sezione, righe di costo ed elenchi puntati vengono riconosciuti e
    formattati in modo diverso dal testo normale, con i colori del brand.
    None se reportlab non è installato o se la generazione fallisce per
    qualunque motivo: chi chiama deve trattarlo come "PDF non disponibile",
    non come un errore fatale, visto che il testo resta comunque disponibile."""
    if not _REPORTLAB_AVAILABLE:
        return None

    import io

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            topMargin=16 * mm, bottomMargin=16 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TMTitle", parent=styles["Title"], fontSize=20, leading=24,
            textColor=_PDF_ACCENT_DARK, spaceAfter=4,
        )
        header_style = ParagraphStyle(
            "TMHeader", parent=styles["Heading2"], fontSize=12.5, leading=16,
            textColor=_PDF_ACCENT_DARK, spaceBefore=10, spaceAfter=4,
        )
        highlight_style = ParagraphStyle(
            "TMHighlight", parent=styles["Normal"], fontSize=12, leading=16,
            textColor=_PDF_TEXT, spaceBefore=4, spaceAfter=2,
        )
        bullet_style = ParagraphStyle(
            "TMBullet", parent=styles["Normal"], fontSize=10.5, leading=15,
            textColor=_PDF_TEXT, leftIndent=12, spaceAfter=1,
        )
        body_style = ParagraphStyle(
            "TMBody", parent=styles["Normal"], fontSize=10.5, leading=15,
            textColor=_PDF_TEXT, spaceAfter=1,
        )
        footer_style = ParagraphStyle(
            "TMFooter", parent=styles["Normal"], fontSize=9, leading=13,
            textColor=_PDF_MUTED, spaceBefore=10,
        )

        story = [
            Paragraph(_escape_pdf_text(_pdf_display_text(title)), title_style),
            HRFlowable(width="100%", thickness=1.4, color=_PDF_ACCENT, spaceAfter=10),
        ]
        for raw_line in body_text.split("\n"):
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # La classificazione (header/footer/scenario/bullet) guarda la
            # riga originale con le emoji intatte, perché sono proprio le
            # emoji a marcare in modo affidabile questi casi (vedi le
            # costanti sopra); solo il TESTO disegnato passa da
            # _pdf_display_text per togliere ciò che il font non sa rendere.
            scenario_color = next((c for prefix, c in _PDF_SCENARIO_COLOR_HEX.items() if line.startswith(prefix)), None)
            display = _escape_pdf_text(_pdf_display_text(line))

            if line in _PDF_SECTION_HEADERS:
                story.append(Paragraph(display, header_style))
            elif line == _PDF_FOOTER_MARKER:
                story.append(HRFlowable(width="100%", thickness=0.7, color=_PDF_MUTED, spaceBefore=8, spaceAfter=6))
                story.append(Paragraph(display, footer_style))
            elif line.startswith("💰 COSTO"):
                story.append(Paragraph(f"<b>{display}</b>", highlight_style))
            elif scenario_color:
                story.append(Paragraph(f'<font color="{scenario_color}"><b>{display}</b></font>', body_style))
            elif line.startswith("- "):
                story.append(Paragraph(f"• {_escape_pdf_text(_pdf_display_text(line[2:]))}", bullet_style))
            else:
                story.append(Paragraph(display, body_style))

        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return None
