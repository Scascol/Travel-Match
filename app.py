"""
TravelMatch — l'app che ti aiuta a scegliere dove andare davvero in vacanza.

Avvio:
    streamlit run app.py

Interfaccia Streamlit: la logica di raccomandazione vive in recommender.py,
il dataset in destinations.py, le utility in utils.py. Questo file si
occupa solo di presentazione e gestione dello stato utente.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import streamlit as st

import random

from destinations import load_destinations_df, TAG_LABELS
from recommender import (
    apply_refinement,
    compare_destinations,
    get_christmas_categories,
    get_default_boosts,
    get_default_weights,
    get_recommendations,
    surprise_me,
)
from trip_builder import (
    apply_trip_refinement,
    compare_trips,
    get_default_trip_adjustments,
    get_default_trip_weights,
    get_top_trips,
    surprise_trip,
)
from checklist import build_destination_checklist, build_trip_checklist
from export import build_pdf_bytes, export_destination_as_text, export_trip_as_text_with_budget
from insights import (
    destination_warnings,
    discarded_destination_alternatives,
    discarded_trip_alternatives,
    organizational_ease,
    trip_organizational_ease,
    trip_warnings,
    travel_style_scores,
    travel_style_scores_for_stops,
)
from social_card import (
    destination_social_card_image,
    destination_social_caption,
    trip_social_card_image,
    trip_social_caption,
)
from travel_estimates import adjust_destinations_for_departure, estimate_alternative_transports
from trip_presentation import generate_timeline_segments, generate_trip_explanation
from utils import (
    AREA_OPTIONS,
    BUDGET_BANDS,
    COMFORT_OPTIONS,
    CHRISTMAS_PERIODS as CHRISTMAS_LIKE,
    CLIMATE_OPTIONS,
    DEPARTURE_CITY_OPTIONS,
    DISTANCE_OPTIONS,
    DURATION_BANDS,
    INTENSITY_OPTIONS,
    MOOD_OPTIONS,
    PEOPLE_OPTIONS,
    PERIOD_OPTIONS,
    QUICK_START_OPTIONS,
    REFINEMENT_ACTIONS,
    SOCIAL_PREFERENCE_OPTIONS,
    TRIP_REFINEMENT_ACTIONS,
    compute_travel_dna,
    cost_scenarios,
    ease_stars,
    flight_duration_label,
    flight_hours_label,
    format_price,
    format_price_range,
    format_temp_range,
    medal_for_rank,
    social_dots,
    travel_dna_description,
)
st.set_page_config(
    page_title="TravelMatch — dove andare davvero in vacanza",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PEOPLE_HEADCOUNT = {"Solo": 1, "Coppia": 2, "Amici": 4, "Famiglia": 4, "Gruppo": 6}


# ---------------------------------------------------------------------------
# Stile
# ---------------------------------------------------------------------------

def inject_css(christmas_mode: bool = False) -> None:
    accent = "#0EA5A0"
    accent_dark = "#0B7A75"
    warm = "#F97316"
    festive = "#B91C1C" if christmas_mode else warm
    st.markdown(
        f"""
        <style>
        /* Forziamo esplicitamente colori chiari/testo scuro: l'app è
        progettata per un tema chiaro (vedi .streamlit/config.toml), ma
        questa regola è una rete di sicurezza nel caso il browser/sistema
        forzi comunque una preferenza di colore diversa. */
        .stApp {{
            background: linear-gradient(180deg, #F8FBFB 0%, #F3F6F6 100%);
            color: #0F172A;
        }}
        h1, h2, h3 {{
            font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
        }}
        .tm-hero {{
            background: linear-gradient(120deg, {accent} 0%, {accent_dark} 55%, #0F172A 100%);
            padding: 2.6rem 2.4rem;
            border-radius: 22px;
            color: white;
            margin-bottom: 1.6rem;
            box-shadow: 0 12px 30px rgba(15, 118, 110, 0.25);
        }}
        .tm-hero h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.3rem;
            color: white;
        }}
        .tm-hero p {{
            font-size: 1.15rem;
            opacity: 0.92;
            margin-bottom: 0;
        }}
        .tm-badge {{
            display: inline-block;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            background: #E6F7F5;
            color: {accent_dark};
            font-size: 0.82rem;
            font-weight: 600;
            margin: 0.12rem 0.28rem 0.12rem 0;
            border: 1px solid #BFEAE6;
        }}
        .tm-badge-festive {{
            background: #FEF2E8;
            color: {festive};
            border: 1px solid #FBD9BE;
        }}
        .tm-match-pill {{
            display: inline-block;
            padding: 0.35rem 1rem;
            border-radius: 999px;
            font-weight: 800;
            font-size: 1.05rem;
            color: white;
        }}
        .tm-card-title {{
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 0;
        }}
        .tm-card-sub {{
            color: #64748B;
            font-size: 0.95rem;
            margin-top: -0.2rem;
        }}
        .tm-section-title {{
            font-weight: 700;
            color: {accent_dark};
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 0.8rem;
            margin-bottom: 0.2rem;
        }}
        .tm-cost-line {{
            font-size: 0.92rem;
            color: #334155;
        }}
        .tm-quote {{
            font-style: italic;
            color: #334155;
            background: #F1F5F9;
            padding: 0.7rem 1rem;
            border-left: 4px solid {accent};
            border-radius: 8px;
        }}
        .tm-surprise-box {{
            background: linear-gradient(120deg, #FDE68A 0%, #FCA5A5 100%);
            padding: 0.4rem;
            border-radius: 20px;
        }}
        .tm-timeline-row {{
            display: flex;
            align-items: baseline;
            gap: 0.6rem;
            padding: 0.4rem 0.7rem;
            border-radius: 10px;
            margin-bottom: 0.35rem;
        }}
        .tm-timeline-explore {{
            background: #E6F7F5;
            border-left: 4px solid {accent};
        }}
        .tm-timeline-transfer {{
            background: #FEF2E8;
            border-left: 4px solid {warm};
            font-style: italic;
        }}
        .tm-timeline-day {{
            font-weight: 700;
            color: #334155;
            min-width: 6.5rem;
            flex-shrink: 0;
        }}
        .tm-scenario-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.3rem 0.6rem;
            border-radius: 8px;
            margin-bottom: 0.25rem;
            font-size: 0.92rem;
        }}
        .tm-scenario-economico {{ background: #E7F7EE; color: #166534; }}
        .tm-scenario-medio {{ background: #FEF9E7; color: #92620A; font-weight: 700; }}
        .tm-scenario-comodo {{ background: #FDEDED; color: #991B1B; }}
        .tm-style-row {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.3rem;
        }}
        .tm-style-label {{
            min-width: 6.5rem;
            font-size: 0.88rem;
            color: #334155;
            flex-shrink: 0;
        }}
        .tm-style-track {{
            flex-grow: 1;
            height: 0.55rem;
            background: #E2E8F0;
            border-radius: 999px;
            overflow: hidden;
        }}
        .tm-style-fill {{
            height: 100%;
            background: linear-gradient(90deg, {accent} 0%, {accent_dark} 100%);
            border-radius: 999px;
        }}
        .tm-style-value {{
            min-width: 2.4rem;
            text-align: right;
            font-size: 0.85rem;
            color: #64748B;
            flex-shrink: 0;
        }}
        .tm-warning-line {{
            background: #FFF7ED;
            color: #7C4A03;
            border-left: 4px solid {warm};
            padding: 0.5rem 0.8rem;
            border-radius: 8px;
            margin-bottom: 0.4rem;
            font-size: 0.92rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Stato
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "stage": "landing",
        "prefs": None,
        "weights": get_default_weights(),
        "boosts": get_default_boosts(),
        "dna": None,
        "results_bundle": None,
        "shown_count": 5,
        "compare_ids": set(),
        "favorites": set(),
        "surprise_pick": None,
        "surprise_exclude": set(),
        "applied_refinements": [],
        # Trip Builder
        "trip_weights": get_default_trip_weights(),
        "trip_adjustments": get_default_trip_adjustments(),
        "trip_bundle": None,
        "shown_trip_count": 3,
        "trip_favorites": set(),
        "applied_trip_refinements": [],
        "surprise_trip_pick": None,
        "surprise_trip_exclude": set(),
        "surprise_kind": None,
        "trip_compare_ids": set(),
        # Modalità Regalo/Sorpresa
        "gift_revealed": False,
        "gift_pick": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_to_landing() -> None:
    keys_to_clear = [
        "stage", "prefs", "weights", "boosts", "dna", "results_bundle",
        "shown_count", "surprise_pick", "surprise_exclude", "applied_refinements",
        "compare_ids", "favorites",
        "trip_weights", "trip_adjustments", "trip_bundle", "shown_trip_count",
        "trip_favorites", "applied_trip_refinements", "surprise_trip_pick",
        "surprise_trip_exclude", "surprise_kind", "trip_compare_ids",
        "gift_revealed", "gift_pick", "results_view_mode", "destination_display_mode",
    ] + [k for k in st.session_state if k.startswith("q_")]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def go(stage: str) -> None:
    st.session_state["stage"] = stage


# ---------------------------------------------------------------------------
# Costruzione preferenze dal form
# ---------------------------------------------------------------------------

def build_prefs_from_form(values: dict) -> dict:
    budget_low, budget_high = BUDGET_BANDS[values["budget_band"]]
    if values["budget_scope"] == "Totale per il gruppo":
        headcount = PEOPLE_HEADCOUNT.get(values["people"], 1)
        budget_low, budget_high = budget_low / headcount, budget_high / headcount

    days_min, days_max = DURATION_BANDS[values["duration_band"]]

    custom_months = None
    if values["period"] == "📅 Date personalizzate" and values.get("date_range"):
        start, end = values["date_range"]
        if start and end and end >= start:
            custom_months = sorted({p.month for p in pd.period_range(start=start, end=end, freq="M")})

    return {
        "budget_range": (budget_low, budget_high),
        "people": values["people"],
        "period": values["period"],
        "custom_months": custom_months,
        "duration_range": (days_min, days_max),
        "moods": values["moods"],
        "intensity": values["intensity"],
        "climate": values["climate"],
        "area": values["area"],
        "max_flight_hours": DISTANCE_OPTIONS[values["distance"]],
        "comfort": values["comfort"],
        "social_slider": values["social_slider"],
        "social_preference": values["social_preference"],
        "tags": values["tags"],
        "departure_city": None if values["departure_city"] == "altro" else values["departure_city"],
    }


def neutral_prefs() -> dict:
    return {
        "budget_range": (0, 100000),
        "people": "Indifferente",
        "period": None,
        "custom_months": None,
        "duration_range": (2, 30),
        "moods": [],
        "intensity": "dynamic",
        "climate": [],
        "area": "nessun_limite",
        "max_flight_hours": 999,
        "comfort": "comfort",
        "social_slider": 50,
        "social_preference": "indifferente",
        "tags": [],
        "departure_city": None,
    }


def recompute_results(top_n: int = 20) -> None:
    df = load_destinations_df()
    df = adjust_destinations_for_departure(df, st.session_state["prefs"].get("departure_city"))
    bundle = get_recommendations(
        df, st.session_state["prefs"], st.session_state["weights"], st.session_state["boosts"], top_n=top_n,
    )
    st.session_state["results_bundle"] = bundle
    st.session_state["shown_count"] = 5
    recompute_trips()


def recompute_trips() -> None:
    df = load_destinations_df()
    df = adjust_destinations_for_departure(df, st.session_state["prefs"].get("departure_city"))
    trip_bundle = get_top_trips(
        df, st.session_state["prefs"], st.session_state["weights"], st.session_state["boosts"],
        st.session_state["trip_weights"], st.session_state["trip_adjustments"], top_n=10,
    )
    st.session_state["trip_bundle"] = trip_bundle
    st.session_state["shown_trip_count"] = 3


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

def render_landing() -> None:
    st.markdown(
        """
        <div class="tm-hero">
            <h1>✈️ TravelMatch</h1>
            <p>Dove dovresti andare <b>davvero</b> in vacanza? Rispondi a qualche domanda,
            scopri il tuo Travel DNA e lascia che facciamo il resto — con un occhio speciale
            a Natale 2026 e Capodanno 2027. 🎄</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Dicci cosa ti va oggi, oppure salta dritto al questionario completo:")
    cols = st.columns(4)
    for i, (key, label) in enumerate(QUICK_START_OPTIONS):
        with cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"quick_{key}"):
                handle_quick_start(key)

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("📝 Fammi tutte le domande (questionario completo)", use_container_width=True, type="primary"):
            go("questionnaire")
            st.rerun()
    with c2:
        with st.expander("📂 Carica una ricerca salvata"):
            uploaded = st.file_uploader(
                "Carica il file .json scaricato in precedenza (vedi \"Salva questa ricerca\" nella barra laterale)",
                type="json", key="load_saved_upload",
            )
            if uploaded is not None:
                handle_load_saved_upload(uploaded)


def handle_quick_start(key: str) -> None:
    # Impostiamo direttamente il session_state delle chiavi dei widget (q_*):
    # è il pattern robusto raccomandato da Streamlit per precompilare un form,
    # perché il valore resta stabile anche nel rerun scatenato dal submit
    # (usare invece un `default=` che cambia tra un rerun e l'altro fa
    # rigenerare l'identità del widget e ne azzera la selezione).
    overrides: dict = {}
    if key == "relax_warm":
        overrides["q_climate"] = ["warm", "tropical"]
        overrides["q_moods"] = ["relax_beach"]
        overrides["q_intensity"] = "relaxed"
    elif key == "christmas_movie":
        overrides["q_period"] = "🎄🎆 Natale + Capodanno"
        overrides["q_moods"] = ["snow_mountain"]
        overrides["q_climate"] = ["snow", "cold"]
        overrides["q_tags"] = ["mercatini di natale", "neve"]
    elif key == "adventure":
        overrides["q_moods"] = ["nature_adventure"]
        overrides["q_intensity"] = "intense"
    elif key == "romantic":
        overrides["q_moods"] = ["romantic"]
        overrides["q_people"] = "Coppia"
    elif key == "social":
        overrides["q_moods"] = ["party_nightlife"]
        overrides["q_social_slider"] = 85
    elif key == "build_trip":
        overrides["q_duration_band"] = "9-14 giorni"
        st.session_state["trip_mode_hint"] = True
    elif key == "surprise":
        prefs = neutral_prefs()
        st.session_state["prefs"] = prefs
        st.session_state["dna"] = compute_travel_dna(prefs)
        recompute_results()
        go("surprise_direct")
        st.rerun()
        return
    elif key == "first_solo_trip":
        # Facilità logistica alta (area vicina, volo corto) + socialità media:
        # non tocca lo scoring, sono solo valori di partenza sensati per chi
        # viaggia da solo/a per la prima volta.
        overrides["q_people"] = "Solo"
        overrides["q_area"] = "europa"
        overrides["q_distance"] = "3h"
        overrides["q_comfort"] = "comfort"
        overrides["q_social_slider"] = 60
        overrides["q_duration_band"] = "6-8 giorni"
    elif key == "gift_surprise":
        prefs = neutral_prefs()
        st.session_state["prefs"] = prefs
        st.session_state["dna"] = compute_travel_dna(prefs)
        recompute_results()
        st.session_state["gift_revealed"] = False
        st.session_state["gift_pick"] = None
        go("gift_surprise")
        st.rerun()
        return

    for widget_key, value in overrides.items():
        st.session_state[widget_key] = value
    go("questionnaire")
    st.rerun()


def handle_load_saved_upload(uploaded_file) -> None:
    """Carica una ricerca da un file .json scaricato in precedenza (vedi
    render_sidebar). Il file viene solo letto in memoria per questa sessione,
    non scritto da nessuna parte sul server: ogni visitatore gestisce il
    proprio file, così anche in una versione online condivisa da più persone
    nessuno vede i dati di un altro (a differenza di un salvataggio unico su
    disco, che sarebbe stato sovrascritto a ogni utente)."""
    try:
        saved = json.load(uploaded_file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        st.error("Il file non sembra una ricerca TravelMatch valida.")
        return
    if not saved or "prefs" not in saved:
        st.error("Il file non sembra una ricerca TravelMatch valida.")
        return
    prefs = saved["prefs"]
    prefs["budget_range"] = tuple(prefs["budget_range"])
    prefs["duration_range"] = tuple(prefs["duration_range"])
    st.session_state["prefs"] = prefs
    st.session_state["dna"] = saved.get("dna") or compute_travel_dna(prefs)
    st.session_state["favorites"] = set(saved.get("favorite_ids", []))
    st.session_state["trip_favorites"] = set(saved.get("favorite_trip_ids", []))
    recompute_results()
    go("results")
    st.success("Preferenze caricate! Ecco di nuovo i tuoi risultati. 🎉")
    st.rerun()


# ---------------------------------------------------------------------------
# Questionario
# ---------------------------------------------------------------------------

def _default_kwargs(widget_key: str, **kwargs) -> dict:
    """Restituisce kwargs di default (index=/value=) solo se il widget non ha
    già un valore in session_state (es. precompilato da un quick-start):
    passarli comunque non cambierebbe il comportamento, ma Streamlit emette
    un warning se un default esplicito coesiste con un valore già presente in
    session_state per la stessa key."""
    return {} if widget_key in st.session_state else kwargs


def render_questionnaire() -> None:
    st.markdown("## 📝 Raccontaci come vuoi la tua vacanza")
    st.caption("Più dettagli ci dai, più il match sarà preciso. Puoi sempre affinare i risultati dopo.")

    # Tutti i widget hanno una key esplicita e stabile (q_*): è ciò che permette
    # sia alla precompilazione da quick-start (vedi handle_quick_start) sia alla
    # selezione manuale dell'utente di sopravvivere al rerun scatenato dal
    # submit del form, invece di essere azzerate.
    with st.form("questionnaire_form"):
        st.markdown("##### 💰 Budget")
        c1, c2 = st.columns([2, 1])
        with c1:
            budget_band = st.select_slider(
                "Fascia di budget", options=list(BUDGET_BANDS.keys()),
                value="1.000 - 1.500 €", key="q_budget_band",
            )
        with c2:
            budget_scope = st.radio("Il budget è:", ["Per persona", "Totale per il gruppo"], index=0, key="q_budget_scope")

        st.markdown("##### 👥 Con chi parti?")
        people = st.radio(
            "Persone", PEOPLE_OPTIONS, horizontal=True, key="q_people",
            **_default_kwargs("q_people", index=1),
        )

        st.markdown("##### 🛫 Parti da...")
        departure_city = st.radio(
            "Città di partenza", list(DEPARTURE_CITY_OPTIONS.keys()), horizontal=True,
            format_func=lambda k: DEPARTURE_CITY_OPTIONS[k], key="q_departure_city",
            **_default_kwargs("q_departure_city", index=2),
        )
        st.caption("Milano o Roma affinano le stime di volo. \"Altro/Indifferente\" usa le stime generiche.")

        st.markdown("##### 📅 Periodo")
        period = st.selectbox(
            "Quando vuoi partire?", PERIOD_OPTIONS, key="q_period",
            **_default_kwargs("q_period", index=2),
        )
        st.caption("Per Natale/Capodanno il riferimento è Natale 2026 / Capodanno 2027 (18 dic 2026 – 6 gen 2027).")
        date_range = None
        if period == "📅 Date personalizzate":
            date_range = st.date_input(
                "Seleziona le date del viaggio",
                value=(dt.date(2026, 12, 24), dt.date(2027, 1, 2)),
                format="DD/MM/YYYY", key="q_date_range",
            )

        st.markdown("##### 🗓️ Durata del viaggio")
        duration_band = st.select_slider(
            "Quanti giorni?", options=list(DURATION_BANDS.keys()), key="q_duration_band",
            **_default_kwargs("q_duration_band", value="6-8 giorni"),
        )

        st.markdown("##### 🎭 Mood — scegli quello che ti rappresenta (anche più di uno)")
        moods = st.multiselect(
            "Cosa cerchi in questo viaggio?",
            options=list(MOOD_OPTIONS.keys()),
            format_func=lambda k: MOOD_OPTIONS[k],
            key="q_moods",
        )

        st.markdown("##### ⚡ Intensità")
        intensity = st.radio(
            "Ritmo del viaggio", list(INTENSITY_OPTIONS.keys()),
            format_func=lambda k: INTENSITY_OPTIONS[k], horizontal=True, key="q_intensity",
            **_default_kwargs("q_intensity", index=1),
        )

        st.markdown("##### 🌡️ Clima")
        climate = st.multiselect(
            "Che clima preferisci?", options=list(CLIMATE_OPTIONS.keys()),
            format_func=lambda k: CLIMATE_OPTIONS[k], key="q_climate",
        )

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### 🌍 Area geografica")
            area = st.selectbox("Dove sei disposto/a a volare?", list(AREA_OPTIONS.keys()), index=3, format_func=lambda k: AREA_OPTIONS[k], key="q_area")
        with c4:
            st.markdown("##### ✈️ Distanza massima di volo")
            distance = st.selectbox("Durata massima del volo", list(DISTANCE_OPTIONS.keys()), index=4, key="q_distance")

        st.markdown("##### 🏨 Comfort")
        comfort = st.select_slider(
            "Livello di comfort desiderato", options=list(COMFORT_OPTIONS.keys()),
            value="comfort", format_func=lambda k: COMFORT_OPTIONS[k], key="q_comfort",
        )

        st.markdown("##### 🎉 Socialità")
        social_slider = st.slider(
            "0 = voglio stare per conto mio · 100 = voglio conoscere gente ogni giorno",
            0, 100, key="q_social_slider",
            **_default_kwargs("q_social_slider", value=50),
        )
        social_preference = st.selectbox(
            "Con chi preferisci socializzare durante il viaggio?",
            list(SOCIAL_PREFERENCE_OPTIONS.keys()), index=3,
            format_func=lambda k: SOCIAL_PREFERENCE_OPTIONS[k], key="q_social_pref",
        )

        st.markdown("##### 🏷️ Preferenze speciali")
        tags = st.multiselect("Seleziona tutto ciò che ti attira", options=TAG_LABELS, key="q_tags")

        submitted = st.form_submit_button("🔎 Trova le mie destinazioni", type="primary", use_container_width=True)

    if submitted:
        values = dict(
            budget_band=budget_band, budget_scope=budget_scope, people=people,
            period=period, date_range=date_range, duration_band=duration_band,
            moods=moods, intensity=intensity, climate=climate, area=area,
            distance=distance, comfort=comfort, social_slider=social_slider,
            social_preference=social_preference, tags=tags, departure_city=departure_city,
        )
        prefs = build_prefs_from_form(values)
        st.session_state["prefs"] = prefs
        st.session_state["dna"] = compute_travel_dna(prefs)
        st.session_state["weights"] = get_default_weights()
        st.session_state["boosts"] = get_default_boosts()
        st.session_state["applied_refinements"] = []
        st.session_state["surprise_pick"] = None
        st.session_state["surprise_exclude"] = set()
        st.session_state["trip_weights"] = get_default_trip_weights()
        st.session_state["trip_adjustments"] = get_default_trip_adjustments()
        st.session_state["applied_trip_refinements"] = []
        st.session_state["surprise_trip_pick"] = None
        st.session_state["surprise_trip_exclude"] = set()
        # Il toggle "Cosa vuoi vedere?" è una preferenza sui risultati appena
        # calcolati, non sull'utente: una nuova ricerca non deve ereditare
        # "Solo viaggi combinati" da quella precedente e nascondere in
        # silenzio l'intera sezione destinazioni senza che sia ovvio perché.
        st.session_state.pop("results_view_mode", None)
        st.session_state.pop("destination_display_mode", None)
        recompute_results()
        go("results")
        st.rerun()

    if st.button("⬅️ Torna alla home"):
        go("landing")
        st.rerun()


# ---------------------------------------------------------------------------
# Travel DNA
# ---------------------------------------------------------------------------

def render_travel_dna() -> None:
    dna = st.session_state.get("dna")
    if not dna:
        return
    with st.container(border=True):
        st.markdown("### 🧬 Il tuo Travel DNA")
        cols = st.columns(2)
        items = list(dna.items())
        half = (len(items) + 1) // 2
        for col, chunk in zip(cols, [items[:half], items[half:]]):
            with col:
                for label, value in chunk:
                    st.markdown(f"**{label}** — {value}%")
                    st.progress(value / 100)
        st.markdown(f'<p class="tm-quote">{travel_dna_description(dna)}</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Card destinazione
# ---------------------------------------------------------------------------

def score_tier_color(score: float) -> str:
    if score >= 85:
        return "#0F9D58"
    if score >= 70:
        return "#0EA5A0"
    if score >= 55:
        return "#F97316"
    return "#94A3B8"


def current_budget_max() -> float | None:
    prefs = st.session_state.get("prefs")
    if not prefs:
        return None
    return prefs.get("budget_range", (None, None))[1]


def current_prefs() -> dict:
    return st.session_state.get("prefs") or {}


def render_anti_fomo(lines: list[str]) -> None:
    """Anti-FOMO leggero: 1-2 alternative valutate ma non mostrate, con una
    ragione onesta — così chi guarda i risultati non si chiede "ma ha
    considerato anche X?" senza avere una risposta."""
    if not lines:
        return
    with st.container(border=True):
        st.markdown("**🤔 Ci abbiamo pensato anche noi**")
        for line in lines:
            st.markdown(f"- {line}")


def render_cost_scenarios(cost_min: float, cost_max: float) -> None:
    scenarios = cost_scenarios(cost_min, cost_max)
    st.markdown('<p class="tm-section-title">💰 Scenari di costo / persona</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="tm-scenario-row tm-scenario-economico"><span>🟢 Economico</span><span>{format_price(scenarios["economico"])}</span></div>'
        f'<div class="tm-scenario-row tm-scenario-medio"><span>🟡 Medio</span><span>{format_price(scenarios["medio"])}</span></div>'
        f'<div class="tm-scenario-row tm-scenario-comodo"><span>🔴 Comodo</span><span>{format_price(scenarios["comodo"])}</span></div>',
        unsafe_allow_html=True,
    )


def render_travel_style_bars(scores: dict[str, float]) -> None:
    st.markdown('<p class="tm-section-title">🎨 Travel Style</p>', unsafe_allow_html=True)
    rows = "".join(
        f'<div class="tm-style-row">'
        f'<span class="tm-style-label">{label}</span>'
        f'<div class="tm-style-track"><div class="tm-style-fill" style="width:{max(0, min(100, value)):.0f}%;"></div></div>'
        f'<span class="tm-style-value">{value:.0f}%</span>'
        f'</div>'
        for label, value in scores.items()
    )
    st.markdown(rows, unsafe_allow_html=True)


def render_contextual_warnings(warnings: list[str]) -> None:
    if not warnings:
        return
    st.markdown('<p class="tm-section-title">🔎 Da sapere prima di partire</p>', unsafe_allow_html=True)
    lines = "".join(f'<div class="tm-warning-line">{w}</div>' for w in warnings)
    st.markdown(lines, unsafe_allow_html=True)


def render_visual_timeline(trip: dict) -> None:
    for seg in generate_timeline_segments(trip):
        if seg["type"] == "explore":
            st.markdown(
                f'<div class="tm-timeline-row tm-timeline-explore">'
                f'<span class="tm-timeline-day">{seg["label"]}</span>'
                f'<span>{seg["icon"]} <b>{seg["title"]}</b>{" — " + seg["detail"] if seg["detail"] else ""}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="tm-timeline-row tm-timeline-transfer">'
                f'<span class="tm-timeline-day">{seg["label"]}</span>'
                f'<span>{seg["title"]} · {seg["detail"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _render_destination_explanation(row: pd.Series) -> None:
    st.markdown('<p class="tm-section-title">Perché fa per te</p>', unsafe_allow_html=True)
    st.write(row["explanation"])
    if row.get("compromise_reasons"):
        reasons = ", ".join(row["compromise_reasons"])
        st.warning(f"Piccolo compromesso su: {reasons}. Il resto però convince parecchio.")


def _render_destination_detail_body(row: pd.Series, rank: int | None, surprise: bool, dest_id: int) -> None:
    """Tutto ciò che sta sotto "Perché fa per te": avvisi, Travel Style, WOW,
    costi+scenari, info pratiche, pro/contro, checklist, export e azioni.
    Condiviso identico tra vista compatta (dentro l'expander di dettaglio) e
    vista dettagliata (sempre visibile), così le due modalità mostrano
    sempre esattamente lo stesso contenuto — cambia solo il contenitore."""
    render_contextual_warnings(destination_warnings(row, current_prefs()))
    render_travel_style_bars(travel_style_scores(row))

    st.markdown('<p class="tm-section-title">⭐ Esperienze WOW</p>', unsafe_allow_html=True)
    for wow in row["wow_experiences"][:3]:
        st.markdown(f"- {wow}")

    cost_col, info_col = st.columns([1.3, 1])
    with cost_col:
        st.markdown('<p class="tm-section-title">💰 Costo indicativo / persona</p>', unsafe_allow_html=True)
        st.markdown(f"**{format_price_range(row['total_cost_min'], row['total_cost_max'])}**")
        st.markdown(f'<p class="tm-cost-line">✈️ Volo: {format_price_range(row["flight_cost_min"], row["flight_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🏨 Hotel: {format_price_range(row["hotel_cost_min"], row["hotel_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🍝 Cibo: {format_price_range(row["food_cost_min"], row["food_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🎟️ Attività: {format_price_range(row["activity_cost_min"], row["activity_cost_max"])}</p>', unsafe_allow_html=True)
        render_cost_scenarios(row["total_cost_min"], row["total_cost_max"])
    with info_col:
        st.markdown('<p class="tm-section-title">Info pratiche</p>', unsafe_allow_html=True)
        st.markdown(f"🌡️ {format_temp_range(row['temp_min'], row['temp_max'])}")
        st.markdown(f"🗓️ {row['days_min']}-{row['days_max']} giorni consigliati")
        st.markdown(f"✈️ {flight_duration_label(row['flight_hours'], current_prefs().get('departure_city'))}")
        st.markdown(f"👥 Social: {social_dots(row['social_level'] * 20)}")
        ease = organizational_ease(row)
        st.markdown(f"🧭 Facilità organizzativa: {ease_stars(ease)} ({ease}/5)")

    alt_transports = estimate_alternative_transports(row)
    if alt_transports:
        st.markdown('<p class="tm-section-title">🚆 Alternative al volo</p>', unsafe_allow_html=True)
        st.caption("Stima indicativa basata sulla distanza, non su orari reali — utile solo per farsi un'idea.")
        for opt in alt_transports:
            st.markdown(
                f"{opt['icon']} **{opt['mode']}**: "
                f"{flight_hours_label(opt['hours_min'])}-{flight_hours_label(opt['hours_max'])} · "
                f"{format_price_range(opt['cost_min'], opt['cost_max'])}"
            )

    with st.expander("👍 Pro, 👎 Contro e consigli pratici"):
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("**Pro**")
            for p in row["pros"]:
                st.markdown(f"- {p}")
        with pc2:
            st.markdown("**Contro**")
            for c in row["cons"]:
                st.markdown(f"- {c}")
        st.markdown("**Consigli pratici**")
        for tip in row["practical_tips"]:
            st.markdown(f"- {tip}")

    with st.expander("🎒 Checklist di viaggio"):
        checklist = build_destination_checklist(row, current_prefs().get("period"))
        for section, items in checklist.items():
            st.markdown(f"**{section}**")
            for item in items:
                st.markdown(f"- {item}")

    with st.expander("📄 Esporta / 📤 Condividi"):
        export_text = export_destination_as_text(row, current_budget_max())
        st.text_area(
            "Riepilogo copiabile (WhatsApp/Telegram)", value=export_text, height=220,
            key=f"dexport_{dest_id}_{rank}_{surprise}", label_visibility="collapsed",
        )
        pdf_bytes = build_pdf_bytes(row["name"], export_text)
        if pdf_bytes:
            st.download_button(
                "⬇️ Scarica PDF", data=pdf_bytes, file_name=f"{row['name'].replace(' ', '_')}.pdf",
                mime="application/pdf", key=f"dpdf_{dest_id}_{rank}_{surprise}",
            )
        else:
            st.caption("PDF non disponibile su questo computer: usa il testo qui sopra (copia/incolla).")

        st.markdown("**📸 Card social**")
        st.text_area(
            "Didascalia pronta per i social", value=destination_social_caption(row), height=140,
            key=f"dcaption_{dest_id}_{rank}_{surprise}", label_visibility="collapsed",
        )
        card_image = destination_social_card_image(row)
        if card_image:
            st.image(card_image, width=220)
            st.download_button(
                "⬇️ Scarica immagine", data=card_image, file_name=f"{row['name'].replace(' ', '_')}_card.png",
                mime="image/png", key=f"dcard_{dest_id}_{rank}_{surprise}",
            )
        else:
            st.caption("Immagine non disponibile su questo computer: usa la didascalia qui sopra.")

    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        is_fav = dest_id in st.session_state["favorites"]
        if st.button("❤️ Nei preferiti" if not is_fav else "💔 Rimuovi", key=f"fav_{dest_id}_{rank}_{surprise}"):
            if is_fav:
                st.session_state["favorites"].discard(dest_id)
            else:
                st.session_state["favorites"].add(dest_id)
            st.rerun()
    with action_cols[1]:
        in_compare = dest_id in st.session_state["compare_ids"]
        label = "✅ In confronto" if in_compare else "➕ Confronta"
        if st.button(label, key=f"cmp_{dest_id}_{rank}_{surprise}"):
            if in_compare:
                st.session_state["compare_ids"].discard(dest_id)
            elif len(st.session_state["compare_ids"]) >= 3:
                st.warning("Puoi confrontare al massimo 3 destinazioni. Rimuovine una prima di aggiungerne un'altra.")
            else:
                st.session_state["compare_ids"].add(dest_id)
            st.rerun()


def render_destination_card(row: pd.Series, rank: int | None = None, surprise: bool = False, compact: bool = True) -> None:
    dest_id = int(row["id"])
    with st.container(border=True):
        header_cols = st.columns([5, 1.4])
        with header_cols[0]:
            medal = medal_for_rank(rank) if rank is not None else ("🎲" if surprise else "🔹")
            st.markdown(f'<p class="tm-card-title">{medal} {row["name"].upper()}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="tm-card-sub">{row["country"]} · {row["region"]}</p>', unsafe_allow_html=True)
        with header_cols[1]:
            color = score_tier_color(row["match_score"])
            st.markdown(
                f'<span class="tm-match-pill" style="background:{color};">{row["match_score"]:.0f}% MATCH</span>',
                unsafe_allow_html=True,
            )

        if compact:
            # Vista compatta: 2-3 tag, riga di metriche chiave, 1 riga di
            # spiegazione — il dettaglio completo (identico a quello della
            # vista dettagliata) sta dietro un solo click.
            mood_labels = [MOOD_OPTIONS.get(m, m) for m in row["moods"][:3]]
            mood_badges = "".join(f'<span class="tm-badge">{m}</span>' for m in mood_labels)
            st.markdown(mood_badges, unsafe_allow_html=True)

            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            metric_cols = st.columns(3)
            scenario_medio = cost_scenarios(row["total_cost_min"], row["total_cost_max"])["medio"]
            with metric_cols[0]:
                st.markdown(f"💰 **{format_price(scenario_medio)}** /persona")
            with metric_cols[1]:
                st.markdown(f"🗓️ {row['days_min']}-{row['days_max']} giorni")
            with metric_cols[2]:
                st.markdown(f"✈️ {flight_duration_label(row['flight_hours'], current_prefs().get('departure_city'))}")
            st.caption(row["explanation"])

            with st.expander("🔍 Vedi dettaglio completo"):
                _render_destination_explanation(row)
                _render_destination_detail_body(row, rank, surprise, dest_id)
        else:
            badge_class = "tm-badge"
            mood_labels = [MOOD_OPTIONS.get(m, m) for m in row["moods"][:4]]
            mood_badges = "".join(f'<span class="{badge_class}">{m}</span>' for m in mood_labels)
            st.markdown(mood_badges, unsafe_allow_html=True)

            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            _render_destination_explanation(row)
            _render_destination_detail_body(row, rank, surprise, dest_id)


def feasibility_tier_color(score: float) -> str:
    if score >= 85:
        return "#0F9D58"
    if score >= 75:
        return "#0EA5A0"
    if score >= 60:
        return "#F97316"
    return "#94A3B8"


def _render_trip_explanation(trip: pd.Series) -> None:
    st.markdown('<p class="tm-section-title">Perché fa per te</p>', unsafe_allow_html=True)
    st.write(generate_trip_explanation(trip))


def _render_trip_detail_body(trip: pd.Series, rank: int | None, surprise: bool) -> None:
    """Tutto ciò che sta sotto "Perché fa per te": avvisi, Travel Style,
    costi+scenari, timeline, dettaglio Feasibility, checklist, export e
    azioni — condiviso identico tra vista compatta (dentro l'expander) e
    vista dettagliata (sempre visibile), stesso principio delle card
    destinazione (vedi _render_destination_detail_body)."""
    render_contextual_warnings(trip_warnings(trip, current_prefs()))
    render_travel_style_bars(travel_style_scores_for_stops(trip["stops"]))

    cost_col, info_col = st.columns([1.3, 1])
    with cost_col:
        st.markdown('<p class="tm-section-title">💰 Costo totale indicativo / persona</p>', unsafe_allow_html=True)
        st.markdown(f"**{format_price_range(trip['total_cost_min'], trip['total_cost_max'])}**")
        st.markdown(f'<p class="tm-cost-line">🔀 Trasferimenti: ~{trip["transfer_cost"]:.0f} €</p>', unsafe_allow_html=True)
        render_cost_scenarios(trip["total_cost_min"], trip["total_cost_max"])
    with info_col:
        st.markdown('<p class="tm-section-title">Info pratiche</p>', unsafe_allow_html=True)
        st.markdown(f"🗓️ {trip['minimum_days']}-{trip['ideal_days']} giorni (ideale: {trip['ideal_days']})")
        entry_flight_hours = trip["stops"][0]["flight_hours"]
        st.markdown(f"✈️ {flight_duration_label(entry_flight_hours, current_prefs().get('departure_city'))}")
        st.markdown(f"🔀 {flight_hours_label(trip['transfer_time_hours'])} di trasferimento totale")
        st.markdown(f"🧭 Efficienza viaggio: {trip['efficiency_score']:.0f}%")
        ease = trip_organizational_ease(trip)
        st.markdown(f"🧭 Facilità organizzativa: {ease_stars(ease)} ({ease}/5)")

    st.markdown('<p class="tm-section-title">🗓️ Timeline del viaggio</p>', unsafe_allow_html=True)
    render_visual_timeline(trip)

    with st.expander("📊 Dettaglio Feasibility Score"):
        st.markdown(f"- Coerenza geografica: {trip['geographic_coherence']:.0f}/100")
        st.markdown(f"- Fattibilità trasporti: {trip['transport_feasibility']:.0f}/100")
        st.markdown(f"- Fattibilità tempo: {trip['time_feasibility']:.0f}/100")
        st.markdown(f"- Fattibilità budget: {trip['budget_feasibility']:.0f}/100")
        st.markdown(f"- Compatibilità stagione: {trip['season_compatibility']:.0f}/100")

    with st.expander("🎒 Checklist di viaggio"):
        checklist = build_trip_checklist(trip, current_prefs().get("period"))
        for section, items in checklist.items():
            st.markdown(f"**{section}**")
            for item in items:
                st.markdown(f"- {item}")

    with st.expander("📄 Esporta / 📤 Condividi"):
        export_text = export_trip_as_text_with_budget(trip, current_budget_max())
        st.text_area(
            "Riepilogo copiabile (WhatsApp/Telegram)", value=export_text, height=260,
            key=f"texport_{trip['trip_id']}_{rank}_{surprise}", label_visibility="collapsed",
        )
        pdf_bytes = build_pdf_bytes(trip["name"], export_text)
        if pdf_bytes:
            st.download_button(
                "⬇️ Scarica PDF", data=pdf_bytes, file_name=f"{trip['name'].replace(' ', '_')}.pdf",
                mime="application/pdf", key=f"tpdf_{trip['trip_id']}_{rank}_{surprise}",
            )
        else:
            st.caption("PDF non disponibile su questo computer: usa il testo qui sopra (copia/incolla).")

        st.markdown("**📸 Card social**")
        st.text_area(
            "Didascalia pronta per i social", value=trip_social_caption(trip), height=140,
            key=f"tcaption_{trip['trip_id']}_{rank}_{surprise}", label_visibility="collapsed",
        )
        card_image = trip_social_card_image(trip)
        if card_image:
            st.image(card_image, width=220)
            st.download_button(
                "⬇️ Scarica immagine", data=card_image, file_name=f"{trip['name'].replace(' ', '_')}_card.png",
                mime="image/png", key=f"tcard_{trip['trip_id']}_{rank}_{surprise}",
            )
        else:
            st.caption("Immagine non disponibile su questo computer: usa la didascalia qui sopra.")

    action_cols = st.columns([1, 1, 2])
    trip_id = trip["trip_id"]
    with action_cols[0]:
        is_fav = trip_id in st.session_state["trip_favorites"]
        if st.button("❤️ Nei preferiti" if not is_fav else "💔 Rimuovi", key=f"tfav_{trip_id}_{rank}_{surprise}"):
            if is_fav:
                st.session_state["trip_favorites"].discard(trip_id)
            else:
                st.session_state["trip_favorites"].add(trip_id)
            st.rerun()
    with action_cols[1]:
        in_compare = trip_id in st.session_state["trip_compare_ids"]
        label = "✅ In confronto" if in_compare else "➕ Confronta"
        if st.button(label, key=f"tcmp_{trip_id}_{rank}_{surprise}"):
            if in_compare:
                st.session_state["trip_compare_ids"].discard(trip_id)
            elif len(st.session_state["trip_compare_ids"]) >= 2:
                st.warning("Puoi confrontare al massimo 2 viaggi combinati. Rimuovine uno prima di aggiungerne un altro.")
            else:
                st.session_state["trip_compare_ids"].add(trip_id)
            st.rerun()


def render_trip_card(trip: pd.Series, rank: int | None = None, surprise: bool = False, compact: bool = True) -> None:
    with st.container(border=True):
        header_cols = st.columns([5, 1.4])
        with header_cols[0]:
            medal = medal_for_rank(rank) if rank is not None else ("🎲" if surprise else "✈️")
            st.markdown(f'<p class="tm-card-title">{medal} {trip["name"].upper()}</p>', unsafe_allow_html=True)
            route_label = " → ".join(trip["stop_names"])
            st.markdown(f'<p class="tm-card-sub">✈️ Viaggio combinato · {route_label}</p>', unsafe_allow_html=True)
        with header_cols[1]:
            color = score_tier_color(trip["trip_match_score"])
            st.markdown(
                f'<span class="tm-match-pill" style="background:{color};">{trip["trip_match_score"]:.0f}% MATCH</span>',
                unsafe_allow_html=True,
            )

        feas_color = feasibility_tier_color(trip["feasibility_score"])
        st.markdown(
            f'<span class="tm-badge" style="background:{feas_color}22; color:{feas_color}; border-color:{feas_color}55;">'
            f'Feasibility {trip["feasibility_score"]:.0f}/100</span>'
            f'<span class="tm-badge">🧭 Travel Efficiency {trip["efficiency_score"]:.0f}%</span>'
            f'<span class="tm-badge">🏷️ {trip["difficulty"].capitalize()}</span>',
            unsafe_allow_html=True,
        )

        if compact:
            # Vista compatta: riga di metriche chiave + 1 riga di
            # spiegazione, tutto il resto (Travel Style, costi+scenari,
            # timeline, checklist, export...) dietro un solo click.
            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            metric_cols = st.columns(3)
            scenario_medio = cost_scenarios(trip["total_cost_min"], trip["total_cost_max"])["medio"]
            with metric_cols[0]:
                st.markdown(f"💰 **{format_price(scenario_medio)}** /persona")
            with metric_cols[1]:
                st.markdown(f"🗓️ {trip['minimum_days']}-{trip['ideal_days']} giorni")
            with metric_cols[2]:
                st.markdown(f"🔀 {flight_hours_label(trip['transfer_time_hours'])} trasferimento")
            st.caption(generate_trip_explanation(trip))

            with st.expander("🔍 Vedi dettaglio completo"):
                _render_trip_explanation(trip)
                _render_trip_detail_body(trip, rank, surprise)
        else:
            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            _render_trip_explanation(trip)
            _render_trip_detail_body(trip, rank, surprise)


# ---------------------------------------------------------------------------
# Sezione Natale/Capodanno
# ---------------------------------------------------------------------------

def render_christmas_spotlight(scored_all: pd.DataFrame) -> None:
    st.markdown("### 🎄❄️ Natale & Capodanno: due anime, tu scegli")
    cats = get_christmas_categories(scored_all)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ☀️ Fuga al caldo")
        st.caption("Ok, abbiamo capito: il freddo non fa per te. 😎")
        for _, row in cats["fuga_al_caldo"].head(3).iterrows():
            st.markdown(f"**{row['name']}**, {row['country']} — {row['match_score']:.0f}% match")
    with c2:
        st.markdown("#### 🎄 Winter Wonderland")
        st.caption("Vuoi neve, Natale e zero sbatti? Abbiamo qualche idea.")
        for _, row in cats["winter_wonderland"].head(3).iterrows():
            st.markdown(f"**{row['name']}**, {row['country']} — {row['match_score']:.0f}% match")
    st.divider()


# ---------------------------------------------------------------------------
# Raffinamento
# ---------------------------------------------------------------------------

def render_refinement_bar() -> None:
    st.markdown("### 🎛️ Affina i risultati")
    st.caption("Ogni click modifica il motore di scoring — non ripete il questionario, lo rende più preciso su ciò che conta per te ora.")
    cols = st.columns(5)
    for i, (action, label) in enumerate(REFINEMENT_ACTIONS):
        with cols[i % 5]:
            if st.button(label, key=f"refine_{action}", use_container_width=True):
                new_w, new_b = apply_refinement(st.session_state["weights"], st.session_state["boosts"], action)
                st.session_state["weights"] = new_w
                st.session_state["boosts"] = new_b
                st.session_state["applied_refinements"].append(label)
                recompute_results()
                st.rerun()

    if st.session_state["applied_refinements"]:
        applied = " · ".join(st.session_state["applied_refinements"][-6:])
        st.caption(f"Raffinamenti applicati: {applied}")

    st.markdown("##### ✈️ Affina i viaggi combinati")
    trip_cols = st.columns(5)
    for i, (action, label) in enumerate(TRIP_REFINEMENT_ACTIONS):
        with trip_cols[i % 5]:
            if st.button(label, key=f"trefine_{action}", use_container_width=True):
                new_tw, new_adj = apply_trip_refinement(st.session_state["trip_weights"], st.session_state["trip_adjustments"], action)
                st.session_state["trip_weights"] = new_tw
                st.session_state["trip_adjustments"] = new_adj
                st.session_state["applied_trip_refinements"].append(label)
                recompute_trips()
                st.rerun()

    if st.session_state["applied_trip_refinements"]:
        applied = " · ".join(st.session_state["applied_trip_refinements"][-6:])
        st.caption(f"Raffinamenti viaggi applicati: {applied}")


# ---------------------------------------------------------------------------
# Confronto
# ---------------------------------------------------------------------------

def render_comparison(scored_all: pd.DataFrame) -> None:
    ids = list(st.session_state["compare_ids"])
    if len(ids) < 2:
        return
    st.markdown("### 📊 Confronto destinazioni")
    table = compare_destinations(scored_all, ids)
    st.dataframe(table, use_container_width=True)

    names = scored_all[scored_all["id"].isin(ids)]
    for _, row in names.iterrows():
        strengths = sorted(
            [("Avventura", row["adventure_score"]), ("Relax", row["relax_score"]),
             ("Cultura", row["culture_score"]), ("Romanticismo", row["romantic_score"]),
             ("Food", row["food_score"]), ("Luxury", row["luxury_score"])],
            key=lambda kv: kv[1], reverse=True,
        )[:2]
        strengths_text = " e ".join(f"{s}" for s, _ in strengths)
        st.markdown(f"**{row['name']}** brilla soprattutto per {strengths_text.lower()}.")

    if st.button("🧹 Svuota confronto"):
        st.session_state["compare_ids"] = set()
        st.rerun()
    st.divider()


def render_trip_comparison(candidates_all: pd.DataFrame) -> None:
    trip_ids = list(st.session_state["trip_compare_ids"])
    if len(trip_ids) < 2 or candidates_all is None or candidates_all.empty:
        return
    st.markdown("### 📊 Confronto viaggi combinati")
    table = compare_trips(candidates_all, trip_ids)
    st.dataframe(table, use_container_width=True)

    trips = candidates_all[candidates_all["trip_id"].isin(trip_ids)]
    for _, trip in trips.iterrows():
        strengths = sorted(
            [("Match", trip["trip_match_score"]), ("Feasibility", trip["feasibility_score"]),
             ("Travel Efficiency", trip["efficiency_score"]), ("Mood coverage", trip["mood_coverage"])],
            key=lambda kv: kv[1], reverse=True,
        )[:2]
        strengths_text = " e ".join(f"{s}" for s, _ in strengths)
        st.markdown(f"**{trip['name']}** brilla soprattutto per {strengths_text.lower()}.")

    if st.button("🧹 Svuota confronto viaggi"):
        st.session_state["trip_compare_ids"] = set()
        st.rerun()
    st.divider()


# ---------------------------------------------------------------------------
# Sorprendimi (destinazione singola O viaggio combinato)
# ---------------------------------------------------------------------------

def handle_surprise(
    results: pd.DataFrame, trip_results: pd.DataFrame, scored_all: pd.DataFrame, trip_bundle: dict | None,
    show_destinations: bool = True, show_trips: bool = True,
) -> None:
    """🎲 Sorprendimi: può restituire sia una destinazione singola sia un
    viaggio combinato. Sceglie con una moneta pesata verso le destinazioni
    quando non esistono viaggi combinati fattibili per la durata scelta.
    Rispetta il toggle "Cosa vuoi vedere?": se una delle due modalità è
    nascosta, la sorpresa non propone mai quel tipo di risultato."""
    can_trip = show_trips and trip_bundle is not None and not trip_bundle.get("candidates_all", pd.DataFrame()).empty
    want_trip = can_trip and (not show_destinations or random.random() < 0.4)

    if want_trip:
        exclude = {frozenset(ids) for ids in trip_results["stop_ids"].head(3)} | st.session_state["surprise_trip_exclude"]
        pick = surprise_trip(trip_bundle["candidates_all"], exclude_stopsets=exclude)
        if pick is not None:
            st.session_state["surprise_trip_pick"] = pick
            st.session_state["surprise_trip_exclude"].add(frozenset(pick["stop_ids"]))
            st.session_state["surprise_kind"] = "trip"
            st.session_state["surprise_pick"] = None
            st.rerun()
            return

    exclude_ids = set(results["id"].head(5).tolist()) | st.session_state["surprise_exclude"]
    pick = surprise_me(scored_all, exclude_ids=exclude_ids)
    if pick is not None:
        st.session_state["surprise_pick"] = pick
        st.session_state["surprise_exclude"].add(int(pick["id"]))
        st.session_state["surprise_kind"] = "destination"
        st.session_state["surprise_trip_pick"] = None
    st.rerun()


# ---------------------------------------------------------------------------
# Risultati
# ---------------------------------------------------------------------------

def render_results() -> None:
    bundle = st.session_state.get("results_bundle")
    if bundle is None:
        recompute_results()
        bundle = st.session_state["results_bundle"]

    render_travel_dna()

    results = bundle["results"]
    scored_all = bundle["scored_all"]

    if results.empty:
        st.info("Non abbiamo trovato destinazioni che rispettino tutti i criteri scelti. Prova ad allargare un po' l'area geografica o il budget: il match perfetto probabilmente c'è, dobbiamo solo cercarlo con meno vincoli. 🧭")
        return

    if bundle["strict_count"] == 0:
        st.info("Nessuna destinazione rispetta perfettamente tutti i criteri: ti mostriamo comunque le migliori alternative, con qualche piccolo compromesso spiegato in ogni card. 🤝")
    elif bundle["used_compromise"]:
        st.info(f"Solo {bundle['strict_count']} destinazion{'e' if bundle['strict_count'] == 1 else 'i'} rispettano perfettamente tutti i criteri. Ti mostriamo anche qualche alternativa con un piccolo compromesso.")

    period = st.session_state["prefs"].get("period")
    if period in CHRISTMAS_LIKE:
        render_christmas_spotlight(scored_all)

    trip_bundle = st.session_state.get("trip_bundle")
    if trip_bundle is None:
        recompute_trips()
        trip_bundle = st.session_state["trip_bundle"]
    trip_results = trip_bundle["results"] if trip_bundle is not None else pd.DataFrame()

    st.markdown("##### 👀 Cosa vuoi vedere?")
    view_mode = st.radio(
        "Modalità risultati",
        ["🌍 Solo destinazioni", "✈️ Solo viaggi combinati", "🔀 Entrambi"],
        index=2, horizontal=True, key="results_view_mode", label_visibility="collapsed",
    )
    show_destinations = view_mode != "✈️ Solo viaggi combinati"
    show_trips = view_mode != "🌍 Solo destinazioni"

    display_mode = st.radio(
        "Vista risultati",
        ["📋 Vista compatta", "📖 Vista dettagliata"],
        index=0, horizontal=True, key="destination_display_mode", label_visibility="collapsed",
    )
    compact = display_mode == "📋 Vista compatta"

    departure_city = st.session_state["prefs"].get("departure_city")
    if departure_city:
        st.caption(f"✈️ Stime di volo calcolate per partenze da {DEPARTURE_CITY_OPTIONS[departure_city].split(' ', 1)[-1]}.")

    top = st.columns([1, 3])
    with top[0]:
        if st.button("🎲 SORPRENDIMI", use_container_width=True, type="secondary"):
            handle_surprise(results, trip_results, scored_all, trip_bundle, show_destinations, show_trips)

    if st.session_state.get("surprise_kind") == "destination" and st.session_state.get("surprise_pick") is not None:
        render_destination_card(st.session_state["surprise_pick"], surprise=True, compact=compact)
    elif st.session_state.get("surprise_kind") == "trip" and st.session_state.get("surprise_trip_pick") is not None:
        render_trip_card(st.session_state["surprise_trip_pick"], surprise=True, compact=compact)

    if show_destinations:
        st.markdown("### 🏆 Destinazioni")
        st.caption("Le migliori mete singole per le tue preferenze.")
        shown = st.session_state["shown_count"]
        for rank, (_, row) in enumerate(results.head(shown).iterrows()):
            render_destination_card(row, rank=rank, compact=compact)

        if shown < len(results):
            if st.button(f"⬇️ Mostra altre destinazioni ({len(results) - shown} disponibili)", use_container_width=True):
                st.session_state["shown_count"] = min(len(results), shown + 5)
                st.rerun()

        shown_ids = set(results.head(shown)["id"].tolist())
        render_anti_fomo(discarded_destination_alternatives(scored_all, shown_ids))

        if show_trips:
            st.divider()

    if show_trips:
        st.markdown("### ✈️ Viaggi combinati")
        st.caption('"Più destinazioni" non significa viaggio migliore: qui trovi solo itinerari di 2-3 tappe davvero fattibili, non semplici combinazioni ad alto punteggio.')
        if trip_results.empty:
            st.info("Per la durata e le preferenze scelte, un viaggio combinato non aggiungerebbe valore. Una singola destinazione ben vissuta resta la scelta migliore. 🎯")
        else:
            if trip_bundle["used_compromise"]:
                st.info(f"Solo {trip_bundle['strict_count']} itinerar{'io' if trip_bundle['strict_count'] == 1 else 'i'} rispetta pienamente i criteri di fattibilità. Ti mostriamo anche qualche alternativa con un piccolo compromesso.")
            shown_trips = st.session_state["shown_trip_count"]
            for rank, (_, trip) in enumerate(trip_results.head(shown_trips).iterrows()):
                render_trip_card(trip, rank=rank, compact=compact)
            if shown_trips < len(trip_results):
                if st.button(f"⬇️ Mostra altri viaggi combinati ({len(trip_results) - shown_trips} disponibili)", use_container_width=True):
                    st.session_state["shown_trip_count"] = min(len(trip_results), shown_trips + 3)
                    st.rerun()

            shown_trip_ids = set(trip_results.head(shown_trips)["trip_id"].tolist())
            candidates_all = trip_bundle["candidates_all"] if trip_bundle is not None else None
            render_anti_fomo(discarded_trip_alternatives(candidates_all, shown_trip_ids))

    st.divider()
    render_refinement_bar()
    st.divider()
    render_comparison(scored_all)
    render_trip_comparison(trip_bundle["candidates_all"] if trip_bundle is not None else None)

    st.markdown("### 🔁 Vuoi ripartire?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Rifai il questionario"):
            go("questionnaire")
            st.rerun()
    with c2:
        if st.button("🏠 Torna alla home"):
            reset_to_landing()
            st.rerun()


def render_surprise_direct() -> None:
    st.markdown("## 🎲 Non hai idea? Ci pensiamo noi.")
    render_travel_dna()
    bundle = st.session_state["results_bundle"]
    scored_all = bundle["scored_all"]
    pick = surprise_me(scored_all, min_score=55.0)
    if pick is None:
        st.error("Non siamo riusciti a trovare una destinazione. Prova il questionario completo!")
        return
    render_destination_card(pick, surprise=True)

    st.markdown("#### Non ti convince? Ecco altre 5 idee ad ampio spettro:")
    for rank, (_, row) in enumerate(scored_all.head(6).iterrows()):
        if row["id"] == pick["id"]:
            continue
        render_destination_card(row, rank=rank)

    if st.button("📝 Preferisco rispondere a qualche domanda in più"):
        go("questionnaire")
        st.rerun()


# ---------------------------------------------------------------------------
# Modalità Regalo / Sorpresa
# ---------------------------------------------------------------------------

def render_gift_surprise() -> None:
    st.markdown(
        """
        <div class="tm-hero" style="text-align:center;">
            <h1>🎁 Un regalo di viaggio</h1>
            <p>Hai scelto di preparare una sorpresa (per qualcuno, o per te stesso/a).
            Quando sei pronto/a, scoprila.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.get("gift_revealed"):
        _, center, _ = st.columns([1, 1, 1])
        with center:
            if st.button("🎁 Scopri il regalo", use_container_width=True, type="primary"):
                bundle = st.session_state.get("results_bundle")
                scored_all = bundle["scored_all"] if bundle is not None else pd.DataFrame()
                st.session_state["gift_pick"] = surprise_me(scored_all, min_score=60.0)
                st.session_state["gift_revealed"] = True
                st.rerun()
        if st.button("⬅️ Torna alla home"):
            reset_to_landing()
            st.rerun()
        return

    pick = st.session_state.get("gift_pick")
    if pick is None:
        st.info(
            "Non siamo riusciti a preparare un regalo con questi criteri. "
            "Prova a ripartire dal questionario completo per qualcosa di più su misura."
        )
    else:
        st.balloons()
        st.markdown("## 🎉 Ecco il regalo!")
        render_destination_card(pick, surprise=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎁 Un altro regalo, per favore"):
            st.session_state["gift_pick"] = None
            st.session_state["gift_revealed"] = False
            st.rerun()
    with c2:
        if st.button("🏠 Torna alla home", key="gift_home_button"):
            reset_to_landing()
            st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ✈️ TravelMatch")
        st.caption("Il tuo motore di raccomandazione viaggi, offline e su misura.")

        if st.session_state.get("favorites"):
            st.markdown(f"❤️ **{len(st.session_state['favorites'])}** destinazioni nei preferiti")
        if st.session_state.get("trip_favorites"):
            st.markdown(f"❤️ **{len(st.session_state['trip_favorites'])}** viaggi combinati nei preferiti")

        if st.session_state.get("prefs") is not None:
            # Il file scaricato resta sul dispositivo del visitatore, non sul
            # server: su una versione online condivisa da più persone, un
            # unico file salvato lato server finirebbe sovrascritto a ogni
            # utente (e visibile a chiunque lo ricarichi) — qui invece ognuno
            # gestisce il proprio file, in locale o online allo stesso modo.
            df = load_destinations_df()
            fav_rows = df[df["id"].isin(st.session_state["favorites"])][["id", "name", "country"]]
            results = st.session_state["results_bundle"]["results"] if st.session_state.get("results_bundle") is not None else pd.DataFrame()
            top_summary = results.head(5)[["id", "name", "match_score"]].to_dict("records") if not results.empty else []
            trip_bundle = st.session_state.get("trip_bundle")
            trip_results = trip_bundle["results"] if trip_bundle is not None else pd.DataFrame()
            top_trip_summary = (
                trip_results.head(3)[["trip_id", "name", "trip_match_score", "feasibility_score"]].to_dict("records")
                if not trip_results.empty else []
            )
            saved_state = {
                "prefs": st.session_state["prefs"],
                "dna": st.session_state["dna"],
                "favorite_ids": list(st.session_state["favorites"]),
                "favorites": fav_rows.to_dict("records"),
                "top_results": top_summary,
                "favorite_trip_ids": list(st.session_state["trip_favorites"]),
                "top_trips": top_trip_summary,
            }
            st.download_button(
                "💾 Scarica questa ricerca",
                data=json.dumps(saved_state, ensure_ascii=False, indent=2, default=str),
                file_name="travelmatch_ricerca.json", mime="application/json", use_container_width=True,
            )

        if st.button("🔄 Ricomincia da capo", use_container_width=True):
            reset_to_landing()
            st.rerun()

        st.divider()
        st.caption("TravelMatch v2.0 — dataset locale, 67 destinazioni + Trip Builder, nessuna connessione richiesta.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    init_state()
    period = (st.session_state.get("prefs") or {}).get("period") if st.session_state.get("prefs") else None
    inject_css(christmas_mode=period in CHRISTMAS_LIKE)
    render_sidebar()

    stage = st.session_state["stage"]
    if stage == "landing":
        render_landing()
    elif stage == "questionnaire":
        render_questionnaire()
    elif stage == "results":
        render_results()
    elif stage == "surprise_direct":
        render_surprise_direct()
    elif stage == "gift_surprise":
        render_gift_surprise()
    else:
        render_landing()


if __name__ == "__main__":
    main()
