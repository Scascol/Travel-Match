"""
Itinerari classici — costruisce un itinerario giorno per giorno (mattina /
pomeriggio / sera) per una destinazione, con un budget di tempo realistico.

COSA C'E' DI VERO QUI DENTRO, E COSA NO
---------------------------------------
Il dataset non contiene attrazioni con orari, zone urbane, prezzi dei
trasporti o tempi di coda: inventarli per 79 destinazioni significherebbe
presentare come informazione di viaggio dei dati fabbricati. Quindi:

- gli ANCORAGGI degli itinerari sono le `wow_experiences` e i
  `practical_tips` gia' curati a mano nel dataset (contenuto reale);
- la STRUTTURA e i TEMPI sono calcolati davvero: ore di luce per latitudine
  e stagione, durata tipica per categoria di attivita', tempi di
  trasferimento per profilo di mobilita', tetto di attivita' per giornata;
- il riempimento tra un'ancora e l'altra usa blocchi generici derivati dai
  tag ("mattina tra i monumenti del centro"), mai nomi di luoghi inventati;
- mobilita' e zone sono descritte per CATEGORIA (compatta a piedi / serve
  l'auto / tutto in resort), non con numeri di linea o prezzi di biglietti.

Nessuna dipendenza da Streamlit: come gli altri moduli di presentazione,
resta testabile in isolamento.
"""

from __future__ import annotations

from typing import Any

import places as places_mod

# ---------------------------------------------------------------------------
# Ore di luce — vincolo forte del "quanto ci sta in una giornata".
#
# In Lapponia a dicembre ci sono ~4 ore di luce utile: un itinerario che
# ignora questo dato proporrebbe tre attivita' all'aperto che nella realta'
# non stanno in una giornata. La banda e' geografia pura (latitudine del
# paese), non un dato inventato sulla singola meta.
# ---------------------------------------------------------------------------

BAND_ARCTIC = "arctic"
BAND_NORDIC = "nordic"
BAND_TEMPERATE = "temperate"
BAND_MEDITERRANEAN = "mediterranean"
BAND_SUBTROPICAL = "subtropical"
BAND_TROPICAL = "tropical"

DAYLIGHT_BAND_BY_COUNTRY: dict[str, str] = {
    # Oltre o a ridosso del circolo polare: escursione estrema tra le stagioni.
    "Islanda": BAND_ARCTIC, "Finlandia": BAND_ARCTIC, "Norvegia": BAND_ARCTIC,
    # Nord Europa: inverni molto corti, estati lunghissime.
    "Svezia": BAND_NORDIC, "Danimarca": BAND_NORDIC, "Estonia": BAND_NORDIC,
    "Irlanda": BAND_NORDIC, "Regno Unito": BAND_NORDIC, "Polonia": BAND_NORDIC,
    # Europa continentale e Nord America temperato.
    "Francia": BAND_TEMPERATE, "Germania": BAND_TEMPERATE, "Paesi Bassi": BAND_TEMPERATE,
    "Belgio": BAND_TEMPERATE, "Austria": BAND_TEMPERATE, "Svizzera": BAND_TEMPERATE,
    "Repubblica Ceca": BAND_TEMPERATE, "Ungheria": BAND_TEMPERATE,
    "Bosnia ed Erzegovina": BAND_TEMPERATE, "Macedonia del Nord": BAND_TEMPERATE,
    "Georgia": BAND_TEMPERATE, "Armenia": BAND_TEMPERATE, "Stati Uniti": BAND_TEMPERATE,
    "Giappone": BAND_TEMPERATE,
    # Mediterraneo e latitudini simili.
    "Italia": BAND_MEDITERRANEAN, "Spagna": BAND_MEDITERRANEAN, "Portogallo": BAND_MEDITERRANEAN,
    "Grecia": BAND_MEDITERRANEAN, "Malta": BAND_MEDITERRANEAN, "Turchia": BAND_MEDITERRANEAN,
    "Albania": BAND_MEDITERRANEAN, "Marocco": BAND_MEDITERRANEAN,
    # Subtropicale: giornate piu' costanti, inverni miti.
    "Egitto": BAND_SUBTROPICAL, "Giordania": BAND_SUBTROPICAL, "Emirati Arabi Uniti": BAND_SUBTROPICAL,
    "Oman": BAND_SUBTROPICAL, "Messico": BAND_SUBTROPICAL, "Cuba": BAND_SUBTROPICAL,
    "Repubblica Dominicana": BAND_SUBTROPICAL, "Capo Verde": BAND_SUBTROPICAL,
    "Sudafrica": BAND_SUBTROPICAL,
    # Tropicale: ~12 ore di luce tutto l'anno.
    "Thailandia": BAND_TROPICAL, "Indonesia": BAND_TROPICAL, "Vietnam": BAND_TROPICAL,
    "Sri Lanka": BAND_TROPICAL, "Maldive": BAND_TROPICAL, "Tanzania": BAND_TROPICAL,
}

#                            gen  feb  mar  apr  mag  giu  lug  ago  set  ott  nov  dic
DAYLIGHT_HOURS: dict[str, list[float]] = {
    BAND_ARCTIC:        [4.5, 7.5, 11.0, 14.5, 18.0, 21.0, 19.5, 16.0, 12.5, 9.0, 5.5, 3.5],
    BAND_NORDIC:        [7.0, 9.0, 11.5, 14.0, 16.5, 17.5, 17.0, 15.0, 12.5, 10.0, 8.0, 6.5],
    BAND_TEMPERATE:     [8.5, 10.0, 12.0, 13.5, 15.0, 16.0, 15.5, 14.5, 12.5, 11.0, 9.5, 8.5],
    BAND_MEDITERRANEAN: [9.5, 10.5, 12.0, 13.0, 14.5, 15.0, 14.5, 13.5, 12.5, 11.0, 10.0, 9.0],
    BAND_SUBTROPICAL:   [10.5, 11.0, 12.0, 12.5, 13.5, 13.5, 13.5, 13.0, 12.5, 11.5, 11.0, 10.5],
    BAND_TROPICAL:      [11.5, 11.5, 12.0, 12.0, 12.5, 12.5, 12.5, 12.0, 12.0, 12.0, 11.5, 11.5],
}


def daylight_hours(country: str, months: list[int] | None) -> float:
    """Ore di luce utilizzabili nel periodo scelto. Nessun mese indicato ->
    media annua, cosi' l'itinerario resta sensato anche senza periodo."""
    band = DAYLIGHT_BAND_BY_COUNTRY.get(country, BAND_TEMPERATE)
    table = DAYLIGHT_HOURS[band]
    if not months:
        return sum(table) / 12
    valid = [table[m - 1] for m in months if 1 <= m <= 12]
    return sum(valid) / len(valid) if valid else sum(table) / 12


# ---------------------------------------------------------------------------
# Mobilita' — come ci si muove. Categoria, non dettagli inventati: da qui
# derivano i tempi di trasferimento usati nel budget di ogni giornata.
# ---------------------------------------------------------------------------

MOB_WALKABLE = "walkable"
MOB_TRANSIT = "transit"
MOB_CAR = "car"
MOB_RESORT = "resort"
MOB_TOUR = "tour"

MOBILITY_INFO: dict[str, dict[str, Any]] = {
    MOB_WALKABLE: {
        "label": "🚶 Tutto a piedi",
        "text": "Centro compatto: le cose principali stanno in un raggio percorribile a piedi. "
                "Il mezzo pubblico serve quasi solo dall'aeroporto o dalla stazione.",
        "transfer_h": 0.3,
    },
    MOB_TRANSIT: {
        "label": "🚇 Mezzi pubblici",
        "text": "Città estesa ma ben servita: metro/bus coprono quasi tutto. "
                "Se resti più di due giorni, verifica se esiste un titolo giornaliero o multi-corsa: "
                "quasi ovunque conviene rispetto ai biglietti singoli.",
        "transfer_h": 0.5,
    },
    MOB_CAR: {
        "label": "🚗 Serve un mezzo proprio",
        "text": "Le cose migliori sono sparse e il trasporto pubblico non le copre bene: "
                "auto a noleggio (o scooter, dove ha senso) cambia completamente il viaggio. "
                "Metti in conto tempo per parcheggio e rifornimenti.",
        "transfer_h": 0.9,
    },
    MOB_RESORT: {
        "label": "🏝️ Poco da spostarsi",
        "text": "Si sta quasi sempre nella stessa zona o struttura: gli spostamenti sono brevi "
                "e le escursioni si organizzano sul posto. Non serve un mezzo proprio.",
        "transfer_h": 0.2,
    },
    MOB_TOUR: {
        "label": "🧭 Escursioni organizzate",
        "text": "Le esperienze che contano si raggiungono con tour guidati o transfer dedicati: "
                "è il mezzo principale, più che un'alternativa. Prenota prima di partire nei periodi di punta.",
        "transfer_h": 0.8,
    },
}

# Casi in cui la regola automatica sbaglierebbe. Tenuti espliciti e pochi:
# se questa lista cresce troppo, conviene rivedere `mobility_profile()`.
MOBILITY_OVERRIDES: dict[int, str] = {
    3: MOB_WALKABLE,    # Venezia: si gira solo a piedi (e vaporetto), mai in auto
    29: MOB_TOUR,       # Rovaniemi: tutto passa da escursioni organizzate
    51: MOB_RESORT,     # Maldive: si resta sull'isola-resort
    66: MOB_TOUR,       # Merzouga: il deserto si fa con guida, non da soli
}


def mobility_profile(row: Any) -> dict[str, Any]:
    """Come ci si muove in questa destinazione.

    Derivato dai segnali gia' presenti (tag, relax, ore di volo, durata,
    punteggi), con una manciata di override espliciti per i casi in cui la
    regola sbaglierebbe. Stesso approccio dei profili stagionali in
    destinations.py: regola + eccezioni dichiarate, non 79 valori a mano."""
    # Gli override sono per id di destinazione. Un viaggio combinato ha un id
    # testuale ("firenze_cinqueterre") e nessun override: gli si applica la
    # regola generale, che e' quella giusta per una sequenza di tappe.
    try:
        override = MOBILITY_OVERRIDES.get(int(row["id"]))
    except (TypeError, ValueError):
        override = None
    if override:
        return {"kind": override, **MOBILITY_INFO[override]}

    tags = set(row.get("tags", []))
    text_blob = " ".join(row.get("wow_experiences", []) + row.get("practical_tips", [])).lower()

    if "road trip" in tags or "noleggia un'auto" in text_blob or "on the road" in text_blob:
        kind = MOB_CAR
    elif {"aurora boreale", "sci"} & tags or "safari" in text_blob:
        kind = MOB_TOUR
    # Mete da spiaggia molto rilassate e lontane: si vive nella propria zona.
    elif row.get("relax_score", 0) >= 78 and row.get("flight_hours", 0) >= 5 and ({"spiaggia", "mare"} & tags):
        kind = MOB_CAR if {"natura", "road trip"} & tags else MOB_RESORT
    # Isole e coste da esplorare: le spiagge belle non sono dietro l'hotel.
    elif {"spiaggia", "mare"} & tags and "natura" in tags:
        kind = MOB_CAR
    elif {"montagna", "trekking"} & tags:
        kind = MOB_CAR
    # Città: compatta se breve e a misura d'uomo, altrimenti mezzi pubblici.
    elif {"cultura", "monumenti"} & tags:
        kind = MOB_WALKABLE if row.get("days_max", 5) <= 4 else MOB_TRANSIT
    else:
        kind = MOB_TRANSIT

    return {"kind": kind, **MOBILITY_INFO[kind]}


# ---------------------------------------------------------------------------
# Zone principali — struttura del territorio, non toponimi inventati.
#
# Diciamo "Centro storico", "Costa", "Entroterra": categorie che valgono
# davvero per la meta perche' derivano dai suoi tag. Non diciamo mai
# "da Trastevere al Colosseo sono 15 minuti", che sarebbe un dato inventato.
# ---------------------------------------------------------------------------

_ZONE_BY_TAG: list[tuple[frozenset[str], str, str]] = [
    (frozenset({"monumenti", "cultura"}), "🏛️ Centro storico",
     "Il nucleo con i monumenti e i musei principali: è qui che si concentrano le code."),
    (frozenset({"spiaggia", "mare", "surf"}), "🏖️ Costa",
     "Spiagge e cale. Le più belle sono spesso le meno comode da raggiungere."),
    (frozenset({"natura", "montagna", "trekking"}), "⛰️ Entroterra e natura",
     "Parchi, sentieri e paesaggio aperto: richiede quasi sempre mezza giornata piena."),
    (frozenset({"nightlife", "food"}), "🍷 Quartieri della sera",
     "Zona di ristoranti e locali, di solito vicina al centro ma con vita propria dopo il tramonto."),
    (frozenset({"shopping"}), "🛍️ Zona commerciale",
     "Vie dello shopping e mercati: si incastra bene in un pomeriggio di trasferimento."),
    (frozenset({"wellness"}), "🧘 Zona wellness",
     "Terme, spa o ritiri: mezza giornata da prendersi con calma, non da incastrare."),
]

_SPREAD_LABEL = {
    MOB_WALKABLE: "Compatta — tra una zona e l'altra si va a piedi in 15-25 minuti.",
    MOB_TRANSIT: "Media — tra una zona e l'altra circa 20-40 minuti con i mezzi.",
    MOB_CAR: "Dispersa — tra una zona e l'altra si va da 30 a 70 minuti di auto.",
    MOB_RESORT: "Concentrata — quasi tutto entro pochi minuti dalla struttura.",
    MOB_TOUR: "Dispersa — le mete sono lontane e i tempi li detta il tour (spesso mezza giornata).",
}


def main_zones(row: Any) -> dict[str, Any]:
    """Le zone che l'itinerario tocca davvero, con la distanza tipica tra
    loro. Vuota per le mete che non hanno una struttura a poli (resort)."""
    tags = set(row.get("tags", []))
    zones = [
        {"name": name, "text": text}
        for keys, name, text in _ZONE_BY_TAG
        if keys & tags
    ]
    mob = mobility_profile(row)
    return {"zones": zones[:4], "spread": _SPREAD_LABEL[mob["kind"]]}


# ---------------------------------------------------------------------------
# Catalogo attivita' — durata e slot naturale.
#
# Le `wow_experiences` del dataset vengono classificate leggendo le parole
# chiave che contengono: "trekking"/"escursione" occupa mezza giornata buona,
# "cena"/"tramonto"/"aurora" e' serale, "museo"/"mercato" e' un blocco corto.
# ---------------------------------------------------------------------------

SLOT_MORNING = "mattina"
SLOT_AFTERNOON = "pomeriggio"
SLOT_EVENING = "sera"

# (parole chiave, durata in ore, slot preferito)
_EXPERIENCE_RULES: list[tuple[tuple[str, ...], float, str | None]] = [
    (("aurora", "stellata"), 3.0, SLOT_EVENING),
    (("cena", "aperitivo", "vino", "taranta", "concerto"), 2.5, SLOT_EVENING),
    (("tramonto", "notte", "illuminat", "sera", "nightlife", "mercatino"), 2.5, SLOT_EVENING),
    (("alba", "sunrise"), 3.0, SLOT_MORNING),
    (("trekking", "escursione", "gola", "safari", "vulcano", "deserto", "dune",
      "cerchio d'oro", "fiordi", "gita", "isola", "tour"), 6.0, SLOT_MORNING),
    (("spiaggia", "snorkeling", "immersione", "surf", "laguna", "barca", "vela",
      "terme", "sauna", "spa"), 4.0, SLOT_AFTERNOON),
    (("museo", "galleria", "rovine", "cattedrale", "cupola", "palazzo", "castello",
      "moschea", "tempio", "colosseo"), 3.0, None),
    (("mercato", "quartiere", "passeggiata", "piazza", "centro storico",
      "street food", "giro"), 2.0, None),
]

_DEFAULT_DURATION = 2.5

# Blocchi generici per riempire gli slot che le wow_experiences non coprono.
# Testi volutamente non specifici: descrivono un modo di passare il tempo,
# non un luogo preciso che non conosciamo.
# (testo, ore, slot preferito — None = flessibile, ripetibile)
# `ripetibile=False` per le attivita' che ha senso fare una volta sola:
# ci si orienta il primo giorno, non anche il sesto.
_FILLER_BY_TAG: dict[str, list[tuple[str, float, str | None, bool]]] = {
    "cultura": [("Musei o centro storico con calma", 3.0, None, True),
                ("Quartieri fuori dal circuito turistico, a piedi", 2.5, None, True)],
    "monumenti": [("I monumenti principali appena aprono, per evitare le code", 3.0, SLOT_MORNING, True)],
    "spiaggia": [("Mezza giornata in spiaggia, senza programma", 4.0, None, True)],
    "mare": [("Cala o tratto di costa raggiungibile in giornata", 4.0, None, True)],
    "natura": [("Sentiero o punto panoramico fuori città", 4.0, None, True)],
    "montagna": [("Salita in quota e pranzo in rifugio", 5.0, SLOT_MORNING, True)],
    "trekking": [("Cammino su sentiero segnalato", 5.0, SLOT_MORNING, True)],
    "food": [("Mercato locale e assaggi in giro", 2.0, SLOT_MORNING, True),
             ("Cena lenta in una trattoria del posto", 2.5, SLOT_EVENING, True)],
    "wellness": [("Terme o spa, senza guardare l'orologio", 3.5, None, True)],
    "shopping": [("Vie dello shopping e botteghe artigiane", 2.5, SLOT_AFTERNOON, True)],
    "nightlife": [("Serata nei locali della zona", 3.0, SLOT_EVENING, True)],
    "sci": [("Giornata sulle piste", 5.0, SLOT_MORNING, True)],
    "neve": [("Attività sulla neve (slitta, ciaspole, motoslitta)", 3.5, None, True)],
    "aurora boreale": [("Uscita serale a caccia di aurora, lontano dalle luci", 3.0, SLOT_EVENING, True)],
    "esperienze insolite": [("L'esperienza insolita per cui si viene qui", 3.0, None, True)],
    "fotografia": [("Giro fotografico nell'ora dorata", 2.0, None, True)],
    "road trip": [("Tratto in auto con soste dove capita", 4.0, SLOT_MORNING, True)],
    # Formulazione diversa da quella di insights.typical_day, che compare
    # nella stessa card poche righe sopra: identiche si leggerebbero due volte.
    "citta illuminate": [("Giro serale tra le vie illuminate del centro", 2.0, SLOT_EVENING, True)],
    "mercatini di natale": [("Giro tra le luci dei mercatini", 2.5, SLOT_EVENING, True)],
    "silenzio": [("Tempo lento, senza programma", 2.5, None, True)],
    "surf": [("Sessione in acqua quando le onde sono buone", 3.5, None, True)],
}

# Tag che esistono solo in una parte dell'anno. Senza questo filtro, una meta
# artica a luglio riceveva come riempimento generico "uscita a caccia di
# aurora" e "attivita' sulla neve": due cose impossibili nel mese scelto, per
# giunta subito dopo aver escluso le stesse attivita' dal contenuto curato.
_FILLER_TAG_MONTHS: dict[str, set[int]] = {
    "aurora boreale": {9, 10, 11, 12, 1, 2, 3},
    "neve": {12, 1, 2, 3, 4},
    "sci": {12, 1, 2, 3, 4},
    "mercatini di natale": {11, 12, 1},
    "citta illuminate": {10, 11, 12, 1, 2},
}


_UNIVERSAL_FILLER: list[tuple[str, float, str | None, bool]] = [
    ("Giro senza meta per orientarsi", 2.0, SLOT_MORNING, False),
    ("Pomeriggio libero, al ritmo che preferisci", 2.5, SLOT_AFTERNOON, True),
    # Formulazione volutamente neutra: "cena nel quartiere" stonava sulle
    # mete che un quartiere non ce l'hanno (isole-resort, villaggi sciistici).
    ("Cena tranquilla e rientro senza fretta", 2.0, SLOT_EVENING, True),
]


def _classify_experience(text: str) -> tuple[float, str | None]:
    """Durata (ore) e slot preferito di un'esperienza, dalle sue parole chiave."""
    lowered = text.lower()
    for keywords, hours, slot in _EXPERIENCE_RULES:
        if any(k in lowered for k in keywords):
            return hours, slot
    return _DEFAULT_DURATION, None


# ---------------------------------------------------------------------------
# Stili di viaggio — cambiano densita', durata della giornata e priorita'.
# ---------------------------------------------------------------------------

STYLE_STANDARD = "standard"
STYLE_RELAX = "relax"
STYLE_INTENSE = "intenso"
STYLE_FOODIE = "foodie"
STYLE_FAMILY = "famiglia"

STYLE_PROFILES: dict[str, dict[str, Any]] = {
    STYLE_STANDARD: {
        "label": "⚖️ Standard", "max_activities": 3, "max_day_hours": 8.0,
        "pause_hours": 1.5, "prefer_tags": (),
        "note": "Due o tre cose al giorno, con tempo per mangiare e camminare senza fretta.",
    },
    STYLE_RELAX: {
        "label": "😌 Relax", "max_activities": 2, "max_day_hours": 5.5,
        "pause_hours": 2.5, "prefer_tags": ("wellness", "spiaggia", "mare"),
        "note": "Una cosa importante al giorno, il resto è tempo libero. Giornate corte per scelta.",
    },
    STYLE_INTENSE: {
        # Tetto a 10h: oltre non e' "intenso", e' una giornata che non regge.
        "label": "🥾 Intenso", "max_activities": 4, "max_day_hours": 10.0,
        "pause_hours": 1.0, "prefer_tags": ("trekking", "natura", "monumenti", "cultura"),
        "note": "Giornate piene ma ancora umane: mai oltre le 10 ore di attività.",
    },
    STYLE_FOODIE: {
        "label": "🍝 Foodie", "max_activities": 3, "max_day_hours": 7.5,
        "pause_hours": 2.0, "prefer_tags": ("food",),
        "note": "Mercati, pranzi lunghi e cene con calma: il cibo è il filo del viaggio, non un intervallo.",
    },
    STYLE_FAMILY: {
        "label": "👨‍👩‍👧 Con bambini", "max_activities": 2, "max_day_hours": 6.0,
        "pause_hours": 2.5, "prefer_tags": ("natura", "spiaggia", "mare"),
        "note": "Ritmi lenti, una attività principale al giorno e pause frequenti. Rientro presto.",
    },
}


# ---------------------------------------------------------------------------
# Costruzione dell'itinerario
# ---------------------------------------------------------------------------

def standard_itinerary_days(row: Any, preferred: int | None = None) -> int:
    """Durata dell'itinerario classico: 3 o 5 giorni, riportati dentro
    days_min-days_max della meta. Per le mete lunghe (Bali 9-14) si usa il
    minimo consigliato: proporre 5 giorni a 15 ore di volo sarebbe assurdo."""
    days_min = int(row.get("days_min", 3))
    days_max = int(row.get("days_max", 5))
    base = preferred if preferred else (5 if days_max >= 5 else 3)
    return max(days_min, min(base, days_max))


def _activity_pool(
    row: Any, style: str, months: list[int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Due liste separate, perche' seguono regole diverse.

    Le ANCORE (`wow_experiences`) sono contenuto curato e unico: si usano una
    volta sola, una per giornata. I FILLER sono blocchi generici e possono
    ripetersi tra i giorni — ed e' giusto che lo facciano: in una vacanza al
    mare di una settimana ci sono davvero piu' giornate di spiaggia. Tenerli
    unici lasciava le giornate finali vuote, che e' peggio che ripetersi."""
    anchors = []
    for exp in row.get("wow_experiences", []):
        hours, slot = _classify_experience(exp)
        anchors.append({"text": exp, "hours": hours, "slot": slot, "anchor": True})

    profile = STYLE_PROFILES[style]
    tags = list(row.get("tags", []))
    # I tag preferiti dallo stile vengono per primi: e' cosi' che "foodie"
    # ottiene davvero piu' cibo e "relax" piu' spiaggia/wellness.
    tags.sort(key=lambda t: 0 if t in profile["prefer_tags"] else 1)

    def tag_in_season(tag: str) -> bool:
        window = _FILLER_TAG_MONTHS.get(tag)
        if not window or not months:
            return True
        return any(m in window for m in months)

    fillers = []
    for tag in tags:
        if not tag_in_season(tag):
            continue
        for text, hours, slot, repeatable in _FILLER_BY_TAG.get(tag, []):
            fillers.append({"text": text, "hours": hours, "slot": slot,
                            "anchor": False, "repeatable": repeatable})
    for text, hours, slot, repeatable in _UNIVERSAL_FILLER:
        fillers.append({"text": text, "hours": hours, "slot": slot,
                        "anchor": False, "repeatable": repeatable})

    return anchors, fillers


def _pick_filler(
    fillers: list[dict[str, Any]], slot: str, max_hours: float, usage: dict[str, int],
) -> dict[str, Any] | None:
    """Il filler piu' adatto a uno slot, preferendo quelli usati meno volte:
    cosi' le ripetizioni arrivano solo quando le alternative sono finite.
    Le attivita' non ripetibili (es. orientarsi) escono dal giro dopo la prima."""
    # `slot is None` significa "mattina o pomeriggio", MAI sera: senza questo
    # vincolo una gita in spiaggia da 4 ore finiva nello slot serale.
    def fits_slot(f: dict[str, Any]) -> bool:
        if slot == SLOT_EVENING:
            return f["slot"] == SLOT_EVENING
        return f["slot"] == slot or f["slot"] is None

    candidates = [
        f for f in fillers
        if f["hours"] <= max_hours
        and fits_slot(f)
        and (f["repeatable"] or usage.get(f["text"], 0) == 0)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda f: (usage.get(f["text"], 0), -f["hours"]))


def build_standard_itinerary(
    row: Any,
    style: str = STYLE_STANDARD,
    days: int | None = None,
    months: list[int] | None = None,
) -> dict[str, Any]:
    """Itinerario giorno per giorno con budget di tempo reale.

    Struttura: al massimo un'attivita' per slot (mattina / pomeriggio / sera),
    quindi al massimo 2 attivita' "principali" di giorno piu' una serale —
    esattamente il tetto di 2-3 cose al giorno. Un'attivita' da mezza giornata
    (>= 4h) occupa mattina E pomeriggio invece di essere impilata su altro.

    Vincoli rispettati in ordine di durezza: ore di luce della stagione,
    tetto orario dello stile, tempo di trasferimento del profilo di mobilita'."""
    style = style if style in STYLE_PROFILES else STYLE_STANDARD
    profile = STYLE_PROFILES[style]
    n_days = days or standard_itinerary_days(row)

    light = daylight_hours(row.get("country", ""), months)
    mob = mobility_profile(row)
    transfer = mob["transfer_h"]

    # Il tetto giornaliero e' il piu' stringente tra lo stile e la luce
    # disponibile (meno le pause): a dicembre in Lapponia comanda la luce.
    #
    # Il pavimento a 4.5h non e' arbitrario: sotto il circolo polare d'inverno
    # ci sono 3-4 ore di luce, ma le attivita' per cui ci si va (aurora,
    # slitte, saune, musei) si fanno al buio o al chiuso. Senza pavimento
    # l'itinerario restava vuoto, che e' falso quanto ignorare del tutto la luce.
    daylight_is_binding = light - profile["pause_hours"] < profile["max_day_hours"]
    day_budget = min(profile["max_day_hours"], max(4.5, light - profile["pause_hours"]))

    anchors, fillers = _activity_pool(row, style, months)
    usage: dict[str, int] = {}
    days_out: list[dict[str, Any]] = []
    anchor_queue = list(anchors)

    for day_index in range(n_days):
        slots: dict[str, dict[str, Any] | None] = {
            SLOT_MORNING: None, SLOT_AFTERNOON: None, SLOT_EVENING: None,
        }
        spent = 0.0

        def place(activity: dict[str, Any], slot: str) -> None:
            """Colloca un'attivita'. Se dura mezza giornata o piu' (>= 4h) e
            non e' serale, occupa mattina E pomeriggio: e' l'unico modo
            onesto di dire "questa cosa ti prende mezza giornata" invece di
            impilarci sopra dell'altro."""
            nonlocal spent
            spans = slot != SLOT_EVENING and activity["hours"] >= 4.0
            entry = {
                "text": activity["text"], "hours": activity["hours"],
                "anchor": activity["anchor"], "half_day": spans,
            }
            if spans:
                slots[SLOT_MORNING] = entry
                slots[SLOT_AFTERNOON] = {**entry, "continued": True}
            else:
                slots[slot] = entry
            usage[activity["text"]] = usage.get(activity["text"], 0) + 1
            if slot != SLOT_EVENING:
                spent += activity["hours"] + transfer

        # 1. L'ancora del giorno: una per giornata, sempre collocata. Sono le
        # esperienze per cui si va in quella meta — se non ci stanno nel
        # budget, e' il resto della giornata a doversi stringere, non loro.
        if anchor_queue:
            anchor = anchor_queue.pop(0)
            place(anchor, anchor["slot"] or SLOT_MORNING)

        # 2. Riempimento degli slot diurni ancora liberi, entro il budget.
        max_main = profile["max_activities"]
        for slot in (SLOT_MORNING, SLOT_AFTERNOON):
            if slots[slot] is not None:
                continue
            used_main = sum(1 for s in (SLOT_MORNING, SLOT_AFTERNOON) if slots[s] is not None)
            if used_main >= max_main:
                break
            remaining = day_budget - spent - transfer
            if remaining < 1.5:
                break
            # Una mezza giornata puo' partire solo dalla mattina: se la
            # mattina e' gia' occupata, per il pomeriggio servono blocchi corti.
            cap = remaining if slot == SLOT_MORNING else min(remaining, 3.9)
            filler = _pick_filler(fillers, slot, cap, usage)
            if filler:
                place(filler, slot)

        # 3. La sera non consuma ore di luce: c'e' sempre spazio per una cosa.
        if slots[SLOT_EVENING] is None:
            evening = _pick_filler(fillers, SLOT_EVENING, 99.0, usage)
            if evening:
                place(evening, SLOT_EVENING)

        n_main = sum(
            1 for s in (SLOT_MORNING, SLOT_AFTERNOON)
            if slots[s] is not None and not slots[s].get("continued")
        )
        days_out.append({
            "day": day_index + 1,
            "slots": slots,
            "active_hours": round(spent, 1),
            "n_activities": n_main,
        })

    return {
        "days": days_out,
        "n_days": n_days,
        "style": style,
        "style_label": profile["label"],
        "style_note": profile["note"],
        "daylight_hours": round(light, 1),
        "day_budget_hours": round(day_budget, 1),
        "daylight_is_binding": daylight_is_binding,
        "transfer_hours": transfer,
        "mobility": mob,
    }


# ---------------------------------------------------------------------------
# Itinerari curati — mete con luoghi reali in places.py
#
# Stessi vincoli del motore generico (ore di luce, tetto dello stile, slot),
# ma le attivita' hanno un nome proprio e una modalita'. In piu' compare la
# BASE: dove si dorme ogni notte. E' il pezzo che il motore generico non puo'
# avere, perche' richiede di sapere dove stanno le cose — a Creta, Cnosso e
# Samaria sono a tre ore d'auto, e un itinerario che le mette in giornate
# consecutive senza spostare la base e' sbagliato anche se "sta" nel budget.
#
# Le ore di ogni luogo includono gia' il tempo per raggiungerlo dalla sua
# base: e' per questo che Elafonissi vale 6 ore e non 4.
# ---------------------------------------------------------------------------

def _allocate_nights(bases: list[dict[str, Any]], n_days: int) -> list[str]:
    """Quante notti per base, e in che ordine. Le basi con `night_weight` 0
    sono porte d'ingresso (ci si atterra, non ci si dorme).

    `max_nights` evita il caso in cui il peso proporzionale darebbe due notti
    a una tappa che ne merita una: a Rethymno si dorme una volta sola, il
    resto delle notti va dove ci sono le cose da fare."""
    hosts = [b for b in bases if b.get("night_weight", 0) > 0]
    if not hosts or n_days <= 0:
        return []

    total_w = sum(b["night_weight"] for b in hosts)
    alloc = {
        b["key"]: max(1, min(int(round(b["night_weight"] / total_w * n_days)),
                             b.get("max_nights", n_days)))
        for b in hosts
    }

    # Aggiustamento dell'arrotondamento, in entrambe le direzioni.
    for _ in range(100):
        current = sum(alloc.values())
        if current == n_days:
            break
        if current < n_days:
            pool = [b for b in hosts
                    if b["key"] in alloc and alloc[b["key"]] < b.get("max_nights", n_days)]
            if not pool:
                break
            alloc[max(pool, key=lambda b: b["night_weight"])["key"]] += 1
        else:
            pool = [b for b in hosts if b["key"] in alloc and alloc[b["key"]] > 1]
            if pool:
                alloc[min(pool, key=lambda b: b["night_weight"])["key"]] -= 1
            else:
                # Tutte a una notte e sono ancora troppe: il viaggio e' corto,
                # si rinuncia alle tappe meno importanti invece di correre.
                droppable = [b for b in hosts if b["key"] in alloc]
                if len(droppable) <= 1:
                    break
                del alloc[min(droppable, key=lambda b: b["night_weight"])["key"]]

    seq: list[str] = []
    for base in bases:  # ordine curato = ordine geografico del percorso
        seq.extend([base["key"]] * alloc.get(base["key"], 0))
    return seq


def _place_fits_slot(place: dict[str, Any], slot: str) -> bool:
    """Come per i filler: `slot is None` vuol dire "di giorno", mai di sera."""
    if slot == SLOT_EVENING:
        return place.get("slot") == SLOT_EVENING
    return place.get("slot") in (slot, None)


def _pick_place(
    pools: dict[str, list[dict[str, Any]]], sources: list[str], slot: str, max_hours: float,
    only_must: bool = False,
) -> dict[str, Any] | None:
    """Il luogo migliore tra le basi consultabili oggi.

    I `must` vincono sempre sugli `extra`, anche quando stanno in una base
    piu' avanti nel percorso: in un giorno di trasferimento e' giusto lasciare
    la Fortezza di Rethymno per andare a Balos, non il contrario. A parita' di
    tier vince la base che si sta lasciando — e' l'ultima occasione di vederla."""
    best: tuple[tuple[int, int], dict[str, Any]] | None = None
    for rank, key in enumerate(sources):
        for place in pools.get(key, []):
            is_must = place.get("tier") == places_mod.MUST
            if only_must and not is_must:
                continue
            if place["hours"] > max_hours or not _place_fits_slot(place, slot):
                continue
            score = (0 if is_must else 1, rank)
            if best is None or score < best[0]:
                best = (score, place)
    return best[1] if best else None


def build_curated_itinerary(
    row: Any,
    style: str = STYLE_STANDARD,
    days: int | None = None,
    months: list[int] | None = None,
    entry: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Itinerario con luoghi reali. `None` se la meta non ha contenuto curato:
    chi chiama deve ricadere su `build_standard_itinerary`.

    `entry` permette di passare basi e luoghi gia' pronti invece di prenderli
    da places.py: e' cosi' che i viaggi combinati riusano questo motore,
    trattando ogni tappa come una base (vedi `build_trip_itinerary`)."""
    if entry is None:
        entry = places_mod.curated_entry(row.get("id"))
    if not entry:
        return None

    style = style if style in STYLE_PROFILES else STYLE_STANDARD
    profile = STYLE_PROFILES[style]

    variants = entry.get("variants", [])
    if days is None:
        variant = variants[0] if variants else None
        n_days = variant["days"] if variant else standard_itinerary_days(row)
    else:
        n_days = days
        variant = next((v for v in variants if v["days"] == days), None)

    light = daylight_hours(row.get("country", ""), months)
    daylight_is_binding = light - profile["pause_hours"] < profile["max_day_hours"]
    day_budget = min(profile["max_day_hours"], max(4.5, light - profile["pause_hours"]))

    bases = entry["bases"]
    by_key = {b["key"]: b for b in bases}
    seq = _allocate_nights(bases, n_days)
    if not seq:
        return None
    gateway = next((b for b in bases if b.get("night_weight", 0) == 0), None)

    # Un luogo si usa una volta sola: hanno un nome proprio, ripeterli sarebbe
    # assurdo. Ordine: prima i `must`, poi gli `extra`, entrambi nell'ordine
    # curato (sort stabile).
    pools: dict[str, list[dict[str, Any]]] = {}
    for place in places_mod.in_season(entry["places"], months):
        pools.setdefault(place["base"], []).append(place)
    for key in pools:
        pools[key].sort(key=lambda p: 0 if p.get("tier") == places_mod.MUST else 1)

    # Rete di sicurezza: finiti i luoghi curati, meglio un blocco generico
    # onesto che una giornata vuota.
    _, fillers = _activity_pool(row, style, months)
    filler_usage: dict[str, int] = {}

    days_out: list[dict[str, Any]] = []
    prev_key = gateway["key"] if gateway else seq[0]

    for day_index, base_key in enumerate(seq):
        base = by_key[base_key]
        moved = base_key != prev_key
        slots: dict[str, dict[str, Any] | None] = {
            SLOT_MORNING: None, SLOT_AFTERNOON: None, SLOT_EVENING: None,
        }
        spent = base.get("transfer_h", 0.0) if moved else 0.0
        labels: list[tuple[bool, str]] = []

        def take(place: dict[str, Any], slot: str) -> None:
            nonlocal spent
            spans = slot != SLOT_EVENING and place["hours"] >= 4.0
            item = {
                "text": place["name"],
                "how": place.get("how"),
                "note": place.get("note"),
                "hours": place["hours"],
                "anchor": place.get("tier") == places_mod.MUST,
                "half_day": spans,
                "curated": True,
                "base": by_key[place["base"]]["name"],
            }
            if spans:
                slots[SLOT_MORNING] = item
                slots[SLOT_AFTERNOON] = {**item, "continued": True}
            else:
                slots[slot] = item
            pools[place["base"]].remove(place)
            if slot != SLOT_EVENING:
                spent += place["hours"]
            labels.append((item["anchor"], place.get("label") or place["name"]))

        def take_filler(slot: str, max_hours: float) -> None:
            nonlocal spent
            filler = _pick_filler(fillers, slot, max_hours, filler_usage)
            if not filler:
                return
            slots[slot] = {
                "text": filler["text"], "how": None, "note": None,
                "hours": filler["hours"], "anchor": False,
                "half_day": False, "curated": False, "base": base["name"],
            }
            filler_usage[filler["text"]] = filler_usage.get(filler["text"], 0) + 1
            if slot != SLOT_EVENING:
                spent += filler["hours"]

        # Di giorno si puo' ancora attingere alla base che si lascia; la sera
        # si e' gia' arrivati, quindi solo alla base dove si dorme.
        day_sources = [prev_key, base_key] if moved else [base_key]

        # 1. Mattina — qui finisce il pezzo forte della giornata.
        #
        # I `must` si piazzano anche se sfondano il tetto orario, come le
        # ancore del motore generico: sono le cose per cui si viene qui. In
        # stile relax il tetto e' 5.5h ed Elafonissi ne vale 6 — rispettare il
        # tetto significherebbe proporre Creta senza la spiaggia rosa, che non
        # e' un ritmo piu' lento, e' un'altra vacanza.
        pick = _pick_place(pools, day_sources, SLOT_MORNING, float("inf"), only_must=True)
        if pick is None:
            pick = _pick_place(pools, day_sources, SLOT_MORNING, day_budget - spent)
        if pick:
            take(pick, SLOT_MORNING)
        elif day_budget - spent >= 1.5:
            take_filler(SLOT_MORNING, day_budget - spent)

        # 2. Pomeriggio, se la mattina non ha gia' occupato mezza giornata.
        if slots[SLOT_AFTERNOON] is None:
            used_main = sum(1 for s in (SLOT_MORNING, SLOT_AFTERNOON) if slots[s] is not None)
            remaining = day_budget - spent
            if used_main < profile["max_activities"] and remaining >= 1.5:
                cap = min(remaining, 3.9)
                pick = _pick_place(pools, day_sources, SLOT_AFTERNOON, cap)
                if pick:
                    take(pick, SLOT_AFTERNOON)
                else:
                    take_filler(SLOT_AFTERNOON, cap)

        # 3. Sera — non consuma ore di luce.
        if slots[SLOT_EVENING] is None:
            pick = _pick_place(pools, [base_key], SLOT_EVENING, 99.0)
            if pick:
                take(pick, SLOT_EVENING)
            else:
                take_filler(SLOT_EVENING, 99.0)

        # Titolo della giornata: i luoghi che la definiscono. I `must` per
        # primi; se la giornata non ne ha, valgono gli altri.
        named = [text for is_must, text in labels if is_must] or [t for _, t in labels]
        seen: list[str] = []
        for text in named:
            if text not in seen:
                seen.append(text)
        title = " & ".join(seen[:2]) if seen else base["name"]

        n_main = sum(
            1 for s in (SLOT_MORNING, SLOT_AFTERNOON)
            if slots[s] is not None and not slots[s].get("continued")
        )
        days_out.append({
            "day": day_index + 1,
            "title": title,
            "slots": slots,
            "sleep_base": base["name"],
            "moved_from": by_key[prev_key]["name"] if moved else None,
            "active_hours": round(spent, 1),
            "n_activities": n_main,
        })
        prev_key = base_key

    nights = [
        {"base": by_key[k]["name"], "nights": seq.count(k)}
        for k in dict.fromkeys(seq)
    ]

    # Su una meta a base unica "Notte a Roma centro" ripetuto per cinque
    # giorni non e' informazione, e' rumore: la base si dice una volta sola
    # nel riepilogo. La riga per giornata serve solo quando ci si sposta.
    if len(nights) < 2:
        for day in days_out:
            day["sleep_base"] = None
            day["moved_from"] = None

    return {
        "days": days_out,
        "n_days": n_days,
        "curated": True,
        "variant": variant,
        "bases": nights,
        "gateway": gateway["name"] if gateway else None,
        "excluded": places_mod.out_of_season(entry["places"], months),
        "style": style,
        "style_label": profile["label"],
        "style_note": profile["note"],
        "daylight_hours": round(light, 1),
        "day_budget_hours": round(day_budget, 1),
        "daylight_is_binding": daylight_is_binding,
        "transfer_hours": mobility_profile(row)["transfer_h"],
        "mobility": mobility_profile(row),
    }


def curated_variants(row: Any) -> list[dict[str, Any]]:
    """Le durate disponibili per la meta, vuote se non e' curata."""
    entry = places_mod.curated_entry(row.get("id"))
    return list(entry.get("variants", [])) if entry else []


# ---------------------------------------------------------------------------
# Itinerari dei viaggi combinati
#
# Un viaggio combinato e' gia' una sequenza di tappe con dei trasferimenti in
# mezzo: e' esattamente la struttura che il motore curato usa per le basi. Qui
# le tappe diventano basi, i luoghi curati di ogni meta finiscono nel pool di
# quella tappa, e i tempi di trasferimento arrivano dagli archi calcolati dal
# Trip Builder invece che da una stima.
# ---------------------------------------------------------------------------

def trip_curated_entry(trip: Any, dest_df: Any) -> dict[str, Any] | None:
    """Costruisce basi e luoghi di un viaggio combinato dalle sue tappe.

    `None` se anche una sola tappa non ha contenuto curato: un itinerario in
    cui la seconda meta e' fatta di blocchi generici sarebbe peggio che non
    proporlo affatto."""
    stop_ids = list(trip.get("stop_ids") or [])
    stop_names = list(trip.get("stop_names") or [])
    if len(stop_ids) < 2:
        return None

    edges = list(trip.get("edges") or [])
    bases: list[dict[str, Any]] = []
    places: list[dict[str, Any]] = []

    for index, dest_id in enumerate(stop_ids):
        entry = places_mod.curated_entry(dest_id)
        if not entry:
            return None

        match = dest_df[dest_df["id"] == dest_id]
        if match.empty:
            return None
        dest = match.iloc[0]

        key = f"stop{index}"
        bases.append({
            "key": key,
            "name": stop_names[index] if index < len(stop_names) else str(dest["name"]),
            # Il peso e' la durata minima consigliata della meta: e' il dato che
            # dice quanto quella tappa "merita" del viaggio, e evita di dare tre
            # notti a una citta' che si vede in due.
            "night_weight": max(1, int(dest["days_min"])),
            "max_nights": max(1, int(dest["days_max"])),
            # Il tempo di trasferimento e' quello reale calcolato dal Trip
            # Builder per l'arco che porta a questa tappa.
            "transfer_h": float(edges[index - 1]["travel_time"]) if index and index <= len(edges) else 0.0,
            "note": None,
        })

        # Dentro una tappa non si cambia base: le basi interne della meta
        # (per Creta sarebbero Rethymno e Chania) collassano in una sola.
        for place in entry["places"]:
            places.append({**place, "base": key})

    minimum = int(trip.get("minimum_days") or len(stop_ids) * 2)
    ideal = int(trip.get("ideal_days") or minimum + 2)
    variants = [{
        "days": minimum,
        "title": "Il minimo per farlo bene",
        "for_who": "Ogni tappa vista senza correre, saltando quello che si può saltare.",
    }]
    if ideal > minimum:
        variants.append({
            "days": ideal,
            "title": "Durata ideale",
            "for_who": "Il tempo per cui questo itinerario è pensato, senza giornate di solo trasferimento.",
        })

    return {"bases": bases, "places": places, "variants": variants}


def build_trip_itinerary(
    trip: Any,
    dest_df: Any,
    style: str = STYLE_STANDARD,
    days: int | None = None,
    months: list[int] | None = None,
) -> dict[str, Any] | None:
    """Itinerario giorno per giorno di un viaggio combinato."""
    entry = trip_curated_entry(trip, dest_df)
    if not entry:
        return None

    stop_ids = list(trip["stop_ids"])
    first = dest_df[dest_df["id"] == stop_ids[0]].iloc[0]
    # Un `row` sintetico: serve al motore per le ore di luce (latitudine della
    # prima tappa) e per i blocchi generici di riempimento, che qui pescano
    # dai tag di tutte le tappe messe insieme.
    tags: list[str] = []
    for dest_id in stop_ids:
        for tag in dest_df[dest_df["id"] == dest_id].iloc[0]["tags"]:
            if tag not in tags:
                tags.append(tag)

    row = {
        "id": trip.get("trip_id"),
        "name": trip.get("name"),
        "country": first["country"],
        "tags": tags,
        "days_min": int(trip.get("minimum_days") or 4),
        "days_max": int(trip.get("ideal_days") or 8),
        "relax_score": 50,
        "flight_hours": float(first["flight_hours"]),
        "wow_experiences": [],
    }
    return build_curated_itinerary(row, style=style, days=days, months=months, entry=entry)


def trip_itinerary_variants(trip: Any, dest_df: Any) -> list[dict[str, Any]]:
    entry = trip_curated_entry(trip, dest_df)
    return list(entry["variants"]) if entry else []


# ---------------------------------------------------------------------------
# Prenotazioni e affollamento
# ---------------------------------------------------------------------------

_BOOKING_KEYWORDS = ("prenota", "biglietti", "anticipo", "in anticipo", "noleggia")

# Esperienze che, per come sono fatte, richiedono quasi sempre di prenotare.
_NEEDS_BOOKING = {
    "mongolfiera": "il volo in mongolfiera si esaurisce con giorni di anticipo",
    "aurora": "i tour per l'aurora vanno prenotati, soprattutto nei weekend",
    "safari": "il safari va organizzato prima di partire",
    "museo": "i musei principali hanno ingressi a orario: comprali online",
    "galleria": "le gallerie più note vanno prenotate con orario prefissato",
    "colosseo": "l'ingresso va prenotato online con fascia oraria",
    "cupola": "la salita ha accessi contingentati: meglio prenotare",
    "rovine": "nei siti archeologici più noti conviene il biglietto online",
    "laguna blu": "gli ingressi sono a slot orari e si esauriscono",
}


def booking_notes(row: Any, months: list[int] | None = None, high_season: bool = False) -> list[str]:
    """Cosa conviene prenotare e quanto tempo aggiungere per le code.

    Le indicazioni concrete vengono dai `practical_tips` curati nel dataset;
    il resto e' derivato dal tipo di esperienza e dalla stagione. I tempi di
    attesa sono dati come intervalli indicativi: non abbiamo (ne' inventiamo)
    i tempi di coda reali attrazione per attrazione."""
    notes: list[str] = []

    for tip in row.get("practical_tips", []):
        if any(k in tip.lower() for k in _BOOKING_KEYWORDS):
            notes.append(f"📌 {tip}")

    blob = " ".join(row.get("wow_experiences", [])).lower()
    for keyword, why in _NEEDS_BOOKING.items():
        if keyword in blob:
            notes.append(f"🎟️ {why.capitalize()}.")
            break

    if high_season:
        notes.append(
            "⏳ Periodo di punta: nelle ore centrali metti in conto 30-60 minuti di attesa "
            "sulle attrazioni più note, o spostale a prima mattina."
        )
    elif months:
        notes.append("🙂 Periodo tranquillo: le code non dovrebbero incidere sui tempi della giornata.")

    return notes


# ---------------------------------------------------------------------------
# Perche' questo itinerario funziona
# ---------------------------------------------------------------------------

def itinerary_rationale(row: Any, itinerary: dict[str, Any]) -> str:
    """1-2 frasi sulla logica editoriale: ritmo, densita', logistica."""
    n_days = itinerary["n_days"]
    budget = itinerary["day_budget_hours"]
    light = itinerary["daylight_hours"]
    mob = itinerary["mobility"]
    avg = sum(d["n_activities"] for d in itinerary["days"]) / max(1, len(itinerary["days"]))

    n_act = max(1, round(avg))
    attivita = "un'attività principale" if n_act == 1 else f"{n_act} attività principali"
    parts = [
        f"{n_days} giorni con {attivita} al giorno e un tetto di {budget:.0f} ore piene: "
        f"il resto è margine per spostamenti, pasti e imprevisti."
    ]

    # La luce diventa il vincolo dominante solo quando lo e' davvero.
    if light < 8:
        parts.append(
            f"In questo periodo qui ci sono circa {light:.0f} ore di luce: "
            f"le giornate sono tarate su quelle, non su un orario teorico."
        )
    if mob["kind"] in (MOB_CAR, MOB_TOUR):
        parts.append(
            f"Gli spostamenti pesano ({mob['transfer_h']*60:.0f} minuti medi tra una tappa e l'altra) "
            "e sono già scontati dal tempo di ogni giornata."
        )
    elif mob["kind"] == MOB_WALKABLE:
        parts.append("Le distanze brevi permettono di cambiare programma in corsa senza perdere la giornata.")

    return " ".join(parts[:3])


# ---------------------------------------------------------------------------
# Confronto pratico: "cosa farei in N giorni qui vs li'"
# ---------------------------------------------------------------------------

def compare_itineraries(
    rows: list[Any], days: int = 4, style: str = STYLE_STANDARD, months: list[int] | None = None,
) -> dict[str, Any]:
    """Itinerari della STESSA durata per piu' mete, per un confronto onesto.

    La durata e' forzata uguale per tutte (anche fuori dal loro range
    consigliato): e' esattamente il senso della domanda "cosa farei in 4
    giorni qui vs li'". Dove la durata non e' quella ideale per la meta, lo
    dichiariamo invece di far finta di niente."""
    out = []
    for row in rows:
        itinerary = build_standard_itinerary(row, style=style, days=days, months=months)
        days_min = int(row.get("days_min", days))
        days_max = int(row.get("days_max", days))
        if days < days_min:
            fit = f"⚠️ Corto per questa meta (consigliati {days_min}-{days_max} giorni)"
        elif days > days_max:
            fit = f"⚠️ Lungo per questa meta (bastano {days_min}-{days_max} giorni)"
        else:
            fit = f"✅ Durata adatta ({days_min}-{days_max} giorni consigliati)"

        # `slots` mappa slot -> singola attivita' (o None), non liste: iterare
        # i valori come fossero liste scorreva le chiavi del dizionario.
        highlights = [
            act["text"]
            for day in itinerary["days"]
            for act in day["slots"].values()
            if act is not None and act["anchor"] and not act.get("continued")
        ]
        out.append({
            "name": row["name"],
            "country": row.get("country", ""),
            "fit": fit,
            "itinerary": itinerary,
            "highlights": highlights[:3],
            "mobility": itinerary["mobility"]["label"],
            "day_budget": itinerary["day_budget_hours"],
        })
    return {"days": days, "style": style, "items": out}
