"""
Motore di raccomandazione di TravelMatch.

Indipendente da Streamlit: prende un DataFrame di destinazioni (vedi
destinations.py) e un dizionario di preferenze utente, e restituisce le
destinazioni ordinate per Travel Match Score (0-100), con spiegazione.

I pesi sono centralizzati in DEFAULT_WEIGHTS e DEFAULT_BOOSTS: modificarli
qui (o passarne una copia modificata a get_recommendations) cambia il
comportamento del motore senza toccare il resto del codice.
"""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from utils import (
    AREA_TO_REGIONS,
    COMFORT_TO_LEVEL,
    NORTH_AFRICA_COUNTRIES,
)

# ---------------------------------------------------------------------------
# Pesi centralizzati
# ---------------------------------------------------------------------------

# Pesi delle componenti "primarie" del Travel Match Score. Devono sommare
# (indicativamente) a 1.0: la normalizzazione finale rende comunque lo score
# sempre confrontabile anche se i pesi vengono alterati dal raffinamento.
DEFAULT_WEIGHTS: dict[str, float] = {
    "budget": 0.20,
    "mood": 0.20,
    "climate": 0.15,
    "season": 0.10,
    "duration": 0.10,
    "social": 0.10,
    "comfort": 0.05,
    "distance": 0.10,
}

# Pesi delle componenti "secondarie" (bonus mirati), attivate/aumentate dai
# pulsanti di raffinamento rapido. Partono da 0: se non richiesti, non
# influenzano lo score.
DEFAULT_BOOSTS: dict[str, float] = {
    "romantic": 0.0,
    "adventure": 0.0,
    "relax": 0.0,
    "food": 0.0,
    "luxury": 0.0,
    "snow": 0.0,
    "warm": 0.0,
}

MAX_WEIGHT = 0.6  # clamp di sicurezza per evitare pesi fuori scala dopo tanti click

REFINEMENT_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "cheaper": {"weights": {"budget": 0.10}, "boosts": {}},
    "warmer": {"weights": {"climate": 0.08}, "boosts": {"warm": 0.14}},
    "snowier": {"weights": {"climate": 0.08}, "boosts": {"snow": 0.16}},
    "closer": {"weights": {"distance": 0.12}, "boosts": {}},
    "romantic": {"weights": {}, "boosts": {"romantic": 0.16}},
    "social": {"weights": {"social": 0.12}, "boosts": {}},
    "adventure": {"weights": {}, "boosts": {"adventure": 0.16}},
    "relax": {"weights": {}, "boosts": {"relax": 0.16}},
    "food": {"weights": {}, "boosts": {"food": 0.16}},
    "luxury": {"weights": {"comfort": 0.05}, "boosts": {"luxury": 0.16}},
}

MOOD_TO_FIELD = {
    "nature_adventure": lambda r: (r["nature_score"] + r["adventure_score"]) / 2,
    "relax_beach": lambda r: r["relax_score"],
    "city_culture": lambda r: r["culture_score"],
    "party_nightlife": lambda r: r["nightlife_score"],
    "snow_mountain": lambda r: (r["snow_score"] + r["nature_score"]) / 2,
    "romantic": lambda r: r["romantic_score"],
    "family": lambda r: max(0, min(100,
        r["relax_score"] * 0.4 + r["culture_score"] * 0.3 + r["nature_score"] * 0.3 - r["nightlife_score"] * 0.15)),
    "food": lambda r: r["food_score"],
    "wellness": lambda r: max(0, min(100, r["relax_score"] * 0.7 + (20 if "wellness" in r["tags"] else 0))),
    "shopping": lambda r: 85 if "shopping" in r["tags"] else max(20, r["luxury_score"] * 0.4),
    "unique": lambda r: 90 if "esperienze insolite" in r["tags"] else (r["nature_score"] + r["adventure_score"]) / 2 * 0.6,
}

CLIMATE_TO_FIELD = {
    "warm": "warm_score",
    "temperate": "temperate_score",
    "cold": "cold_score",
    "snow": "snow_score",
    "tropical": "warm_score",
}

PERIOD_TO_MONTHS = {
    "🎄 Natale": [12],
    "🎆 Capodanno": [1],
    "🎄🎆 Natale + Capodanno": [12, 1],
    "🌸 Primavera": [3, 4, 5],
    "☀️ Estate": [6, 7, 8],
    "🍂 Autunno": [9, 10, 11],
    "🏃 Weekend": None,
    "📅 Date personalizzate": None,
}

CHRISTMAS_LIKE_PERIODS = {"🎄 Natale", "🎆 Capodanno", "🎄🎆 Natale + Capodanno"}


def get_default_weights() -> dict[str, float]:
    return dict(DEFAULT_WEIGHTS)


def get_default_boosts() -> dict[str, float]:
    return dict(DEFAULT_BOOSTS)


def apply_refinement(weights: dict[str, float], boosts: dict[str, float], action: str) -> tuple[dict[str, float], dict[str, float]]:
    """Restituisce nuove copie di weights/boosts con l'effetto di un pulsante di raffinamento applicato."""
    effect = REFINEMENT_EFFECTS.get(action)
    if effect is None:
        return dict(weights), dict(boosts)

    new_weights = dict(weights)
    new_boosts = dict(boosts)
    for k, delta in effect["weights"].items():
        new_weights[k] = min(MAX_WEIGHT, new_weights.get(k, 0.0) + delta)
    for k, delta in effect["boosts"].items():
        new_boosts[k] = min(MAX_WEIGHT, new_boosts.get(k, 0.0) + delta)
    return new_weights, new_boosts


# ---------------------------------------------------------------------------
# Filtro geografico
# ---------------------------------------------------------------------------

def filter_by_area(df: pd.DataFrame, area_key: str) -> pd.DataFrame:
    if area_key in ("mondo", "nessun_limite") or area_key is None:
        return df

    if area_key == "europa_nordafrica":
        base = df[df["region"].isin({"Italia", "Europa"})]
        extra = df[(df["region"] == "Extra-Europa") & (df["country"].isin(NORTH_AFRICA_COUNTRIES))]
        return pd.concat([base, extra]).sort_index()

    allowed_regions = AREA_TO_REGIONS.get(area_key, {"Italia", "Europa", "Extra-Europa"})
    return df[df["region"].isin(allowed_regions)]


# ---------------------------------------------------------------------------
# Componenti dello score (ognuna 0-100)
# ---------------------------------------------------------------------------

def _budget_match(row, budget_min: float, budget_max: float) -> float:
    if budget_max is None or budget_max <= 0:
        return 70.0
    cost_mid = (row["total_cost_min"] + row["total_cost_max"]) / 2
    if cost_mid <= budget_max:
        ratio = cost_mid / max(budget_max, 1)
        return max(70.0, 100.0 - ratio * 15.0)
    overage = (cost_mid - budget_max) / budget_max
    return max(0.0, 100.0 - overage * 140.0)


def _mood_match(row, moods: list[str], tags: list[str]) -> float:
    mood_scores = [MOOD_TO_FIELD[m](row) for m in moods if m in MOOD_TO_FIELD]
    mood_component = sum(mood_scores) / len(mood_scores) if mood_scores else None

    if tags:
        overlap = len(set(tags) & set(row["tags"]))
        tag_component = min(100.0, (overlap / len(tags)) * 100.0 + (10 if overlap else 0))
    else:
        tag_component = None

    if mood_component is not None and tag_component is not None:
        return 0.7 * mood_component + 0.3 * tag_component
    if mood_component is not None:
        return mood_component
    if tag_component is not None:
        return tag_component
    return 60.0


def _climate_match(row, climates: list[str]) -> float:
    if not climates:
        return 65.0
    values = [row[CLIMATE_TO_FIELD[c]] for c in climates if c in CLIMATE_TO_FIELD]
    return sum(values) / len(values) if values else 65.0


def _season_match(row, period: str | None, custom_months: list[int] | None) -> float:
    if period == "📅 Date personalizzate":
        req_months = custom_months
    else:
        req_months = PERIOD_TO_MONTHS.get(period)

    if not req_months:
        base = 85.0
    else:
        overlap = set(req_months) & set(row["best_months"])
        base = 100.0 if overlap else 45.0

    if period in CHRISTMAS_LIKE_PERIODS or (custom_months and (12 in custom_months or 1 in custom_months)):
        wants_christmas = period in ("🎄 Natale", "🎄🎆 Natale + Capodanno") or (custom_months and 12 in custom_months)
        wants_newyear = period in ("🎆 Capodanno", "🎄🎆 Natale + Capodanno") or (custom_months and 1 in custom_months)

        festive_components = []
        if wants_christmas:
            festive_components.append(max(row["christmas_score"], row["warm_score"] * 0.6))
        if wants_newyear:
            festive_components.append(max(row["new_year_score"], row["warm_score"] * 0.6))
        if festive_components:
            festive_score = sum(festive_components) / len(festive_components)
            base = 0.55 * base + 0.45 * festive_score

    return max(0.0, min(100.0, base))


def _duration_match(row, days_min: int | None, days_max: int | None) -> float:
    if days_min is None or days_max is None:
        return 75.0
    dest_min, dest_max = row["days_min"], row["days_max"]
    overlap_start = max(days_min, dest_min)
    overlap_end = min(days_max, dest_max)
    if overlap_start <= overlap_end:
        union = max(days_max, dest_max) - min(days_min, dest_min)
        overlap = overlap_end - overlap_start
        return 80.0 + 20.0 * (overlap / union if union > 0 else 1.0)
    gap = max(days_min - dest_max, dest_min - days_max, 0)
    return max(15.0, 80.0 - gap * 10.0)


def _social_match(row, social_slider: float | None) -> float:
    if social_slider is None:
        return 70.0
    dest_social_pct = row["social_level"] * 20.0
    return max(0.0, 100.0 - abs(social_slider - dest_social_pct) * 1.1)


def _comfort_match(row, comfort_key: str | None) -> float:
    if not comfort_key:
        return 75.0
    user_level = COMFORT_TO_LEVEL.get(comfort_key, 3)
    diff = abs(user_level - row["comfort_level"])
    return max(0.0, 100.0 - diff * 22.0)


def _distance_match(row, max_flight_hours: float | None) -> float:
    if not max_flight_hours or max_flight_hours >= 999:
        return 100.0
    if row["flight_hours"] <= max_flight_hours:
        return 100.0
    return max(0.0, 100.0 - (row["flight_hours"] - max_flight_hours) * 18.0)


COMPONENT_LABELS = {
    "budget": "il tuo budget",
    "mood": "il mood che cerchi",
    "climate": "il clima desiderato",
    "season": "il periodo scelto",
    "duration": "la durata del viaggio",
    "social": "la socialità che cerchi",
    "comfort": "il livello di comfort",
    "distance": "la distanza di volo preferita",
    "romantic": "l'atmosfera romantica",
    "adventure": "la voglia di avventura",
    "relax": "la voglia di relax",
    "food": "la passione per il cibo",
    "luxury": "la ricerca di lusso ed esclusività",
    "snow": "la voglia di neve",
    "warm": "la voglia di caldo",
}


def _compute_components(row, prefs: dict[str, Any]) -> dict[str, float]:
    budget_min, budget_max = prefs.get("budget_range", (None, None))
    days_min, days_max = prefs.get("duration_range", (None, None))
    return {
        "budget": _budget_match(row, budget_min, budget_max),
        "mood": _mood_match(row, prefs.get("moods", []), prefs.get("tags", [])),
        "climate": _climate_match(row, prefs.get("climate", [])),
        "season": _season_match(row, prefs.get("period"), prefs.get("custom_months")),
        "duration": _duration_match(row, days_min, days_max),
        "social": _social_match(row, prefs.get("social_slider")),
        "comfort": _comfort_match(row, prefs.get("comfort")),
        "distance": _distance_match(row, prefs.get("max_flight_hours")),
        "romantic": row["romantic_score"],
        "adventure": row["adventure_score"],
        "relax": row["relax_score"],
        "food": row["food_score"],
        "luxury": row["luxury_score"],
        "snow": row["snow_score"],
        "warm": row["warm_score"],
    }


def score_destination(row, prefs: dict[str, Any], weights: dict[str, float], boosts: dict[str, float]) -> tuple[float, dict[str, float], dict[str, float]]:
    components = _compute_components(row, prefs)
    all_weights = {**weights, **boosts}
    total_weight = sum(all_weights.values()) or 1.0
    score = sum(components[k] * w for k, w in all_weights.items()) / total_weight
    return round(max(0.0, min(100.0, score)), 1), components, all_weights


NEUTRAL_BASELINE = 70.0  # valore "generico" che una componente assume quando non differenzia le destinazioni


def explain_match(row, components: dict[str, float], weights: dict[str, float], top_n: int = 3) -> str:
    # Ordiniamo per quanto una componente si discosta (in positivo) da un valore neutro,
    # pesato per la sua importanza: cosi' evidenziamo cio' che e' davvero distintivo per
    # questa destinazione, non le componenti sempre alte per costruzione (es. "nessun limite").
    contributions = sorted(
        ((k, (components[k] - NEUTRAL_BASELINE) * weights.get(k, 0.0)) for k in components if weights.get(k, 0.0) > 0),
        key=lambda kv: kv[1], reverse=True,
    )
    top_keys = [k for k, score in contributions[:top_n] if components[k] >= 55 and score > 0]
    if not top_keys:
        return f"{row['name']} è una scelta solida, anche se non perfettamente allineata a tutte le tue preferenze."

    labels = [COMPONENT_LABELS.get(k, k) for k in top_keys]
    if len(labels) == 1:
        joined = labels[0]
    else:
        joined = ", ".join(labels[:-1]) + " e " + labels[-1]
    return f"Ti abbiamo proposto {row['name']} soprattutto per {joined}."


# ---------------------------------------------------------------------------
# Motore principale
# ---------------------------------------------------------------------------

def _meets_strict_criteria(row, prefs: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    budget_min, budget_max = prefs.get("budget_range", (None, None))
    if budget_max:
        cost_mid = (row["total_cost_min"] + row["total_cost_max"]) / 2
        if cost_mid > budget_max * 1.15:
            reasons.append("budget")

    max_flight_hours = prefs.get("max_flight_hours")
    if max_flight_hours and max_flight_hours < 999 and row["flight_hours"] > max_flight_hours:
        reasons.append("distanza di volo")

    days_min, days_max = prefs.get("duration_range", (None, None))
    if days_min and days_max:
        if row["days_max"] < days_min or row["days_min"] > days_max:
            reasons.append("durata")

    period = prefs.get("period")
    req_months = prefs.get("custom_months") if period == "📅 Date personalizzate" else PERIOD_TO_MONTHS.get(period)
    if req_months and not (set(req_months) & set(row["best_months"])):
        reasons.append("periodo")

    return (len(reasons) == 0), reasons


def score_all(df: pd.DataFrame, prefs: dict[str, Any], weights: dict[str, float], boosts: dict[str, float]) -> pd.DataFrame:
    filtered = filter_by_area(df, prefs.get("area"))
    if filtered.empty:
        filtered = df

    records = []
    for _, row in filtered.iterrows():
        score, components, all_weights = score_destination(row, prefs, weights, boosts)
        meets_strict, fail_reasons = _meets_strict_criteria(row, prefs)
        explanation = explain_match(row, components, all_weights)
        records.append({
            "id": row["id"],
            "match_score": score,
            "meets_strict": meets_strict,
            "compromise_reasons": fail_reasons,
            "explanation": explanation,
        })

    scored = pd.DataFrame(records)
    result = filtered.merge(scored, on="id")
    return result.sort_values("match_score", ascending=False).reset_index(drop=True)


def get_recommendations(
    df: pd.DataFrame,
    prefs: dict[str, Any],
    weights: dict[str, float] | None = None,
    boosts: dict[str, float] | None = None,
    top_n: int = 5,
    exclude_ids: set[int] | None = None,
) -> dict[str, Any]:
    """Restituisce le migliori destinazioni per le preferenze date.

    Ritorna un dizionario con:
      - "results": DataFrame ordinato (fino a top_n righe)
      - "strict_count": quante destinazioni rispettano tutti i criteri
      - "used_compromise": True se sono stati inclusi risultati di compromesso
      - "scored_all": DataFrame con TUTTE le destinazioni valutate (per Sorprendimi/confronto)
    """
    weights = weights or get_default_weights()
    boosts = boosts or get_default_boosts()

    scored = score_all(df, prefs, weights, boosts)
    if exclude_ids:
        scored = scored[~scored["id"].isin(exclude_ids)]

    strict = scored[scored["meets_strict"]]
    strict_count = len(strict)

    if strict_count >= top_n:
        results = strict.head(top_n)
        used_compromise = False
    else:
        remaining_slots = top_n - strict_count
        compromise_pool = scored[~scored["meets_strict"]]
        results = pd.concat([strict, compromise_pool.head(remaining_slots)])
        used_compromise = remaining_slots > 0 and not compromise_pool.empty

    return {
        "results": results.reset_index(drop=True),
        "strict_count": strict_count,
        "used_compromise": used_compromise,
        "scored_all": scored,
    }


def surprise_me(
    scored_all: pd.DataFrame,
    exclude_ids: set[int] | None = None,
    min_score: float = 65.0,
    seed: int | None = None,
) -> pd.Series | None:
    """Sceglie una destinazione coerente ma meno ovvia (match >= min_score)."""
    pool = scored_all.copy()
    if exclude_ids:
        pool = pool[~pool["id"].isin(exclude_ids)]

    threshold = min_score
    candidates = pool[pool["match_score"] >= threshold]
    while candidates.empty and threshold > 45:
        threshold -= 5
        candidates = pool[pool["match_score"] >= threshold]

    if candidates.empty:
        candidates = pool

    if candidates.empty:
        return None

    # Favorisce le mete "meno scontate": pesa la scelta random inversamente
    # rispetto al rango (le prime posizioni assolute sono meno probabili),
    # ma resta comunque coerente grazie al filtro min_score.
    candidates = candidates.sort_values("match_score", ascending=False).reset_index(drop=True)
    ranks = candidates.index.to_numpy()
    weights_for_choice = [1.0 / (r + 2) for r in ranks]  # rank 0 pesa meno di rank 5, 10...
    # invertiamo leggermente per favorire la "coda alta ma non il podio assoluto"
    mid_bias = [w if r >= 3 else w * 0.4 for r, w in zip(ranks, weights_for_choice)]

    rng = random.Random(seed)
    chosen_idx = rng.choices(range(len(candidates)), weights=mid_bias, k=1)[0]
    return candidates.iloc[chosen_idx]


def get_christmas_categories(scored_all: pd.DataFrame, top_n: int = 4) -> dict[str, pd.DataFrame]:
    """Divide le destinazioni in 'Fuga al caldo' e 'Winter Wonderland' per la modalità Natale/Capodanno."""
    warm_escape = scored_all[scored_all["warm_score"] >= 60].sort_values(
        ["warm_score", "match_score"], ascending=False
    ).head(top_n)
    winter_wonderland = scored_all[
        (scored_all["snow_score"] >= 50) | (scored_all["christmas_score"] >= 70)
    ].sort_values(["christmas_score", "match_score"], ascending=False).head(top_n)
    return {"fuga_al_caldo": warm_escape, "winter_wonderland": winter_wonderland}


COMPARISON_COLUMNS = {
    "match_score": "Match %",
    "total_cost_min": "Budget min €",
    "total_cost_max": "Budget max €",
    "temp_min": "Temp min °C",
    "temp_max": "Temp max °C",
    "days_min": "Giorni min",
    "days_max": "Giorni max",
    "social_level": "Socialità (1-5)",
    "adventure_score": "Avventura",
    "relax_score": "Relax",
    "culture_score": "Cultura",
    "flight_hours": "Ore di volo",
}


def compare_destinations(scored_all: pd.DataFrame, ids: list[int]) -> pd.DataFrame:
    subset = scored_all[scored_all["id"].isin(ids)].set_index("name")
    cols = [c for c in COMPARISON_COLUMNS if c in subset.columns]
    table = subset[cols].rename(columns=COMPARISON_COLUMNS)
    return table.T
