"""
Travel Estimates — stime di volo più precise in base alla città di
partenza (Milano/Roma), e stime approssimative di trasporti alternativi
(treno/bus/auto/traghetto) per le destinazioni italiane.

Principio guida esplicito: quando abbiamo un motivo concreto per pensare che
un numero cambi (es. Milano ha più voli low-cost diretti verso il Centro-Nord
Europa; Roma è il hub intercontinentale italiano) applichiamo un
aggiustamento dichiarato e modesto. In ogni altro caso restiamo sui valori
generici del dataset — mai una falsa precisione inventata.

Deliberatamente separato da recommender.py/trip_builder.py: questo modulo
non calcola nessun punteggio di match/feasibility, produce solo un
DataFrame con flight_hours/flight_cost aggiustati (stessa forma di
destinations.load_destinations_df()) che il motore, invariato, consuma
esattamente come consumerebbe quello generico. Nessuna chiamata di rete:
gli aggiustamenti sono heuristics dichiarate, non tariffe in tempo reale.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Aggiustamento voli per città di partenza
# ---------------------------------------------------------------------------

# Cluster italiani (vedi destinations.CLUSTER_BY_ID) raggruppati per area
# geografica di massima, usati solo per stimare se Milano o Roma sono
# "più vicine" — non è un dato nuovo, solo una lettura di cluster già
# esistenti.
_ITALY_NORD_CLUSTERS = {"Veneto-Dolomiti", "Nord Italia-Laghi"}
_ITALY_CENTRO_CLUSTERS = {"Centro Italia", "Toscana-Liguria"}
_ITALY_SUD_CLUSTERS = {"Sicilia", "Campania", "Sardegna", "Puglia"}


def _adjustment_factors(row: Any, departure_city: str) -> tuple[float, float]:
    """(fattore_ore, fattore_costo) da applicare a flight_hours/flight_cost.
    1.0 su entrambi = nessun aggiustamento, restano i valori generici."""
    region = row["region"]

    if region == "Italia":
        cluster = row.get("cluster")
        if departure_city == "milano" and cluster in _ITALY_NORD_CLUSTERS:
            return 0.75, 0.70
        if departure_city == "roma" and cluster in _ITALY_CENTRO_CLUSTERS:
            return 0.75, 0.70
        if departure_city == "roma" and cluster in _ITALY_SUD_CLUSTERS:
            return 0.85, 0.80
        return 1.0, 1.0

    # Milano (Malpensa/Bergamo): più voli low-cost diretti verso l'Europa.
    if region == "Europa" and departure_city == "milano":
        return 0.92, 0.88
    # Roma (Fiumicino): hub intercontinentale, più diretti long-haul.
    if region == "Extra-Europa" and departure_city == "roma":
        return 0.92, 0.90

    return 1.0, 1.0


def adjust_destinations_for_departure(df: pd.DataFrame, departure_city: str | None) -> pd.DataFrame:
    """Restituisce una copia del DataFrame destinazioni con flight_hours e
    flight_cost_min/max (e i total_cost derivati) aggiustati per la città di
    partenza scelta. departure_city None (o non "milano"/"roma") -> il
    DataFrame torna invariato: è il caso "Altro / Indifferente", dove
    restiamo sui valori generici per definizione."""
    if departure_city not in ("milano", "roma"):
        return df

    df = df.copy()
    factors = df.apply(lambda r: _adjustment_factors(r, departure_city), axis=1)
    hours_factor = factors.apply(lambda t: t[0])
    cost_factor = factors.apply(lambda t: t[1])

    df["flight_hours"] = df["flight_hours"] * hours_factor
    df["flight_cost_min"] = df["flight_cost_min"] * cost_factor
    df["flight_cost_max"] = df["flight_cost_max"] * cost_factor

    df["total_cost_min"] = df["flight_cost_min"] + df["hotel_cost_min"] + df["food_cost_min"] + df["activity_cost_min"]
    df["total_cost_max"] = df["flight_cost_max"] + df["hotel_cost_max"] + df["food_cost_max"] + df["activity_cost_max"]

    return df


# ---------------------------------------------------------------------------
# Trasporti alternativi al volo — Italia (treno/bus/auto, + traghetto per le
# isole maggiori), Europa "raggiungibile via terra" dall'Italia (treno/bus/
# auto con fattori più alti: un confine internazionale in più costa tempo),
# e una manciata di traghetti internazionali realmente esistenti, dichiarati
# come tali (non stimati per distanza) perché sono rotte note e comode:
# Ancona-Patrasso per la Grecia continentale, Pozzallo-Malta, Bari-Durazzo.
# Per il resto dell'estero (Extra-Europa, Scandinavia/Islanda/Artico troppo
# lontani via terra) un'alternativa del genere non è quasi mai sensata su un
# viaggio vacanza standard, quindi non viene proposta.
# ---------------------------------------------------------------------------

_ISLAND_CLUSTERS = {"Sicilia", "Sardegna"}

# (fattore_ore_min, fattore_ore_max), (fattore_costo_min, fattore_costo_max)
# applicati a flight_hours/flight_cost_min/max: stime di massima basate
# sulla distanza (non su orari reali), dichiarate come tali in UI.
_TRANSPORT_MODELS = [
    ("Treno", "🚄", (2.2, 3.8), (0.30, 0.60)),
    ("Bus", "🚌", (2.8, 4.5), (0.15, 0.35)),
    ("Auto (stima carburante e pedaggi)", "🚗", (2.5, 4.2), (0.35, 0.70)),
]
_FERRY_MODEL = ("Traghetto", "⛴️", (4.0, 7.0), (0.25, 0.55))

# Cluster europei con un collegamento ferroviario internazionale ragionevole
# dall'Italia (vedi destinations.CLUSTER_BY_ID): fattori più alti di quelli
# italiani perché un viaggio via terra tra paesi diversi richiede tipicamente
# più cambi e più ore rispetto a una tratta interna.
_EUROPE_RAIL_CLUSTERS = {
    "Francia", "Catalogna", "Europa Centrale", "Tirolo", "Svizzera",
    "Germania", "Benelux", "Polonia",
}
_EUROPE_RAIL_MODELS = [
    ("Treno", "🚄", (3.4, 6.0), (0.35, 0.65)),
    ("Bus", "🚌", (4.2, 7.0), (0.18, 0.38)),
    ("Auto (stima carburante e pedaggi)", "🚗", (4.0, 6.5), (0.40, 0.75)),
]

# Balcani: rete ferroviaria internazionale poco praticabile per un turista,
# quindi solo bus/auto (nessun treno).
_EUROPE_ROAD_ONLY_CLUSTERS = {"Balcani"}
_EUROPE_ROAD_ONLY_MODELS = [
    ("Bus", "🚌", (4.5, 7.5), (0.18, 0.38)),
    ("Auto (stima carburante e pedaggi)", "🚗", (4.2, 7.0), (0.40, 0.75)),
]

# Traghetti internazionali reali usati come alternativa al volo per poche
# destinazioni specifiche: valori dichiarati (rotta nota), non scalati da
# flight_hours come il resto — scalare linearmente darebbe stime assurde per
# rotte via mare molto più lunghe di un volo diretto.
_EXPLICIT_FERRY_ROUTES: dict[int, dict[str, Any]] = {
    34: dict(mode="Traghetto (Ancona-Patrasso)", icon="⛴️", hours=(20.0, 24.0), cost=(90, 150)),  # Atene
    37: dict(mode="Traghetto (Pozzallo-Malta)", icon="⛴️", hours=(8.0, 10.0), cost=(60, 110)),  # Malta
    77: dict(mode="Traghetto (Bari-Durazzo)", icon="⛴️", hours=(9.0, 11.0), cost=(70, 120)),  # Tirana
}


def _scaled_transport_options(
    models: list, flight_hours: float, flight_cost_min: float, flight_cost_max: float
) -> list[dict[str, Any]]:
    return [
        {
            "mode": mode,
            "icon": icon,
            "hours_min": flight_hours * hours_factors[0],
            "hours_max": flight_hours * hours_factors[1],
            "cost_min": flight_cost_min * cost_factors[0],
            "cost_max": flight_cost_max * cost_factors[1],
        }
        for mode, icon, hours_factors, cost_factors in models
    ]


def estimate_alternative_transports(row: Any) -> list[dict[str, Any]]:
    """Alternative al volo per una destinazione, quando ha senso mostrarle:
    Italia (tutte), Europa raggiungibile via terra per cluster (vedi sopra),
    più le rotte di traghetto internazionali dichiarate esplicitamente.
    Stima approssimativa scalando flight_hours/flight_cost già presenti —
    nessun nuovo dato, nessun orario reale — tranne per i traghetti espliciti,
    che sono rotte note e quindi dichiarate come tali."""
    flight_hours = row["flight_hours"]
    flight_cost_min = row["flight_cost_min"]
    flight_cost_max = row["flight_cost_max"]
    cluster = row.get("cluster")

    options: list[dict[str, Any]] = []
    if row["region"] == "Italia":
        models = list(_TRANSPORT_MODELS)
        if cluster in _ISLAND_CLUSTERS:
            models.append(_FERRY_MODEL)
        options.extend(_scaled_transport_options(models, flight_hours, flight_cost_min, flight_cost_max))
    elif row["region"] == "Europa" and cluster in _EUROPE_RAIL_CLUSTERS:
        options.extend(_scaled_transport_options(_EUROPE_RAIL_MODELS, flight_hours, flight_cost_min, flight_cost_max))
    elif row["region"] == "Europa" and cluster in _EUROPE_ROAD_ONLY_CLUSTERS:
        options.extend(_scaled_transport_options(_EUROPE_ROAD_ONLY_MODELS, flight_hours, flight_cost_min, flight_cost_max))

    explicit = _EXPLICIT_FERRY_ROUTES.get(int(row["id"]))
    if explicit:
        options.append({
            "mode": explicit["mode"],
            "icon": explicit["icon"],
            "hours_min": explicit["hours"][0],
            "hours_max": explicit["hours"][1],
            "cost_min": explicit["cost"][0],
            "cost_max": explicit["cost"][1],
        })

    return options
