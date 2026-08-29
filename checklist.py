"""
Checklist — genera una piccola checklist pratica (cosa portare, documenti
tipici, consigli rapidi) per una destinazione o un viaggio combinato, a
partire da clima, area geografica e periodo scelto.

Pura lettura/derivazione di dati già presenti (temp_min/max, tags, region,
practical_tips): nessun nuovo campo nel dataset, nessuna fonte esterna.
Indipendente da Streamlit, come gli altri moduli di presentazione.
"""

from __future__ import annotations

from typing import Any

from utils import CHRISTMAS_PERIODS

# ---------------------------------------------------------------------------
# Cosa portare — basato su temperature min/max e tag dell'attività.
# ---------------------------------------------------------------------------

WEATHER_TAG_ITEMS: dict[str, str] = {
    "neve": "🎿 Abbigliamento tecnico da neve e scarpe impermeabili",
    "sci": "🎿 Abbigliamento tecnico da neve e scarpe impermeabili",
    "spiaggia": "🩱 Costume, telo mare e ciabatte",
    "mare": "🩱 Costume, telo mare e ciabatte",
    "surf": "🏄 Costume e crema solare resistente all'acqua",
    "trekking": "🥾 Scarpe da trekking comode e già rodate",
    "montagna": "🥾 Scarpe comode per camminare su terreni irregolari",
    "aurora boreale": "🔦 Torcia frontale e batterie di scorta (per il buio prolungato)",
    "mercatini di natale": "🧣 Sciarpa, guanti e strati caldi per le serate all'aperto",
}


def packing_list_for_climate(temp_min: float, temp_max: float, tags: set[str]) -> list[str]:
    items = []
    if temp_min <= 5:
        items.append("🧥 Piumino/giacca pesante e maglie a strati")
        items.append("🧤 Guanti e cappello")
    elif temp_min <= 15:
        items.append("🧥 Giacca leggera o felpa per le serate")

    if temp_max >= 28:
        items.append("👕 Abbigliamento leggero e traspirante")
        items.append("🧴 Crema solare ad alta protezione")
    elif temp_max <= 12:
        items.append("🧣 Strati caldi anche di giorno")

    for tag, item in WEATHER_TAG_ITEMS.items():
        if tag in tags and item not in items:
            items.append(item)

    if not items:
        items.append("👕 Abbigliamento versatile a strati, adatto a clima temperato")
    return items


# ---------------------------------------------------------------------------
# Documenti tipici — in base all'area geografica del dataset (Italia/Europa/
# Extra-Europa, vedi destinations.py). Indicazioni generiche e prudenti, non
# un servizio di consulenza visti: l'app resta offline e non verifica requisiti
# in tempo reale.
# ---------------------------------------------------------------------------

_REGION_STRICTNESS = {"Italia": 0, "Europa": 1, "Extra-Europa": 2}


def _strictest_region(regions: set[str]) -> str:
    return max(regions, key=lambda r: _REGION_STRICTNESS.get(r, 2))


def documents_for_region(region: str) -> list[str]:
    if region == "Italia":
        return ["🪪 Carta d'identità (o patente) in corso di validità"]
    if region == "Europa":
        return ["🪪 Carta d'identità valida per l'espatrio (area Schengen) o passaporto"]
    return [
        "🛂 Passaporto con validità residua di almeno 6 mesi dalla data di rientro",
        "📋 Verifica per tempo se è richiesto un visto turistico",
    ]


# ---------------------------------------------------------------------------
# Assemblaggio della checklist completa
# ---------------------------------------------------------------------------

_CHRISTMAS_TIP = (
    "🎁 A Natale/Capodanno negozi, musei e ristoranti possono avere orari ridotti "
    "o essere chiusi nei giorni di festa: controlla in anticipo."
)


def build_destination_checklist(row: Any, period: str | None) -> dict[str, list[str]]:
    tags = set(row.get("tags", []))
    tips = list(row.get("practical_tips", []))[:2]
    if period in CHRISTMAS_PERIODS:
        tips.append(_CHRISTMAS_TIP)
    return {
        "🎒 Cosa portare": packing_list_for_climate(row["temp_min"], row["temp_max"], tags),
        "📄 Documenti tipici": documents_for_region(row["region"]),
        "💡 Consigli pratici rapidi": tips or ["Nessun consiglio specifico: una meta senza sorprese particolari."],
    }


def build_trip_checklist(trip: dict[str, Any], period: str | None) -> dict[str, list[str]]:
    stops = trip.get("stops", [])
    if not stops:
        return {"🎒 Cosa portare": [], "📄 Documenti tipici": [], "💡 Consigli pratici rapidi": []}

    temp_min = min(s["temp_min"] for s in stops)
    temp_max = max(s["temp_max"] for s in stops)
    tags: set[str] = set()
    for s in stops:
        tags |= set(s.get("tags", []))
    region = _strictest_region({s["region"] for s in stops})

    tips = []
    for s in stops:
        stop_tips = list(s.get("practical_tips", []))
        if stop_tips:
            tips.append(f"{s['name']}: {stop_tips[0]}")
    if period in CHRISTMAS_PERIODS:
        tips.append(_CHRISTMAS_TIP)

    return {
        "🎒 Cosa portare": packing_list_for_climate(temp_min, temp_max, tags),
        "📄 Documenti tipici": documents_for_region(region),
        "💡 Consigli pratici rapidi": tips[:4] or ["Nessun consiglio specifico: itinerario senza sorprese particolari."],
    }
