"""
Dataset "leggero" dei collegamenti tra destinazioni, usato dal Trip Builder
(trip_builder.py) per generare itinerari multi-tappa realistici.

Non contiene una rotta per ogni possibile coppia di destinazioni: solo i
collegamenti effettivamente utili a costruire combinazioni sensate. Questo e'
anche il principale meccanismo con cui il motore evita combinazioni
geograficamente assurde (es. Reykjavik + Bali): se non esiste una rotta
autorata tra due destinazioni, il Trip Builder non le combinera' mai, a
prescindere da quanto siano simili come punteggi.

Le rotte sono simmetriche (si viaggia normalmente in entrambe le direzioni
con costo/tempo comparabili): vengono quindi cercate in entrambi i sensi da
get_route(), senza bisogno di duplicare ogni riga.
"""

from __future__ import annotations

import pandas as pd


def _r(origin_id, destination_id, transport_mode, travel_time, transport_cost, convenience_score):
    return dict(
        origin_id=origin_id, destination_id=destination_id, transport_mode=transport_mode,
        travel_time=travel_time, transport_cost=transport_cost, convenience_score=convenience_score,
    )


# id destinazione -> vedi destinations.py per la mappa id/nome
RAW_ROUTES = [
    # --- Turchia ---
    _r(58, 57, "volo", 1.3, 60, 80),          # Istanbul -> Cappadocia

    # --- Portogallo ---
    _r(19, 61, "treno", 2.5, 25, 90),         # Lisbona -> Porto
    _r(19, 20, "volo", 1.6, 90, 80),          # Lisbona -> Madeira

    # --- Giappone ---
    _r(60, 62, "treno", 2.3, 130, 95),        # Tokyo -> Kyoto (shinkansen)
    _r(62, 63, "treno", 0.5, 10, 98),         # Kyoto -> Osaka
    _r(60, 63, "treno", 2.8, 140, 90),        # Tokyo -> Osaka (diretto)

    # --- Thailandia ---
    _r(47, 64, "volo", 1.3, 45, 85),          # Bangkok -> Chiang Mai
    _r(47, 46, "volo", 1.3, 55, 82),          # Bangkok -> Phuket & Krabi

    # --- Marocco ---
    _r(42, 65, "bus/auto", 2.5, 15, 85),      # Marrakech -> Essaouira
    _r(42, 66, "bus/auto", 8.0, 60, 55),      # Marrakech -> Merzouga (Sahara)

    # --- Europa Centrale ---
    _r(22, 23, "treno", 2.5, 40, 90),         # Vienna -> Budapest
    _r(21, 22, "treno", 4.0, 35, 82),         # Praga -> Vienna
    _r(21, 23, "treno", 7.0, 45, 65),         # Praga -> Budapest

    # --- Catalogna ---
    _r(18, 67, "treno", 1.5, 15, 88),         # Barcellona -> Costa Brava

    # --- Toscana-Liguria ---
    _r(2, 5, "treno", 1.3, 20, 88),           # Firenze -> Cinque Terre

    # --- Veneto-Dolomiti ---
    _r(3, 9, "bus/auto", 2.0, 25, 75),        # Venezia -> Cortina d'Ampezzo
    _r(9, 10, "bus/auto", 1.5, 20, 78),       # Cortina -> Bolzano
    _r(3, 10, "treno", 2.0, 25, 82),          # Venezia -> Bolzano

    # --- Nord Italia-Laghi ---
    _r(11, 12, "treno", 1.0, 20, 92),         # Milano -> Torino
    _r(11, 14, "treno", 0.7, 10, 95),         # Milano -> Lago di Como
    _r(12, 14, "treno", 1.8, 22, 80),         # Torino -> Lago di Como

    # --- Sicilia ---
    _r(6, 7, "treno", 2.5, 20, 75),           # Palermo -> Taormina

    # --- Centro Italia ---
    _r(1, 15, "treno", 1.5, 18, 85),          # Roma -> Umbria

    # --- Benelux ---
    _r(25, 41, "treno", 3.3, 40, 80),         # Amsterdam -> Bruges

    # --- Scandinavia ---
    _r(26, 40, "treno", 5.0, 60, 75),         # Copenaghen -> Stoccolma

    # --- Grecia ---
    _r(34, 35, "volo", 0.75, 90, 88),         # Atene -> Santorini
    _r(35, 36, "traghetto", 2.5, 45, 70),     # Santorini -> Creta
    _r(34, 36, "volo", 0.75, 70, 85),         # Atene -> Creta

    # --- Golfo ---
    _r(43, 44, "volo", 1.2, 90, 82),          # Dubai -> Muscat

    # --- Regno Unito ---
    _r(17, 32, "treno", 4.5, 60, 80),         # Londra -> Edimburgo

    # --- Canarie ---
    _r(69, 70, "traghetto", 1.5, 35, 80),     # Fuerteventura -> Lanzarote

    # --- Artico norvegese ---
    _r(28, 73, "bus/auto", 5.0, 40, 65),      # Tromso -> Isole Lofoten

    # --- Baltico-Scandinavia ---
    _r(40, 74, "traghetto", 16.0, 70, 60),    # Stoccolma -> Tallinn

    # --- Caucaso ---
    _r(75, 76, "bus/auto", 6.0, 25, 60),      # Tbilisi -> Yerevan

    # --- Balcani ---
    _r(77, 78, "bus/auto", 3.0, 15, 75),      # Tirana -> Ohrid
]


RAW_TRIP_TEMPLATES = [
    dict(
        trip_id="istanbul_cappadocia", name="Istanbul & Cappadocia",
        destinations=[58, 57], minimum_days=6, ideal_days=8,
        estimated_transport_cost=60, transport_time=1.3, difficulty="facile",
        best_months=[4, 5, 9, 10], trip_style=["city_culture", "unique", "food"],
        description="Storia millenaria e bazar a Istanbul, mongolfiere e valli lunari in Cappadocia.",
    ),
    dict(
        trip_id="lisbona_porto", name="Lisbona & Porto",
        destinations=[19, 61], minimum_days=5, ideal_days=7,
        estimated_transport_cost=25, transport_time=2.5, difficulty="facile",
        best_months=[3, 4, 5, 9, 10], trip_style=["city_culture", "food"],
        description="Le due grandi città del Portogallo, collegate da un comodo treno costiero.",
    ),
    dict(
        trip_id="tokyo_kyoto_osaka", name="Tokyo, Kyoto & Osaka",
        destinations=[60, 62, 63], minimum_days=9, ideal_days=12,
        estimated_transport_cost=140, transport_time=2.8, difficulty="media",
        best_months=[3, 4, 10, 11], trip_style=["city_culture", "food", "unique"],
        description="Il classico giro del Giappone: futuro a Tokyo, tradizione a Kyoto, cibo di strada a Osaka.",
    ),
    dict(
        trip_id="bangkok_chiangmai", name="Bangkok & Chiang Mai",
        destinations=[47, 64], minimum_days=7, ideal_days=9,
        estimated_transport_cost=45, transport_time=1.3, difficulty="facile",
        best_months=[11, 12, 1, 2], trip_style=["city_culture", "food", "nature_adventure"],
        description="La capitale frenetica e il nord più autentico e verde della Thailandia.",
    ),
    dict(
        trip_id="marrakech_sahara_essaouira", name="Marrakech, Sahara & Essaouira",
        destinations=[42, 66, 65], minimum_days=8, ideal_days=10,
        estimated_transport_cost=75, transport_time=10.5, difficulty="media",
        best_months=[3, 4, 10, 11, 12], trip_style=["unique", "nature_adventure", "city_culture"],
        description="Souk e riad a Marrakech, notte sotto le stelle nel deserto, oceano a Essaouira.",
    ),
    dict(
        trip_id="vienna_budapest", name="Vienna & Budapest",
        destinations=[22, 23], minimum_days=5, ideal_days=7,
        estimated_transport_cost=40, transport_time=2.5, difficulty="facile",
        best_months=[4, 5, 9, 12], trip_style=["city_culture"],
        description="Eleganza asburgica e terme danubiane, collegate da un treno comodissimo.",
    ),
    dict(
        trip_id="barcellona_costabrava", name="Barcellona & Costa Brava",
        destinations=[18, 67], minimum_days=5, ideal_days=7,
        estimated_transport_cost=15, transport_time=1.5, difficulty="facile",
        best_months=[5, 6, 9], trip_style=["city_culture", "relax_beach"],
        description="Città e mare: Gaudì e tapas a Barcellona, calette turchesi in Costa Brava.",
    ),
]


def load_routes_df() -> pd.DataFrame:
    return pd.DataFrame(RAW_ROUTES)


def load_trip_templates() -> list[dict]:
    return RAW_TRIP_TEMPLATES


TRIP_TEMPLATES = load_trip_templates()
