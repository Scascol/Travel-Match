"""
TravelMatch — l'app che ti aiuta a scegliere dove andare davvero in vacanza.

Avvio:
    streamlit run app.py

Interfaccia Streamlit: la logica di raccomandazione vive in recommender.py,
il dataset in destinations.py, le utility in utils.py. Questo file si
occupa solo di presentazione e gestione dello stato utente.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import math

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
    requested_months,
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
from export import (
    build_pdf_bytes,
    export_destination_as_stories,
    export_destination_as_text,
    export_trip_as_text_with_budget,
)
from insights import (
    accessible_alternatives,
    destination_warnings,
    discarded_destination_alternatives,
    discarded_trip_alternatives,
    dna_vs_destination,
    emotional_takeaways,
    narrative_explanation,
    organizational_ease,
    seasonality_months,
    seasonality_note,
    trip_organizational_ease,
    trip_warnings,
    travel_style_scores,
    travel_style_scores_for_stops,
    typical_day,
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
    PACE_DESCRIPTIONS,
    PACE_LABELS,
    PEOPLE_OPTIONS,
    PERIOD_OPTIONS,
    QUICK_START_OPTIONS,
    REFINEMENT_ACTIONS,
    SOCIAL_PREFERENCE_OPTIONS,
    TRAVELLER_MODE_BY_PEOPLE,
    TRAVELLER_MODE_LABELS,
    TRAVELLER_STAY_HINTS,
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
    # "auto" (non "expanded"): su desktop la sidebar resta aperta come prima,
    # ma su schermi stretti (mobile) parte chiusa invece di coprire l'intero
    # contenuto — Streamlit decide da solo in base alla larghezza reale.
    initial_sidebar_state="auto",
)

PEOPLE_HEADCOUNT = {"Solo": 1, "Coppia": 2, "Amici": 4, "Famiglia": 4, "Gruppo": 6}


# ---------------------------------------------------------------------------
# Stile
# ---------------------------------------------------------------------------

def inject_css(christmas_mode: bool = False) -> None:
    # Palette "cielo": azzurri per aria/leggerezza, navy per il testo (massima
    # leggibilità senza dover ricorrere al nero puro), verde/arancio riservati
    # a segnali di stato (successo/compromesso) così restano distinguibili
    # dal blu che domina il resto dell'interfaccia.
    primary = "#4A90E2"
    primary_light = "#E3F2FD"
    primary_soft = "#BBDEFB"
    accent = "#1E88E5"
    bg = "#F5F9FC"
    success = "#43A047"
    success_light = "#E8F5E9"
    warning = "#FB8C00"
    warning_light = "#FFF3E0"
    festive = "#D32F2F" if christmas_mode else warning
    festive_light = "#FDE7E7" if christmas_mode else warning_light
    festive_border = "#F5B8B8" if christmas_mode else "#FFCC80"
    ink = "#1A237E"
    ink_muted = "#546E7A"
    line = primary_light
    line_strong = primary_soft
    display_font = "'Poppins', 'Trebuchet MS', sans-serif"
    body_font = "'Inter', 'Segoe UI', sans-serif"
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        /* Forziamo esplicitamente colori chiari/testo scuro: l'app è
        progettata per un tema chiaro (vedi .streamlit/config.toml), ma
        questa regola è una rete di sicurezza nel caso il browser/sistema
        forzi comunque una preferenza di colore diversa. */
        .stApp {{
            background: linear-gradient(180deg, {bg} 0%, {primary_light} 100%);
            color: {ink};
        }}
        /* !important necessario: lo stile tipografico integrato di
        Streamlit usa selettori più specifici dei nostri (es. scoped ai
        propri contenitori), quindi vincerebbe altrimenti la cascata.
        Escludiamo esplicitamente [data-testid="stIconMaterial"]: sono le
        icone (freccine, download, ecc.) disegnate da Streamlit tramite un
        font a legature (il testo "keyboard_arrow_right" ecc. diventa un
        glifo solo con QUEL font) — forzare Inter anche lì rompe le
        legature e mostra il nome dell'icona come testo sovrapposto invece
        del disegno. */
        .stApp, .stApp p, .stApp span:not([data-testid="stIconMaterial"]), .stApp label, .stApp li {{
            font-family: {body_font} !important;
            color: {ink};
        }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
            font-family: {display_font} !important;
            font-weight: 700 !important;
            text-wrap: balance;
            color: {ink};
        }}
        .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{
            color: {ink_muted} !important;
        }}
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {line_strong} 15%, {line_strong} 85%, transparent);
            margin: 1.7rem 0;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, {primary_light} 100%);
            border-right: 1px solid {line};
        }}
        .tm-sidebar-brand {{
            font-family: {display_font};
            font-size: 1.4rem;
            font-weight: 800;
            color: {ink};
            margin-bottom: 0.15rem;
        }}
        .tm-sidebar-tag {{
            font-family: {body_font};
            font-size: 0.85rem;
            color: {ink_muted};
            margin-bottom: 1.1rem;
        }}

        /* --- Pulsanti: selettori data-testid stabili di Streamlit, non
        classi generate automaticamente (che cambiano tra versioni). --- */
        button[data-testid="stBaseButton-primary"], button[data-testid="stFormSubmitButton-primary"] {{
            font-family: {display_font};
            font-weight: 600;
            letter-spacing: 0.01em;
            border: none;
            border-radius: 14px;
            /* Gradiente scuro→accent: bianco su #1E88E5 supera 4.5:1, su
            #4A90E2 no — il pulsante primario deve restare leggibile. */
            background: linear-gradient(135deg, #1565C0 0%, {accent} 100%);
            box-shadow: 0 6px 16px -4px rgba(21, 101, 192, 0.45);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stFormSubmitButton-primary"]:hover {{
            transform: translateY(-1px);
            box-shadow: 0 8px 20px -4px rgba(21, 101, 192, 0.55);
        }}
        button[data-testid="stBaseButton-secondary"], button[data-testid="stFormSubmitButton-secondary"] {{
            font-family: {display_font};
            font-weight: 600;
            border-radius: 14px;
            border: 1.5px solid {line_strong};
            background: #FFFFFF;
            color: {accent};
            transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
        }}
        button[data-testid="stBaseButton-secondary"]:hover, button[data-testid="stFormSubmitButton-secondary"]:hover {{
            border-color: {accent};
            background: {primary_light};
            transform: translateY(-1px);
        }}
        div[data-testid="stExpander"] {{
            border-radius: 14px !important;
            border-color: {line_strong} !important;
            background: #FFFFFF;
        }}
        div[data-testid="stExpander"] summary {{
            font-weight: 600;
            color: {ink};
        }}

        /* --- Card: individuate via un marcatore invisibile inserito come
        primo elemento di ogni st.container(border=True) (vedi
        render_destination_card/render_trip_card/render_anti_fomo/ecc. in
        app.py), non via le classi auto-generate di Streamlit — quelle
        cambiano hash a ogni versione/build e romperebbero lo stile al
        primo aggiornamento di Streamlit Cloud. */
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"]:first-child span.tm-card-marker-primary) {{
            border: 1px solid {line} !important;
            border-radius: 20px !important;
            background: #FFFFFF;
            box-shadow: 0 2px 4px rgba(26, 35, 126, 0.03), 0 14px 28px -14px rgba(74, 144, 226, 0.28);
            padding: 1.5rem 1.7rem !important;
            margin-bottom: 1.3rem;
            transition: box-shadow 0.18s ease, transform 0.18s ease;
        }}
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"]:first-child span.tm-card-marker-primary):hover {{
            box-shadow: 0 4px 10px rgba(26, 35, 126, 0.05), 0 20px 36px -14px rgba(74, 144, 226, 0.38);
            transform: translateY(-2px);
        }}
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"]:first-child span.tm-card-marker-light) {{
            border: 1px solid {line_strong} !important;
            border-radius: 16px !important;
            background: {primary_light};
            box-shadow: none !important;
            padding: 1.1rem 1.3rem !important;
            margin-bottom: 1.1rem;
        }}
        /* --- Card "domanda" del questionario: stesso marcatore-invisibile,
        classe dedicata per non confondersi con le card dei risultati. --- */
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"]:first-child span.tm-q-marker) {{
            border: 1px solid {line} !important;
            border-radius: 18px !important;
            background: #FFFFFF;
            box-shadow: 0 8px 20px -14px rgba(74, 144, 226, 0.35);
            padding: 1.3rem 1.6rem 1rem !important;
            margin-bottom: 1.1rem;
        }}
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"]:first-child span.tm-q-marker) h5 {{
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            margin-top: 0.3rem;
            margin-bottom: 0.1rem;
        }}
        .tm-q-step {{
            display: inline-block;
            font-family: {body_font};
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {accent};
            background: {primary_light};
            border: 1px solid {line_strong};
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
        }}

        .tm-hero {{
            position: relative;
            overflow: hidden;
            /* Parte dall'accent (non dal primary chiaro): il testo bianco
            dell'hero deve restare leggibile anche nell'angolo più chiaro
            del gradiente — con #4A90E2 il contrasto scendeva sotto 3:1. */
            background: linear-gradient(135deg, {accent} 0%, #1565C0 45%, {ink} 100%);
            padding: 3rem 2.6rem;
            border-radius: 28px;
            color: white;
            margin-bottom: 1.8rem;
            box-shadow: 0 20px 45px -14px rgba(30, 136, 229, 0.45);
        }}
        /* Nuvole morbide sullo sfondo dell'hero: puro CSS, nessuna immagine
        da caricare, per rinforzare la sensazione "cielo" senza appesantire. */
        .tm-hero::before, .tm-hero::after {{
            content: "";
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.14);
            pointer-events: none;
        }}
        .tm-hero::before {{ width: 22rem; height: 22rem; top: -10rem; right: -6rem; }}
        .tm-hero::after {{ width: 14rem; height: 14rem; bottom: -7rem; left: 8%; background: rgba(255, 255, 255, 0.08); }}
        .tm-hero > * {{ position: relative; z-index: 1; }}
        .tm-hero h1 {{
            font-family: {display_font};
            font-size: 2.75rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin-bottom: 0.5rem;
            color: #FFFFFF !important;
        }}
        /* `color` esplicito (non ereditato da .tm-hero): la regola globale
        `.stApp p` colora il <p> direttamente, e il targeting diretto batte
        sempre l'ereditarietà — senza questa riga il testo dell'hero
        tornerebbe navy su fondo blu. */
        .tm-hero p, .tm-hero p b {{
            font-family: {body_font};
            font-size: 1.15rem;
            line-height: 1.55;
            color: #FFFFFF !important;
            opacity: 0.95;
            margin-bottom: 0;
            max-width: 600px;
        }}
        /* Variante landing: hero centrato e più arioso — è la prima cosa
        che si vede, deve dare respiro prima ancora che informazione. */
        .tm-hero-landing {{
            text-align: center;
            padding: 4rem 2.6rem;
        }}
        .tm-hero-landing p {{
            margin-left: auto;
            margin-right: auto;
            font-size: 1.22rem;
        }}
        .tm-landing-divider {{
            text-align: center;
            font-family: {body_font};
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {ink_muted};
            margin: 2.2rem 0 1.1rem;
        }}
        /* Intestazione di pagina leggera (questionario / risultati): stessa
        aria dell'hero ma senza il blocco colorato, che a metà flusso
        peserebbe più di quanto orienti. */
        .tm-page-head {{
            margin: 0.2rem 0 1.5rem;
        }}
        .tm-page-head h2 {{
            font-family: {display_font};
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin: 0 0 0.3rem;
            color: {ink};
        }}
        .tm-page-head p {{
            font-family: {body_font};
            color: {ink_muted};
            font-size: 1rem;
            margin: 0;
        }}
        .tm-results-header {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            background: linear-gradient(90deg, {primary_light} 0%, #FFFFFF 100%);
            border: 1px solid {line_strong};
            border-radius: 16px;
            padding: 0.85rem 1.3rem;
            margin-bottom: 1.2rem;
            font-family: {display_font};
            font-weight: 700;
            font-size: 1.05rem;
            color: {ink};
        }}
        .tm-badge {{
            display: inline-block;
            font-family: {body_font};
            padding: 0.3rem 0.85rem;
            border-radius: 999px;
            background: {primary_light};
            color: {accent};
            font-size: 0.82rem;
            font-weight: 600;
            margin: 0.15rem 0.3rem 0.15rem 0;
            border: 1px solid {line_strong};
        }}
        .tm-badge-festive {{
            background: {festive_light};
            color: {festive};
            border: 1px solid {festive_border};
        }}
        .tm-match-pill {{
            display: inline-block;
            font-family: {display_font};
            padding: 0.4rem 1.1rem;
            border-radius: 999px;
            font-weight: 800;
            font-size: 1.05rem;
            color: white;
            box-shadow: 0 4px 10px -2px rgba(26, 35, 126, 0.3);
        }}
        .tm-card-title {{
            font-family: {display_font};
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin-bottom: 0;
            color: {ink};
        }}
        .tm-card-sub {{
            font-family: {body_font};
            color: {ink_muted};
            font-size: 0.95rem;
            margin-top: -0.15rem;
        }}
        /* Le sezioni dentro il dettaglio card sono molte e ravvicinate:
        senza un margine superiore generoso il titolo di una sezione sembra
        appartenere al blocco precedente invece di aprire il successivo.
        Il primo titolo di un contenitore non ha bisogno dello stacco. */
        .tm-section-title {{
            font-family: {body_font};
            font-weight: 700;
            color: {accent};
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            /* !important: Streamlit azzera i margini dei <p> dentro i propri
            contenitori con selettori piu' specifici dei nostri — senza
            questo il margine superiore veniva semplicemente ignorato e le
            sezioni restavano attaccate. */
            margin-top: 2.1rem !important;
            margin-bottom: 0.55rem !important;
            padding-top: 0.9rem;
            border-top: 1px solid {line};
        }}
        /* Nessuna riga sopra il primo titolo di una colonna/contenitore:
        lì il bordo della card fa già da separatore. */
        div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:first-child .tm-section-title,
        div[data-testid="column"] > div > div[data-testid="stElementContainer"]:first-child .tm-section-title {{
            margin-top: 0.6rem !important;
            padding-top: 0;
            border-top: none;
        }}
        .tm-cost-line {{
            font-size: 0.92rem;
            color: {ink_muted};
        }}
        .tm-quote {{
            font-style: italic;
            color: {ink};
            background: {primary_light};
            padding: 0.7rem 1rem;
            border-left: 4px solid {primary};
            border-radius: 8px;
        }}
        .tm-surprise-box {{
            background: linear-gradient(120deg, {primary_soft} 0%, {primary} 100%);
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
            background: {primary_light};
            border-left: 4px solid {primary};
        }}
        .tm-timeline-transfer {{
            background: {warning_light};
            border-left: 4px solid {warning};
            font-style: italic;
        }}
        .tm-timeline-day {{
            font-weight: 700;
            color: {ink_muted};
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
        /* L'Economico ha un bordo pieno: è lo scenario su cui il motore
        calcola davvero il match col budget (vedi recommender._budget_match),
        gli altri due sono informativi. */
        .tm-scenario-economico {{ background: {success_light}; color: #1B5E20; border-left: 4px solid {success}; }}
        .tm-scenario-medio {{ background: {warning_light}; color: #B45300; font-weight: 700; }}
        .tm-scenario-comodo {{ background: {primary_light}; color: #0D47A1; }}
        /* Striscia metriche della card: il costo "da" domina, le altre
        metriche restano leggibili ma chiaramente secondarie. */
        .tm-metric-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.9rem 0 0.2rem;
        }}
        .tm-metric {{
            flex: 1 1 6.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
            padding: 0.6rem 0.9rem;
            border-radius: 14px;
            background: {bg};
            border: 1px solid {line};
        }}
        .tm-metric-primary {{
            background: {primary_light};
            border-color: {line_strong};
        }}
        .tm-metric-value {{
            font-family: {display_font};
            font-weight: 700;
            font-size: 1rem;
            color: {ink};
            line-height: 1.25;
        }}
        .tm-metric-primary .tm-metric-value {{
            font-size: 1.22rem;
            font-weight: 800;
            color: {accent};
        }}
        .tm-metric-label {{
            font-family: {body_font};
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {ink_muted};
        }}
        .tm-badge-pace {{
            background: #FFFFFF;
            border-color: {primary};
            color: {accent};
        }}

        /* Striscia stagionalità: 12 caselle, una per mese. */
        .tm-month-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.22rem;
            margin-bottom: 0.4rem;
        }}
        .tm-month {{
            flex: 1 1 auto;
            min-width: 2.1rem;
            text-align: center;
            padding: 0.28rem 0.1rem;
            border-radius: 7px;
            font-size: 0.72rem;
            font-weight: 600;
            background: {bg};
            border: 1px solid {line};
            color: {ink_muted};
        }}
        .tm-month-best {{
            background: {success_light};
            border-color: {success};
            color: #1B5E20;
        }}
        /* Il mese scelto dall'utente ha un contorno spesso: si deve capire
        subito se cade dentro o fuori la finestra buona. */
        .tm-month-picked {{
            outline: 2px solid {accent};
            outline-offset: -2px;
        }}

        /* Giornata tipo */
        .tm-day-row {{
            display: flex;
            gap: 0.7rem;
            align-items: baseline;
            padding: 0.4rem 0.7rem;
            border-radius: 10px;
            background: {primary_light};
            margin-bottom: 0.3rem;
        }}
        .tm-day-slot {{
            min-width: 8rem;
            flex-shrink: 0;
            font-weight: 700;
            font-size: 0.85rem;
            color: {accent};
        }}
        .tm-day-text {{ font-size: 0.92rem; color: {ink}; }}

        .tm-takeaway {{
            padding: 0.45rem 0.8rem;
            border-left: 3px solid {primary};
            background: {bg};
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.3rem;
            font-size: 0.92rem;
        }}

        /* Confronto DNA: due barre sovrapposte nella stessa traccia. */
        .tm-dna-row {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.3rem;
        }}
        .tm-dna-label {{
            min-width: 7.5rem;
            flex-shrink: 0;
            font-size: 0.82rem;
            color: {ink_muted};
        }}
        .tm-dna-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 1.1rem;
            margin-bottom: 0.6rem;
            font-size: 0.8rem;
            color: {ink_muted};
        }}
        .tm-dna-legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .tm-dna-swatch {{
            width: 1.6rem;
            height: 0.7rem;
            border-radius: 999px;
            display: inline-block;
            flex-shrink: 0;
        }}
        .tm-dna-swatch-user {{ background: {ink}; opacity: 0.75; }}
        .tm-dna-swatch-dest {{ background: {primary}; opacity: 0.55; }}
        .tm-dna-status {{
            min-width: 5.6rem;
            flex-shrink: 0;
            text-align: right;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .tm-dna-status-match {{ color: {success}; }}
        .tm-dna-status-more {{ color: {accent}; }}
        .tm-dna-status-less {{ color: {warning}; }}
        .tm-dna-track {{
            position: relative;
            flex-grow: 1;
            height: 1.05rem;
            background: {primary_light};
            border-radius: 999px;
            overflow: hidden;
        }}
        .tm-dna-fill {{
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            border-radius: 999px;
        }}
        .tm-dna-user {{ background: {ink}; opacity: 0.75; }}
        /* La barra della meta è sopra ma semitrasparente: si leggono
        entrambe anche quando una contiene l'altra. */
        .tm-dna-dest {{ background: {primary}; opacity: 0.55; }}

        .tm-radar-wrap {{ max-width: 360px; margin: 0 auto; }}
        .tm-radar-legend {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.9rem;
            margin-top: 0.2rem;
        }}
        .tm-radar-legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.82rem;
            color: {ink_muted};
        }}
        .tm-radar-swatch {{
            width: 0.8rem;
            height: 0.8rem;
            border-radius: 4px;
            display: inline-block;
        }}

        .tm-style-row {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.3rem;
        }}
        .tm-style-label {{
            min-width: 6.5rem;
            font-size: 0.88rem;
            color: {ink_muted};
            flex-shrink: 0;
        }}
        .tm-style-track {{
            flex-grow: 1;
            height: 0.55rem;
            background: {primary_light};
            border-radius: 999px;
            overflow: hidden;
        }}
        .tm-style-fill {{
            height: 100%;
            background: linear-gradient(90deg, {primary} 0%, {accent} 100%);
            border-radius: 999px;
        }}
        .tm-style-value {{
            min-width: 2.4rem;
            text-align: right;
            font-size: 0.85rem;
            color: {ink_muted};
            flex-shrink: 0;
        }}
        .tm-warning-line {{
            background: {warning_light};
            color: #8A5200;
            border-left: 4px solid {warning};
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
        "first_solo_hint", "controlled_pick", "controlled_searched",
    ] + [k for k in st.session_state if k.startswith("q_")]
    keys_to_clear += [k for k in st.session_state if k.startswith("cs_")]
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

    # "primo viaggio da solo/a" è una modalità a sé (checklist e avvisi
    # dedicati), non deducibile da "Solo": la imposta il quick-start.
    traveller_mode = (
        "primo_solo" if st.session_state.get("first_solo_hint") and values["people"] == "Solo"
        else TRAVELLER_MODE_BY_PEOPLE.get(values["people"], "solo")
    )

    return {
        "budget_range": (budget_low, budget_high),
        "people": values["people"],
        "traveller_mode": traveller_mode,
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
        # 1 = nessun filtro (vedi render_questionnaire): lo teniamo come None
        # per non far apparire un filtro attivo quando non lo è.
        "min_ease": values.get("min_ease") if values.get("min_ease", 1) > 1 else None,
    }


def neutral_prefs() -> dict:
    return {
        "budget_range": (0, 100000),
        "people": "Indifferente",
        "traveller_mode": None,
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
        "min_ease": None,
    }


def _prepared_df() -> pd.DataFrame:
    """Il dataset pronto per il motore: stime di volo aggiustate per la città
    di partenza, più il filtro di facilità organizzativa se l'utente ne ha
    chiesto uno.

    Il filtro vive qui e non in recommender.py di proposito:
    `organizational_ease` è una lettura di presentazione (insights.py), e far
    dipendere il motore di scoring da un modulo di presentazione
    invertirebbe la direzione delle dipendenze dell'intera architettura.
    Se il filtro azzerasse i risultati lo ignoriamo: meglio mostrare mete
    "più impegnative" che una pagina vuota senza spiegazione."""
    prefs = st.session_state["prefs"]
    df = load_destinations_df()
    df = adjust_destinations_for_departure(df, prefs.get("departure_city"))

    min_ease = prefs.get("min_ease")
    if min_ease:
        df = df.copy()
        df["organizational_ease"] = df.apply(organizational_ease, axis=1)
        filtered = df[df["organizational_ease"] >= min_ease]
        if not filtered.empty:
            df = filtered
    return df


def recompute_results(top_n: int = 20) -> None:
    df = _prepared_df()
    bundle = get_recommendations(
        df, st.session_state["prefs"], st.session_state["weights"], st.session_state["boosts"], top_n=top_n,
    )
    st.session_state["results_bundle"] = bundle
    st.session_state["shown_count"] = 5
    recompute_trips()


def recompute_trips() -> None:
    df = _prepared_df()
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
    # Hero centrato e volutamente scarno: una promessa in una riga sola.
    # Tutto il "come funziona" è stato tolto — si capisce facendo, non
    # leggendo, e il testo lungo era la cosa che appesantiva di più la home.
    st.markdown(
        """
        <div class="tm-hero tm-hero-landing">
            <h1>✈️ TravelMatch</h1>
            <p>Dove dovresti andare <b>davvero</b> in vacanza?<br>
            Rispondi a qualche domanda, ci pensiamo noi.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA principale centrata e isolata: è l'unica azione che vogliamo
    # davvero far notare al primo colpo d'occhio.
    _, cta, _ = st.columns([1, 1.6, 1])
    with cta:
        if st.button("Inizia il questionario", use_container_width=True, type="primary"):
            go("questionnaire")
            st.rerun()

    st.markdown('<p class="tm-landing-divider">oppure parti da un\'idea</p>', unsafe_allow_html=True)

    # Griglia a 3 colonne (invece di 4): pulsanti più larghi, etichette che
    # non vanno a capo, più aria tra una scorciatoia e l'altra.
    cols = st.columns(3)
    for i, (key, label) in enumerate(QUICK_START_OPTIONS):
        with cols[i % 3]:
            if st.button(label, use_container_width=True, key=f"quick_{key}"):
                handle_quick_start(key)

    st.write("")
    _, loader, _ = st.columns([1, 2, 1])
    with loader:
        with st.expander("📂 Hai già una ricerca salvata?"):
            uploaded = st.file_uploader(
                "Carica il file .json scaricato in precedenza",
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
    elif key == "controlled_surprise":
        st.session_state["controlled_pick"] = None
        st.session_state["controlled_searched"] = False
        go("controlled_surprise")
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
        # Flag di sessione (non un widget): distingue "primo viaggio da
        # solo/a" dal semplice "Solo" quando si costruiscono le prefs, e
        # sblocca checklist e avvisi dedicati.
        st.session_state["first_solo_hint"] = True
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


QUESTION_STEPS_TOTAL = 8


@contextlib.contextmanager
def _question_card(step: int, title: str, hint: str | None = None):
    """Una domanda (o un gruppo logico di domande) dentro la propria card.

    Il marcatore invisibile `tm-q-marker` è lo stesso trucco usato dalle card
    dei risultati (vedi inject_css): stilizza il container senza dipendere
    dalle classi auto-generate di Streamlit, che cambiano hash a ogni build.
    L'indicatore "Domanda X di N" dà orientamento senza fingere un wizard a
    step: il form resta una pagina sola, inviata una volta."""
    with st.container(border=True):
        st.markdown('<span class="tm-card-marker tm-q-marker"></span>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="tm-q-step">Domanda {step} di {QUESTION_STEPS_TOTAL}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"##### {title}")
        if hint:
            st.caption(hint)
        yield


def render_questionnaire() -> None:
    st.markdown(
        """
        <div class="tm-page-head">
            <h2>📝 Raccontaci come vuoi la tua vacanza</h2>
            <p>8 domande veloci. Nessuna è obbligatoria: più rispondi, più il match è preciso.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tutti i widget hanno una key esplicita e stabile (q_*): è ciò che permette
    # sia alla precompilazione da quick-start (vedi handle_quick_start) sia alla
    # selezione manuale dell'utente di sopravvivere al rerun scatenato dal
    # submit del form, invece di essere azzerate.
    with st.form("questionnaire_form"):
        with _question_card(1, "💰 Qual è il tuo budget?",
                            "Lo confrontiamo con lo scenario più economico di ogni meta (hostel/1-2★)."):
            c1, c2 = st.columns([2, 1])
            with c1:
                budget_band = st.select_slider(
                    "Fascia di budget", options=list(BUDGET_BANDS.keys()),
                    value="1.000 - 1.500 €", key="q_budget_band",
                )
            with c2:
                budget_scope = st.radio("Il budget è:", ["Per persona", "Totale per il gruppo"], index=0, key="q_budget_scope")

        with _question_card(2, "👥 Con chi parti, e da dove?"):
            people = st.radio(
                "Persone", PEOPLE_OPTIONS, horizontal=True, key="q_people",
                **_default_kwargs("q_people", index=1),
            )
            departure_city = st.radio(
                "Città di partenza", list(DEPARTURE_CITY_OPTIONS.keys()), horizontal=True,
                format_func=lambda k: DEPARTURE_CITY_OPTIONS[k], key="q_departure_city",
                **_default_kwargs("q_departure_city", index=2),
            )
            st.caption("Milano o Roma affinano le stime di volo.")

        with _question_card(3, "📅 Quando vuoi partire?"):
            period = st.selectbox(
                "Periodo", PERIOD_OPTIONS, key="q_period", label_visibility="collapsed",
                **_default_kwargs("q_period", index=PERIOD_OPTIONS.index("🏃 Weekend")),
            )
            if period in CHRISTMAS_LIKE:
                st.caption("Riferimento: Natale 2026 / Capodanno 2027 (18 dic 2026 – 6 gen 2027).")
            date_range = None
            if period == "📅 Date personalizzate":
                default_start = dt.date.today() + dt.timedelta(days=60)
                date_range = st.date_input(
                    "Seleziona le date del viaggio",
                    value=(default_start, default_start + dt.timedelta(days=7)),
                    format="DD/MM/YYYY", key="q_date_range",
                )

        with _question_card(4, "🗓️ Quanto dura il viaggio?"):
            duration_band = st.select_slider(
                "Quanti giorni?", options=list(DURATION_BANDS.keys()), key="q_duration_band",
                label_visibility="collapsed",
                **_default_kwargs("q_duration_band", value="6-8 giorni"),
            )

        with _question_card(5, "🎭 Che tipo di viaggio cerchi?",
                            "Scegli uno o più mood, poi il ritmo che preferisci."):
            moods = st.multiselect(
                "Mood", options=list(MOOD_OPTIONS.keys()),
                format_func=lambda k: MOOD_OPTIONS[k], key="q_moods",
                label_visibility="collapsed", placeholder="Scegli uno o più mood",
            )
            intensity = st.radio(
                "Ritmo del viaggio", list(INTENSITY_OPTIONS.keys()),
                format_func=lambda k: INTENSITY_OPTIONS[k], horizontal=True, key="q_intensity",
                **_default_kwargs("q_intensity", index=1),
            )

        with _question_card(6, "🌍 Dove, e con che clima?"):
            climate = st.multiselect(
                "Che clima preferisci?", options=list(CLIMATE_OPTIONS.keys()),
                format_func=lambda k: CLIMATE_OPTIONS[k], key="q_climate",
                placeholder="Indifferente",
            )
            c3, c4 = st.columns(2)
            with c3:
                area = st.selectbox("Area geografica", list(AREA_OPTIONS.keys()), index=3, format_func=lambda k: AREA_OPTIONS[k], key="q_area")
            with c4:
                distance = st.selectbox("Volo massimo", list(DISTANCE_OPTIONS.keys()), index=4, key="q_distance")

        with _question_card(7, "🏨 Comfort e socialità"):
            comfort = st.select_slider(
                "Livello di comfort desiderato", options=list(COMFORT_OPTIONS.keys()),
                value="comfort", format_func=lambda k: COMFORT_OPTIONS[k], key="q_comfort",
            )
            social_slider = st.slider(
                "0 = per conto mio · 100 = conoscere gente ogni giorno",
                0, 100, key="q_social_slider",
                **_default_kwargs("q_social_slider", value=50),
            )
            social_preference = st.selectbox(
                "Con chi preferisci socializzare?",
                list(SOCIAL_PREFERENCE_OPTIONS.keys()), index=3,
                format_func=lambda k: SOCIAL_PREFERENCE_OPTIONS[k], key="q_social_pref",
            )

        with _question_card(8, "🏷️ Qualcosa che non può mancare?",
                            "Facoltativo — lascia vuoto se non hai preferenze particolari."):
            tags = st.multiselect(
                "Preferenze speciali", options=TAG_LABELS, key="q_tags",
                label_visibility="collapsed", placeholder="Es. spiaggia, trekking, food...",
            )
            min_ease = st.select_slider(
                "Quanto vuoi che sia semplice da organizzare?",
                options=[1, 2, 3, 4, 5], value=1,
                format_func=lambda v: "Non importa" if v == 1 else f"Almeno {ease_stars(v)}",
                key="q_min_ease",
            )
            st.caption("Filtra le mete che richiedono più organizzazione (visti, più scali, meno infrastruttura turistica).")

        st.write("")
        submitted = st.form_submit_button("🔎 Trova le mie destinazioni", type="primary", use_container_width=True)

    if submitted:
        values = dict(
            budget_band=budget_band, budget_scope=budget_scope, people=people,
            period=period, date_range=date_range, duration_band=duration_band,
            moods=moods, intensity=intensity, climate=climate, area=area,
            distance=distance, comfort=comfort, social_slider=social_slider,
            social_preference=social_preference, tags=tags, departure_city=departure_city,
            min_ease=min_ease,
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

def render_travel_dna(bare: bool = False) -> None:
    """`bare=True` rende solo il contenuto, senza card né titolo: serve a
    chi lo mostra già dentro un proprio contenitore (es. l'expander della
    pagina risultati), per non annidare due bordi uno dentro l'altro."""
    dna = st.session_state.get("dna")
    if not dna:
        return

    def _body() -> None:
        cols = st.columns(2)
        items = list(dna.items())
        half = (len(items) + 1) // 2
        for col, chunk in zip(cols, [items[:half], items[half:]]):
            with col:
                for label, value in chunk:
                    st.markdown(f"**{label}** — {value}%")
                    st.progress(value / 100)
        st.markdown(f'<p class="tm-quote">{travel_dna_description(dna)}</p>', unsafe_allow_html=True)

    if bare:
        _body()
        return

    with st.container(border=True):
        st.markdown('<span class="tm-card-marker tm-card-marker-primary"></span>', unsafe_allow_html=True)
        st.markdown("### 🧬 Il tuo Travel DNA")
        _body()


# ---------------------------------------------------------------------------
# Card destinazione
# ---------------------------------------------------------------------------

def score_tier_color(score: float) -> str:
    if score >= 85:
        return "#43A047"  # success — match eccellente
    if score >= 70:
        return "#4A90E2"  # primary — buon match
    if score >= 55:
        return "#FB8C00"  # warning — match accettabile, qualche compromesso
    return "#90A4AE"  # neutro


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
        st.markdown('<span class="tm-card-marker tm-card-marker-light"></span>', unsafe_allow_html=True)
        st.markdown("**🤔 Ci abbiamo pensato anche noi**")
        for line in lines:
            st.markdown(f"- {line}")


def _overage_label(cost_econ: float, budget_max: float | None) -> str:
    if not budget_max or budget_max <= 0:
        return ""
    overage_pct = round((cost_econ - budget_max) / budget_max * 100)
    return f" · +{overage_pct}% sul budget" if overage_pct > 0 else ""


def render_over_budget_destinations(
    over_budget: pd.DataFrame, budget_max: float | None, scored_all: pd.DataFrame | None = None,
) -> None:
    """Sezione leggera e separata per le destinazioni oltre budget+buffer
    (vedi recommender.BUDGET_BUFFER_RATIO): non competono mai per i
    risultati principali, ma restano visibili qui con l'etichetta di quanto
    sforano — mai nascoste, mai spacciate per un match dentro budget. Lo
    sforamento è calcolato sullo scenario Economico, lo stesso usato dal
    motore per escluderle.

    Se `scored_all` è disponibile, ogni meta fuori portata porta con sé 1-2
    ripieghi concreti nello stesso cluster/mood (insights.accessible_alternatives):
    dire "costa troppo" senza dire "guarda invece qui" è metà del lavoro."""
    if over_budget.empty:
        return
    prefs = current_prefs()
    with st.container(border=True):
        st.markdown('<span class="tm-card-marker tm-card-marker-light"></span>', unsafe_allow_html=True)
        st.markdown("#### 💡 Idee oltre budget")
        st.caption("Non entrano nel budget scelto, ma potrebbero valere lo sforo.")
        for _, row in over_budget.iterrows():
            cost = row.get("seasonal_cost_min", row["total_cost_min"])
            st.markdown(
                f"**{row['name']}**, {row['country']} — {row['match_score']:.0f}% match · "
                f"Da {format_price(cost)}{_overage_label(cost, budget_max)}"
            )
            if scored_all is not None:
                for line in accessible_alternatives(
                    scored_all, row, budget_max, prefs.get("max_flight_hours"), n=1,
                ):
                    st.caption(line)


def render_over_budget_trips(over_budget: pd.DataFrame, budget_max: float | None) -> None:
    """Stesso principio di render_over_budget_destinations, per i viaggi
    combinati: mai mescolati ai risultati principali, sempre etichettati."""
    if over_budget.empty:
        return
    with st.container(border=True):
        st.markdown('<span class="tm-card-marker tm-card-marker-light"></span>', unsafe_allow_html=True)
        st.markdown("#### 💡 Idee di viaggio oltre budget")
        st.caption("Non entrano nel budget scelto, ma potrebbero valere lo sforo.")
        for _, trip in over_budget.iterrows():
            route_label = " → ".join(trip["stop_names"])
            st.markdown(
                f"**{trip['name']}** ({route_label}) — {trip['trip_match_score']:.0f}% match · "
                f"Da {format_price(trip['total_cost_min'])}{_overage_label(trip['total_cost_min'], budget_max)}"
            )


def render_cost_scenarios(cost_min: float, cost_max: float) -> None:
    """Economico (hostel/1-2 stelle) è lo scenario che conta per il match col
    budget (vedi recommender._budget_match); Medio e Elevato sono qui solo a
    scopo informativo, per farsi un'idea di cosa cambia con un alloggio
    migliore — non influenzano mai lo score."""
    scenarios = cost_scenarios(cost_min, cost_max)
    st.markdown('<p class="tm-section-title">💰 Scenari di costo / persona</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="tm-scenario-row tm-scenario-economico"><span>🟢 Economico (hostel/1-2★)</span><span>{format_price(scenarios["economico"])}</span></div>'
        f'<div class="tm-scenario-row tm-scenario-medio"><span>🟡 Medio (3★/B&B)</span><span>{format_price(scenarios["medio"])}</span></div>'
        f'<div class="tm-scenario-row tm-scenario-comodo"><span>🔴 Elevato (4-5★)</span><span>{format_price(scenarios["comodo"])}</span></div>',
        unsafe_allow_html=True,
    )


def render_metric_strip(primary: tuple[str, str], secondary: list[tuple[str, str]]) -> None:
    """Riga di metriche chiave di una card. La prima cella (il costo "da")
    è volutamente dominante: insieme alla pill del match è ciò che l'occhio
    deve cogliere per primo — "quanto matcha" e "quanto costa", il resto
    è supporto."""
    cells = (
        f'<div class="tm-metric tm-metric-primary">'
        f'<span class="tm-metric-value">{primary[0]}</span>'
        f'<span class="tm-metric-label">{primary[1]}</span></div>'
    )
    cells += "".join(
        f'<div class="tm-metric">'
        f'<span class="tm-metric-value">{value}</span>'
        f'<span class="tm-metric-label">{label}</span></div>'
        for value, label in secondary
    )
    st.markdown(f'<div class="tm-metric-strip">{cells}</div>', unsafe_allow_html=True)


def pace_badge_html(pace: str | None) -> str:
    """Badge del ritmo (Rilassato/Dinamico/Intenso). Stringa invece di
    st.markdown diretto perché va concatenata agli altri badge nella stessa
    riga: emetterla separatamente creerebbe un a capo indesiderato."""
    if not pace or pace not in PACE_LABELS:
        return ""
    return f'<span class="tm-badge tm-badge-pace" title="{PACE_DESCRIPTIONS.get(pace, "")}">{PACE_LABELS[pace]}</span>'


def render_seasonality_strip(row: pd.Series, requested: list[int] | None) -> None:
    """Striscia dei 12 mesi con evidenziati quelli migliori per la meta, più
    una riga di lettura. Molto più immediata dell'elenco testuale dei mesi:
    si capisce a colpo d'occhio se il proprio periodo cade nella finestra
    buona o appena fuori."""
    months = seasonality_months(row)
    requested_set = set(requested or [])
    cells = ""
    for m in months:
        classes = ["tm-month"]
        if m["is_best"]:
            classes.append("tm-month-best")
        if m["month"] in requested_set:
            classes.append("tm-month-picked")
        cells += f'<span class="{" ".join(classes)}">{m["label"]}</span>'
    st.markdown('<p class="tm-section-title">📅 Quando andarci</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="tm-month-strip">{cells}</div>', unsafe_allow_html=True)
    note = seasonality_note(row, requested)
    if note:
        st.caption(note)


def render_typical_day(row: pd.Series) -> None:
    st.markdown('<p class="tm-section-title">🕐 Una giornata tipo</p>', unsafe_allow_html=True)
    rows = "".join(
        f'<div class="tm-day-row">'
        f'<span class="tm-day-slot">{slot["icon"]} {slot["label"]}</span>'
        f'<span class="tm-day-text">{slot["text"]}</span>'
        f'</div>'
        for slot in typical_day(row)
    )
    st.markdown(rows, unsafe_allow_html=True)


def render_takeaways(row: pd.Series) -> None:
    takeaways = emotional_takeaways(row)
    if not takeaways:
        return
    st.markdown('<p class="tm-section-title">💭 Cosa ti porti a casa</p>', unsafe_allow_html=True)
    st.markdown(
        "".join(f'<div class="tm-takeaway">{t}</div>' for t in takeaways),
        unsafe_allow_html=True,
    )


def render_dna_comparison(row: pd.Series) -> None:
    """Confronto Travel DNA utente vs destinazione: due barre sovrapposte per
    tratto. Mostra solo i tratti dove almeno uno dei due supera 25, altrimenti
    dieci righe quasi vuote nasconderebbero le tre che contano."""
    comparison = dna_vs_destination(st.session_state.get("dna"), row)
    if not comparison:
        return
    visible = [c for c in comparison if max(c["user"], c["destination"]) >= 25]
    if not visible:
        return

    st.markdown('<p class="tm-section-title">🧬 Tu vs questa meta</p>', unsafe_allow_html=True)

    # Legenda con campioni veri dei due colori usati nelle barre: dire
    # "barra scura / barra chiara" a parole costringeva il lettore a
    # indovinare quale fosse quale.
    st.markdown(
        '<div class="tm-dna-legend">'
        '<span class="tm-dna-legend-item"><span class="tm-dna-swatch tm-dna-swatch-user"></span>quanto lo cerchi tu</span>'
        '<span class="tm-dna-legend-item"><span class="tm-dna-swatch tm-dna-swatch-dest"></span>quanto lo offre la meta</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Stato scritto per esteso al posto dei pallini colorati: tre emoji senza
    # relazione visiva con le barre erano un secondo codice da decifrare.
    status_text = {
        "match": ("in linea", "tm-dna-status-match"),
        "destination_higher": ("offre di più", "tm-dna-status-more"),
        "user_higher": ("offre meno", "tm-dna-status-less"),
    }
    rows = ""
    for c in visible:
        label, css_class = status_text[c["status"]]
        rows += (
            f'<div class="tm-dna-row">'
            f'<span class="tm-dna-label">{c["trait"]}</span>'
            f'<div class="tm-dna-track">'
            f'<div class="tm-dna-fill tm-dna-user" style="width:{c["user"]:.0f}%;"></div>'
            f'<div class="tm-dna-fill tm-dna-dest" style="width:{c["destination"]:.0f}%;"></div>'
            f'</div>'
            f'<span class="tm-dna-status {css_class}">{label}</span>'
            f'</div>'
        )
    st.markdown(rows, unsafe_allow_html=True)


# Angoli dei 5 assi del radar, in gradi partendo dall'alto e in senso orario.
_RADAR_AXES = ["🥾 Avventura", "🏖️ Relax", "🏛️ Cultura", "🎉 Social", "💎 Lusso"]
_RADAR_COLORS = ["#1E88E5", "#FB8C00", "#43A047"]


def _radar_points(values: list[float], cx: float, cy: float, radius: float) -> str:
    """Converte 5 valori 0-100 nei punti di un pentagono SVG. Il primo asse
    punta in alto (-90°), gli altri seguono in senso orario."""
    pts = []
    n = len(values)
    for i, value in enumerate(values):
        angle = math.radians(-90 + (360 / n) * i)
        r = radius * max(0.0, min(100.0, value)) / 100.0
        pts.append(f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
    return " ".join(pts)


def render_travel_style_radar(series: list[tuple[str, dict[str, float]]]) -> None:
    """Radar dei Travel Style per 2-3 elementi sovrapposti. SVG inline: niente
    librerie di grafici in più (matplotlib/plotly sarebbero una dipendenza
    pesante per cinque assi), e si tinge con la palette dell'app."""
    if not series:
        return
    size, cx, cy, radius = 320, 160, 155, 110

    grid = ""
    for level in (0.25, 0.5, 0.75, 1.0):
        pts = _radar_points([100 * level] * 5, cx, cy, radius)
        grid += f'<polygon points="{pts}" fill="none" stroke="#BBDEFB" stroke-width="1"/>'

    axes = ""
    labels = ""
    for i, axis in enumerate(_RADAR_AXES):
        angle = math.radians(-90 + 72 * i)
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#BBDEFB" stroke-width="1"/>'
        lx, ly = cx + (radius + 22) * math.cos(angle), cy + (radius + 14) * math.sin(angle)
        anchor = "middle" if abs(lx - cx) < 20 else ("start" if lx > cx else "end")
        labels += (
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="11" font-weight="600" fill="#546E7A">{axis}</text>'
        )

    shapes = ""
    legend_items = []
    for idx, (name, scores) in enumerate(series[:3]):
        color = _RADAR_COLORS[idx % len(_RADAR_COLORS)]
        values = [scores.get(axis, 0.0) for axis in _RADAR_AXES]
        pts = _radar_points(values, cx, cy, radius)
        shapes += (
            f'<polygon points="{pts}" fill="{color}" fill-opacity="0.18" '
            f'stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>'
        )
        legend_items.append(
            f'<span class="tm-radar-legend-item"><span class="tm-radar-swatch" '
            f'style="background:{color};"></span>{name}</span>'
        )

    st.markdown(
        f'<div class="tm-radar-wrap">'
        f'<svg viewBox="0 0 {size} {size}" width="100%" height="auto" role="img" '
        f'aria-label="Confronto Travel Style">{grid}{axes}{shapes}{labels}</svg>'
        f'<div class="tm-radar-legend">{"".join(legend_items)}</div>'
        f'</div>',
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
    # La spiegazione narrativa (2-3 frasi costruite su mood, stagione, budget
    # e Travel DNA) sostituisce la frase secca di recommender.explain_match,
    # che resta il fallback se qui non c'è abbastanza materiale.
    prefs = current_prefs()
    narrative = narrative_explanation(
        row, prefs, st.session_state.get("dna"), requested_months(prefs),
    )
    st.write(narrative or row["explanation"])
    if row.get("compromise_reasons"):
        reasons = ", ".join(row["compromise_reasons"])
        st.warning(f"Piccolo compromesso su: {reasons}. Il resto però convince parecchio.")


def _render_destination_detail_body(row: pd.Series, rank: int | None, surprise: bool, dest_id: int) -> None:
    """Tutto ciò che sta sotto "Perché fa per te": avvisi, Travel Style, WOW,
    costi+scenari, info pratiche, pro/contro, checklist, export e azioni.
    Condiviso identico tra vista compatta (dentro l'expander di dettaglio) e
    vista dettagliata (sempre visibile), così le due modalità mostrano
    sempre esattamente lo stesso contenuto — cambia solo il contenitore."""
    prefs = current_prefs()
    render_contextual_warnings(destination_warnings(row, prefs))

    style_col, dna_col = st.columns(2)
    with style_col:
        render_travel_style_bars(travel_style_scores(row))
    with dna_col:
        render_dna_comparison(row)

    render_seasonality_strip(row, requested_months(prefs))
    render_typical_day(row)

    st.markdown('<p class="tm-section-title">⭐ Esperienze WOW</p>', unsafe_allow_html=True)
    for wow in row["wow_experiences"][:3]:
        st.markdown(f"- {wow}")

    render_takeaways(row)

    stay_hint = TRAVELLER_STAY_HINTS.get(prefs.get("traveller_mode") or "")
    if stay_hint:
        st.markdown('<p class="tm-section-title">🛏️ Dove dormire, per come viaggi</p>', unsafe_allow_html=True)
        st.caption(stay_hint)

    cost_col, info_col = st.columns([1.3, 1])
    with cost_col:
        st.markdown('<p class="tm-section-title">💰 Costo indicativo / persona</p>', unsafe_allow_html=True)
        st.markdown(f"**Da {format_price(row['total_cost_min'])}**")
        st.caption(f"Range indicativo: {format_price_range(row['total_cost_min'], row['total_cost_max'])}")
    with info_col:
        st.markdown('<p class="tm-section-title">Info pratiche</p>', unsafe_allow_html=True)
        st.markdown(f"🌡️ {format_temp_range(row['temp_min'], row['temp_max'])}")
        st.markdown(f"🗓️ {row['days_min']}-{row['days_max']} giorni consigliati")
        st.markdown(f"✈️ {flight_duration_label(row['flight_hours'], current_prefs().get('departure_city'))}")
        st.markdown(f"👥 Social: {social_dots(row['social_level'] * 20)}")
        ease = organizational_ease(row)
        st.markdown(f"🧭 Facilità organizzativa: {ease_stars(ease)} ({ease}/5)")

    # Il dettaglio voce-per-voce interessa a chi sta già facendo i conti:
    # collassato di default, così la card resta leggibile a colpo d'occhio.
    with st.expander("💰 Dettaglio costi e scenari"):
        st.markdown(f'<p class="tm-cost-line">✈️ Volo: {format_price_range(row["flight_cost_min"], row["flight_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🏨 Hotel: {format_price_range(row["hotel_cost_min"], row["hotel_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🍝 Cibo: {format_price_range(row["food_cost_min"], row["food_cost_max"])}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="tm-cost-line">🎟️ Attività: {format_price_range(row["activity_cost_min"], row["activity_cost_max"])}</p>', unsafe_allow_html=True)
        render_cost_scenarios(row["total_cost_min"], row["total_cost_max"])

        alt_transports = estimate_alternative_transports(row)
        if alt_transports:
            st.markdown('<p class="tm-section-title">🚆 Alternative al volo</p>', unsafe_allow_html=True)
            st.caption("Stima indicativa basata sulla distanza, non su orari reali.")
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
        checklist = build_destination_checklist(
            row, prefs.get("period"), prefs.get("traveller_mode"),
        )
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

        st.markdown("**📲 Versione stories**")
        st.text_area(
            "Testo breve per storie/status", value=export_destination_as_stories(row), height=180,
            key=f"dstories_{dest_id}_{rank}_{surprise}", label_visibility="collapsed",
        )

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
        st.markdown('<span class="tm-card-marker tm-card-marker-primary"></span>', unsafe_allow_html=True)
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
            st.markdown(mood_badges + pace_badge_html(row.get("pace")), unsafe_allow_html=True)

            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            render_metric_strip(
                (f"Da {format_price(row['total_cost_min'])}", "a persona"),
                [
                    (f"{row['days_min']}-{row['days_max']} giorni", "durata"),
                    (flight_duration_label(row["flight_hours"], current_prefs().get("departure_city")), "volo"),
                ],
            )

            with st.expander("🔍 Vedi dettaglio completo"):
                _render_destination_explanation(row)
                _render_destination_detail_body(row, rank, surprise, dest_id)
        else:
            mood_labels = [MOOD_OPTIONS.get(m, m) for m in row["moods"][:4]]
            mood_badges = "".join(f'<span class="tm-badge">{m}</span>' for m in mood_labels)
            st.markdown(mood_badges + pace_badge_html(row.get("pace")), unsafe_allow_html=True)

            if surprise:
                st.markdown(
                    '<p class="tm-quote">Non era tra le scelte più ovvie. Ma secondo noi potrebbe piacerti parecchio. 🎲</p>',
                    unsafe_allow_html=True,
                )

            _render_destination_explanation(row)
            _render_destination_detail_body(row, rank, surprise, dest_id)


def _render_trip_explanation(trip: pd.Series) -> None:
    st.markdown('<p class="tm-section-title">Perché fa per te</p>', unsafe_allow_html=True)
    st.write(generate_trip_explanation(trip))


def _render_trip_detail_body(trip: pd.Series, rank: int | None, surprise: bool) -> None:
    """Tutto ciò che sta sotto "Perché fa per te": avvisi, Travel Style,
    costi+scenari, timeline, checklist, export e azioni — condiviso identico
    tra vista compatta (dentro l'expander) e vista dettagliata (sempre
    visibile), stesso principio delle card destinazione (vedi
    _render_destination_detail_body). Il Feasibility Score che regola quali
    itinerari arrivano fin qui resta un dettaglio interno del motore (vedi
    trip_builder.py): non compare da nessuna parte nell'interfaccia."""
    render_contextual_warnings(trip_warnings(trip, current_prefs()))
    render_travel_style_bars(travel_style_scores_for_stops(trip["stops"]))

    cost_col, info_col = st.columns([1.3, 1])
    with cost_col:
        st.markdown('<p class="tm-section-title">💰 Costo totale indicativo / persona</p>', unsafe_allow_html=True)
        st.markdown(f"**Da {format_price(trip['total_cost_min'])}**")
        st.caption(f"Range indicativo: {format_price_range(trip['total_cost_min'], trip['total_cost_max'])}")
    with info_col:
        st.markdown('<p class="tm-section-title">Info pratiche</p>', unsafe_allow_html=True)
        st.markdown(f"🗓️ {trip['minimum_days']}-{trip['ideal_days']} giorni (ideale: {trip['ideal_days']})")
        entry_flight_hours = trip["stops"][0]["flight_hours"]
        st.markdown(f"✈️ {flight_duration_label(entry_flight_hours, current_prefs().get('departure_city'))}")
        st.markdown(f"🔀 {flight_hours_label(trip['transfer_time_hours'])} di trasferimento totale")
        st.markdown(f"🧭 Efficienza viaggio: {trip['efficiency_score']:.0f}%")
        ease = trip_organizational_ease(trip)
        st.markdown(f"🧭 Facilità organizzativa: {ease_stars(ease)} ({ease}/5)")

    with st.expander("💰 Dettaglio costi e scenari"):
        st.markdown(f'<p class="tm-cost-line">🔀 Trasferimenti: ~{trip["transfer_cost"]:.0f} €</p>', unsafe_allow_html=True)
        render_cost_scenarios(trip["total_cost_min"], trip["total_cost_max"])

    with st.expander("🗓️ Timeline del viaggio"):
        render_visual_timeline(trip)

    with st.expander("🎒 Checklist di viaggio"):
        checklist = build_trip_checklist(
            trip, current_prefs().get("period"), current_prefs().get("traveller_mode"),
        )
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
        st.markdown('<span class="tm-card-marker tm-card-marker-primary"></span>', unsafe_allow_html=True)
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

        st.markdown(
            f'<span class="tm-badge">🧭 Travel Efficiency {trip["efficiency_score"]:.0f}%</span>'
            f'<span class="tm-badge">🏷️ {trip["difficulty"].capitalize()}</span>'
            + pace_badge_html(trip.get("pace")),
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

            render_metric_strip(
                (f"Da {format_price(trip['total_cost_min'])}", "a persona"),
                [
                    (f"{trip['minimum_days']}-{trip['ideal_days']} giorni", "durata"),
                    (flight_hours_label(trip["transfer_time_hours"]), "trasferimenti"),
                ],
            )

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
    """Azione secondaria: potente ma non è il motivo per cui si guarda la
    pagina — sta dietro un expander per non competere con i risultati."""
    with st.expander("🎛️ Non è quello che cercavi? Affina i risultati"):
        st.caption("Ogni click rende il motore più preciso su ciò che conta per te ora. Non ripete il questionario.")
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
            st.caption(f"Applicati: {applied}")

        st.markdown('<p class="tm-section-title">✈️ Viaggi combinati</p>', unsafe_allow_html=True)
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
            st.caption(f"Applicati ai viaggi: {applied}")


# ---------------------------------------------------------------------------
# Confronto
# ---------------------------------------------------------------------------

def render_comparison(scored_all: pd.DataFrame) -> None:
    ids = list(st.session_state["compare_ids"])
    if len(ids) < 2:
        return
    st.markdown('<div class="tm-results-header">📊 Confronto destinazioni</div>', unsafe_allow_html=True)

    names = scored_all[scored_all["id"].isin(ids)]

    # Radar prima della tabella: il profilo si coglie a colpo d'occhio, i
    # numeri esatti restano sotto per chi li vuole.
    radar_col, table_col = st.columns([1, 1.4])
    with radar_col:
        render_travel_style_radar([(r["name"], travel_style_scores(r)) for _, r in names.iterrows()])
    with table_col:
        st.dataframe(compare_destinations(scored_all, ids), use_container_width=True)

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
            [("Match", trip["trip_match_score"]),
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

    results = bundle["results"]
    scored_all = bundle["scored_all"]

    st.markdown(
        """
        <div class="tm-page-head">
            <h2>✨ Ecco dove potresti andare</h2>
            <p>Ordinate per quanto si avvicinano a quello che cerchi.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if results.empty:
        if bundle.get("budget_exhausted"):
            st.info("Con questo budget non abbiamo trovato mete in linea, ma queste ci vanno vicino. 👇")
            render_over_budget_destinations(bundle["over_budget"], current_budget_max(), scored_all)
        else:
            st.info("Il match perfetto probabilmente c'è: proviamo a cercarlo con qualche vincolo in meno? Allargare l'area geografica di solito basta. 🧭")
        return

    if bundle["strict_count"] == 0:
        st.info("Ti mostriamo le mete che ci vanno più vicino: in ogni card trovi il piccolo compromesso da fare. 🤝")
    elif bundle["used_compromise"]:
        st.info(f"{bundle['strict_count']} destinazion{'e centra' if bundle['strict_count'] == 1 else 'i centrano'} tutti i criteri. Sotto trovi anche qualche alternativa che ci va vicino.")

    # Travel DNA: interessante ma non è il motivo per cui si è arrivati qui —
    # sta dietro un expander per lasciare l'apertura di pagina ai risultati.
    with st.expander("🧬 Il tuo Travel DNA"):
        render_travel_dna(bare=True)

    period = st.session_state["prefs"].get("period")
    if period in CHRISTMAS_LIKE:
        render_christmas_spotlight(scored_all)

    trip_bundle = st.session_state.get("trip_bundle")
    if trip_bundle is None:
        recompute_trips()
        trip_bundle = st.session_state["trip_bundle"]
    trip_results = trip_bundle["results"] if trip_bundle is not None else pd.DataFrame()

    # Barra controlli su una riga sola: i due toggle + Sorprendimi occupavano
    # tre blocchi verticali con altrettante etichette, spingendo i risultati
    # sotto la piega senza aggiungere informazione.
    ctrl_view, ctrl_display, ctrl_surprise = st.columns([2.2, 1.8, 1])
    with ctrl_view:
        view_mode = st.radio(
            "Modalità risultati",
            ["🌍 Solo destinazioni", "✈️ Solo viaggi combinati", "🔀 Entrambi"],
            index=2, horizontal=True, key="results_view_mode", label_visibility="collapsed",
        )
    with ctrl_display:
        display_mode = st.radio(
            "Vista risultati",
            ["📋 Vista compatta", "📖 Vista dettagliata"],
            index=0, horizontal=True, key="destination_display_mode", label_visibility="collapsed",
        )
    with ctrl_surprise:
        surprise_clicked = st.button("🎲 Sorprendimi", use_container_width=True, type="secondary")

    show_destinations = view_mode != "✈️ Solo viaggi combinati"
    show_trips = view_mode != "🌍 Solo destinazioni"
    compact = display_mode == "📋 Vista compatta"

    departure_city = st.session_state["prefs"].get("departure_city")
    if departure_city:
        st.caption(f"✈️ Stime di volo per partenze da {DEPARTURE_CITY_OPTIONS[departure_city].split(' ', 1)[-1]}.")

    if surprise_clicked:
        handle_surprise(results, trip_results, scored_all, trip_bundle, show_destinations, show_trips)

    if st.session_state.get("surprise_kind") == "destination" and st.session_state.get("surprise_pick") is not None:
        render_destination_card(st.session_state["surprise_pick"], surprise=True, compact=compact)
    elif st.session_state.get("surprise_kind") == "trip" and st.session_state.get("surprise_trip_pick") is not None:
        render_trip_card(st.session_state["surprise_trip_pick"], surprise=True, compact=compact)

    if show_destinations:
        st.markdown('<div class="tm-results-header">🏆 Destinazioni</div>', unsafe_allow_html=True)
        shown = st.session_state["shown_count"]
        for rank, (_, row) in enumerate(results.head(shown).iterrows()):
            render_destination_card(row, rank=rank, compact=compact)

        if shown < len(results):
            if st.button(f"⬇️ Mostra altre destinazioni ({len(results) - shown} disponibili)", use_container_width=True):
                st.session_state["shown_count"] = min(len(results), shown + 5)
                st.rerun()

        shown_ids = set(results.head(shown)["id"].tolist()) | set(bundle["over_budget"]["id"].tolist())
        render_anti_fomo(discarded_destination_alternatives(scored_all, shown_ids))
        render_over_budget_destinations(bundle["over_budget"], current_budget_max(), scored_all)

        if show_trips:
            st.divider()

    if show_trips:
        st.markdown('<div class="tm-results-header">✈️ Viaggi combinati</div>', unsafe_allow_html=True)
        if trip_results.empty:
            if trip_bundle.get("budget_exhausted"):
                st.info("Con questo budget non abbiamo trovato itinerari in linea, ma questi ci vanno vicino. 👇")
                render_over_budget_trips(trip_bundle["over_budget"], current_budget_max())
            else:
                st.info("Per la durata scelta, una singola destinazione ben vissuta batte qualsiasi combinazione. 🎯")
        else:
            st.caption("Solo itinerari di 2-3 tappe davvero fattibili — mai combinazioni forzate.")
            if trip_bundle["used_compromise"]:
                st.info(f"{trip_bundle['strict_count']} itinerar{'io centra' if trip_bundle['strict_count'] == 1 else 'i centrano'} tutti i criteri di fattibilità. Sotto trovi anche qualche alternativa che ci va vicino.")
            shown_trips = st.session_state["shown_trip_count"]
            for rank, (_, trip) in enumerate(trip_results.head(shown_trips).iterrows()):
                render_trip_card(trip, rank=rank, compact=compact)
            if shown_trips < len(trip_results):
                if st.button(f"⬇️ Mostra altri viaggi combinati ({len(trip_results) - shown_trips} disponibili)", use_container_width=True):
                    st.session_state["shown_trip_count"] = min(len(trip_results), shown_trips + 3)
                    st.rerun()

            shown_trip_ids = set(trip_results.head(shown_trips)["trip_id"].tolist()) | set(trip_bundle["over_budget"]["trip_id"].tolist())
            candidates_all = trip_bundle["candidates_all"] if trip_bundle is not None else None
            render_anti_fomo(discarded_trip_alternatives(candidates_all, shown_trip_ids))
            render_over_budget_trips(trip_bundle["over_budget"], current_budget_max())

    st.divider()
    render_refinement_bar()
    st.divider()
    render_comparison(scored_all)
    render_trip_comparison(trip_bundle["candidates_all"] if trip_bundle is not None else None)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("📝 Rifai il questionario", use_container_width=True):
            go("questionnaire")
            st.rerun()
    with c2:
        if st.button("❤️ I miei viaggi", use_container_width=True):
            go("my_trips")
            st.rerun()
    with c3:
        if st.button("🏠 Torna alla home", use_container_width=True):
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
# I miei viaggi — area dedicata a ciò che è stato salvato nei preferiti,
# con confronto e export. Finora i preferiti erano solo un contatore in
# sidebar: si potevano aggiungere, ma non c'era un posto dove rivederli.
# ---------------------------------------------------------------------------

def render_my_trips() -> None:
    st.markdown(
        """
        <div class="tm-page-head">
            <h2>❤️ I miei viaggi</h2>
            <p>Quello che hai salvato, pronto da confrontare o da esportare.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fav_ids = st.session_state.get("favorites") or set()
    fav_trip_ids = st.session_state.get("trip_favorites") or set()

    if not fav_ids and not fav_trip_ids:
        st.info("Non hai ancora salvato niente. Aggiungi una meta ai preferiti con ❤️ dalle card dei risultati.")
        if st.button("⬅️ Torna ai risultati"):
            go("results")
            st.rerun()
        return

    bundle = st.session_state.get("results_bundle")
    scored_all = bundle["scored_all"] if bundle is not None else pd.DataFrame()
    trip_bundle = st.session_state.get("trip_bundle")
    candidates_all = trip_bundle.get("candidates_all") if trip_bundle else None

    saved_rows = scored_all[scored_all["id"].isin(fav_ids)] if not scored_all.empty else pd.DataFrame()

    if not saved_rows.empty:
        st.markdown('<div class="tm-results-header">🌍 Destinazioni salvate</div>', unsafe_allow_html=True)

        # Radar di confronto: fino a 3 mete sovrapposte. È qui che il radar
        # rende di più — su una card singola una barra è più leggibile.
        if len(saved_rows) >= 2:
            with st.expander("📊 Confronta i Travel Style", expanded=True):
                series = [(r["name"], travel_style_scores(r)) for _, r in saved_rows.head(3).iterrows()]
                render_travel_style_radar(series)
                cost_table = pd.DataFrame({
                    "Match %": [f"{r['match_score']:.0f}%" for _, r in saved_rows.iterrows()],
                    "Da (€)": [format_price(r.get("seasonal_cost_min", r["total_cost_min"])) for _, r in saved_rows.iterrows()],
                    "Giorni": [f"{r['days_min']}-{r['days_max']}" for _, r in saved_rows.iterrows()],
                    "Ritmo": [PACE_LABELS.get(r.get("pace", ""), "—") for _, r in saved_rows.iterrows()],
                    "Volo": [flight_hours_label(r["flight_hours"]) for _, r in saved_rows.iterrows()],
                }, index=saved_rows["name"])
                st.dataframe(cost_table, use_container_width=True)

        for _, row in saved_rows.iterrows():
            render_destination_card(row, compact=True)

    if fav_trip_ids and candidates_all is not None and not candidates_all.empty:
        saved_trips = candidates_all[candidates_all["trip_id"].isin(fav_trip_ids)]
        if not saved_trips.empty:
            st.markdown('<div class="tm-results-header">✈️ Viaggi combinati salvati</div>', unsafe_allow_html=True)
            for _, trip in saved_trips.iterrows():
                render_trip_card(trip, compact=True)

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("⬅️ Torna ai risultati", use_container_width=True):
            go("results")
            st.rerun()
    with c2:
        if st.button("🧹 Svuota i preferiti", use_container_width=True):
            st.session_state["favorites"] = set()
            st.session_state["trip_favorites"] = set()
            st.rerun()


# ---------------------------------------------------------------------------
# Sorpresa controllata — l'utente fissa 2-3 vincoli duri e il motore pesca
# una meta meno ovvia ma coerente. Diverso da "Sorprendimi": lì la sorpresa
# nasce dalle preferenze complete, qui da pochi paletti espliciti, il che la
# rende utilizzabile anche senza aver fatto il questionario.
# ---------------------------------------------------------------------------

def render_controlled_surprise() -> None:
    st.markdown(
        """
        <div class="tm-page-head">
            <h2>🎯 Sorpresa controllata</h2>
            <p>Dimmi solo cosa NON deve succedere. Al resto pensiamo noi.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("controlled_surprise_form"):
        c1, c2 = st.columns(2)
        with c1:
            budget_band = st.select_slider(
                "Budget massimo (a persona)", options=list(BUDGET_BANDS.keys()),
                value="1.000 - 1.500 €", key="cs_budget",
            )
            max_flight = st.selectbox(
                "Volo massimo", list(DISTANCE_OPTIONS.keys()), index=3, key="cs_flight",
            )
        with c2:
            area = st.selectbox(
                "Area", list(AREA_OPTIONS.keys()), index=3,
                format_func=lambda k: AREA_OPTIONS[k], key="cs_area",
            )
            pace_choice = st.selectbox(
                "Ritmo", ["Indifferente"] + list(PACE_LABELS.keys()),
                format_func=lambda k: PACE_LABELS.get(k, "🤷 Indifferente"), key="cs_pace",
            )
        exclusions = st.multiselect(
            "Escludi tassativamente", ["neve", "spiaggia", "nightlife", "trekking", "shopping"],
            key="cs_exclude", placeholder="Niente da escludere",
        )
        submitted = st.form_submit_button("🎲 Pesca una meta", type="primary", use_container_width=True)

    if submitted:
        low, high = BUDGET_BANDS[budget_band]
        prefs = neutral_prefs()
        prefs.update({
            "budget_range": (low, high),
            "area": area,
            "max_flight_hours": DISTANCE_OPTIONS[max_flight],
            "intensity": None if pace_choice == "Indifferente" else pace_choice,
        })
        st.session_state["prefs"] = prefs
        st.session_state["dna"] = compute_travel_dna(prefs)
        recompute_results()

        pool = st.session_state["results_bundle"]["scored_all"]
        # I vincoli di esclusione sono duri: filtrano il pool PRIMA della
        # pesca, invece di limitarsi ad abbassare un punteggio. È tutto il
        # senso della modalità — "no neve" deve voler dire no neve.
        pool = pool[pool["within_budget_buffer"]]
        for tag in exclusions:
            pool = pool[~pool["tags"].apply(lambda ts, t=tag: t in ts)]

        pick = surprise_me(pool, min_score=55.0) if not pool.empty else None
        st.session_state["controlled_pick"] = pick
        # Flag esplicito: le chiavi dei widget (cs_*) esistono già al primo
        # render, quindi non possono distinguere "non ha ancora cercato" da
        # "ha cercato e non c'è nulla".
        st.session_state["controlled_searched"] = True
        st.rerun()

    pick = st.session_state.get("controlled_pick")
    if pick is not None:
        st.balloons()
        render_destination_card(pick, surprise=True, compact=True)
    elif st.session_state.get("controlled_searched"):
        st.info("Con questi vincoli non resta nessuna meta. Prova ad allentarne uno: di solito basta il budget o il volo. 🧭")

    if st.button("🏠 Torna alla home"):
        reset_to_landing()
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="tm-sidebar-brand">✈️ TravelMatch</div>'
            '<p class="tm-sidebar-tag">Il tuo motore di viaggi, offline.</p>',
            unsafe_allow_html=True,
        )

        # Travel DNA sempre sott'occhio: è il filo che lega questionario e
        # risultati, e tenerlo solo dentro un expander della pagina risultati
        # lo rendeva di fatto invisibile.
        dna = st.session_state.get("dna")
        if dna:
            prefs = st.session_state.get("prefs") or {}
            mode = prefs.get("traveller_mode")
            if mode and mode in TRAVELLER_MODE_LABELS:
                st.markdown(f'<span class="tm-badge">{TRAVELLER_MODE_LABELS[mode]}</span>', unsafe_allow_html=True)
            st.markdown('<p class="tm-section-title">🧬 Il tuo Travel DNA</p>', unsafe_allow_html=True)
            top = sorted(dna.items(), key=lambda kv: kv[1], reverse=True)[:4]
            rows = "".join(
                f'<div class="tm-style-row">'
                f'<span class="tm-style-label">{label}</span>'
                f'<div class="tm-style-track"><div class="tm-style-fill" style="width:{value}%;"></div></div>'
                f'</div>'
                for label, value in top
            )
            st.markdown(rows, unsafe_allow_html=True)

        n_fav = len(st.session_state.get("favorites") or set())
        n_trip_fav = len(st.session_state.get("trip_favorites") or set())
        if n_fav or n_trip_fav:
            if st.button(f"❤️ I miei viaggi ({n_fav + n_trip_fav})", use_container_width=True):
                go("my_trips")
                st.rerun()

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
                trip_results.head(3)[["trip_id", "name", "trip_match_score"]].to_dict("records")
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
        n_destinations = len(load_destinations_df())
        st.caption(f"TravelMatch v2.0 — dataset locale, {n_destinations} destinazioni + Trip Builder, nessuna connessione richiesta.")


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
    elif stage == "my_trips":
        render_my_trips()
    elif stage == "controlled_surprise":
        render_controlled_surprise()
    elif stage == "surprise_direct":
        render_surprise_direct()
    elif stage == "gift_surprise":
        render_gift_surprise()
    else:
        render_landing()


if __name__ == "__main__":
    main()
