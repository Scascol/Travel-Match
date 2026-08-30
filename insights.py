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
# Travel DNA vs destinazione — mette a confronto il profilo dell'utente
# (utils.compute_travel_dna) con quello della meta, sulle stesse dimensioni.
# Serve a rispondere alla domanda "questa meta mi somiglia?", che il solo
# match % non racconta: due mete all'80% possono somigliarmi per ragioni
# opposte.
# ---------------------------------------------------------------------------

# Le chiavi sono quelle del Travel DNA (vedi utils.compute_travel_dna); i
# valori il campo corrispondente nel dataset. Non tutte le dimensioni del DNA
# hanno un gemello nel dataset e viceversa: teniamo solo quelle confrontabili
# davvero, perché un confronto inventato sarebbe peggio di un confronto in meno.
DNA_TO_DESTINATION_FIELD: dict[str, str] = {
    "🥾 Adventure": "adventure_score",
    "🌿 Nature": "nature_score",
    "🍝 Food": "food_score",
    "🎉 Social": "social_level",
    "🏖️ Relax": "relax_score",
    "💎 Luxury": "luxury_score",
    "🏛️ Culture": "culture_score",
    "❤️ Romance": "romantic_score",
    "🏔️ Snow": "snow_score",
    "☀️ Warmth": "warm_score",
}

# Sotto questa differenza consideriamo utente e meta "allineati": non è una
# soglia statistica, è la sensibilità oltre la quale uno scarto diventa
# percepibile leggendo due barre affiancate.
DNA_ALIGNMENT_TOLERANCE = 18.0


def _destination_trait_value(row: Any, field: str) -> float:
    """social_level è 1-5 nel dataset, tutto il resto è 0-100: normalizziamo
    qui, come fa travel_style_scores, così il confronto è sempre omogeneo."""
    value = row[field]
    return value * 20 if field == "social_level" else value


def dna_vs_destination(dna: dict[str, int] | None, row: Any) -> list[dict[str, Any]]:
    """Confronto dimensione per dimensione tra Travel DNA e destinazione.

    Ogni voce contiene il valore utente, quello della meta e uno stato:
    "match" (allineati), "destination_higher" (la meta offre più di quanto
    cerchi — non è un difetto, è un di più) o "user_higher" (la meta offre
    meno di quanto cerchi: è qui che nascono le delusioni)."""
    if not dna:
        return []
    rows = []
    for trait, field in DNA_TO_DESTINATION_FIELD.items():
        if trait not in dna or field not in row:
            continue
        user_value = float(dna[trait])
        dest_value = float(_destination_trait_value(row, field))
        delta = dest_value - user_value
        if abs(delta) <= DNA_ALIGNMENT_TOLERANCE:
            status = "match"
        elif delta > 0:
            status = "destination_higher"
        else:
            status = "user_higher"
        rows.append({
            "trait": trait, "user": user_value, "destination": dest_value,
            "delta": delta, "status": status,
        })
    return rows


def dna_alignment_summary(dna: dict[str, int] | None, row: Any) -> str | None:
    """Una frase sul rapporto tra il DNA dell'utente e la meta: cosa combacia
    e, se c'è, l'unico scarto che vale la pena nominare. Silenzio (None) se
    non c'è un DNA: meglio non dire nulla che dire una banalità."""
    comparison = dna_vs_destination(dna, row)
    if not comparison:
        return None

    matches = [c for c in comparison if c["status"] == "match"]
    # Ordiniamo per valore utente: uno scarto su un tratto che all'utente
    # interessa poco non merita di essere segnalato come "mancanza".
    gaps = sorted(
        [c for c in comparison if c["status"] == "user_higher"],
        key=lambda c: c["user"], reverse=True,
    )

    def _clean(trait: str) -> str:
        return trait.split(" ", 1)[1].lower()

    strong_matches = sorted(matches, key=lambda c: c["user"], reverse=True)[:2]
    parts = []
    if strong_matches:
        joined = " e ".join(_clean(c["trait"]) for c in strong_matches)
        parts.append(f"Sul fronte {joined} siete sulla stessa lunghezza d'onda")
    if gaps and gaps[0]["user"] >= 55:
        parts.append(f"mentre su {_clean(gaps[0]['trait'])} offre meno di quanto cerchi di solito")
    if not parts:
        return None
    return ", ".join(parts) + "."


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

    warnings.extend(traveller_mode_warnings(row, prefs.get("traveller_mode")))

    budget_msg = _budget_warning_for(row["total_cost_min"], row["total_cost_max"], prefs)
    if budget_msg:
        warnings.append(budget_msg)

    return warnings


def traveller_mode_warnings(row: Any, traveller_mode: str | None) -> list[str]:
    """Avvisi specifici per come si viaggia. Lo stesso posto pone problemi
    diversi a chi parte solo, in coppia o con dei bambini: qui segnaliamo solo
    i casi in cui la modalità cambia davvero qualcosa, non per ogni meta."""
    if not traveller_mode:
        return []
    warnings = []
    social_level = row.get("social_level", 3)
    nightlife = row.get("nightlife_score", 0)
    relax = row.get("relax_score", 0)

    if traveller_mode in ("solo", "primo_solo"):
        if social_level <= 2:
            warnings.append(
                "🎒 Meta poco 'social': bellissima, ma da soli si fa fatica a incontrare altri viaggiatori. "
                "Un ostello o un tour di gruppo aiutano parecchio."
            )
        if traveller_mode == "primo_solo" and row.get("region") == "Extra-Europa":
            warnings.append(
                "🧳 Per un primo viaggio da solo/a è una meta impegnativa: fattibilissima, "
                "ma metti in conto più preparazione rispetto a una destinazione europea."
            )
    elif traveller_mode == "famiglia":
        if nightlife >= 75:
            warnings.append(
                "👨‍👩‍👧 Zona molto votata alla vita notturna: valuta un alloggio defilato dal centro "
                "se viaggi con bambini piccoli."
            )
        if row.get("flight_hours", 0) >= 9:
            warnings.append("👨‍👩‍👧 Volo lungo con bambini: metti in conto il fuso e una giornata di assestamento.")
    elif traveller_mode == "coppia":
        if relax <= 35 and row.get("activity_level", 3) >= 3:
            warnings.append("❤️ Meta piuttosto dinamica: se cercate una fuga rilassante, mettete in conto ritmi pieni.")
    elif traveller_mode == "gruppo":
        if row.get("comfort_level", 3) >= 5:
            warnings.append("🎉 Meta di fascia alta: in gruppo numeroso il conto sale in fretta, meglio fissare un tetto prima.")

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
# Giorno tipo — una giornata plausibile in questa meta, costruita dai tag e
# dalle esperienze WOW già nel dataset. Volutamente NON un itinerario: è un
# assaggio di atmosfera per far capire "com'è davvero stare lì", che nessun
# elenco di punteggi riesce a trasmettere.
# ---------------------------------------------------------------------------

# Per ogni momento della giornata, le attività associate a un tag. Il primo
# tag della destinazione che compare qui vince: l'ordine di questo dizionario
# è quindi una priorità editoriale (ciò che più caratterizza una giornata).
_MORNING_BY_TAG: dict[str, str] = {
    "sci": "Prime discese con la neve fresca e la pista ancora vuota",
    "trekking": "Partenza presto per il sentiero, quando l'aria è ancora fresca",
    "spiaggia": "Colazione con calma, poi spiaggia prima che arrivi il pieno sole",
    "mare": "Colazione con calma, poi mare nelle ore più tranquille",
    "monumenti": "I monumenti principali appena aprono, senza code",
    "cultura": "Un museo o il centro storico con la luce del mattino",
    "natura": "Escursione mattutina, quando la natura è più viva",
    "montagna": "Salita in quota con la vista libera dalle nuvole",
    "surf": "In acqua all'alba, quando le onde sono più pulite",
}

_AFTERNOON_BY_TAG: dict[str, str] = {
    "spiaggia": "Pomeriggio lento tra bagno, ombra e un libro",
    "mare": "Giro in barca o cala nascosta raggiunta a piedi",
    "wellness": "Pausa alle terme o alla spa, senza guardare l'orologio",
    "shopping": "Giro tra le vie dello shopping e le botteghe locali",
    "cultura": "Quartieri meno turistici, a piedi e senza programma",
    "food": "Mercato locale e assaggi in giro, invece del pranzo seduto",
    "natura": "Escursione più lunga o punto panoramico per il tramonto",
    "fotografia": "Caccia agli scorci migliori con la luce del pomeriggio",
    "road trip": "Tratto in auto con soste dove capita, senza fretta",
}

_EVENING_BY_TAG: dict[str, str] = {
    "nightlife": "Aperitivo lungo che scivola nei locali fino a tardi",
    "citta illuminate": "Passeggiata serale con la città illuminata",
    "mercatini di natale": "Giro tra le luci dei mercatini con qualcosa di caldo in mano",
    "aurora boreale": "Uscita a caccia di aurora, lontano dalle luci",
    "food": "Cena lenta in una trattoria del posto, consigliata da un locale",
    "silenzio": "Cena tranquilla e presto a dormire",
    "romantico": "Cena con vista e passeggiata al rientro",
}

_MORNING_DEFAULT = "Colazione senza fretta e primo giro per orientarsi"
_AFTERNOON_DEFAULT = "Pomeriggio libero tra le cose che ti hanno incuriosito la mattina"
_EVENING_DEFAULT = "Cena nel quartiere e rientro con calma"


def _slot_activity(tags: list[str], table: dict[str, str], default: str) -> str:
    for tag in table:
        if tag in tags:
            return table[tag]
    return default


def typical_day(row: Any) -> list[dict[str, str]]:
    """Mattina / pomeriggio / sera per questa meta. La sera aggancia, quando
    c'è, un'esperienza WOW: è il momento della giornata in cui una meta si
    ricorda, e usare un dato già curato a mano batte qualsiasi frase generica."""
    tags = list(row.get("tags", []))
    wow = list(row.get("wow_experiences", []))

    evening = _slot_activity(tags, _EVENING_BY_TAG, _EVENING_DEFAULT)
    if row.get("romantic_score", 0) >= 75 and "romantico" not in tags:
        evening = _EVENING_BY_TAG["romantico"]

    slots = [
        {"icon": "🌅", "label": "Mattina", "text": _slot_activity(tags, _MORNING_BY_TAG, _MORNING_DEFAULT)},
        {"icon": "☀️", "label": "Pomeriggio", "text": _slot_activity(tags, _AFTERNOON_BY_TAG, _AFTERNOON_DEFAULT)},
        {"icon": "🌙", "label": "Sera", "text": evening},
    ]
    if wow:
        slots.append({"icon": "⭐", "label": "Da non perdere", "text": wow[0]})
    return slots


# ---------------------------------------------------------------------------
# "Cosa porteresti via da questo viaggio" — 3 highlight emotivi, non pratici.
# Derivati dai punteggi più alti della meta: è il contraltare della checklist,
# che dice cosa mettere in valigia all'andata.
# ---------------------------------------------------------------------------

_TAKEAWAY_BY_TRAIT: list[tuple[str, str, str]] = [
    ("nature_score", "🌿", "La sensazione di essere piccolo davanti a un paesaggio enorme"),
    ("culture_score", "🏛️", "Qualche storia che non conoscevi e che racconterai al ritorno"),
    ("food_score", "🍝", "Un piatto che proverai a rifare a casa senza riuscirci"),
    ("adventure_score", "🥾", "La soddisfazione di avercela fatta, con le gambe stanche"),
    ("relax_score", "🏖️", "Il ritmo lento che ti porterai dietro ancora per qualche giorno"),
    ("romantic_score", "❤️", "Un tramonto che diventerà la vostra foto di riferimento"),
    ("nightlife_score", "🎉", "Una serata finita molto più tardi del previsto"),
    ("snow_score", "🏔️", "Il silenzio della neve, che non somiglia a nessun altro silenzio"),
    ("luxury_score", "💎", "La sensazione di esserti trattato bene, per una volta"),
]

TAKEAWAY_MIN_SCORE = 65.0


def emotional_takeaways(row: Any, n: int = 3) -> list[str]:
    """I 3 tratti più forti della meta, tradotti in cosa te ne resta addosso.
    Solo sopra TAKEAWAY_MIN_SCORE: se una meta non eccelle in niente, meglio
    due righe vere che tre riempitivi."""
    candidates = [
        (row.get(field, 0), f"{icon} {text}")
        for field, icon, text in _TAKEAWAY_BY_TRAIT
        if row.get(field, 0) >= TAKEAWAY_MIN_SCORE
    ]
    candidates.sort(key=lambda kv: kv[0], reverse=True)
    return [text for _, text in candidates[:n]]


# ---------------------------------------------------------------------------
# Stagionalità visuale — quanto il periodo scelto è quello giusto per la meta.
# ---------------------------------------------------------------------------

_MONTH_LABELS = ["gen", "feb", "mar", "apr", "mag", "giu",
                 "lug", "ago", "set", "ott", "nov", "dic"]


def seasonality_months(row: Any) -> list[dict[str, Any]]:
    """I 12 mesi con l'indicazione se sono tra i `best_months` della meta:
    la UI può renderli come una striscia, molto più leggibile di un elenco."""
    best = set(row.get("best_months", []))
    return [{"label": label, "month": i + 1, "is_best": (i + 1) in best}
            for i, label in enumerate(_MONTH_LABELS)]


def seasonality_note(row: Any, requested: list[int] | None) -> str | None:
    """Una riga onesta sul rapporto tra il periodo scelto e la meta. None se
    l'utente non ha indicato un periodo con mesi definiti (es. "Weekend"):
    senza mesi non c'è nulla di sensato da dire."""
    best = set(row.get("best_months", []))
    if not best:
        return None
    best_labels = ", ".join(_MONTH_LABELS[m - 1] for m in sorted(best))
    if not requested:
        return f"📅 Periodo migliore per andarci: {best_labels}."
    overlap = best & set(requested)
    if overlap:
        return f"✅ Il periodo che hai scelto è tra i migliori per questa meta ({best_labels})."
    return f"🗓️ Ci si può andare, ma il periodo top sarebbe un altro: {best_labels}."


# ---------------------------------------------------------------------------
# "Perché questa meta per te" narrativo — 2-3 frasi umane che intrecciano
# mood, stagione, budget e Travel DNA. Sostituisce (in UI) la frase secca
# generata da recommender.explain_match, che resta il fallback quando qui non
# c'è abbastanza materiale per dire qualcosa di specifico.
# ---------------------------------------------------------------------------

# Etichette dei mood in forma "narrativa", pensate per stare dentro una frase
# ("Hai chiesto relax al mare e cucina..."). Diverse da utils.MOOD_OPTIONS, che
# sono etichette da interfaccia con emoji: infilarle in una frase darebbe
# risultati goffi ("Hai chiesto 🏖️ Relax & Beach").
MOOD_NARRATIVE_LABELS: dict[str, str] = {
    "nature_adventure": "natura e avventura",
    "relax_beach": "relax al mare",
    "city_culture": "città e cultura",
    "party_nightlife": "vita notturna",
    "snow_mountain": "neve e montagna",
    "romantic": "atmosfera romantica",
    "family": "un viaggio adatto alla famiglia",
    "food": "cucina",
    "wellness": "benessere",
    "shopping": "shopping",
    "unique": "esperienze fuori dagli schemi",
}


def narrative_explanation(
    row: Any,
    prefs: dict[str, Any],
    dna: dict[str, int] | None = None,
    requested: list[int] | None = None,
) -> str:
    """2-3 frasi specifiche su PERCHÉ questa meta, per QUESTA persona.

    Ogni frase nasce da un dato reale (mood coperti, stagione, margine di
    budget, DNA): niente entusiasmo generico, che è esattamente ciò che fa
    sembrare finta una raccomandazione. `requested` sono i mesi del periodo
    scelto (vedi recommender.requested_months), passati esplicitamente per
    non far dipendere questo modulo dal recommender."""
    sentences: list[str] = []
    name = row["name"]

    # 1. L'aggancio: il tratto più forte della meta tra quelli che l'utente cerca.
    moods = list(prefs.get("moods", []))
    matched = [MOOD_NARRATIVE_LABELS[m] for m in moods if m in MOOD_NARRATIVE_LABELS]
    if matched:
        joined = matched[0] if len(matched) == 1 else ", ".join(matched[:-1]) + " e " + matched[-1]
        sentences.append(f"Hai chiesto {joined}: {name} è esattamente questo terreno.")
    else:
        top_field, _ = max(
            ((f, row.get(f, 0)) for f in ["culture_score", "nature_score", "relax_score",
                                          "adventure_score", "food_score"]),
            key=lambda kv: kv[1],
        )
        descriptor = {
            "culture_score": "quello che ha da raccontare",
            "nature_score": "i paesaggi",
            "relax_score": "il ritmo lento che permette",
            "adventure_score": "quanto c'è da fare",
            "food_score": "quello che si mangia",
        }[top_field]
        sentences.append(f"{name} spicca soprattutto per {descriptor}.")

    # 2. Stagione: dice qualcosa solo se l'utente ha indicato dei mesi.
    season_line = seasonality_note(row, requested)
    if season_line and season_line.startswith("✅"):
        sentences.append("E ci arrivi nel periodo giusto, non in una finestra di ripiego.")
    elif season_line and season_line.startswith("🗓️"):
        sentences.append("Non è il suo mese migliore, ma resta pienamente godibile — e trovi meno gente.")

    # 3. Budget: il margine (o l'assenza di margine) rispetto allo scenario Economico.
    budget_max = prefs.get("budget_range", (None, None))[1]
    cost_econ = row.get("seasonal_cost_min", row.get("total_cost_min"))
    if budget_max and budget_max > 0 and cost_econ:
        ratio = cost_econ / budget_max
        if ratio <= 0.7:
            sentences.append("Sul budget stai comodo: resta margine per concederti qualcosa in più sul posto.")
        elif ratio <= 1.0:
            sentences.append("Rientra nel budget che hai indicato, senza troppo margine.")

    # 4. DNA: solo se aggiunge davvero informazione.
    dna_line = dna_alignment_summary(dna, row)
    if dna_line and len(sentences) < 3:
        sentences.append(dna_line)

    return " ".join(sentences[:3])


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


def accessible_alternatives(
    scored_all: pd.DataFrame,
    row: Any,
    budget_max: float | None = None,
    max_flight_hours: float | None = None,
    n: int = 2,
) -> list[str]:
    """Alternative più accessibili a una meta fuori portata.

    Cerca nello stesso cluster geografico o con mood simile, ma con un costo
    Economico più basso (o un volo più corto) della meta di partenza. È il
    contraltare costruttivo dell'anti-FOMO: invece di spiegare perché una
    meta è stata scartata, propone dove ripiegare senza rinunciare al genere
    di viaggio che si aveva in mente. Lista vuota se non c'è nulla di
    davvero più accessibile: suggerire un ripiego che costa uguale sarebbe
    peggio che non suggerire niente."""
    if scored_all is None or scored_all.empty:
        return []

    cost_field = "seasonal_cost_min" if "seasonal_cost_min" in scored_all.columns else "total_cost_min"
    ref_cost = row.get(cost_field, row.get("total_cost_min", 0))
    ref_moods = set(row.get("moods", []))

    pool = scored_all[scored_all["id"] != row["id"]].copy()
    if pool.empty:
        return []

    # Affini: stesso cluster (vicine davvero) oppure almeno un mood condiviso.
    same_cluster = pool["cluster"] == row.get("cluster")
    shared_mood = pool["moods"].apply(lambda ms: bool(ref_moods & set(ms))) if ref_moods else False
    pool = pool[same_cluster | shared_mood] if ref_moods is not None else pool[same_cluster]
    if pool.empty:
        return []

    # Più accessibili: almeno il 15% più economiche, o un volo più corto se
    # il problema era la distanza.
    cheaper = pool[cost_field] <= ref_cost * 0.85
    if max_flight_hours and max_flight_hours < 999:
        closer = pool["flight_hours"] <= max_flight_hours
        pool = pool[cheaper | closer]
    else:
        pool = pool[cheaper]

    if budget_max and budget_max > 0:
        pool = pool[pool[cost_field] <= budget_max * 1.0]

    if pool.empty:
        return []

    pool = pool.sort_values("match_score", ascending=False).head(n)
    lines = []
    for _, alt in pool.iterrows():
        saving = ref_cost - alt[cost_field]
        if saving >= 50:
            why = f"costa circa {int(round(saving, -1))} € in meno"
        elif alt["flight_hours"] < row.get("flight_hours", 99):
            why = f"il volo è più corto ({flight_hours_label(alt['flight_hours'])})"
        else:
            why = "è più facile da incastrare con i tuoi vincoli"
        lines.append(
            f"Se **{row['name']}** resta fuori portata, guarda **{alt['name']}** "
            f"({alt['country']}): {why}, con un match del {alt['match_score']:.0f}%."
        )
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
