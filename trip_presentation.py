"""
Trip Presentation — formattazione in linguaggio naturale dei viaggi combinati
generati da trip_builder.py.

Separato deliberatamente dal motore (trip_builder.py) e dal recommender
(recommender.py): questo modulo NON calcola punteggi, non decide se un
itinerario è fattibile, non genera candidati. Prende in input i dict
prodotti da trip_builder (una riga del DataFrame di generate_trip_candidates
/ get_top_trips, o un risultato di surprise_trip) e produce testo semplice —
mai HTML, mai una chiamata a Streamlit — cosi' resta riusabile da qualunque
frontend futuro (CLI, API, export PDF) senza dipendenze.

Punti di estensione pensati per feature future:
- generate_trip_explanation / generate_timeline: già usati da app.py per le
  card dei viaggi combinati.
- format_cost_breakdown / export_trip_as_text: pronti all'uso ma non ancora
  agganciati a una feature specifica (es. un futuro pulsante "Esporta PDF"
  potrebbe wrappare export_trip_as_text in un generatore di PDF senza
  toccare né questo modulo né trip_builder.py).
"""

from __future__ import annotations

from typing import Any

from trip_builder import compute_trip_cost_breakdown
from utils import flight_hours_label, format_price, format_price_range

TRANSPORT_ICONS = {
    "volo": "✈️",
    "treno": "🚄",
    "bus/auto": "🚌",
    "traghetto": "⛴️",
}


def _transport_icon(mode: str) -> str:
    return TRANSPORT_ICONS.get(mode, "🔀")


def generate_trip_explanation(trip: dict[str, Any]) -> str:
    """Testo "Perché fa per te" per un itinerario: 2-4 frasi che spiegano
    perché QUESTE tappe funzionano insieme, perché sono realistiche per la
    durata scelta, ed eventualmente un compromesso onesto — non una ripetizione
    dei punteggi, ma una lettura di ciò che quei punteggi già dicono (mood
    coverage, efficienza, cluster geografico, tempo di trasferimento, punteggi
    per tappa).

    La frase di apertura usa la descrizione curata del trip template quando
    esiste (vedi trip_routes.py), altrimenti ne genera una neutra dai nomi
    delle tappe. La descrizione dei template arriva da un DataFrame pandas:
    colonne miste stringa/None spesso diventano NaN (float), non None —
    isinstance(..., str) copre entrambi i casi senza bisogno di pd.isna()."""
    description = trip.get("description")
    if isinstance(description, str) and description:
        intro = description
    else:
        names = ", ".join(trip.get("stop_names", []))
        intro = f"Una combinazione coerente e fattibile tra {names}."

    efficiency = trip.get("efficiency_score", 0.0)
    transfer_hours = trip.get("transfer_time_hours", 0.0)
    mood_coverage = trip.get("mood_coverage", 0.0)
    clusters = trip.get("clusters", [])
    same_cluster = len(clusters) > 1 and len(set(clusters)) == 1

    if transfer_hours > 0:
        realism = (
            f"Il trasferimento tra le tappe richiede solo {flight_hours_label(transfer_hours)}, "
            f"quindi resta il {efficiency:.0f}% del tempo per esplorare davvero"
        )
        realism += (
            " — le tappe sono anche vicine tra loro, quindi gli spostamenti non pesano sul viaggio."
            if same_cluster else "."
        )
    else:
        realism = "Un'unica area da vivere senza nessun trasferimento interno: zero tempo perso a spostarsi."

    coverage_sentence = None
    if mood_coverage >= 80:
        coverage_sentence = "Messe insieme, le tappe coprono molto bene tutto ciò che avevi chiesto."
    elif mood_coverage >= 60:
        coverage_sentence = "Le tappe si completano bene: quello che manca in una lo offre l'altra."

    stop_scores = trip.get("stop_scores", [])
    compromise = None
    if len(stop_scores) >= 2:
        best_name, best_score = max(stop_scores, key=lambda kv: kv[1])
        weak_name, weak_score = min(stop_scores, key=lambda kv: kv[1])
        if weak_name != best_name and (best_score - weak_score) >= 12:
            compromise = (
                f"Compromesso onesto: {weak_name} da sola avrebbe un match un po' più basso, "
                f"ma nell'insieme dell'itinerario si ripaga."
            )
    if compromise is None and efficiency < 70:
        compromise = "Compromesso onesto: una parte non trascurabile del viaggio se ne va in spostamenti."

    parts = [intro, realism]
    if coverage_sentence:
        parts.append(coverage_sentence)
    if compromise:
        parts.append(compromise)
    return " ".join(parts)


def generate_timeline_segments(trip: dict[str, Any]) -> list[dict[str, Any]]:
    """Timeline strutturata (un dict per blocco: esplorazione o trasferimento)
    — pensata per essere consumata sia da generate_timeline (puro testo, per
    export) sia da una UI che vuole colorare/distinguere visivamente i due
    tipi di blocco senza dover ri-parsare stringhe già formattate."""
    stops = trip.get("stops", [])
    edges = trip.get("edges", [])
    segments = []
    day = 1
    for i, stop in enumerate(stops):
        span = stop["ideal_days"]
        end_day = day + span - 1
        wow_experiences = stop.get("wow_experiences", [])
        wow = wow_experiences[0] if len(wow_experiences) else ""
        label = f"Giorno {day}" if day == end_day else f"Giorni {day}-{end_day}"
        segments.append({
            "type": "explore", "label": label, "title": stop["name"], "detail": wow, "icon": "📍",
        })
        day = end_day + 1
        if i < len(edges):
            e = edges[i]
            next_stop = stops[i + 1]["name"]
            icon = _transport_icon(e["transport_mode"])
            segments.append({
                "type": "transfer", "label": "Trasferimento",
                "title": f"{icon} Verso {next_stop}",
                "detail": f"{e['transport_mode']} (~{flight_hours_label(e['travel_time'])})",
                "icon": icon,
            })
    return segments


def generate_timeline(trip: dict[str, Any]) -> list[str]:
    """Itinerario sintetico giorno-per-giorno in puro testo: una panoramica
    utile alla decisione (quante notti per tappa, come ci si sposta), non un
    programma dettagliato ora per ora. Ogni tappa occupa i suoi `ideal_days`
    (trip_builder assegna questo numero di giorni a ciascuna tappa nel
    calcolo del Travel Efficiency Score, quindi la timeline resta coerente
    con gli altri numeri mostrati nella card)."""
    lines = []
    for seg in generate_timeline_segments(trip):
        if seg["type"] == "explore":
            lines.append(f"{seg['label']}: {seg['icon']} {seg['title']} — {seg['detail']}")
        else:
            lines.append(f"↳ {seg['title']}: {seg['detail']}")
    return lines


def format_cost_breakdown(trip: dict[str, Any]) -> list[str]:
    """Righe leggibili del breakdown costi, a partire dai dati strutturati
    di trip_builder.compute_trip_cost_breakdown. Tenuta separata dal calcolo
    stesso: qui si decide solo COME mostrare i numeri, non come si ottengono."""
    breakdown = compute_trip_cost_breakdown(trip["stops"], trip["edges"])
    lines = [f"✈️ Volo andata/ritorno: {format_price_range(breakdown['flight_in_min'], breakdown['flight_in_max'])}"]
    for stop_cost in breakdown["local_by_stop"]:
        lines.append(f"📍 {stop_cost['name']}: {format_price_range(stop_cost['min'], stop_cost['max'])}")
    lines.append(f"🔀 Trasferimenti (a/r): ~{breakdown['transport_total']:.0f} €")
    return lines


def format_cost_scenarios_lines(cost_min: float, cost_max: float) -> list[str]:
    """Righe leggibili dei 3 scenari di costo (economico/medio/comodo), a
    partire da utils.cost_scenarios — riusata sia nell'export testo/PDF sia
    dalla card in app.py, cosi' i numeri mostrati restano identici ovunque."""
    from utils import cost_scenarios  # import locale per evitare un ciclo (utils non dipende da questo modulo)
    scenarios = cost_scenarios(cost_min, cost_max)
    return [
        f"🟢 Economico: {format_price(scenarios['economico'])}",
        f"🟡 Medio: {format_price(scenarios['medio'])}",
        f"🔴 Comodo: {format_price(scenarios['comodo'])}",
    ]


def export_trip_as_text(trip: dict[str, Any]) -> str:
    """Riepilogo testuale completo e condivisibile di un itinerario — pronto
    per essere copiato, incollato su WhatsApp/Telegram, salvato come .txt, o
    passato al generatore di PDF (vedi export.py) senza modifiche: l'export
    PDF è solo un layer di formattazione sopra questo stesso testo, non una
    nuova fonte di verità."""
    lines = [
        f"✈️ {trip['name']}",
        f"{' → '.join(trip.get('stop_names', []))}",
        "",
        f"Match: {trip['trip_match_score']:.0f}%  ·  Travel Efficiency: {trip['efficiency_score']:.0f}%",
        "",
        generate_trip_explanation(trip),
        "",
        f"Durata: {trip['minimum_days']}-{trip['ideal_days']} giorni (ideale: {trip['ideal_days']})",
        f"Trasferimento totale: ~{trip['transfer_time_hours']:.1f}h",
        "",
        "🗓️ ITINERARIO",
    ]
    lines.extend(generate_timeline(trip))
    lines.append("")
    lines.append(f"💰 COSTO STIMATO / PERSONA: {format_price_range(trip['total_cost_min'], trip['total_cost_max'])}")
    lines.extend(format_cost_scenarios_lines(trip["total_cost_min"], trip["total_cost_max"]))
    lines.append("")
    lines.append("Dettaglio (scenario medio):")
    lines.extend(format_cost_breakdown(trip))
    lines.append("")
    lines.append("— Generato con TravelMatch ✈️")
    return "\n".join(lines)
