"""
Trip Builder — motore di generazione di itinerari multi-tappa per TravelMatch.

Estende (senza duplicare) il motore a singola destinazione di recommender.py:
riusa `score_destination` per valutare ogni tappa, e aggiunge la logica di
fattibilità/efficienza necessaria per capire se un itinerario di 2-3 tappe e'
davvero consigliabile, non solo teoricamente possibile.

Principio guida: piu' destinazioni non significa viaggio migliore. Un
itinerario viene generato SOLO se esiste una rotta autorata (trip_routes.py)
tra le tappe coinvolte — questo e' anche il meccanismo con cui evitiamo
combinazioni geograficamente assurde: se una coppia di destinazioni non ha
una rotta sensata, il motore non la propone mai, indipendentemente dai
punteggi individuali.

Questo modulo contiene SOLO logica di generazione/scoring: restituisce dati
puri (dict/DataFrame), mai HTML o testo pensato per essere mostrato così
com'è. La formattazione per l'utente (spiegazioni in linguaggio naturale,
timeline leggibile, export testuale) vive in trip_presentation.py, che
consuma queste strutture dati senza che trip_builder.py debba conoscere
Streamlit o il formato di output finale — è il punto di estensione pensato
per future feature di presentazione/export senza toccare il motore.

Determinismo: `generate_trip_candidates` e `get_top_trips` sono puramente
funzionali (nessuna randomicità, nessuno stato globale) — stesso input,
stesso output, sempre. L'unica funzione che introduce casualità è
`surprise_trip`, di proposito.
"""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from recommender import (
    BUDGET_BUFFER_RATIO,
    MAX_WEIGHT,
    MOOD_TO_FIELD,
    _season_match,
    get_default_boosts,
    get_default_weights,
    score_destination,
)
from trip_routes import TRIP_TEMPLATES, load_routes_df

# ---------------------------------------------------------------------------
# Pesi e costanti di tuning — TUTTI centralizzati qui.
#
# Questo blocco è l'unico punto in cui vanno modificati i pesi e le costanti
# usate dal motore: nessun "numero magico" dovrebbe comparire più sotto nelle
# funzioni di scoring. Comodo sia per il raffinamento rapido (che modifica
# trip_weights/adjustments a runtime) sia per chi vuole ritarare il modello.
# ---------------------------------------------------------------------------

# Blend finale dei 3 punteggi di viaggio (Trip Match / Feasibility / Efficiency)
# nell'overall_score usato per ordinare i risultati.
TRIP_DEFAULT_WEIGHTS: dict[str, float] = {
    "trip_match": 0.50,
    "feasibility": 0.35,
    "efficiency": 0.15,
}

# Pesi delle 5 componenti del Feasibility Score (vedi score_trip).
FEASIBILITY_WEIGHTS: dict[str, float] = {
    "geographic": 0.25,
    "transport": 0.25,
    "time": 0.25,
    "budget": 0.15,
    "season": 0.10,
}

# Pesi delle 4 componenti del Trip Match Score (vedi score_trip e
# _mood_coverage per il perché non è una semplice media delle tappe).
TRIP_MATCH_WEIGHTS: dict[str, float] = {
    "avg_stop": 0.40,
    "min_stop": 0.20,
    "mood_coverage": 0.25,
    "efficiency": 0.15,
}

# Moltiplicatori di default per le penalità interne (modificati dal
# raffinamento rapido tramite apply_trip_refinement, mai dal questionario).
DEFAULT_TRIP_ADJUSTMENTS: dict[str, float] = {
    "hop_penalty_mult": 1.0,
    "transfer_time_penalty_mult": 1.0,
    "stop_count_penalty_mult": 1.0,
    "ideal_days_bias": 1.0,
}

# --- Costanti di scoring delle singole componenti (vedi funzioni _xxx sotto) ---

# geographic_coherence: punteggio base meno una penalità per ora di viaggio
# media, più un bonus se le tappe consecutive condividono il cluster.
GEO_BASE_SCORE = 88.0
GEO_TRAVEL_TIME_PENALTY_PER_HOUR = 6.0
GEO_SAME_CLUSTER_BONUS = 15.0

# transport_feasibility: media della convenience_score delle rotte, meno una
# penalità per ogni cambio oltre il primo (2 tappe = 1 rotta = 0 penalità).
HOP_PENALTY_PER_EXTRA_HOP = 6.0

# time_feasibility: penalità se il tempo disponibile è sotto il minimo
# richiesto dalle tappe; nessuna penalità fino all'ideale; lieve decadimento
# (con un pavimento) se il tempo disponibile supera di molto l'ideale.
TIME_SHORTFALL_PENALTY_PER_DAY = 18.0
TIME_SURPLUS_PENALTY_PER_DAY = 4.0
TIME_SURPLUS_FLOOR = 60.0

# budget_feasibility: dentro budget → punteggio alto con lieve differenziazione
# (più economico = leggermente meglio); fuori budget → crollo rapido.
BUDGET_WITHIN_BUDGET_FLOOR = 65.0
BUDGET_WITHIN_BUDGET_PENALTY_RATIO = 15.0
BUDGET_OVERAGE_PENALTY_RATIO = 130.0

# Penalità dirette sul Feasibility Score (dopo il blend pesato):
# - se i trasferimenti superano MAX_TRANSFER_FRACTION del tempo ideale di
#   viaggio, penalità pesante; tra il 30% e quella soglia, penalità lieve di
#   preavviso. Questo è il meccanismo richiesto esplicitamente dalla spec:
#   "penalizza fortemente itinerari in cui >30-35% del tempo è trasferimento".
TRANSFER_FRACTION_WARNING = 0.30
MAX_TRANSFER_FRACTION = 0.35
TRANSFER_PENALTY_HARD = 25.0
TRANSFER_PENALTY_WARNING = 10.0

# - se il numero di tappe eccede la linea guida per la durata scelta
#   (vedi ideal_stop_range/DURATION_STOP_GUIDELINES), penalità proporzionale
#   all'eccesso.
STOP_COUNT_PENALTY_PER_EXTRA_STOP = 15.0

FEASIBILITY_THRESHOLD = 75.0
FEASIBILITY_THRESHOLD_FALLBACK = 60.0

TRIP_REFINEMENT_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "fewer_transfers": {
        "trip_weights": {},
        "adjustments": {"hop_penalty_mult": 0.5, "transfer_time_penalty_mult": 0.5},
    },
    "more_destinations": {
        "trip_weights": {},
        "adjustments": {"stop_count_penalty_mult": -0.6},
    },
    "trip_relaxed": {
        "trip_weights": {},
        "adjustments": {"ideal_days_bias": 0.12},
    },
    "trip_intense": {
        "trip_weights": {},
        "adjustments": {"ideal_days_bias": -0.12},
    },
    "time_optimized": {
        "trip_weights": {"efficiency": 0.15},
        "adjustments": {},
    },
}

# Linee guida (non regole assolute) sul numero di tappe per durata del
# viaggio: (giorni_min, giorni_max, tappe_min_consigliate, tappe_max_consigliate).
DURATION_STOP_GUIDELINES = [
    (2, 4, 1, 1),
    (5, 7, 1, 2),
    (8, 10, 2, 3),
    (11, 14, 2, 4),
    (15, 999, 2, 5),
]


def get_default_trip_weights() -> dict[str, float]:
    """Copia fresca dei pesi di default per il blend Trip Match/Feasibility/Efficiency."""
    return dict(TRIP_DEFAULT_WEIGHTS)


def get_default_trip_adjustments() -> dict[str, float]:
    """Copia fresca dei moltiplicatori di penalità di default (nessun raffinamento applicato)."""
    return dict(DEFAULT_TRIP_ADJUSTMENTS)


def apply_trip_refinement(
    trip_weights: dict[str, float], adjustments: dict[str, float], action: str
) -> tuple[dict[str, float], dict[str, float]]:
    """Applica l'effetto di un pulsante di raffinamento rapido (es. "Meno
    spostamenti") a copie di trip_weights/adjustments, senza mutare gli
    originali. Azione sconosciuta → nessun cambiamento (no-op sicuro).
    I valori restano clampati per evitare che tanti click consecutivi
    sbilancino lo scoring fuori scala."""
    effect = TRIP_REFINEMENT_EFFECTS.get(action)
    if effect is None:
        return dict(trip_weights), dict(adjustments)

    new_weights = dict(trip_weights)
    for k, delta in effect["trip_weights"].items():
        new_weights[k] = min(MAX_WEIGHT, new_weights.get(k, 0.0) + delta)

    new_adjustments = dict(adjustments)
    for k, delta in effect["adjustments"].items():
        if k == "ideal_days_bias":
            new_adjustments[k] = max(-0.6, min(0.6, new_adjustments.get(k, 0.0) + delta))
        else:
            new_adjustments[k] = max(0.1, min(3.0, new_adjustments.get(k, 1.0) + delta))
    return new_weights, new_adjustments


def ideal_stop_range(days_min: int | None, days_max: int | None) -> tuple[int, int]:
    """Numero di tappe consigliato (min, max) per la durata scelta, secondo
    DURATION_STOP_GUIDELINES. Linea guida non vincolante: generate_trip_candidates
    non la usa per escludere combinazioni, solo per penalizzarle in
    _stop_count_penalty quando la superano. Durata mancante o fuori da tutte
    le fasce (es. < 2 giorni) → fallback conservativo (1, 1): una sola tappa."""
    if not days_min or not days_max:
        return 1, 2
    mid = (days_min + days_max) / 2
    for lo, hi, smin, smax in DURATION_STOP_GUIDELINES:
        if lo <= mid <= hi:
            return smin, smax
    return (2, 5) if mid > 14 else (1, 1)


# ---------------------------------------------------------------------------
# Grafo delle rotte
# ---------------------------------------------------------------------------

def _route_index(routes_df: pd.DataFrame) -> dict[tuple[int, int], dict]:
    """Indice simmetrico: (a,b) e (b,a) puntano entrambi alla stessa rotta."""
    index: dict[tuple[int, int], dict] = {}
    for _, r in routes_df.iterrows():
        rec = r.to_dict()
        index[(r["origin_id"], r["destination_id"])] = rec
        index[(r["destination_id"], r["origin_id"])] = rec
    return index


def get_route(route_index: dict, a: int, b: int) -> dict | None:
    """Rotta tra le destinazioni a e b, in qualunque ordine (indice
    simmetrico). None se non esiste alcuna rotta autorata tra le due — il
    caso comune per la stragrande maggioranza delle coppie possibili, ed è
    esattamente ciò che impedisce al Trip Builder di generare combinazioni
    geograficamente assurde."""
    return route_index.get((a, b))


def _build_pairs(route_index: dict) -> list[tuple[int, int, dict]]:
    """Tutte le coppie di destinazioni con una rotta diretta, senza doppioni
    (a,b) e (b,a). L'ordine (origin_id, destination_id) di ogni rotta, così
    come autorato in trip_routes.py, diventa l'ordine di visita suggerito
    nell'itinerario."""
    seen = set()
    pairs = []
    for a, b in route_index:
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
        route = get_route(route_index, a, b)
        pairs.append((route["origin_id"], route["destination_id"], route))
    return pairs


def _build_triples(route_index: dict) -> list[tuple[int, int, int, dict, dict]]:
    """Catene A-B-C dove B fa da 'hub': servono rotte A-B e B-C autorate
    (non serve una rotta diretta A-C — è normale visitare la terza tappa
    passando per la seconda, es. Essaouira-Marrakech-Merzouga). Ogni
    combinazione di 3 tappe è deduplicata una sola volta indipendentemente
    da quale nodo funge da hub."""
    pairs = _build_pairs(route_index)
    by_node: dict[int, list[tuple[int, dict]]] = {}
    for a, b, route in pairs:
        by_node.setdefault(a, []).append((b, route))
        by_node.setdefault(b, []).append((a, route))

    triples = []
    seen = set()
    for hub, neighbors in by_node.items():
        for i in range(len(neighbors)):
            for j in range(len(neighbors)):
                if i == j:
                    continue
                a, route_a = neighbors[i]
                c, route_c = neighbors[j]
                if a == c:
                    continue
                key = (a, hub, c)
                key_rev = (c, hub, a)
                if key in seen or key_rev in seen:
                    continue
                seen.add(key)
                triples.append((a, hub, c, route_a, route_c))
    return triples


# ---------------------------------------------------------------------------
# Componenti del Feasibility Score
# ---------------------------------------------------------------------------

def _geographic_coherence(stops: list, edges: list[dict]) -> float:
    """Quanto ha senso il percorso geografico: parte da GEO_BASE_SCORE,
    sottrae una penalità proporzionale all'ora di viaggio media tra le tappe,
    e aggiunge un bonus se le tappe consecutive condividono il cluster
    geografico (vedi CLUSTER_BY_ID in destinations.py). Nessun trasferimento
    (destinazione singola) → punteggio pieno, il concetto non si applica."""
    if not edges:
        return 100.0
    same_cluster_hits = sum(1 for i in range(len(edges)) if stops[i]["cluster"] == stops[i + 1]["cluster"])
    bonus = (same_cluster_hits * GEO_SAME_CLUSTER_BONUS) / len(edges)
    avg_travel_time = sum(e["travel_time"] for e in edges) / len(edges)
    return max(0.0, min(100.0, GEO_BASE_SCORE - avg_travel_time * GEO_TRAVEL_TIME_PENALTY_PER_HOUR + bonus))


def _transport_feasibility(edges: list[dict], hop_penalty_mult: float) -> float:
    """Media della convenience_score delle rotte usate, meno una penalità
    per ogni cambio di mezzo oltre il primo (2 tappe = 1 rotta = 0 tappe
    intermedie = nessuna penalità; 3 tappe = 2 rotte = 1 cambio in più)."""
    if not edges:
        return 100.0
    avg_convenience = sum(e["convenience_score"] for e in edges) / len(edges)
    hop_penalty = (len(edges) - 1) * HOP_PENALTY_PER_EXTRA_HOP * hop_penalty_mult
    return max(0.0, min(100.0, avg_convenience - hop_penalty))


def _time_feasibility(stops: list, days_min: int | None, days_max: int | None, ideal_days_bias: float) -> float:
    """Il tempo disponibile basta per le tappe? Sotto la somma dei
    minimum_days → penalità severa (l'itinerario non ci sta fisicamente).
    Tra il minimo e l'ideale (eventualmente distorto da ideal_days_bias, es.
    "Più rilassato") → punteggio pieno. Oltre l'ideale → lieve decadimento
    con un pavimento, perché non è un problema di fattibilità vera e propria,
    solo un itinerario un po' "vuoto" per i giorni a disposizione."""
    total_min = sum(s["minimum_days"] for s in stops)
    total_ideal = sum(s["ideal_days"] for s in stops) * (1.0 + ideal_days_bias)
    available = (days_min + days_max) / 2 if (days_min and days_max) else total_ideal
    if available < total_min:
        return max(0.0, 100.0 - (total_min - available) * TIME_SHORTFALL_PENALTY_PER_DAY)
    if available <= total_ideal:
        return 100.0
    return max(TIME_SURPLUS_FLOOR, 100.0 - (available - total_ideal) * TIME_SURPLUS_PENALTY_PER_DAY)


# ---------------------------------------------------------------------------
# Costo dell'itinerario — funzioni pure componibili.
#
# Scomposto deliberatamente in pezzi piccoli e riusabili (invece di un unico
# blocco) per preparare il terreno a future estensioni come scenari di costo
# alternativi (es. "economico / medio / comodo" basati su comfort_level) o un
# breakdown dettagliato in UI/export: quel giorno basterà applicare un
# moltiplicatore a _local_costs_by_stop senza toccare _time_feasibility,
# score_trip o il resto del motore.
# ---------------------------------------------------------------------------

def _flight_in_cost(stops: list) -> tuple[float, float]:
    """Volo internazionale andata/ritorno verso la tappa d'ingresso (la
    prima della lista). Le tappe successive si raggiungono via trasferimenti
    locali (vedi _transport_cost_total), non con un nuovo volo internazionale."""
    first = stops[0]
    return first["flight_cost_min"], first["flight_cost_max"]


def _local_costs_by_stop(stops: list) -> list[dict]:
    """Costo locale (hotel + cibo + attività) per ciascuna tappa,
    separatamente — pensato per essere riusato sia nel totale sia in un
    futuro breakdown per tappa (UI o export)."""
    return [
        {
            "name": s["name"],
            "min": s["hotel_cost_min"] + s["food_cost_min"] + s["activity_cost_min"],
            "max": s["hotel_cost_max"] + s["food_cost_max"] + s["activity_cost_max"],
        }
        for s in stops
    ]


def _transport_cost_total(edges: list[dict]) -> float:
    """Costo dei trasferimenti interni, andata E ritorno: un itinerario
    multi-tappa tipicamente si chiude tornando verso il gateway per il volo
    di casa, quindi ogni tratta viene percorsa due volte."""
    return sum(e["transport_cost"] for e in edges) * 2


def compute_trip_cost_breakdown(stops: list, edges: list[dict]) -> dict[str, Any]:
    """Breakdown completo del costo di un itinerario: un solo volo
    internazionale andata/ritorno verso la tappa d'ingresso (il gateway) +
    costo locale di ogni tappa + trasferimenti interni andata/ritorno.
    Usare anche il flight_cost della tappa finale (pensato per un volo
    diretto lì da un hub generico) gonfierebbe artificialmente il costo di
    itinerari che finiscono in mete meno connesse (es. Cappadocia).

    Punto di estensione pubblico: sia il totale (_compute_trip_cost, usato
    da score_trip) sia qualunque futura UI/export di dettaglio costi
    dovrebbero passare da qui invece di ricalcolare i pezzi."""
    flight_min, flight_max = _flight_in_cost(stops)
    local_by_stop = _local_costs_by_stop(stops)
    local_min = sum(s["min"] for s in local_by_stop)
    local_max = sum(s["max"] for s in local_by_stop)
    transport = _transport_cost_total(edges)

    return {
        "flight_in_min": flight_min,
        "flight_in_max": flight_max,
        "local_by_stop": local_by_stop,
        "local_min": local_min,
        "local_max": local_max,
        "transport_total": transport,
        "total_min": flight_min + local_min + transport,
        "total_max": flight_max + local_max + transport,
    }


def _compute_trip_cost(stops: list, edges: list[dict]) -> tuple[float, float]:
    """Wrapper leggero su compute_trip_cost_breakdown per il solo uso interno
    di score_trip, che ha bisogno soltanto dei totali min/max."""
    breakdown = compute_trip_cost_breakdown(stops, edges)
    return breakdown["total_min"], breakdown["total_max"]


def _mood_coverage(stops: list, moods: list[str]) -> float:
    """Quanto bene l'itinerario nel suo insieme copre i mood richiesti:
    per ogni mood prende il MEGLIO tra le tappe (non la media), cosi' un
    itinerario complementare (una tappa forte su cultura/food, l'altra su
    avventura) viene premiato invece di essere penalizzato perche' nessuna
    singola tappa e' forte su tutto. E' proprio questo il meccanismo che fa
    del Trip Match Score qualcosa di piu' di una semplice media dei punteggi
    delle singole destinazioni: valuta la coerenza complessiva
    dell'esperienza, non solo la qualita' media di ogni tappa presa da sola.
    Nessun mood selezionato -> valore neutro (70), ne' premiante ne' punitivo."""
    valid_moods = [m for m in moods if m in MOOD_TO_FIELD]
    if not valid_moods:
        return 70.0
    best_per_mood = [max(MOOD_TO_FIELD[m](s) for s in stops) for m in valid_moods]
    return sum(best_per_mood) / len(best_per_mood)


def _budget_feasibility(total_cost_min: float, budget_max: float | None) -> float:
    """Dentro budget -> punteggio alto con una lieve differenziazione (piu'
    economico = leggermente meglio, cosi' il raffinamento "Piu' economico" ha
    un segnale su cui lavorare anche tra itinerari gia' tutti nel budget).
    Fuori budget -> crollo rapido proporzionale allo sforamento. Nessun
    budget massimo impostato -> valore neutro (70). Usa lo scenario Economico
    (total_cost_min), coerente con recommender._budget_match: Medio ed
    Elevato restano solo informativi, mai parte dello score."""
    if not budget_max or budget_max <= 0:
        return 70.0
    if total_cost_min <= budget_max:
        ratio = total_cost_min / max(budget_max, 1)
        return max(BUDGET_WITHIN_BUDGET_FLOOR, 100.0 - ratio * BUDGET_WITHIN_BUDGET_PENALTY_RATIO)
    overage = (total_cost_min - budget_max) / budget_max
    return max(0.0, 100.0 - overage * BUDGET_OVERAGE_PENALTY_RATIO)


def _season_compatibility(stops: list, period: str | None, custom_months: list[int] | None) -> float:
    """Il punto debole della catena: prende il MINIMO (non la media) tra le
    tappe, perché una singola tappa fuori stagione rovina la finestra
    temporale dell'intero itinerario — non basta che le altre siano perfette."""
    scores = [_season_match(s, period, custom_months) for s in stops]
    return min(scores) if scores else 100.0


def _transfer_time_penalty(edges: list[dict], total_ideal_days: float, mult: float) -> float:
    """Penalità diretta sul Feasibility Score se i trasferimenti assorbono
    troppo tempo rispetto ai giorni ideali di viaggio: sopra
    MAX_TRANSFER_FRACTION (35%) penalità piena, tra il 30% e quella soglia un
    preavviso più leggero. È il meccanismo esplicito richiesto dalla spec per
    "itinerari in cui >30-35% del tempo è assorbito dagli spostamenti"."""
    if not edges or total_ideal_days <= 0:
        return 0.0
    transfer_days_equiv = sum(e["travel_time"] for e in edges) / 24.0
    fraction = transfer_days_equiv / total_ideal_days
    if fraction > MAX_TRANSFER_FRACTION:
        return TRANSFER_PENALTY_HARD * mult
    if fraction > TRANSFER_FRACTION_WARNING:
        return TRANSFER_PENALTY_WARNING * mult
    return 0.0


def _stop_count_penalty(n_stops: int, days_min: int | None, days_max: int | None, mult: float) -> float:
    """Penalità se il numero di tappe eccede la linea guida per la durata
    scelta (ideal_stop_range) — non un limite duro, solo un disincentivo a
    "stipare" troppe tappe in poco tempo. Sotto la linea guida: nessuna
    penalità, meno tappe di quante ne "servirebbero" non è mai un problema."""
    _min_stops, max_stops = ideal_stop_range(days_min, days_max)
    if n_stops > max_stops:
        return max(0.0, STOP_COUNT_PENALTY_PER_EXTRA_STOP * (n_stops - max_stops) * (1.0 + mult))
    return 0.0


# ---------------------------------------------------------------------------
# Scoring completo di un itinerario
# ---------------------------------------------------------------------------

def score_trip(
    stops: list, edges: list[dict], prefs: dict[str, Any],
    weights: dict[str, float], boosts: dict[str, float],
    trip_weights: dict[str, float], adjustments: dict[str, float],
) -> dict[str, Any]:
    """Calcola i 3 punteggi di un itinerario in modo indipendente e
    trasparente (nessuno è derivato dagli altri):

    - feasibility_score: media pesata (FEASIBILITY_WEIGHTS) di coerenza
      geografica, fattibilità trasporti/tempo/budget e compatibilità
      stagionale, meno le penalità dirette per trasferimenti eccessivi e
      troppe tappe per la durata scelta.
    - efficiency_score: quota di tempo del viaggio spesa a esplorare (vs in
      trasferimento) — vedi il commento inline sotto.
    - trip_match_score: quanto l'itinerario nel suo insieme rispecchia le
      preferenze; NON una media dei punteggi delle singole tappe (vedi
      _mood_coverage) — combina qualità media, tappa più debole e copertura
      dei mood richiesti.

    `weights`/`boosts` sono gli stessi del motore a singola destinazione
    (recommender.py, riusati tappa per tappa via score_destination);
    `trip_weights`/`adjustments` sono specifici del Trip Builder e vengono
    modificati dal raffinamento rapido (apply_trip_refinement)."""
    days_min, days_max = prefs.get("duration_range", (None, None))

    geo = _geographic_coherence(stops, edges)
    transport = _transport_feasibility(edges, adjustments.get("hop_penalty_mult", 1.0))
    time_score = _time_feasibility(stops, days_min, days_max, adjustments.get("ideal_days_bias", 0.0))

    total_cost_min, total_cost_max = _compute_trip_cost(stops, edges)
    _budget_min, budget_max = prefs.get("budget_range", (None, None))
    budget = _budget_feasibility(total_cost_min, budget_max)

    season = _season_compatibility(stops, prefs.get("period"), prefs.get("custom_months"))

    feasibility = (
        geo * FEASIBILITY_WEIGHTS["geographic"]
        + transport * FEASIBILITY_WEIGHTS["transport"]
        + time_score * FEASIBILITY_WEIGHTS["time"]
        + budget * FEASIBILITY_WEIGHTS["budget"]
        + season * FEASIBILITY_WEIGHTS["season"]
    )

    total_ideal_days = sum(s["ideal_days"] for s in stops)
    feasibility -= _transfer_time_penalty(edges, total_ideal_days, adjustments.get("transfer_time_penalty_mult", 1.0))
    feasibility -= _stop_count_penalty(len(stops), days_min, days_max, adjustments.get("stop_count_penalty_mult", 1.0))
    feasibility = max(0.0, min(100.0, feasibility))

    # Travel Efficiency Score: quota del "tempo di viaggio" spesa a esplorare
    # invece che a spostarsi. exploration_days è la somma degli ideal_days
    # delle tappe; il tempo di trasferimento (ore) viene convertito in
    # giorni-equivalenti sulla stessa scala per poterli sommare nel denominatore.
    transfer_time_hours = sum(e["travel_time"] for e in edges)
    transfer_days_equiv = transfer_time_hours / 24.0
    exploration_days = total_ideal_days
    denom = exploration_days + transfer_days_equiv
    efficiency = (exploration_days / denom * 100.0) if denom > 0 else 100.0
    efficiency = max(0.0, min(100.0, efficiency))

    stop_scores = []
    stop_explanations = []
    for s in stops:
        score, _components, _all_weights = score_destination(s, prefs, weights, boosts)
        stop_scores.append(score)
        stop_explanations.append((s["name"], score))
    avg_stop = sum(stop_scores) / len(stop_scores)
    min_stop = min(stop_scores)
    mood_coverage = _mood_coverage(stops, prefs.get("moods", []))
    trip_match = (
        avg_stop * TRIP_MATCH_WEIGHTS["avg_stop"]
        + min_stop * TRIP_MATCH_WEIGHTS["min_stop"]
        + mood_coverage * TRIP_MATCH_WEIGHTS["mood_coverage"]
        + efficiency * TRIP_MATCH_WEIGHTS["efficiency"]
    )
    trip_match = max(0.0, min(100.0, trip_match))

    total_weight = sum(trip_weights.values()) or 1.0
    overall = (
        trip_match * trip_weights.get("trip_match", 0.0)
        + feasibility * trip_weights.get("feasibility", 0.0)
        + efficiency * trip_weights.get("efficiency", 0.0)
    ) / total_weight

    return {
        "overall_score": round(overall, 1),
        "trip_match_score": round(trip_match, 1),
        "feasibility_score": round(feasibility, 1),
        "efficiency_score": round(efficiency, 1),
        "geographic_coherence": round(geo, 1),
        "transport_feasibility": round(transport, 1),
        "time_feasibility": round(time_score, 1),
        "budget_feasibility": round(budget, 1),
        "season_compatibility": round(season, 1),
        "mood_coverage": round(mood_coverage, 1),
        "total_cost_min": total_cost_min,
        "total_cost_max": total_cost_max,
        "transfer_time_hours": transfer_time_hours,
        "transfer_cost": sum(e["transport_cost"] for e in edges),
        "ideal_days": total_ideal_days,
        "minimum_days": sum(s["minimum_days"] for s in stops),
        "stop_scores": stop_explanations,
    }


# Nota: la timeline giorno-per-giorno, le spiegazioni testuali e l'export
# vivono in trip_presentation.py, non qui (vedi docstring di modulo in cima
# al file) — build_day_by_day è stata spostata lì come generate_timeline().

TEMPLATE_BY_STOPSET = {frozenset(t["destinations"]): t for t in TRIP_TEMPLATES}


def _enrich_with_template(stop_ids: list[int]) -> dict | None:
    """Se le tappe corrispondono esattamente a un trip template curato (vedi
    trip_routes.RAW_TRIP_TEMPLATES), lo restituisce per arricchire nome/
    descrizione/difficoltà del candidato. I template sono esempi validati,
    non un elenco chiuso: generate_trip_candidates produce liberamente anche
    combinazioni non presenti qui, purché abbiano una rotta autorata."""
    return TEMPLATE_BY_STOPSET.get(frozenset(stop_ids))


# ---------------------------------------------------------------------------
# Generazione dei candidati
# ---------------------------------------------------------------------------

def generate_trip_candidates(
    dest_df: pd.DataFrame,
    prefs: dict[str, Any],
    weights: dict[str, float] | None = None,
    boosts: dict[str, float] | None = None,
    trip_weights: dict[str, float] | None = None,
    adjustments: dict[str, float] | None = None,
    routes_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Genera e valuta TUTTI gli itinerari di 2-3 tappe raggiungibili dalle
    rotte disponibili (trip_routes.py) — non un sottoinsieme filtrato per
    soglia: quella scelta spetta a get_top_trips. Funzione pura e
    deterministica: stesso dest_df/prefs/pesi -> stesso DataFrame in output,
    ordinato per overall_score decrescente (nessuna randomicità qui).

    Il "non inventare combinazioni assurde" non è un controllo esplicito in
    questa funzione: è una conseguenza diretta del fatto che le uniche
    coppie/triple considerate sono quelle con una rotta autorata
    (_build_pairs/_build_triples) — se una combinazione non è nel grafo delle
    rotte, semplicemente non viene mai generata.

    DataFrame vuoto se dest_df/routes_df non hanno destinazioni in comune
    (es. area geografica molto ristretta) o se routes_df è vuoto."""
    weights = weights or get_default_weights()
    boosts = boosts or get_default_boosts()
    trip_weights = trip_weights or get_default_trip_weights()
    adjustments = adjustments or get_default_trip_adjustments()
    routes_df = routes_df if routes_df is not None else load_routes_df()

    if routes_df.empty:
        return pd.DataFrame()

    id_to_row = {row["id"]: row for _, row in dest_df.iterrows()}
    route_index = _route_index(routes_df)

    records = []

    for a, b, route in _build_pairs(route_index):
        if a not in id_to_row or b not in id_to_row:
            continue
        stops = [id_to_row[a], id_to_row[b]]
        edges = [route]
        records.append(_build_trip_record(stops, edges, prefs, weights, boosts, trip_weights, adjustments))

    for a, hub, c, route_a, route_c in _build_triples(route_index):
        if a not in id_to_row or hub not in id_to_row or c not in id_to_row:
            continue
        stops = [id_to_row[a], id_to_row[hub], id_to_row[c]]
        edges = [route_a, route_c]
        records.append(_build_trip_record(stops, edges, prefs, weights, boosts, trip_weights, adjustments))

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    # kind="stable" + trip_id come chiave secondaria: a parità di
    # overall_score (frequente, gli score sono arrotondati a 1 decimale)
    # l'ordine di output resta lo stesso a ogni esecuzione, non dipende
    # dall'ordine di iterazione interno di un dizionario/route_index.
    df = df.sort_values(["overall_score", "trip_id"], ascending=[False, True], kind="stable").reset_index(drop=True)

    # Deduplica per insieme di tappe: con 3 destinazioni mutuamente connesse
    # (es. Venezia-Cortina-Bolzano) ogni scelta di "hub" genera un ordine di
    # visita diverso ma stesse mete. Teniamo solo l'ordine con punteggio
    # migliore, altrimenti il Top 3 mostrerebbe varianti quasi identiche.
    df["_stopset"] = df["stop_ids"].apply(lambda ids: frozenset(ids))
    df = df.drop_duplicates(subset="_stopset", keep="first").drop(columns="_stopset")

    return df.reset_index(drop=True)


def _build_trip_record(stops, edges, prefs, weights, boosts, trip_weights, adjustments) -> dict:
    """Assembla il record completo di un candidato: punteggi (score_trip) +
    identità/metadata (nome, template curato se esiste, tappe, rotte). Non
    contiene testo pensato per l'utente finale oltre al nome — le frasi
    descrittive vivono in trip_presentation.py."""
    result = score_trip(stops, edges, prefs, weights, boosts, trip_weights, adjustments)
    stop_ids = [int(s["id"]) for s in stops]
    template = _enrich_with_template(stop_ids)

    budget_max = prefs.get("budget_range", (None, None))[1]
    if budget_max:
        within_budget_buffer = result["total_cost_min"] <= budget_max * (1 + BUDGET_BUFFER_RATIO)
    else:
        within_budget_buffer = True

    if template:
        name = template["name"]
        description = template["description"]
        difficulty = template["difficulty"]
    else:
        name = " + ".join(s["name"] for s in stops)
        description = None
        difficulty = "media" if result["efficiency_score"] < 70 else "facile"

    return {
        "trip_id": template["trip_id"] if template else "-".join(str(i) for i in stop_ids),
        "name": name,
        "description": description,
        "is_template": template is not None,
        "stop_ids": stop_ids,
        "stop_names": [s["name"] for s in stops],
        "clusters": [s["cluster"] for s in stops],
        "difficulty": difficulty,
        "stops": stops,
        "edges": edges,
        "within_budget_buffer": within_budget_buffer,
        **result,
    }


def get_top_trips(
    dest_df: pd.DataFrame,
    prefs: dict[str, Any],
    weights: dict[str, float] | None = None,
    boosts: dict[str, float] | None = None,
    trip_weights: dict[str, float] | None = None,
    adjustments: dict[str, float] | None = None,
    top_n: int = 3,
    exclude_stopsets: set[frozenset] | None = None,
    over_budget_n: int = 3,
) -> dict[str, Any]:
    """Genera tutti i candidati (generate_trip_candidates, deterministico) e
    applica la soglia di Feasibility richiesta dalla spec: solo itinerari
    con feasibility_score >= FEASIBILITY_THRESHOLD (75) vengono mostrati per
    default. Se non ce ne sono abbastanza per riempire top_n, scende fino a
    FEASIBILITY_THRESHOLD_FALLBACK (60) come compromesso esplicito
    (used_compromise=True lo segnala al chiamante, che può avvisare
    l'utente). Se nemmeno il fallback basta, results contiene semplicemente
    meno di top_n righe — mai itinerari sotto la soglia di fallback.

    Gli itinerari oltre BUDGET_BUFFER_RATIO sopra il budget scelto non
    competono mai per "results" (stesso principio di recommender.
    get_recommendations): finiscono solo in "over_budget", per una sezione
    separata e leggera in fondo alla pagina.

    Ritorna sempre un dict con "results" (DataFrame, eventualmente vuoto),
    "strict_count", "used_compromise", "candidates_all" (l'intero pool
    generato, usato da surprise_trip e dalla UI per il conteggio totale),
    "over_budget" (i migliori itinerari oltre budget+buffer) e
    "budget_exhausted" (True se nessun itinerario rientra nel budget+buffer)."""
    candidates = generate_trip_candidates(dest_df, prefs, weights, boosts, trip_weights, adjustments)
    if candidates.empty:
        return {
            "results": candidates, "strict_count": 0, "used_compromise": False, "candidates_all": candidates,
            "over_budget": candidates, "budget_exhausted": False,
        }

    if exclude_stopsets:
        candidates = candidates[~candidates["stop_ids"].apply(lambda ids: frozenset(ids) in exclude_stopsets)]

    in_budget = candidates[candidates["within_budget_buffer"]]
    over_budget = candidates[~candidates["within_budget_buffer"]].sort_values("overall_score", ascending=False)

    strict = in_budget[in_budget["feasibility_score"] >= FEASIBILITY_THRESHOLD]
    strict_count = len(strict)

    if strict_count >= top_n:
        results = strict.head(top_n)
        used_compromise = False
    else:
        fallback = in_budget[
            (in_budget["feasibility_score"] >= FEASIBILITY_THRESHOLD_FALLBACK)
            & (in_budget["feasibility_score"] < FEASIBILITY_THRESHOLD)
        ]
        remaining = top_n - strict_count
        results = pd.concat([strict, fallback.head(remaining)])
        used_compromise = remaining > 0 and not fallback.empty

    return {
        "results": results.reset_index(drop=True),
        "over_budget": over_budget.head(over_budget_n).reset_index(drop=True),
        "budget_exhausted": in_budget.empty,
        "strict_count": strict_count,
        "used_compromise": used_compromise,
        "candidates_all": candidates,
    }


def surprise_trip(candidates_all: pd.DataFrame, exclude_stopsets: set[frozenset] | None = None, min_score: float = 65.0):
    """Sceglie un itinerario coerente ma meno ovvio (l'unica funzione di
    questo modulo con una componente casuale, di proposito). Filtra sempre
    per feasibility_score >= FEASIBILITY_THRESHOLD_FALLBACK — non propone
    mai un itinerario che il motore stesso considera poco fattibile, anche
    in modalità "sorpresa" — poi per overall_score >= min_score (soglia che
    scende gradualmente se il pool è vuoto). La scelta finale pesa le
    posizioni oltre il podio più di quelle in cima al ranking, così il
    risultato è quasi sempre diverso dal Top 3 già mostrato senza essere
    campato in aria. None se non esiste nessun candidato fattibile."""
    pool = candidates_all.copy()
    if exclude_stopsets:
        pool = pool[~pool["stop_ids"].apply(lambda ids: frozenset(ids) in exclude_stopsets)]
    pool = pool[pool["feasibility_score"] >= FEASIBILITY_THRESHOLD_FALLBACK]

    threshold = min_score
    candidates = pool[pool["overall_score"] >= threshold]
    while candidates.empty and threshold > 45:
        threshold -= 5
        candidates = pool[pool["overall_score"] >= threshold]

    if candidates.empty:
        return None

    candidates = candidates.sort_values("overall_score", ascending=False, kind="stable").reset_index(drop=True)
    weights_for_choice = [1.0 / (r + 2) if r >= 2 else 0.4 / (r + 2) for r in candidates.index]
    idx = random.choices(range(len(candidates)), weights=weights_for_choice, k=1)[0]
    return candidates.iloc[idx]


# ---------------------------------------------------------------------------
# Confronto tra viaggi combinati — stesso principio di
# recommender.compare_destinations, applicato ai record prodotti da questo
# modulo. Legge da candidates_all (l'intero pool generato, non solo il Top N
# mostrato) cosi' un viaggio selezionato per il confronto resta disponibile
# anche se un raffinamento successivo lo fa scendere in classifica.
# ---------------------------------------------------------------------------

TRIP_COMPARISON_COLUMNS: dict[str, str] = {
    "trip_match_score": "Match %",
    "efficiency_score": "Travel Efficiency %",
    "total_cost_min": "Costo min €",
    "total_cost_max": "Costo max €",
    "minimum_days": "Giorni minimi",
    "ideal_days": "Giorni ideali",
    "transfer_time_hours": "Trasferimento (h)",
    "mood_coverage": "Mood coverage",
}


def compare_trips(candidates_all: pd.DataFrame, trip_ids: list[str]) -> pd.DataFrame:
    subset = candidates_all[candidates_all["trip_id"].isin(trip_ids)].set_index("name")
    cols = [c for c in TRIP_COMPARISON_COLUMNS if c in subset.columns]
    table = subset[cols].rename(columns=TRIP_COMPARISON_COLUMNS)
    return table.T
