"""
Travel Estimates — come arrivare a ogni meta partendo da Milano, Bergamo o
Roma: aereo, treno, auto, auto + traghetto. Per ogni mezzo stima il tempo
porta a porta (solo andata) e il costo a persona (andata e ritorno), anche
per un gruppo: in auto carburante e pedaggi si dividono tra chi viaggia.

Principio guida, lo stesso di tutto il progetto: numeri onesti e dichiarati
come stime, mai una falsa precisione.
- Treno e traghetti vengono da tabelle scritte a mano su collegamenti che
  esistono davvero (orari tipici, prezzi tipici), non da una formula: una
  formula sulla distanza direbbe che Roma-Palermo in treno è come
  Roma-Milano, e non è vero.
- L'auto invece si calcola bene dalla distanza: chilometri stimati in linea
  d'aria per un fattore strada, velocità media da autostrada con le soste,
  carburante e pedaggi medi, più gli extra noti (Stretto di Messina,
  Eurotunnel, vignette).
- Il volo parte dai valori generici del dataset e li corregge per
  l'aeroporto di partenza con fattori dichiarati e modesti.

Nessuna chiamata di rete e nessuna dipendenza da Streamlit. Il motore di
raccomandazione non sa nulla di treni e traghetti: apply_travel() gli
restituisce lo stesso DataFrame di sempre, con il costo del volo sostituito
dal costo del mezzo scelto e in più le colonne travel_mode / travel_hours /
travel_available, che servono al filtro distanza e all'interfaccia.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from utils import flight_hours_label

# ---------------------------------------------------------------------------
# Città di partenza
# ---------------------------------------------------------------------------

DEPARTURES: dict[str, dict[str, Any]] = {
    "milano": dict(
        label="Milano", coords=(45.4642, 9.1900), airport="Malpensa o Linate",
        airport_hours=0.75, airport_cost=13,
    ),
    "bergamo": dict(
        label="Bergamo", coords=(45.6983, 9.6773), airport="Orio al Serio",
        airport_hours=0.3, airport_cost=3,
    ),
    "roma": dict(
        label="Roma", coords=(41.9028, 12.4964), airport="Fiumicino o Ciampino",
        airport_hours=0.6, airport_cost=14,
    ),
}

MODES: dict[str, tuple[str, str]] = {
    "plane": ("✈️", "Aereo"),
    "train": ("🚆", "Treno"),
    "car": ("🚗", "Auto"),
    "ferry": ("⛴️", "Auto + traghetto"),
}

# Preferenza espressa nel questionario -> mezzi che la soddisfano. Chi vuole
# muoversi in auto accetta anche un traghetto (ci si imbarca con la propria
# auto); chi sceglie l'aereo per una meta senza voli sensati (Firenze da
# Milano) non viene penalizzato: si usa il mezzo più comodo che c'è.
MODE_PREFERENCES: dict[str, set[str]] = {
    "best": {"plane", "train", "car", "ferry"},
    "plane": {"plane"},
    "train": {"train"},
    "car": {"car", "ferry"},
}

# Quanto "vale" un'ora di viaggio per scegliere il mezzo più conveniente:
# senza, vincerebbe sempre il bus notturno di 20 ore che costa 10 € in meno.
VALUE_OF_HOUR = 12.0
MAX_CAR_SEATS = 5

# ---------------------------------------------------------------------------
# Coordinate delle mete (il punto di riferimento dove si dorme la prima notte)
# ---------------------------------------------------------------------------

COORDS: dict[int, tuple[float, float]] = {
    1: (41.9028, 12.4964), 2: (43.7696, 11.2558), 3: (45.4408, 12.3155), 4: (40.6340, 14.6027),
    5: (44.1350, 9.6840), 6: (38.1157, 13.3615), 7: (37.8516, 15.2853), 8: (41.1360, 9.5350),
    9: (46.5405, 12.1357), 10: (46.4983, 11.3548), 11: (45.4642, 9.1900), 12: (45.0703, 7.6869),
    13: (40.3515, 18.1750), 14: (45.9870, 9.2610), 15: (43.1107, 12.3908), 16: (48.8566, 2.3522),
    17: (51.5074, -0.1278), 18: (41.3874, 2.1686), 19: (38.7223, -9.1393), 20: (32.6669, -16.9241),
    21: (50.0755, 14.4378), 22: (48.2082, 16.3738), 23: (47.4979, 19.0402), 24: (52.5200, 13.4050),
    25: (52.3676, 4.9041), 26: (55.6761, 12.5683), 27: (64.1466, -21.9426), 28: (69.6492, 18.9553),
    29: (66.5039, 25.7294), 30: (46.0207, 7.7491), 31: (47.2692, 11.4041), 32: (55.9533, -3.1883),
    33: (53.3498, -6.2603), 34: (37.9838, 23.7275), 35: (36.3932, 25.4615), 36: (35.5138, 24.0180),
    37: (35.8989, 14.5146), 38: (28.2916, -16.6291), 39: (50.0647, 19.9450), 40: (59.3293, 18.0686),
    41: (51.2093, 3.2247), 42: (31.6295, -7.9811), 43: (25.2048, 55.2708), 44: (23.5880, 58.3829),
    45: (-6.1659, 39.2026), 46: (7.8804, 98.3923), 47: (13.7563, 100.5018), 48: (-8.4095, 115.1889),
    49: (21.0278, 105.8342), 50: (6.9271, 79.8612), 51: (4.1755, 73.5093), 52: (40.7128, -74.0060),
    53: (25.7617, -80.1918), 54: (19.4326, -99.1332), 55: (23.1136, -82.3666), 56: (18.5601, -68.3725),
    57: (38.6431, 34.8289), 58: (41.0082, 28.9784), 59: (-33.9249, 18.4241), 60: (35.6762, 139.6503),
    61: (41.1579, -8.6291), 62: (35.0116, 135.7681), 63: (34.6937, 135.5023), 64: (18.7883, 98.9853),
    65: (31.5085, -9.7595), 66: (31.0802, -4.0133), 67: (41.7200, 2.9320), 68: (16.7479, -22.9491),
    69: (28.3587, -14.0537), 70: (29.0469, -13.5900), 71: (27.2579, 33.8116), 72: (29.5321, 35.0063),
    73: (68.2343, 14.5683), 74: (59.4370, 24.7536), 75: (41.7151, 44.8271), 76: (40.1792, 44.4991),
    77: (41.3275, 19.8187), 78: (41.1231, 20.8016), 79: (43.8563, 18.4131),
}


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distanza in linea d'aria (formula dell'emisfero, raggio 6371 km)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------------------
# Aereo
# ---------------------------------------------------------------------------

# Mete italiane: si propone l'aereo solo da dove esiste un volo sensato.
# Milano-Firenze in aereo non lo prende nessuno; Roma-Venezia sì.
_ITALY_FLIGHTS: dict[int, set[str]] = {
    1: {"milano", "bergamo"},
    3: {"roma"},
    4: {"milano", "bergamo"},          # Napoli, poi la costiera
    6: {"milano", "bergamo", "roma"},
    7: {"milano", "bergamo", "roma"},  # Catania
    8: {"milano", "bergamo", "roma"},  # Olbia
    9: {"roma"},                       # Venezia, poi bus per Cortina
    11: {"roma"},
    12: {"roma"},
    13: {"milano", "bergamo", "roma"},  # Brindisi
    14: {"roma"},                      # Milano, poi treno per il lago
}

# Da Orio al Serio partono voli diretti low cost anche fuori Europa, ma solo
# verso questi paesi; per il resto si vola da Malpensa (circa un'ora di
# strada in più da Bergamo).
_BERGAMO_DIRECT_COUNTRIES = {"Marocco", "Egitto", "Turchia", "Giordania", "Georgia"}

# Dall'aeroporto d'arrivo al posto dove si dorme, quando è lontano.
_AIRPORT_LAST_MILE: dict[int, float] = {
    4: 1.5, 7: 1.0, 8: 0.6, 9: 2.5, 13: 0.8, 14: 1.0, 30: 3.5, 57: 1.0,
    65: 0.5, 66: 8.0, 73: 1.5,
}
_DEFAULT_LAST_MILE = 0.75
_AIRPORT_BEFORE_FLIGHT = 1.75  # arrivo in aeroporto, controlli, imbarco

_ITALY_SOUTH_CLUSTERS = {"Sicilia", "Campania", "Sardegna", "Puglia"}


def _flight_factors(row: Any, city: str) -> tuple[float, float, float]:
    """(fattore ore, fattore costo, ore extra per arrivare all'aeroporto)."""
    region, country = row["region"], row["country"]
    if city == "roma":
        if region == "Italia" and row.get("cluster") in _ITALY_SOUTH_CLUSTERS:
            return 0.85, 0.80, 0.0
        if region == "Extra-Europa":
            return 0.92, 0.90, 0.0  # Fiumicino: l'hub intercontinentale italiano
        return 1.0, 1.0, 0.0
    if city == "milano":
        if region == "Europa":
            return 0.92, 0.88, 0.0
        return 1.0, 1.0, 0.0
    if city == "bergamo":
        if region in ("Italia", "Europa"):
            return 0.95, 0.80, 0.0  # la base low cost più grande d'Italia
        if country in _BERGAMO_DIRECT_COUNTRIES:
            return 1.0, 0.85, 0.0
        return 1.0, 1.0, 0.6  # si vola da Malpensa
    return 1.0, 1.0, 0.0


def _plane_option(row: Any, city: str) -> dict[str, Any] | None:
    dest_id = int(row["id"])
    if row["region"] == "Italia" and city not in _ITALY_FLIGHTS.get(dest_id, set()):
        return None
    dep = DEPARTURES[city]
    hours_f, cost_f, extra_access = _flight_factors(row, city)
    flight_hours = float(row["flight_hours"]) * hours_f
    door = (
        dep["airport_hours"] + extra_access + _AIRPORT_BEFORE_FLIGHT
        + flight_hours + _AIRPORT_LAST_MILE.get(dest_id, _DEFAULT_LAST_MILE)
    )
    airport_ar = 2 * dep["airport_cost"]
    airport = dep["airport"] if not extra_access else "Malpensa"
    note = f"Da {airport}"
    if dest_id in _AIRPORT_LAST_MILE and _AIRPORT_LAST_MILE[dest_id] >= 1.0:
        note += f", poi circa {flight_hours_label(_AIRPORT_LAST_MILE[dest_id])} per arrivare a destinazione"
    return dict(
        mode="plane", hours=flight_hours, door_hours=door,
        cost_min=float(row["flight_cost_min"]) * cost_f + airport_ar,
        cost_max=float(row["flight_cost_max"]) * cost_f + airport_ar,
        shared=False, note=note + ".",
    )


# ---------------------------------------------------------------------------
# Treno (collegamenti reali, valori tipici di sola andata a persona)
# ---------------------------------------------------------------------------

# id -> città -> (ore, costo min, costo max, come ci si arriva)
_TRAIN: dict[int, dict[str, tuple[float, float, float, str]]] = {
    1: {"milano": (3.2, 35, 95, "Frecciarossa o Italo diretto")},
    2: {"milano": (1.9, 25, 65, "Alta velocità diretta"), "roma": (1.5, 20, 55, "Alta velocità diretta")},
    3: {"milano": (2.4, 20, 50, "Treno diretto"), "roma": (3.8, 35, 85, "Alta velocità diretta")},
    4: {"milano": (6.0, 50, 120, "Alta velocità fino a Salerno, poi traghetto o bus per Amalfi"),
        "roma": (2.8, 30, 70, "Alta velocità fino a Salerno, poi traghetto o bus per Amalfi")},
    5: {"milano": (3.3, 20, 45, "Fino a La Spezia o Levanto, poi il treno delle Cinque Terre"),
        "roma": (4.2, 35, 75, "Intercity fino a La Spezia, poi il treno delle Cinque Terre")},
    6: {"roma": (11.5, 45, 110, "Intercity Notte con cuccetta: il treno passa lo Stretto sul traghetto")},
    7: {"roma": (9.0, 45, 110, "Intercity fino a Taormina: il treno passa lo Stretto sul traghetto")},
    9: {"milano": (5.5, 35, 70, "Treno fino a Venezia Mestre, poi bus Cortina Express"),
        "roma": (6.8, 50, 100, "Alta velocità fino a Venezia Mestre, poi bus Cortina Express")},
    10: {"milano": (3.5, 30, 60, "Via Verona, un cambio"),
         "roma": (5.0, 50, 100, "Alta velocità fino a Verona, poi regionale")},
    11: {"roma": (3.2, 35, 95, "Frecciarossa o Italo diretto"), "bergamo": (0.8, 6, 8, "Regionale diretto")},
    12: {"milano": (1.0, 15, 35, "Alta velocità diretta"), "roma": (4.3, 45, 100, "Alta velocità diretta")},
    13: {"milano": (8.5, 55, 130, "Frecciarossa diretto per Lecce"),
         "roma": (5.5, 35, 90, "Frecciarossa o Intercity per Lecce")},
    14: {"milano": (1.2, 6, 12, "Regionale per Varenna, poi battello per Bellagio"),
         "bergamo": (1.5, 6, 10, "Regionale via Lecco per Varenna, poi battello per Bellagio"),
         "roma": (4.5, 45, 100, "Alta velocità fino a Milano, poi regionale e battello")},
    15: {"milano": (4.0, 35, 70, "Alta velocità fino a Firenze, poi regionale per Perugia"),
         "roma": (2.2, 10, 25, "Regionale diretto per Assisi e Perugia")},
    16: {"milano": (7.2, 40, 150, "Frecciarossa diretto Milano-Parigi"),
         "roma": (10.5, 70, 190, "Alta velocità fino a Milano, poi Frecciarossa per Parigi")},
    17: {"milano": (10.5, 110, 280, "Frecciarossa per Parigi, poi Eurostar")},
    18: {"milano": (12.5, 90, 220, "Via Nizza e Marsiglia (o via Parigi), due cambi")},
    67: {"milano": (13.0, 90, 220, "Fino a Girona, poi bus per la costa")},
    21: {"milano": (12.5, 70, 170, "Via Monaco di Baviera, uno o due cambi")},
    22: {"milano": (11.0, 60, 160, "Nightjet notturno o via Venezia"),
         "roma": (13.5, 60, 170, "Nightjet notturno Roma-Vienna")},
    23: {"milano": (13.5, 80, 190, "Via Vienna, due cambi")},
    24: {"milano": (12.0, 80, 200, "Via Monaco o Zurigo, uno o due cambi")},
    25: {"milano": (12.0, 90, 230, "Via Zurigo e Francoforte, o via Parigi")},
    41: {"milano": (11.0, 90, 230, "Via Parigi e Bruxelles, poi regionale")},
    30: {"milano": (3.3, 45, 110, "EuroCity per Briga o Visp, poi il trenino per Zermatt"),
         "roma": (6.8, 80, 180, "Alta velocità fino a Milano, poi EuroCity e trenino per Zermatt")},
    31: {"milano": (5.5, 45, 90, "Via Verona e il Brennero"),
         "roma": (7.0, 60, 130, "Alta velocità fino a Verona, poi il Brennero")},
}

# Da Bergamo, dove non c'è un collegamento dedicato, si passa da Milano.
_BERGAMO_TO_MILANO = (0.8, 6)
_STATION_ACCESS = 0.3  # arrivare in stazione, e dalla stazione all'alloggio


def _train_option(row: Any, city: str) -> dict[str, Any] | None:
    by_city = _TRAIN.get(int(row["id"]), {})
    if city in by_city:
        hours, cmin, cmax, note = by_city[city]
    elif city == "bergamo" and "milano" in by_city:
        hours, cmin, cmax, note = by_city["milano"]
        hours += _BERGAMO_TO_MILANO[0]
        cmin, cmax = cmin + _BERGAMO_TO_MILANO[1], cmax + _BERGAMO_TO_MILANO[1]
        note = "Regionale fino a Milano, poi: " + note[0].lower() + note[1:]
    else:
        return None
    return dict(
        mode="train", hours=hours, door_hours=hours + 2 * _STATION_ACCESS,
        cost_min=2 * cmin, cost_max=2 * cmax, shared=False, note=note + ".",
    )


# ---------------------------------------------------------------------------
# Auto
# ---------------------------------------------------------------------------

# Raggiungibili su strada dall'Italia (senza traghetti lunghi). Sicilia sì:
# lo Stretto è una traversata di venti minuti. Londra sì, con l'Eurotunnel.
_ROAD_OK = {
    1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15,
    16, 17, 18, 21, 22, 23, 24, 25, 26, 30, 31, 39, 41, 67, 77, 78, 79,
}
_ROAD_FACTOR_DEFAULT = 1.25  # km su strada per km in linea d'aria
_ROAD_FACTOR = {9: 1.35, 30: 1.35, 31: 1.3, 5: 1.3, 79: 1.4, 77: 1.4, 78: 1.4}

# Passaggi obbligati: in linea d'aria Roma-Palermo "attraversa" il Tirreno e
# Roma-Barcellona il Mar Ligure. Su strada si passa da qui.
_VILLA_SAN_GIOVANNI = (38.2195, 15.6370)  # imbarco per lo Stretto di Messina
_NIZZA = (43.7102, 7.2620)
_TRIESTE = (45.6495, 13.7768)
_VISP = (46.2934, 7.8812)
_ROAD_VIA: dict[int, tuple[float, float]] = {
    6: _VILLA_SAN_GIOVANNI, 7: _VILLA_SAN_GIOVANNI,
    18: _NIZZA, 67: _NIZZA,
    77: _TRIESTE, 78: _TRIESTE, 79: _TRIESTE,
    30: _VISP,
}
# Ore fisse oltre la guida: traversata dello Stretto, Eurotunnel, navetta.
_ROAD_EXTRA_HOURS = {6: 0.6, 7: 0.6, 17: 1.2, 30: 0.4}
_CAR_SPEED = 100.0           # km/h medi in autostrada
_BREAK_EVERY_KM = 300        # una sosta di un quarto d'ora ogni ~3 ore
_MAX_DRIVE_HOURS = 13.0      # oltre, da solo andata, non è più una vacanza in auto
_FUEL_EUR_PER_KM = 0.12      # ~6,5 l/100 km a ~1,85 €/l
_TOLL_EUR_PER_KM = 0.06      # media tra tratti a pedaggio e non

# Extra a viaggio (a macchina, solo andata) e cosa sapere.
_ROAD_EXTRAS: dict[int, tuple[float, str]] = {
    6: (40, "Traversata dello Stretto di Messina compresa"),
    7: (40, "Traversata dello Stretto di Messina compresa"),
    16: (45, "Traforo del Fréjus o del Monte Bianco compreso; in Francia le autostrade sono a pagamento"),
    41: (45, "Traforo del Fréjus o del Monte Bianco e autostrade francesi compresi"),
    25: (40, "Vignetta svizzera compresa; in Germania e Olanda le autostrade sono gratuite"),
    17: (175, "Traforo alpino ed Eurotunnel sotto la Manica compresi. A Londra si guida a sinistra e il centro è a pagamento"),
    30: (35, "Vignetta svizzera e parcheggio a Täsch compresi: a Zermatt le auto non entrano"),
    31: (12, "Vignetta austriaca compresa"),
    22: (15, "Vignetta austriaca compresa"),
    21: (25, "Vignette di Austria e Repubblica Ceca comprese"),
    23: (27, "Vignette di Austria e Ungheria comprese"),
    39: (35, "Vignette e pedaggi di Austria, Repubblica Ceca e Polonia compresi"),
    24: (12, "Vignetta austriaca compresa; in Germania le autostrade sono gratuite"),
    5: (0, "Nei borghi non si entra in auto: parcheggio a La Spezia o Levanto e poi treno"),
    4: (0, "In costiera parcheggiare è difficile e caro: meglio lasciare l'auto e usare bus e traghetti"),
    1: (0, "In centro c'è la ZTL: meglio un alloggio con parcheggio e poi mezzi pubblici"),
    2: (0, "Centro in ZTL: meglio parcheggiare fuori e muoversi a piedi"),
    3: (0, "Si lascia l'auto a Piazzale Roma o al Tronchetto (a pagamento)"),
    11: (0, "In centro si entra solo pagando l'Area C e i parcheggi sono cari: il treno è più comodo"),
}


def _cars_needed(people: int) -> int:
    return max(1, math.ceil(max(1, people) / MAX_CAR_SEATS))


def _drive(
    from_coords: tuple[float, float], to_coords: tuple[float, float], factor: float,
    via: tuple[float, float] | None = None,
) -> tuple[float, float]:
    """(km su strada, ore di guida con le soste), passando da `via` se
    indicato."""
    if via is not None:
        km = (distance_km(from_coords, via) + distance_km(via, to_coords)) * factor
    else:
        km = distance_km(from_coords, to_coords) * factor
    hours = km / _CAR_SPEED + 0.25 * int(km // _BREAK_EVERY_KM)
    return km, hours


def _car_option(row: Any, city: str, people: int) -> dict[str, Any] | None:
    dest_id = int(row["id"])
    if dest_id not in _ROAD_OK or dest_id not in COORDS:
        return None
    km, hours = _drive(
        DEPARTURES[city]["coords"], COORDS[dest_id],
        _ROAD_FACTOR.get(dest_id, _ROAD_FACTOR_DEFAULT), _ROAD_VIA.get(dest_id),
    )
    if hours > _MAX_DRIVE_HOURS or km < 20:
        return None
    hours += _ROAD_EXTRA_HOURS.get(dest_id, 0.0)
    extra, note = _ROAD_EXTRAS.get(dest_id, (0, ""))
    per_car_one_way = km * (_FUEL_EUR_PER_KM + _TOLL_EUR_PER_KM) + extra
    per_person = 2 * per_car_one_way * _cars_needed(people) / max(1, people)
    base_note = f"Circa {int(round(km, -1))} km, carburante e pedaggi"
    base_note += " divisi tra chi viaggia" if people > 1 else " a carico tuo"
    if hours > 8:
        base_note += ". È un viaggio lungo: meglio spezzarlo con una notte di sosta"
    return dict(
        mode="car", hours=hours, door_hours=hours + 0.3,
        # Il costo dell'auto è quasi certo (distanza nota): forbice stretta.
        cost_min=per_person * 0.9, cost_max=per_person * 1.15,
        shared=True, note=base_note + (". " + note if note else "") + ".",
    )


# ---------------------------------------------------------------------------
# Auto + traghetto (rotte reali, valori tipici di sola andata)
# ---------------------------------------------------------------------------

_PORTS = {
    "Genova": (44.4056, 8.9463),
    "Civitavecchia": (42.0930, 11.7960),
    "Bari": (41.1171, 16.8719),
    "Ancona": (43.6158, 13.5189),
    "Pozzallo": (36.7300, 14.8490),
}

# port, ore di traversata, (passeggero min, max), (auto min, max), mete servite
# e, per ciascuna, le ore dal porto d'arrivo all'alloggio.
_FERRY_ROUTES = [
    dict(name="Genova-Olbia", port="Genova", crossing=10.5, pax=(55, 110), car=(80, 160), dests={8: 0.6}),
    dict(name="Civitavecchia-Olbia", port="Civitavecchia", crossing=6.5, pax=(45, 95), car=(70, 140), dests={8: 0.6}),
    dict(name="Genova-Palermo", port="Genova", crossing=20.0, pax=(70, 140), car=(90, 170), dests={6: 0.2}),
    dict(name="Civitavecchia-Palermo", port="Civitavecchia", crossing=14.0, pax=(55, 115), car=(80, 150), dests={6: 0.2}),
    dict(name="Genova-Barcellona", port="Genova", crossing=19.0, pax=(60, 130), car=(90, 170), dests={18: 0.3, 67: 1.3}),
    dict(name="Civitavecchia-Barcellona", port="Civitavecchia", crossing=20.5, pax=(60, 130), car=(90, 170), dests={18: 0.3, 67: 1.3}),
    dict(name="Bari-Durazzo", port="Bari", crossing=9.0, pax=(50, 90), car=(70, 120), dests={77: 0.75, 78: 3.0}),
    dict(name="Ancona-Patrasso", port="Ancona", crossing=22.0, pax=(60, 120), car=(90, 160), dests={34: 2.8}),
    dict(name="Bari-Patrasso", port="Bari", crossing=16.0, pax=(60, 120), car=(90, 160), dests={34: 2.8}),
    dict(name="Pozzallo-La Valletta", port="Pozzallo", crossing=1.75, pax=(55, 90), car=(90, 140), dests={37: 0.2}),
]
_FERRY_BOARDING = 1.0     # arrivo al porto prima della partenza
_MAX_FERRY_DOOR_HOURS = 30.0
_STRAIT_PORTS = {"Pozzallo"}  # in Sicilia si arriva passando lo Stretto


def _ferry_option(row: Any, city: str, people: int) -> dict[str, Any] | None:
    dest_id = int(row["id"])
    best = None
    for route in _FERRY_ROUTES:
        if dest_id not in route["dests"]:
            continue
        strait = route["port"] in _STRAIT_PORTS
        km, drive_h = _drive(
            DEPARTURES[city]["coords"], _PORTS[route["port"]], _ROAD_FACTOR_DEFAULT,
            _VILLA_SAN_GIOVANNI if strait else None,
        )
        if drive_h > _MAX_DRIVE_HOURS:
            continue
        strait = 40.0 if strait else 0.0
        if strait:
            drive_h += 0.6
        door = drive_h + _FERRY_BOARDING + route["crossing"] + route["dests"][dest_id]
        if door > _MAX_FERRY_DOOR_HOURS:
            continue
        cars = _cars_needed(people)
        per_car_road = km * (_FUEL_EUR_PER_KM + _TOLL_EUR_PER_KM) + strait
        lo = 2 * (route["pax"][0] + (route["car"][0] + per_car_road) * cars / max(1, people))
        hi = 2 * (route["pax"][1] + (route["car"][1] + per_car_road) * cars / max(1, people))
        overnight = route["crossing"] >= 8
        note = f"Traghetto {route['name']}"
        note += " di notte, in cabina o poltrona" if overnight else ""
        note += f"; {int(round(km, -1))} km in auto fino al porto"
        option = dict(
            mode="ferry", hours=door - 0.3, door_hours=door, cost_min=lo, cost_max=hi,
            shared=True, note=note + ".",
        )
        if best is None or option["door_hours"] < best["door_hours"]:
            best = option
    return best


# ---------------------------------------------------------------------------
# Confronto e scelta
# ---------------------------------------------------------------------------

def generalized_cost(option: dict[str, Any]) -> float:
    """Costo medio a persona + il valore del tempo passato in viaggio
    (andata e ritorno): è il criterio del "più conveniente"."""
    return (option["cost_min"] + option["cost_max"]) / 2 + VALUE_OF_HOUR * 2 * option["door_hours"]


def travel_options(row: Any, city: str | None, people: int = 2) -> list[dict[str, Any]]:
    """Tutti i modi sensati per arrivare alla meta dalla città indicata,
    ordinati dal più conveniente. Ogni opzione ha: mode, hours (in viaggio),
    door_hours (porta a porta, solo andata), cost_min/cost_max (a persona,
    andata e ritorno), shared (costo diviso tra chi viaggia), note, tags
    ("più economico", "più veloce", "il più conveniente")."""
    if city not in DEPARTURES:
        return []
    people = max(1, int(people or 1))
    options = [
        o for o in (
            _plane_option(row, city),
            _train_option(row, city),
            _car_option(row, city, people),
            _ferry_option(row, city, people),
        ) if o is not None
    ]
    options.sort(key=generalized_cost)
    if len(options) > 1:
        cheapest = min(options, key=lambda o: o["cost_min"] + o["cost_max"])
        fastest = min(options, key=lambda o: o["door_hours"])
        for o in options:
            o["tags"] = []
        options[0]["tags"].append("il più conveniente")
        cheapest["tags"].append("più economico")
        fastest["tags"].append("più veloce")
    elif options:
        options[0]["tags"] = []
    return options


def _is_home(row: Any, city: str) -> bool:
    dest = COORDS.get(int(row["id"]))
    return dest is not None and distance_km(DEPARTURES[city]["coords"], dest) < 20


def apply_travel(df: pd.DataFrame, city: str | None, preference: str = "best", people: int = 2) -> pd.DataFrame:
    """Il dataset visto da chi parte da `city` con il mezzo preferito.

    Per ogni meta sceglie il mezzo (il più conveniente tra quelli ammessi
    dalla preferenza) e mette il suo costo al posto del volo generico, così
    budget, costi totali e viaggi combinati lo usano senza cambiare nulla
    nel motore. Aggiunge:
      - travel_mode: "plane" / "train" / "car" / "ferry" / "home"
      - travel_hours: ore in viaggio di quel mezzo (le usa il filtro distanza)
      - travel_door_hours: porta a porta, solo andata
      - travel_available: False se la meta non si raggiunge col mezzo voluto
    flight_hours resta quello del volo: altrove significa "quanto è lontana".
    Senza città (o "altro") il dataset resta quello generico, in aereo."""
    df = df.copy()
    if city not in DEPARTURES:
        df["travel_mode"] = "plane"
        df["travel_hours"] = df["flight_hours"]
        df["travel_door_hours"] = df["flight_hours"] + 3.0
        df["travel_available"] = True
        return df

    accepted = MODE_PREFERENCES.get(preference, MODE_PREFERENCES["best"])
    modes, hours, door, available, cmin, cmax = [], [], [], [], [], []
    for _, row in df.iterrows():
        if _is_home(row, city):
            modes.append("home"); hours.append(0.0); door.append(0.0); available.append(True)
            cmin.append(0.0); cmax.append(0.0)
            continue
        options = travel_options(row, city, people)
        allowed = [o for o in options if o["mode"] in accepted]
        ok = bool(allowed)
        if not allowed and preference in ("plane", "best"):
            allowed, ok = options, True
        chosen = allowed[0] if allowed else None
        if chosen is None:
            # Irraggiungibile col mezzo voluto: restano i valori del volo
            # (per mostrarla comunque, se servisse ripiegare) ma segnata.
            chosen = _plane_option(row, city) or dict(
                mode="plane", hours=float(row["flight_hours"]), door_hours=float(row["flight_hours"]) + 3.0,
                cost_min=float(row["flight_cost_min"]), cost_max=float(row["flight_cost_max"]),
            )
        modes.append(chosen["mode"]); hours.append(chosen["hours"]); door.append(chosen["door_hours"])
        available.append(ok); cmin.append(chosen["cost_min"]); cmax.append(chosen["cost_max"])

    df["travel_mode"] = modes
    df["travel_hours"] = hours
    df["travel_door_hours"] = door
    df["travel_available"] = available
    df["flight_cost_min"] = [round(v, -1) for v in cmin]
    df["flight_cost_max"] = [round(v, -1) for v in cmax]
    df["total_cost_min"] = df["flight_cost_min"] + df["hotel_cost_min"] + df["food_cost_min"] + df["activity_cost_min"]
    df["total_cost_max"] = df["flight_cost_max"] + df["hotel_cost_max"] + df["food_cost_max"] + df["activity_cost_max"]
    return df


def keep_reachable(df: pd.DataFrame, preference: str) -> pd.DataFrame:
    """Chi vuole viaggiare solo in treno o in auto vede solo le mete che si
    raggiungono così. Se non ne resta nessuna (vincoli troppo stretti)
    meglio mostrare tutto che una pagina vuota."""
    if preference not in ("train", "car") or "travel_available" not in df.columns:
        return df
    reachable = df[df["travel_available"]]
    return reachable if not reachable.empty else df


def travel_label(mode: str | None, hours: float, city: str | None) -> str:
    """'Volo da Milano · 1h50', 'In auto da Roma · 6h30'... Senza città:
    la sola durata del volo generico."""
    duration = flight_hours_label(hours)
    if city not in DEPARTURES or not mode:
        return f"{duration} di volo"
    origin = DEPARTURES[city]["label"]
    return {
        "plane": f"Volo da {origin} · {duration}",
        "train": f"Treno da {origin} · {duration}",
        "car": f"In auto da {origin} · {duration}",
        "ferry": f"Auto e traghetto da {origin} · {duration}",
        "home": f"Sei già a {origin}",
    }.get(mode, f"{duration} di viaggio")
