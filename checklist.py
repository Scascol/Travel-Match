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


# ---------------------------------------------------------------------------
# Cosa NON portare — la sezione che manca a tutte le checklist. Ridurre il
# bagaglio è più utile che allungarlo, e il consiglio giusto dipende dalla
# meta: "lascia a casa il phon" ha senso in hotel, non in ostello.
# ---------------------------------------------------------------------------

_LEAVE_HOME_BY_TAG: dict[str, str] = {
    "spiaggia": "🧺 Telo mare ingombrante: quasi ovunque lo trovi sul posto a poco",
    "mare": "🤿 Attrezzatura da snorkeling voluminosa: si noleggia in loco",
    "trekking": "🏕️ Attrezzatura da campeggio, se dormi in struttura",
    "sci": "🎿 Sci e scarponi: noleggiarli sul posto costa meno del sovrapprezzo bagaglio",
    "cultura": "📚 Guide cartacee pesanti: bastano le mappe offline sul telefono",
}


def leave_at_home_items(row_or_stops: Any, comfort_level: int, days: int) -> list[str]:
    """Cosa evitare di mettere in valigia. Dipende da comfort (in struttura
    3+ stelle asciugamani e phon ci sono già) e durata (sotto la settimana
    il bagaglio a mano basta quasi sempre)."""
    tags = set(row_or_stops)
    items = []
    if comfort_level >= 3:
        items.append("🧴 Asciugamani, phon e set da bagno: la struttura li fornisce")
    if days <= 5:
        items.append("🧳 La valigia grande: per pochi giorni il bagaglio a mano basta e ti fa risparmiare")
    for tag, item in _LEAVE_HOME_BY_TAG.items():
        if tag in tags:
            items.append(item)
    items.append("👗 Il vestito 'per l'occasione speciale' che non useresti: quasi sempre torna a casa pulito")
    return items[:4]


# ---------------------------------------------------------------------------
# Le cose che si dimenticano davvero — non ovvietà (passaporto, biglietti) ma
# il secondo strato, quello che ci si accorge di aver scordato una volta lì.
# ---------------------------------------------------------------------------

_COMMONLY_FORGOTTEN_BASE = [
    "🔌 Adattatore di corrente (e un caricatore in più: se ne perde sempre uno)",
    "💊 Farmaci abituali in quantità sufficiente, nel bagaglio a mano",
    "📱 Screenshot/copia offline di prenotazioni e documenti (la rete non è garantita)",
]

_COMMONLY_FORGOTTEN_BY_CONDITION: list[tuple[str, str]] = [
    ("extra_europe", "💳 Avvisare la banca del viaggio ed evitare il blocco della carta all'estero"),
    ("hot", "🕶️ Occhiali da sole e un copricapo: banali finché non servono"),
    ("cold", "🧴 Burrocacao e crema mani: il freddo secco si fa sentire subito"),
    ("beach", "🩹 Ciabatte per la doccia e una borsa impermeabile per il telefono"),
    ("hike", "🩹 Cerotti per vesciche: la cosa più dimenticata da chi cammina molto"),
    ("solo", "📇 Un contatto di emergenza scritto su carta, non solo nel telefono"),
]


def commonly_forgotten_items(
    temp_min: float, temp_max: float, tags: set[str], region: str, is_solo: bool = False,
) -> list[str]:
    conditions = set()
    if region == "Extra-Europa":
        conditions.add("extra_europe")
    if temp_max >= 26:
        conditions.add("hot")
    if temp_min <= 5:
        conditions.add("cold")
    if {"spiaggia", "mare", "surf"} & tags:
        conditions.add("beach")
    if {"trekking", "montagna"} & tags:
        conditions.add("hike")
    if is_solo:
        conditions.add("solo")

    extras = [text for cond, text in _COMMONLY_FORGOTTEN_BY_CONDITION if cond in conditions]
    return _COMMONLY_FORGOTTEN_BASE + extras[:3]


def _solo_first_trip_tips(region: str) -> list[str]:
    """Consigli specifici per chi parte da solo/a la prima volta. Attivati
    dalla modalità viaggiatore (vedi app.handle_quick_start), non da un
    campo del dataset."""
    tips = [
        "🛏️ Ostelli con camere private: costo contenuto ma è facile conoscere gente",
        "📍 Condividi la posizione con qualcuno a casa e aggiornalo sugli spostamenti",
        "🌆 Arriva in una città nuova con la luce, non di notte: cambia tutto",
    ]
    if region != "Italia":
        tips.append("🗺️ Scarica mappa offline e qualche frase base nella lingua locale")
    return tips


def build_destination_checklist(
    row: Any, period: str | None, traveller_mode: str | None = None, days: int | None = None,
) -> dict[str, list[str]]:
    """Checklist completa per una destinazione.

    `traveller_mode` ("solo"/"coppia"/"gruppo"/"primo_solo") e `days` sono
    opzionali: senza di essi la checklist resta esattamente quella di prima,
    così i chiamanti esistenti non si rompono."""
    tags = set(row.get("tags", []))
    tips = list(row.get("practical_tips", []))[:2]
    if period in CHRISTMAS_PERIODS:
        tips.append(_CHRISTMAS_TIP)

    is_solo = traveller_mode in ("solo", "primo_solo")
    effective_days = days or int(row.get("ideal_days", row.get("days_min", 4)))

    checklist = {
        "🎒 Cosa portare": packing_list_for_climate(row["temp_min"], row["temp_max"], tags),
        "📄 Documenti tipici": documents_for_region(row["region"]),
        "🚫 Cosa lasciare a casa": leave_at_home_items(tags, int(row.get("comfort_level", 3)), effective_days),
        "🤦 Cose che si dimenticano spesso": commonly_forgotten_items(
            row["temp_min"], row["temp_max"], tags, row["region"], is_solo,
        ),
        "💡 Consigli pratici rapidi": tips or ["Nessun consiglio specifico: una meta senza sorprese particolari."],
    }
    if traveller_mode == "primo_solo":
        checklist["🧳 Primo viaggio da solo/a"] = _solo_first_trip_tips(row["region"])
    return checklist


def build_trip_checklist(
    trip: dict[str, Any], period: str | None, traveller_mode: str | None = None,
) -> dict[str, list[str]]:
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

    is_solo = traveller_mode in ("solo", "primo_solo")
    # Il comfort che conta per "cosa lasciare a casa" è il più basso tra le
    # tappe: se una notte è in ostello, gli asciugamani servono comunque.
    min_comfort = min(int(s.get("comfort_level", 3)) for s in stops)
    total_days = int(trip.get("ideal_days", 7))

    checklist = {
        "🎒 Cosa portare": packing_list_for_climate(temp_min, temp_max, tags),
        "📄 Documenti tipici": documents_for_region(region),
        "🚫 Cosa lasciare a casa": leave_at_home_items(tags, min_comfort, total_days),
        "🤦 Cose che si dimenticano spesso": commonly_forgotten_items(
            temp_min, temp_max, tags, region, is_solo,
        ),
        "💡 Consigli pratici rapidi": tips[:4] or ["Nessun consiglio specifico: itinerario senza sorprese particolari."],
    }
    if traveller_mode == "primo_solo":
        checklist["🧳 Primo viaggio da solo/a"] = _solo_first_trip_tips(region)
    # Un itinerario multi-tappa ha un vincolo che una meta singola non ha.
    if len(stops) > 1:
        checklist["🚫 Cosa lasciare a casa"].insert(
            0, "🧳 Il bagaglio pesante: lo sposterai a ogni cambio tappa"
        )
    return checklist
