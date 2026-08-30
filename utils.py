"""
Funzioni di utilita' per TravelMatch: costanti del questionario, calcolo del
Travel DNA, formattazione di testo/numeri. Nessuna dipendenza da Streamlit:
puo' essere testato e riusato in isolamento.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# ---------------------------------------------------------------------------
# Costanti di dominio / opzioni del questionario
# ---------------------------------------------------------------------------

BUDGET_BANDS = {
    "< 500 €": (0, 500),
    "500 - 1.000 €": (500, 1000),
    "1.000 - 1.500 €": (1000, 1500),
    "1.500 - 2.500 €": (1500, 2500),
    "2.500 - 4.000 €": (2500, 4000),
    "> 4.000 €": (4000, 100000),
}

PEOPLE_OPTIONS = ["Solo", "Coppia", "Amici", "Famiglia", "Gruppo"]

PERIOD_OPTIONS = [
    "🌸 Primavera",
    "☀️ Estate",
    "🍂 Autunno",
    "❄️ Inverno",
    "🏃 Weekend",
    "📅 Date personalizzate",
    "🎄 Natale",
    "🎆 Capodanno",
    "🎄🎆 Natale + Capodanno",
]

CHRISTMAS_PERIODS = {"🎄 Natale", "🎆 Capodanno", "🎄🎆 Natale + Capodanno"}

# Riferimento esplicito richiesto: Natale 2026 / Capodanno 2027
CHRISTMAS_2026_RANGE = (date(2026, 12, 18), date(2027, 1, 6))

DURATION_BANDS = {
    "2-3 giorni": (2, 3),
    "4-5 giorni": (4, 5),
    "6-8 giorni": (6, 8),
    "9-14 giorni": (9, 14),
    "15+ giorni": (15, 30),
}

MOOD_OPTIONS = {
    "nature_adventure": "🌿 Natura & Avventura",
    "relax_beach": "🏖️ Relax & Beach",
    "city_culture": "🏛️ Città & Cultura",
    "party_nightlife": "🎉 Party & Nightlife",
    "snow_mountain": "🏔️ Neve & Montagna",
    "romantic": "❤️ Romantico",
    "family": "👨‍👩‍👧 Famiglia",
    "food": "🍝 Food",
    "wellness": "🧘 Wellness",
    "shopping": "🛍️ Shopping",
    "unique": "🌌 Esperienze uniche",
}

INTENSITY_OPTIONS = {
    "relaxed": "😌 Relaxed",
    "dynamic": "🚶 Dynamic",
    "intense": "🥾 Intense",
}

# Etichette del ritmo di una meta/itinerario (destinations.pace). Stesse
# chiavi di INTENSITY_OPTIONS — è voluto: l'intensità chiesta all'utente e il
# ritmo della destinazione vivono sulla stessa scala, ed è ciò che permette a
# recommender._pace_match di confrontarli direttamente.
PACE_LABELS = {
    "relaxed": "😌 Rilassato",
    "dynamic": "🚶 Dinamico",
    "intense": "🥾 Intenso",
}

PACE_DESCRIPTIONS = {
    "relaxed": "Poche cose al giorno, tempi larghi",
    "dynamic": "Un buon ritmo, senza correre",
    "intense": "Giornate piene, si cammina parecchio",
}

# Modalità viaggiatore: derivata da "Con chi parti?" (PEOPLE_OPTIONS), più il
# caso speciale "primo viaggio da solo/a" attivato dal quick-start dedicato.
# Influenza socialità suggerita, tipo di alloggio e avvisi — mai lo scoring
# di base, che resta guidato dalle risposte esplicite del questionario.
TRAVELLER_MODE_BY_PEOPLE = {
    "Solo": "solo",
    "Coppia": "coppia",
    "Amici": "gruppo",
    "Gruppo": "gruppo",
    "Famiglia": "famiglia",
}

TRAVELLER_MODE_LABELS = {
    "solo": "🎒 In solitaria",
    "primo_solo": "🧳 Primo viaggio da solo/a",
    "coppia": "❤️ In coppia",
    "gruppo": "🎉 In gruppo",
    "famiglia": "👨‍👩‍👧 In famiglia",
}

# Suggerimento di alloggio per modalità: non è una prenotazione, è
# l'inquadratura giusta per leggere gli scenari di costo.
TRAVELLER_STAY_HINTS = {
    "solo": "Ostello con camera privata o B&B centrale: costo contenuto e facile conoscere gente.",
    "primo_solo": "Ostello ben recensito con camere private: il compromesso migliore tra sicurezza, costo e compagnia.",
    "coppia": "B&B o piccolo hotel di charme: la differenza di prezzo su due persone si sente poco.",
    "gruppo": "Appartamento intero: dividendo tra più persone scende sotto il costo di camere separate.",
    "famiglia": "Appartamento con cucina: fa risparmiare sui pasti e dà spazio ai bambini.",
}

CLIMATE_OPTIONS = {
    "warm": "☀️ Caldo",
    "temperate": "🌤️ Temperato",
    "cold": "❄️ Freddo",
    "snow": "🏔️ Neve",
    "tropical": "🌴 Tropicale",
}

AREA_OPTIONS = {
    "italia": "Italia",
    "europa": "Europa",
    "europa_nordafrica": "Europa + Nord Africa",
    "mondo": "Mondo",
    "nessun_limite": "Nessun limite",
}

# Aree geografiche del dataset ammesse per ciascuna scelta dell'utente
AREA_TO_REGIONS = {
    "italia": {"Italia"},
    "europa": {"Europa"},
    "europa_nordafrica": {"Italia", "Europa", "Extra-Europa"},  # filtrato via country nel recommender
    "mondo": {"Italia", "Europa", "Extra-Europa"},
    "nessun_limite": {"Italia", "Europa", "Extra-Europa"},
}

NORTH_AFRICA_COUNTRIES = {"Marocco"}

# "Altro / Indifferente" = nessuna preferenza sulla città di partenza: le
# stime restano quelle generiche del dataset (vedi travel_estimates.py).
DEPARTURE_CITY_OPTIONS = {
    "milano": "🛫 Milano",
    "roma": "🛫 Roma",
    "altro": "🤷 Altro / Indifferente",
}

DISTANCE_OPTIONS = {
    "2h": 2,
    "3h": 3,
    "5h": 5,
    "8h": 8,
    "Nessun limite": 999,
}

COMFORT_OPTIONS = {
    "backpacker": "🎒 Backpacker",
    "comfort": "🏨 Comfort",
    "premium": "✨ Premium",
    "luxury": "💎 Luxury",
}

COMFORT_TO_LEVEL = {"backpacker": 1, "comfort": 3, "premium": 4, "luxury": 5}

SOCIAL_PREFERENCE_OPTIONS = {
    "solo": "Da solo/a con altri viaggiatori",
    "coppia": "In coppia",
    "gruppo": "In gruppo",
    "indifferente": "Indifferente",
}

# La lista dei tag mostrati in UI vive in destinations.TAG_LABELS (unica
# fonte di verità: sono anche gli stessi tag usati come valori nel dataset).

QUICK_START_OPTIONS = [
    ("relax_warm", "🏖️ Voglio staccare e stare al caldo"),
    ("christmas_movie", "🎄 Voglio un Natale da film"),
    ("adventure", "🥾 Voglio avventura"),
    ("romantic", "❤️ Voglio una fuga romantica"),
    ("social", "🎉 Voglio conoscere gente"),
    ("build_trip", "✈️ Costruisci il mio viaggio"),
    ("surprise", "🎲 Non ne ho idea. Sorprendimi."),
    ("controlled_surprise", "🎯 Sorprendimi, ma con dei paletti"),
    ("first_solo_trip", "🧳 È il mio primo viaggio da solo/a"),
    ("gift_surprise", "🎁 Voglio regalare un viaggio (sorpresa)"),
]

REFINEMENT_ACTIONS = [
    ("cheaper", "💰 Più economico"),
    ("warmer", "☀️ Più caldo"),
    ("snowier", "❄️ Più neve"),
    ("closer", "✈️ Più vicino"),
    ("romantic", "❤️ Più romantico"),
    ("social", "🎉 Più social"),
    ("adventure", "🥾 Più avventura"),
    ("relax", "🏖️ Più relax"),
    ("food", "🍝 Più food"),
    ("luxury", "💎 Più luxury"),
]

# Raffinamento specifico per i viaggi combinati (Trip Builder): questi pulsanti
# modificano i pesi/le penalita' interne del motore di itinerari, non il
# questionario (vedi trip_builder.apply_trip_refinement).
TRIP_REFINEMENT_ACTIONS = [
    ("fewer_transfers", "🧳 Meno spostamenti"),
    ("more_destinations", "🗺️ Più destinazioni"),
    ("trip_relaxed", "🧘 Più rilassato"),
    ("trip_intense", "⚡ Più intenso"),
    ("time_optimized", "⏱️ Ottimizza il tempo"),
]

# ---------------------------------------------------------------------------
# Travel DNA
# ---------------------------------------------------------------------------

def compute_travel_dna(preferences: dict[str, Any]) -> dict[str, int]:
    """Deriva il Travel DNA (percentuali 0-100) dalle preferenze utente.

    Il DNA e' calcolato combinando mood selezionati, intensita', socialita',
    comfort e clima: nessuna dipendenza dal dataset, cosi' resta stabile
    anche se il dataset cresce.
    """
    moods = set(preferences.get("moods", []))
    intensity = preferences.get("intensity", "dynamic")
    social_slider = preferences.get("social_slider", 50)
    comfort = preferences.get("comfort", "comfort")
    climate = set(preferences.get("climate", []))
    tags = set(preferences.get("tags", []))

    def mood_bonus(key: str, base: int = 55) -> int:
        return base + (30 if key in moods else 0)

    adventure = mood_bonus("nature_adventure", 40)
    adventure += {"relaxed": -10, "dynamic": 5, "intense": 20}.get(intensity, 0)
    adventure += 10 if "trekking" in tags or "sci" in tags else 0

    nature = mood_bonus("nature_adventure", 40)
    nature += 10 if "natura" in tags or "montagna" in tags else 0

    food = mood_bonus("food", 40)
    food += 10 if "food" in tags else 0

    social = mood_bonus("party_nightlife", 30)
    social = int(0.6 * social + 0.4 * social_slider)
    social += 10 if "nightlife" in tags else 0

    relax = mood_bonus("relax_beach", 45)
    relax += mood_bonus("wellness", 0) // 3
    relax += {"relaxed": 20, "dynamic": 0, "intense": -15}.get(intensity, 0)
    relax += 10 if "silenzio" in tags or "wellness" in tags else 0

    luxury = {"backpacker": 15, "comfort": 40, "premium": 65, "luxury": 90}.get(comfort, 40)

    culture = mood_bonus("city_culture", 40)
    culture += 10 if "cultura" in tags or "monumenti" in tags else 0

    romantic = mood_bonus("romantic", 35)

    snow = mood_bonus("snow_mountain", 20)
    snow += 30 if "snow" in climate else 0
    snow += 10 if "neve" in tags or "sci" in tags else 0

    warmth = 30
    warmth += 35 if "warm" in climate else 0
    warmth += 25 if "tropical" in climate else 0
    warmth -= 20 if "snow" in climate or "cold" in climate else 0

    raw = {
        "🥾 Adventure": adventure,
        "🌿 Nature": nature,
        "🍝 Food": food,
        "🎉 Social": social,
        "🏖️ Relax": relax,
        "💎 Luxury": luxury,
        "🏛️ Culture": culture,
        "❤️ Romance": romantic,
        "🏔️ Snow": snow,
        "☀️ Warmth": warmth,
    }
    return {k: max(0, min(100, int(v))) for k, v in raw.items()}


def travel_dna_top_traits(dna: dict[str, int], n: int = 3) -> list[str]:
    return [k for k, _ in sorted(dna.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def travel_dna_description(dna: dict[str, int]) -> str:
    if not dna:
        return "Rispondi al questionario per scoprire il tuo Travel DNA."
    ordered = sorted(dna.items(), key=lambda kv: kv[1], reverse=True)
    top = ordered[:3]
    bottom = ordered[-1]

    clean = lambda label: label.split(" ", 1)[1].lower()
    top_labels = " + ".join(clean(k) for k, _ in top)
    bottom_label = clean(bottom[0])

    return (
        f'Il tuo Travel DNA: sei più "{top_labels}" che "{bottom_label}". '
        f"Abbiamo capito. 😎"
    )


# ---------------------------------------------------------------------------
# Formattazione
# ---------------------------------------------------------------------------

def format_price_range(low: float, high: float) -> str:
    low, high = int(round(low, -1)), int(round(high, -1))
    return f"{low:,}-{high:,} €".replace(",", ".")


def format_price(value: float) -> str:
    return f"{int(round(value, -1)):,} €".replace(",", ".")


# ---------------------------------------------------------------------------
# Scenari di costo (Economico / Medio / Comodo) e avviso budget
#
# Riusa i range di costo min/max già presenti nel dataset (destinazioni) o
# già calcolati (trip_builder.compute_trip_cost_breakdown, che include i
# trasferimenti nei totali) — nessun nuovo campo dati, solo tre modi di
# leggere lo stesso range: il minimo (chi vuole spendere il meno possibile),
# la media (lo scenario "di default" già mostrato nelle card) e il massimo
# maggiorato di COMFORT_SCENARIO_MULTIPLIER (chi vuole viaggiare più comodo
# di quanto il range massimo già preveda).
# ---------------------------------------------------------------------------

COMFORT_SCENARIO_MULTIPLIER = 1.15
BUDGET_WARNING_THRESHOLD = 0.15  # oltre il 15% sopra il budget_max -> avviso


def cost_scenarios(cost_min: float, cost_max: float) -> dict[str, float]:
    """Tre stime di costo totale a partire da un range min/max già calcolato:
    Economico (il minimo), Medio (il punto medio, lo scenario "di default"
    mostrato altrove nell'app) e Comodo (il massimo maggiorato)."""
    return {
        "economico": cost_min,
        "medio": (cost_min + cost_max) / 2,
        "comodo": cost_max * COMFORT_SCENARIO_MULTIPLIER,
    }


def budget_warning_message(scenario_medio: float, budget_max: float | None) -> str | None:
    """Avviso amichevole se lo scenario Medio sfora il budget_max dell'utente
    di oltre BUDGET_WARNING_THRESHOLD (15%). None se non c'è nulla da
    segnalare (nessun budget impostato, o costo in linea)."""
    if not budget_max or budget_max <= 0:
        return None
    overage_ratio = (scenario_medio - budget_max) / budget_max
    if overage_ratio <= BUDGET_WARNING_THRESHOLD:
        return None
    overage_amount = scenario_medio - budget_max
    return f"⚠️ Questo viaggio rischia di sforare il tuo budget di circa {format_price(overage_amount)} a persona."


def budget_warning_for_range(cost_min: float, cost_max: float, budget_max: float | None) -> str | None:
    """Scorciatoia su cost_scenarios + budget_warning_message: calcola lo
    scenario Medio da un range min/max e verifica lo sforamento in un solo
    passo. Punto di estensione unico per chi ha già un range di costo (row
    di una destinazione o breakdown di un viaggio) e vuole solo sapere se
    avvisare l'utente, senza ricalcolare lo scenario a mano ogni volta."""
    return budget_warning_message(cost_scenarios(cost_min, cost_max)["medio"], budget_max)


def format_temp_range(low: float, high: float) -> str:
    return f"{int(round(low))}°C / {int(round(high))}°C" if low != high else f"{int(round(low))}°C"


def social_dots(level_0_100: float) -> str:
    """Converte un livello 0-100 in una barra di pallini ●●●○○ (5 livelli)."""
    filled = max(0, min(5, round(level_0_100 / 20)))
    return "●" * filled + "○" * (5 - filled)


def ease_stars(level_1_5: int) -> str:
    """Converte un livello 1-5 (vedi insights.organizational_ease) in una
    barra di stelle ★★★★☆."""
    filled = max(0, min(5, level_1_5))
    return "★" * filled + "☆" * (5 - filled)


def flight_hours_label(hours: float) -> str:
    """Arrotonda sempre al multiplo di 5 minuti più vicino: i dati sorgente
    in destinations.py sono già puliti, ma alcuni calcoli a valle (es.
    l'aggiustamento per città di partenza in travel_estimates.py, che
    moltiplica flight_hours per un fattore) possono reintrodurre minuti non
    arrotondati — questa funzione garantisce che il numero mostrato resti
    sempre leggibile, indipendentemente da dove viene calcolato."""
    total_minutes = round(hours * 60 / 5) * 5
    if total_minutes < 60:
        return f"{total_minutes} min"
    whole, minutes = divmod(total_minutes, 60)
    return f"{whole}h{minutes:02d}" if minutes else f"{whole}h"


# Milano ha tre aeroporti (Malpensa/Linate/Bergamo): mostriamo solo il nome
# città per non dichiarare un aeroporto specifico che l'utente non ha scelto.
# Roma ha Fiumicino come riferimento standard per i voli internazionali.
DEPARTURE_AIRPORT_CODES = {"roma": "FCO"}


def flight_duration_label(hours: float, departure_city: str | None) -> str:
    """Durata di volo pronta per la UI, con città/aeroporto di partenza se
    l'utente l'ha scelta (vedi DEPARTURE_CITY_OPTIONS). "Altro/Indifferente"
    o nessuna scelta -> solo la durata generica, senza dichiarare una
    partenza che l'utente non ha specificato."""
    duration = flight_hours_label(hours)
    if not departure_city or departure_city not in DEPARTURE_CITY_OPTIONS or departure_city == "altro":
        return f"{duration} di volo"
    city_label = DEPARTURE_CITY_OPTIONS[departure_city].split(" ", 1)[-1]
    code = DEPARTURE_AIRPORT_CODES.get(departure_city)
    origin = f"{city_label} ({code})" if code else city_label
    return f"Volo da {origin} · {duration}"


def medal_for_rank(rank: int) -> str:
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(rank, "🔹")
