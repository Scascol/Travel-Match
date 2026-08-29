"""
Insights — piccoli arricchimenti "di lettura" per le card di destinazioni e
viaggi combinati: Travel Style (il profilo della meta/dell'itinerario, non
quello dell'utente — per quello vedi utils.compute_travel_dna), avvisi
contestuali (trasferimenti lunghi, affollamento stagionale, esperienze
meteo-dipendenti, sforamento budget), facilità organizzativa (1-5) e le
alternative "quasi scelte" (anti-FOMO leggero).

Deliberatamente separato da recommender.py/trip_builder.py: qui non si
calcola né si altera nessun punteggio di match/feasibility, si leggono solo
punteggi già calcolati e si formattano in informazioni utili per l'utente.
Nessuna dipendenza da Streamlit, cosi' resta testabile in isolamento come
gli altri moduli "di presentazione".
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from utils import CHRISTMAS_PERIODS, budget_warning_for_range, flight_hours_label

# ---------------------------------------------------------------------------
# Travel Style — il "carattere" della meta/dell'itinerario secondo i punteggi
# già presenti nel dataset. Occhio alla differenza con il Travel DNA
# dell'utente (utils.compute_travel_dna): quello descrive le preferenze di
# chi cerca, questo descrive la destinazione stessa.
# ---------------------------------------------------------------------------

TRAVEL_STYLE_FIELDS: dict[str, str] = {
    "🥾 Avventura": "adventure_score",
    "🏖️ Relax": "relax_score",
    "🏛️ Cultura": "culture_score",
    "🎉 Social": "social_level",
    "💎 Lusso": "luxury_score",
}


def travel_style_scores(row: Any) -> dict[str, float]:
    """Le 5 barre Travel Style per UNA destinazione. social_level e' su
    scala 1-5 nel dataset (vedi destinations.py): *20 lo riporta a 0-100
    come le altre, cosi' le barre sono confrontabili tra loro."""
    scores = {}
    for label, field in TRAVEL_STYLE_FIELDS.items():
        value = row[field]
        scores[label] = value * 20 if field == "social_level" else value
    return scores


def travel_style_scores_for_stops(stops: list) -> dict[str, float]:
    """Le stesse 5 barre per un viaggio combinato: media semplice tra le
    tappe. Una media (non il massimo, come _mood_coverage in trip_builder)
    perché qui l'obiettivo è descrivere il carattere complessivo del
    viaggio, non premiare la tappa più forte su un singolo aspetto."""
    if not stops:
        return {label: 0.0 for label in TRAVEL_STYLE_FIELDS}
    per_stop = [travel_style_scores(s) for s in stops]
    return {label: sum(d[label] for d in per_stop) / len(per_stop) for label in TRAVEL_STYLE_FIELDS}


# ---------------------------------------------------------------------------
# Avvisi contestuali — non allarmistici, solo cose utili da sapere prima di
# prenotare. Ogni avviso e' opzionale (appare solo se la condizione si
# verifica) e usa dati gia' calcolati altrove: nessun nuovo campo dataset.
# ---------------------------------------------------------------------------

LONG_TRANSFER_HOURS_THRESHOLD = 4.5
CROWD_SCORE_THRESHOLD = 85.0

# Parole chiave (in italiano, minuscolo) che identificano un'esperienza WOW
# legata al meteo o alle condizioni naturali del momento: non e' un elenco
# esaustivo, solo i casi più comuni nel dataset (vedi destinations.py).
WEATHER_DEPENDENT_KEYWORDS = [
    "mongolfiera", "aurora boreale", "safari", "trekking", "escursione",
    "vulcano", "immersione", "snorkeling", "surf", "slitta", "igloo",
    "geyser", "vela", "barca",
]


def _first_weather_dependent_experience(experiences: list[str]) -> str | None:
    for exp in experiences:
        lowered = exp.lower()
        if any(keyword in lowered for keyword in WEATHER_DEPENDENT_KEYWORDS):
            return exp
    return None


def _budget_warning_for(cost_min: float, cost_max: float, prefs: dict[str, Any]) -> str | None:
    budget_max = prefs.get("budget_range", (None, None))[1]
    return budget_warning_for_range(cost_min, cost_max, budget_max)


def destination_warnings(row: Any, prefs: dict[str, Any]) -> list[str]:
    """Avvisi per una destinazione singola: affollamento stagionale,
    esperienza meteo-dipendente, sforamento budget."""
    warnings = []

    period = prefs.get("period")
    if period in CHRISTMAS_PERIODS:
        crowd = max(row.get("christmas_score", 0), row.get("new_year_score", 0))
        if crowd >= CROWD_SCORE_THRESHOLD:
            warnings.append(
                "🎉 Meta molto gettonata nel periodo scelto: meglio prenotare alloggi e ristoranti con un po' di anticipo."
            )

    experience = _first_weather_dependent_experience(list(row.get("wow_experiences", [])))
    if experience:
        warnings.append(f'🌤️ "{experience}" dipende dal meteo: tieni un piano B per i giorni no.')

    budget_msg = _budget_warning_for(row["total_cost_min"], row["total_cost_max"], prefs)
    if budget_msg:
        warnings.append(budget_msg)

    return warnings


def trip_warnings(trip: dict[str, Any], prefs: dict[str, Any]) -> list[str]:
    """Avvisi per un viaggio combinato: trasferimento lungo, affollamento
    stagionale su una delle tappe, esperienza meteo-dipendente, sforamento
    budget (che qui include già i trasferimenti, vedi trip_builder)."""
    warnings = []

    edges = trip.get("edges", [])
    if edges:
        longest_leg = max(e["travel_time"] for e in edges)
        if longest_leg > LONG_TRANSFER_HOURS_THRESHOLD:
            warnings.append(
                f"🚗 Un trasferimento dura circa {flight_hours_label(longest_leg)}: da mettere in conto nella "
                f"pianificazione delle giornate."
            )

    stops = trip.get("stops", [])
    period = prefs.get("period")
    if period in CHRISTMAS_PERIODS and stops:
        crowd = max(max(s.get("christmas_score", 0), s.get("new_year_score", 0)) for s in stops)
        if crowd >= CROWD_SCORE_THRESHOLD:
            warnings.append(
                "🎉 Una delle tappe è molto gettonata nel periodo scelto: meglio prenotare con un po' di anticipo."
            )

    all_experiences = [w for s in stops for w in s.get("wow_experiences", [])]
    experience = _first_weather_dependent_experience(all_experiences)
    if experience:
        warnings.append(f'🌤️ "{experience}" dipende dal meteo: tieni un piano B per i giorni no.')

    budget_msg = _budget_warning_for(trip["total_cost_min"], trip["total_cost_max"], prefs)
    if budget_msg:
        warnings.append(budget_msg)

    return warnings


# ---------------------------------------------------------------------------
# Facilità organizzativa (1-5) — quanto è semplice organizzarsi da soli,
# calcolata (non un nuovo campo dataset) da segnali già presenti: area
# geografica, ore di volo, comfort_level. Una lettura sintetica, non un nuovo
# punteggio di match: non entra mai in score_destination/score_trip.
# ---------------------------------------------------------------------------

_EASE_REGION_BONUS = {"Italia": 1.5, "Europa": 0.5}
_EASE_REGION_DEFAULT = -1.0


def organizational_ease(row: Any) -> int:
    """1 (richiede più organizzazione) - 5 (semplicissima da organizzare da
    soli). Parte da un valore neutro (3) e lo aggiusta in base a quanto la
    meta è "battuta" (area, distanza di volo) e a quanta infrastruttura
    turistica ha tipicamente (comfort_level, usato qui come proxy di
    facilità di prenotazione, non di lusso)."""
    score = 3.0
    score += _EASE_REGION_BONUS.get(row["region"], _EASE_REGION_DEFAULT)

    flight_hours = row["flight_hours"]
    if flight_hours <= 2:
        score += 0.5
    elif flight_hours >= 8:
        score -= 1.0

    score += (row["comfort_level"] - 3) * 0.3

    return int(round(max(1, min(5, score))))


def trip_organizational_ease(trip: dict[str, Any]) -> int:
    """Un itinerario è facile da organizzare quanto la sua tappa più
    complessa (minimo, non media), meno una piccola penalità per ogni tappa
    oltre la prima: più tappe significano più prenotazioni e più cose da
    incastrare, anche quando ognuna singolarmente è semplice."""
    stops = trip.get("stops", [])
    if not stops:
        return 3
    base = min(organizational_ease(s) for s in stops)
    extra_stops_penalty = (len(stops) - 1) * 0.5
    return int(max(1, min(5, round(base - extra_stops_penalty))))


# ---------------------------------------------------------------------------
# Anti-FOMO leggero — 1-2 alternative valutate ma non mostrate, con una
# ragione onesta e specifica (non un generico "punteggio più basso"). Legge
# da candidates_all/scored_all (l'intero pool), mai da un dato nuovo.
# ---------------------------------------------------------------------------

_DESTINATION_REASON_PHRASES = {
    "budget": "il costo stimato è un po' sopra il tuo budget",
    "distanza di volo": "il volo è più lungo di quanto preferisci",
    "durata": "la durata ideale non combacia bene con i giorni che hai a disposizione",
    "periodo": "non è il periodo migliore dell'anno per andarci",
}

_TRIP_WEAKNESS_REASONS = {
    "geographic_coherence": "il percorso tra le tappe non è il massimo della comodità geografica",
    "transport_feasibility": "i collegamenti tra le tappe non sono così comodi",
    "time_feasibility": "il tempo a disposizione è un po' risicato per quelle tappe",
    "budget_feasibility": "il costo totale è più alto rispetto al tuo budget",
    "season_compatibility": "il periodo scelto non è l'ideale per quelle mete",
}


def _destination_discard_reason(compromise_reasons: list[str]) -> str:
    if not compromise_reasons:
        return "il match complessivo era comunque leggermente più basso"
    return _DESTINATION_REASON_PHRASES.get(compromise_reasons[0], "c'era qualche piccolo compromesso in più")


def _trip_discard_reason(trip: Any) -> str:
    components = {key: trip[key] for key in _TRIP_WEAKNESS_REASONS}
    weakest = min(components, key=components.get)
    return _TRIP_WEAKNESS_REASONS[weakest]


def discarded_destination_alternatives(scored_all: pd.DataFrame, shown_ids: set[int], n: int = 2) -> list[str]:
    """1-2 destinazioni valutate ma non mostrate in classifica, con una frase
    onesta sul perché. Prende le migliori tra quelle escluse (non a caso),
    così restano alternative plausibili, non scarti qualunque."""
    if scored_all is None or scored_all.empty:
        return []
    pool = scored_all[~scored_all["id"].isin(shown_ids)].sort_values("match_score", ascending=False).head(n)
    lines = []
    for _, row in pool.iterrows():
        reasons = [] if row.get("meets_strict", True) else list(row.get("compromise_reasons", []))
        reason = _destination_discard_reason(reasons)
        lines.append(f"Abbiamo considerato anche **{row['name']}**, ma l'abbiamo scartata perché {reason}.")
    return lines


def discarded_trip_alternatives(candidates_all: pd.DataFrame | None, shown_trip_ids: set[str], n: int = 2) -> list[str]:
    """Stesso principio per i viaggi combinati: le migliori tra le
    combinazioni non mostrate, con il motivo dedotto dalla componente di
    Feasibility più debole di ciascuna."""
    if candidates_all is None or candidates_all.empty:
        return []
    pool = candidates_all[~candidates_all["trip_id"].isin(shown_trip_ids)].sort_values(
        "overall_score", ascending=False
    ).head(n)
    lines = []
    for _, trip in pool.iterrows():
        reason = _trip_discard_reason(trip)
        lines.append(f"Abbiamo considerato anche **{trip['name']}**, ma l'abbiamo scartata perché {reason}.")
    return lines
