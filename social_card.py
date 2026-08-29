"""
Social Card — un'immagine verticale (formato "storia") pronta da condividere
su WhatsApp/Telegram/Instagram, più una didascalia testuale breve e curata
distinta dal riepilogo completo di export.py (quello è un itinerario
dettagliato da leggere; questo è un teaser da postare).

Generata con Pillow se disponibile; se non lo è, o se qualcosa va storto nel
disegno (font mancante, ecc.), build_social_card_image restituisce None e chi
chiama mostra solo la didascalia testuale — mai un errore per l'utente.
Nessuna emoji viene disegnata nell'immagine: molti font TrueType non hanno i
glifi a colori (o non hanno affatto il glifo, "tofu") e il risultato sarebbe
un quadratino vuoto. Si usa solo il punto elenco "•" (U+2022), presente nel
set Latin di base di qualunque font TrueType standard.
"""

from __future__ import annotations

import io
import os
from typing import Any

from utils import format_price

try:
    from PIL import Image, ImageDraw, ImageFont

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

CARD_WIDTH, CARD_HEIGHT = 1080, 1000

ACCENT = (14, 165, 160)
ACCENT_DARK = (11, 40, 60)
WHITE = (255, 255, 255)
MUTED = (214, 231, 229)

_FONT_BOLD_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
_FONT_REGULAR_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _load_font(candidates: list[str], size: int):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _vertical_gradient(draw, width: int, height: int, top: tuple, bottom: tuple) -> None:
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def _wrap_text(text: str, font, draw, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_social_card_image(title: str, subtitle: str, match_score: float, highlight: str, cost_line: str) -> bytes | None:
    """PNG verticale 1080x1350. None se Pillow non è disponibile o se il
    disegno fallisce per qualunque motivo (font di sistema mancanti, ecc.)."""
    if not _PIL_AVAILABLE:
        return None
    try:
        img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), ACCENT)
        draw = ImageDraw.Draw(img)
        _vertical_gradient(draw, CARD_WIDTH, CARD_HEIGHT, ACCENT, ACCENT_DARK)

        font_badge = _load_font(_FONT_BOLD_CANDIDATES, 38)
        font_title = _load_font(_FONT_BOLD_CANDIDATES, 74)
        font_subtitle = _load_font(_FONT_REGULAR_CANDIDATES, 36)
        font_body = _load_font(_FONT_REGULAR_CANDIDATES, 40)
        font_footer = _load_font(_FONT_REGULAR_CANDIDATES, 30)

        margin = 80

        badge_text = f"{match_score:.0f}% MATCH"
        badge_w = draw.textlength(badge_text, font=font_badge) + 60
        draw.rounded_rectangle([margin, 90, margin + badge_w, 160], radius=35, fill=WHITE)
        draw.text((margin + 30, 105), badge_text, font=font_badge, fill=ACCENT_DARK)

        y = 240
        for line in _wrap_text(title.upper(), font_title, draw, CARD_WIDTH - 2 * margin)[:3]:
            draw.text((margin, y), line, font=font_title, fill=WHITE)
            y += 88

        y += 16
        for line in _wrap_text(subtitle, font_subtitle, draw, CARD_WIDTH - 2 * margin)[:2]:
            draw.text((margin, y), line, font=font_subtitle, fill=MUTED)
            y += 48

        y += 30
        draw.line([(margin, y), (CARD_WIDTH - margin, y)], fill=MUTED, width=2)
        y += 50

        draw.text((margin, y), "\u2022", font=font_body, fill=WHITE)
        for line in _wrap_text(highlight, font_body, draw, CARD_WIDTH - 2 * margin - 60):
            draw.text((margin + 40, y), line, font=font_body, fill=WHITE)
            y += 54
        y += 40

        draw.text((margin, y), cost_line, font=font_body, fill=WHITE)

        draw.text((margin, CARD_HEIGHT - 90), "Generato con TravelMatch", font=font_footer, fill=MUTED)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        return None


def _first_wow(experiences: list[str]) -> str:
    return experiences[0] if experiences else "un'esperienza pensata su misura"


def destination_social_card_image(row: Any) -> bytes | None:
    highlight = _first_wow(list(row.get("wow_experiences", [])))
    cost_line = f"Da {format_price(row['total_cost_min'])} a persona"
    return build_social_card_image(
        title=row["name"], subtitle=f"{row['country']} · {row['region']}",
        match_score=row["match_score"], highlight=highlight, cost_line=cost_line,
    )


def trip_social_card_image(trip: dict[str, Any]) -> bytes | None:
    all_wow = [w for s in trip.get("stops", []) for w in s.get("wow_experiences", [])]
    highlight = _first_wow(all_wow)
    subtitle = " + ".join(trip.get("stop_names", []))
    cost_line = f"Da {format_price(trip['total_cost_min'])} a persona"
    return build_social_card_image(
        title=trip["name"], subtitle=subtitle,
        match_score=trip["trip_match_score"], highlight=highlight, cost_line=cost_line,
    )


def destination_social_caption(row: Any) -> str:
    wow = _first_wow(list(row.get("wow_experiences", [])))
    return (
        f"📍 {row['name']}, {row['country']}\n"
        f"{row['match_score']:.0f}% di match con quello che cercavo ✨\n"
        f"{wow}\n"
        f"Scoperta con TravelMatch ✈️"
    )


def trip_social_caption(trip: dict[str, Any]) -> str:
    all_wow = [w for s in trip.get("stops", []) for w in s.get("wow_experiences", [])]
    wow = _first_wow(all_wow)
    route = " + ".join(trip.get("stop_names", []))
    return (
        f"✈️ {route}\n"
        f"{trip['trip_match_score']:.0f}% di match ✨\n"
        f"{wow}\n"
        f"Itinerario scoperto con TravelMatch"
    )
