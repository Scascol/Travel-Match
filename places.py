"""
Luoghi curati per destinazione — il contenuto reale da cui `itinerary.py`
costruisce gli itinerari con nomi propri.

PERCHE' QUESTO MODULO ESISTE
----------------------------
`itinerary.py` si rifiuta (giustamente) di inventare toponimi: con le sole
`wow_experiences` del dataset — tre per meta — un itinerario di 5 giorni
esaurisce il contenuto reale al terzo giorno e prosegue con blocchi generici
("mezza giornata in spiaggia"). Il limite non e' il motore, e' il contenuto.

Qui il contenuto c'e': luoghi con nome, base logistica, durata, modalita' di
visita e stagionalita'. Il motore li assembla rispettando gli stessi vincoli
di sempre (ore di luce, stile, trasferimenti), quindi le varianti per durata
e per stile continuano a uscire da sole invece di essere scritte a mano.

COPERTURA
---------
Modulo pilota: per ora la sola Creta (id 36). Le mete non coperte usano il
motore generico di prima — `has_curated_places()` decide, e non c'e' nessun
degrado per le altre 78.

REGOLE PER AGGIUNGERE UNA META
------------------------------
- Solo luoghi verificabili: niente orari, prezzi o tempi di percorrenza
  puntuali, che invecchiano e non sappiamo tenere aggiornati.
- `how` e' la modalita', ed e' obbligatoria: come ci si arriva e in che modo
  si vive il posto ("in barca da Kissamos", "a piedi tra i vicoli",
  "nel tardo pomeriggio, per il tramonto"). E' cio' che distingue un
  itinerario utile da un elenco di nomi.
- `months` solo quando la stagionalita' e' un vincolo vero (le Gole di
  Samaria sono chiuse in inverno), non per dire "si sta meglio a maggio".
"""

from __future__ import annotations

from typing import Any

# Slot: riusa le costanti di itinerary.py senza importarle (evita import
# circolare: itinerary importa questo modulo, non il contrario).
_MORNING = "mattina"
_AFTERNOON = "pomeriggio"
_EVENING = "sera"

# Tier: "must" = i luoghi per cui si viene, uno per giornata dove possibile.
# "extra" = riempie le giornate in piu' senza scadere nel generico.
MUST = "must"
EXTRA = "extra"


CURATED: dict[int, dict[str, Any]] = {
    # =====================================================================
    # 36 — CRETA
    # Tre basi da est a ovest, nell'ordine in cui si percorre l'isola
    # atterrando a Heraklion. Il nord-ovest concentra quasi tutto quello
    # per cui si viene, quindi e' li' che stanno le notti.
    # =====================================================================
    36: {
        "bases": [
            {
                "key": "heraklion",
                "name": "Heraklion",
                "night_weight": 0,   # porta d'ingresso: si atterra e si prosegue
                "max_nights": 0,
                "transfer_h": 0.0,
                "note": "Aeroporto principale dell'isola e sito minoico: si visita il giorno dell'arrivo.",
            },
            {
                "key": "rethymno",
                "name": "Rethymno",
                "night_weight": 1,
                "max_nights": 1,
                "transfer_h": 1.2,
                "note": "Tappa intermedia sulla strada verso ovest: una notte basta per il borgo.",
            },
            {
                "key": "chania",
                "name": "Chania",
                "night_weight": 2,
                "max_nights": 6,
                "transfer_h": 1.0,
                "note": "Base per tutto il nord-ovest: da qui partono Balos, Elafonissi, Samaria e Akrotiri.",
            },
        ],
        "places": [
            # --- Heraklion ------------------------------------------------
            {
                "name": "Palazzo di Cnosso",
                "label": "Heraklion",
                "base": "heraklion",
                "hours": 3.0,
                "slot": _MORNING,
                "how": "visita guidata al sito minoico, appena apre per evitare il caldo e i gruppi",
                "tier": MUST,
            },
            {
                "name": "Museo Archeologico di Heraklion",
                "label": "Heraklion",
                "base": "heraklion",
                "hours": 2.0,
                "slot": _AFTERNOON,
                "how": "a piedi nel centro: custodisce i reperti originali di Cnosso, si visita dopo il sito",
                "tier": MUST,
            },
            # --- Rethymno -------------------------------------------------
            {
                "name": "Borgo veneziano di Rethymno",
                "label": "Rethymno",
                "base": "rethymno",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "esplorazione a piedi tra i vicoli e il porticciolo veneziano, con cena sul lungomare",
                "tier": MUST,
            },
            {
                "name": "Fortezza di Rethymno",
                "label": "Rethymno",
                "base": "rethymno",
                "hours": 2.0,
                "slot": _MORNING,
                "how": "a piedi dal centro, sulla collina sopra il porto: vista aperta sulla costa nord",
                "tier": EXTRA,
            },
            {
                "name": "Spiaggia di Georgioupoli",
                "base": "rethymno",
                "hours": 4.0,
                "slot": None,
                "how": "giornata lenta sulla spiaggia lunga, con la chiesetta di Agios Nikolaos in fondo al molo",
                "tier": EXTRA,
            },
            # --- Chania e nord-ovest --------------------------------------
            {
                "name": "Laguna di Balos",
                "base": "chania",
                "hours": 6.0,
                "slot": _MORNING,
                "how": "in barca da Kissamos — l'alternativa via terra è uno sterrato impegnativo "
                       "più discesa a piedi",
                "tier": MUST,
                "months": [5, 6, 7, 8, 9, 10],
                "note": "I collegamenti in barca da Kissamos funzionano solo nella stagione estiva.",
            },
            {
                "name": "Porto veneziano di Chania",
                "label": "Chania",
                "base": "chania",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "passeggiata a piedi fino al faro veneziano e cena in una taverna sul porto",
                "tier": MUST,
            },
            {
                "name": "Spiaggia di Elafonissi",
                "base": "chania",
                "hours": 6.0,
                "slot": _MORNING,
                "how": "giornata intera sulla sabbia rosa: circa un'ora e mezza di strada da Chania, "
                       "in auto o con il bus giornaliero",
                "tier": MUST,
            },
            {
                "name": "Gole di Samaria",
                "base": "chania",
                "hours": 8.0,
                "slot": _MORNING,
                "how": "16 km di discesa a piedi da Omalos ad Agia Roumeli, rientro in traghetto e bus: "
                       "richiede l'intera giornata e scarpe da trekking",
                "tier": EXTRA,
                "months": [5, 6, 7, 8, 9, 10],
                "note": "Il sentiero è percorribile solo da maggio a ottobre; fuori stagione è chiuso.",
            },
            {
                "name": "Spiaggia di Falassarna",
                "base": "chania",
                "hours": 3.0,
                "slot": _EVENING,
                "how": "nel tardo pomeriggio, per il tramonto sul mare aperto: è la costa esposta a ovest",
                "tier": EXTRA,
            },
            {
                "name": "Canyon di Seitan Limania",
                "base": "chania",
                "hours": 3.0,
                "slot": _AFTERNOON,
                "how": "nella penisola di Akrotiri, con discesa ripida a piedi fino alla cala incassata",
                "tier": EXTRA,
            },
            {
                "name": "Spiaggia di Marathi",
                "base": "chania",
                "hours": 3.5,
                "slot": _AFTERNOON,
                "how": "sempre ad Akrotiri ma attrezzata e riparata: l'alternativa comoda a Seitan Limania",
                "tier": EXTRA,
            },
            {
                "name": "Mercato e agora di Chania",
                "base": "chania",
                "hours": 1.5,
                "slot": _MORNING,
                "how": "a piedi tra i banchi dell'agora coperta, per erbe, formaggi e street food cretese",
                "tier": EXTRA,
            },
        ],
        "variants": [
            {
                "days": 3,
                "title": "Il meglio del Nord-Ovest",
                "for_who": "Ideale per chi visita l'isola per la prima volta e vuole vedere i luoghi cartolina.",
            },
            {
                "days": 5,
                "title": "Ovest completo e natura",
                "for_who": "Permette di aggiungere spiagge selvagge e una giornata di trekking o di relax.",
            },
        ],
    },

    # =====================================================================
    # 1 — ROMA
    # Base unica: tutto il centro è raggiungibile a piedi o con due fermate
    # di metro. Qui il vincolo non è la distanza, sono le code.
    # =====================================================================
    1: {
        "bases": [
            {
                "key": "roma",
                "name": "Roma centro",
                "night_weight": 1,
                "max_nights": 10,
                "transfer_h": 0.0,
                "note": "Un'unica base: il centro storico si gira a piedi, il resto con due fermate di metro.",
            },
        ],
        "places": [
            {
                "name": "Colosseo e Foro Romano",
                "base": "roma",
                "hours": 3.5,
                "slot": _MORNING,
                "how": "biglietto unico con Palatino e Foro, da prendere online con orario di ingresso: "
                       "senza prenotazione la fila è la più lunga della città",
                "tier": MUST,
            },
            {
                "name": "Musei Vaticani e Cappella Sistina",
                "base": "roma",
                "hours": 3.5,
                "slot": _MORNING,
                "how": "ingresso a orario prenotato, dal lato nord delle mura vaticane e non da San Pietro; "
                       "il percorso è lungo, si esce dopo circa tre ore di cammino",
                "tier": MUST,
            },
            {
                "name": "Basilica di San Pietro e cupola",
                "base": "roma",
                "hours": 2.5,
                "slot": _MORNING,
                "how": "salita alla cupola con ascensore fino al primo livello e poi a piedi, "
                       "oppure tutti i gradini: la scala finale è stretta e in pendenza",
                "tier": MUST,
            },
            {
                "name": "Pantheon, Fontana di Trevi e Piazza Navona",
                "label": "Centro storico",
                "base": "roma",
                "hours": 2.5,
                "slot": None,
                "how": "un unico giro a piedi: sono a dieci minuti l'una dall'altra, "
                       "presto la mattina o dopo cena si vedono senza la calca",
                "tier": MUST,
            },
            {
                "name": "Trastevere",
                "base": "roma",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "cena e passeggiata a piedi nei vicoli attorno a Santa Maria in Trastevere, "
                       "il quartiere più vivo del centro dopo il tramonto",
                "tier": MUST,
            },
            {
                "name": "Galleria Borghese",
                "base": "roma",
                "hours": 2.0,
                "slot": None,
                "how": "prenotazione obbligatoria a fasce orarie contingentate, poi passeggiata "
                       "nel parco di Villa Borghese",
                "tier": EXTRA,
            },
            {
                "name": "Mercato di Testaccio",
                "base": "roma",
                "hours": 1.5,
                "slot": _MORNING,
                "how": "a piedi tra i banchi del mercato coperto, per il pranzo romano di strada "
                       "(trapizzino, supplì) invece del ristorante",
                "tier": EXTRA,
            },
            {
                "name": "Quartiere ebraico e Portico d'Ottavia",
                "base": "roma",
                "hours": 2.0,
                "slot": None,
                "how": "a piedi dal Teatro Marcello, tra i forni storici e le botteghe: "
                       "è il pezzo di centro rimasto più vissuto e meno da cartolina",
                "tier": EXTRA,
            },
            {
                "name": "Appia Antica",
                "base": "roma",
                "hours": 4.0,
                "slot": _MORNING,
                "how": "in bici lungo il basolato romano originale, noleggiando all'ingresso del parco; "
                       "le catacombe si visitano solo con guida",
                "tier": EXTRA,
            },
            {
                "name": "Castel Sant'Angelo",
                "base": "roma",
                "hours": 2.0,
                "slot": None,
                "how": "salita a spirale fino alla terrazza, con la vista che allinea "
                       "il ponte degli angeli e la cupola di San Pietro",
                "tier": EXTRA,
            },
            {
                "name": "Tramonto dal Gianicolo",
                "base": "roma",
                "hours": 1.5,
                "slot": _EVENING,
                "how": "salita a piedi da Trastevere nell'ora prima del tramonto, "
                       "per la vista d'insieme sui tetti e le cupole",
                "tier": EXTRA,
            },
            {
                "name": "Terme di Caracalla",
                "base": "roma",
                "hours": 2.0,
                "slot": None,
                "how": "a piedi dal Circo Massimo, tra volte alte trenta metri: "
                       "molto meno affollate dei Fori a parità di scala",
                "tier": EXTRA,
            },
        ],
        "variants": [
            {
                "days": 3,
                "title": "Roma classica",
                "for_who": "Per chi ci va la prima volta e non vuole rinunciare a niente di iconico.",
            },
            {
                "days": 5,
                "title": "Roma con calma",
                "for_who": "Aggiunge i quartieri, i mercati e l'Appia Antica: la città come la vive chi ci abita.",
            },
        ],
    },

    # =====================================================================
    # 4 — COSTIERA AMALFITANA
    # Due basi, e non è un dettaglio: la statale costiera è lenta e stretta,
    # e fare avanti e indietro da un solo albergo brucia mezze giornate.
    # =====================================================================
    4: {
        "bases": [
            {
                "key": "positano",
                "name": "Positano",
                "night_weight": 1,
                "max_nights": 2,
                "transfer_h": 0.0,
                "note": "Base occidentale: da qui partono il Sentiero degli Dei e i traghetti per Capri.",
            },
            {
                "key": "amalfi",
                "name": "Amalfi",
                "night_weight": 2,
                "max_nights": 5,
                "transfer_h": 1.0,
                "note": "Base centrale: Ravello, Atrani e la Valle delle Ferriere sono tutte a pochi minuti.",
            },
        ],
        "places": [
            {
                "name": "Positano",
                "base": "positano",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "discesa a piedi lungo le scalinate fino alla Spiaggia Grande: "
                       "in auto non si parcheggia, conviene arrivare in bus o in traghetto",
                "tier": MUST,
            },
            {
                "name": "Sentiero degli Dei",
                "base": "positano",
                "hours": 5.0,
                "slot": _MORNING,
                "how": "da Bomerano (Agerola) a Nocelle, circa tre ore di cammino di livello intermedio: "
                       "si sale in bus e si scende a piedi fino a Positano",
                "tier": MUST,
            },
            {
                "name": "Spiaggia di Fornillo",
                "base": "positano",
                "hours": 3.5,
                "slot": _AFTERNOON,
                "how": "a piedi da Positano lungo il sentiero a picco sul mare, dieci minuti: "
                       "più piccola e molto più tranquilla della Spiaggia Grande",
                "tier": EXTRA,
            },
            {
                "name": "Capri in giornata",
                "base": "positano",
                "hours": 6.0,
                "slot": _MORNING,
                "how": "in traghetto da Positano, andata e ritorno in giornata",
                "tier": EXTRA,
                "months": [4, 5, 6, 7, 8, 9, 10],
                "note": "I collegamenti veloci via mare funzionano solo nella stagione turistica.",
            },
            {
                "name": "Duomo di Amalfi",
                "label": "Amalfi",
                "base": "amalfi",
                "hours": 2.0,
                "slot": None,
                "how": "a piedi dalla piazza, salendo la scalinata monumentale; "
                       "dentro si visita anche il Chiostro del Paradiso",
                "tier": MUST,
            },
            {
                "name": "Villa Cimbrone a Ravello",
                "label": "Ravello",
                "base": "amalfi",
                "hours": 3.0,
                "slot": None,
                "how": "si sale a Ravello in bus o in auto da Amalfi, poi a piedi nel borgo "
                       "fino alla Terrazza dell'Infinito affacciata sul golfo",
                "tier": MUST,
            },
            {
                "name": "Villa Rufolo",
                "base": "amalfi",
                "hours": 1.5,
                "slot": None,
                "how": "nel centro di Ravello, a due passi dal Duomo: giardini a terrazza "
                       "che d'estate diventano il palco dei concerti all'aperto",
                "tier": EXTRA,
            },
            {
                "name": "Valle delle Ferriere",
                "base": "amalfi",
                "hours": 4.0,
                "slot": _MORNING,
                "how": "si parte a piedi dal centro di Amalfi e si sale nella riserva naturale, "
                       "tra cascate e felci giganti: fresca anche in piena estate",
                "tier": EXTRA,
            },
            {
                "name": "Atrani",
                "base": "amalfi",
                "hours": 1.5,
                "slot": None,
                "how": "dieci minuti a piedi da Amalfi lungo la costa: il borgo più piccolo "
                       "della costiera, e l'unico rimasto senza folla",
                "tier": EXTRA,
            },
            {
                "name": "Grotta dello Smeraldo",
                "base": "amalfi",
                "hours": 1.5,
                "slot": None,
                "how": "in barca da Amalfi, oppure in ascensore direttamente dalla strada costiera",
                "tier": EXTRA,
                "months": [4, 5, 6, 7, 8, 9, 10],
                "note": "L'accesso via mare dipende dalle condizioni: fuori stagione è spesso sospeso.",
            },
            {
                "name": "Cetara",
                "base": "amalfi",
                "hours": 2.0,
                "slot": _EVENING,
                "how": "cena nel borgo di pescatori all'estremità orientale della costiera, "
                       "dove si mangia la colatura di alici alla fonte",
                "tier": EXTRA,
            },
        ],
        "variants": [
            {
                "days": 4,
                "title": "I tre borghi simbolo",
                "for_who": "Positano, Amalfi e Ravello senza corse: il minimo per non vedere la costiera dal finestrino.",
            },
            {
                "days": 6,
                "title": "Costiera a piedi e in barca",
                "for_who": "Aggiunge il Sentiero degli Dei, le cale e una giornata a Capri.",
            },
        ],
    },

    # =====================================================================
    # 27 — REYKJAVIK
    # Base unica, ma giornate lunghissime: qui quasi tutto è un'escursione
    # in giornata dalla città, e la stagione decide cosa è possibile.
    # =====================================================================
    27: {
        "bases": [
            {
                "key": "reykjavik",
                "name": "Reykjavík",
                "night_weight": 1,
                "max_nights": 10,
                "transfer_h": 0.0,
                "note": "Si dorme sempre in città: le escursioni partono e tornano tutte da qui.",
            },
        ],
        "places": [
            {
                "name": "Circolo d'Oro",
                "base": "reykjavik",
                "hours": 8.0,
                "slot": _MORNING,
                "how": "giornata intera in auto o con tour: la faglia di Þingvellir, l'area geotermale "
                       "di Geysir e la cascata di Gullfoss, tutte sullo stesso anello",
                "tier": MUST,
            },
            {
                "name": "Costa sud e spiaggia nera di Reynisfjara",
                "base": "reykjavik",
                "hours": 9.0,
                "slot": _MORNING,
                "how": "giornata intera lungo la strada 1 verso est: le cascate di Seljalandsfoss e "
                       "Skógafoss, poi la sabbia nera e le colonne di basalto vicino a Vík",
                "tier": MUST,
            },
            {
                "name": "Blue Lagoon",
                "base": "reykjavik",
                "hours": 4.0,
                "slot": None,
                "how": "ingresso a orario prenotato con settimane di anticipo; è vicina all'aeroporto "
                       "di Keflavík, quindi conviene incastrarla nel giorno di arrivo o di partenza",
                "tier": MUST,
            },
            {
                "name": "Caccia all'aurora boreale",
                "base": "reykjavik",
                "hours": 3.5,
                "slot": _EVENING,
                "how": "uscita serale lontano dalle luci, in tour o in auto propria: dipende da "
                       "cielo sereno e attività solare, quindi va messa in conto più di una serata",
                "tier": MUST,
                "months": [9, 10, 11, 12, 1, 2, 3],
                "note": "Servono notti buie: tra maggio e agosto non fa mai abbastanza scuro.",
            },
            {
                "name": "Hallgrímskirkja e centro di Reykjavík",
                "label": "Reykjavík",
                "base": "reykjavik",
                "hours": 2.0,
                "slot": None,
                "how": "a piedi in centro, con salita in ascensore alla torre della chiesa "
                       "per la vista sui tetti colorati e sulla baia",
                "tier": EXTRA,
            },
            {
                "name": "Penisola di Snæfellsnes",
                "base": "reykjavik",
                "hours": 10.0,
                "slot": _MORNING,
                "how": "giornata intera verso nord-ovest, in auto: il monte Kirkjufell, le scogliere "
                       "e i villaggi di pescatori, con pochissimo traffico turistico",
                "tier": EXTRA,
            },
            {
                "name": "Grotta di ghiaccio nel ghiacciaio",
                "base": "reykjavik",
                "hours": 8.0,
                "slot": _MORNING,
                "how": "solo con guida, si entra nel ghiacciaio con mezzi attrezzati: "
                       "le grotte naturali cambiano forma ogni anno",
                "tier": EXTRA,
                "months": [11, 12, 1, 2, 3],
                "note": "Le grotte di ghiaccio naturali sono sicure solo nei mesi freddi: d'estate si sciolgono.",
            },
            {
                "name": "Avvistamento balene dal vecchio porto",
                "base": "reykjavik",
                "hours": 3.5,
                "slot": None,
                "how": "in barca dal porto di Reykjavík, vestiti a strati: in mare aperto "
                       "fa molto più freddo che in città",
                "tier": EXTRA,
                "months": [4, 5, 6, 7, 8, 9, 10],
                "note": "Fuori dalla stagione migratoria le uscite si diradano e gli avvistamenti crollano.",
            },
            {
                "name": "Fiume caldo di Reykjadalur",
                "base": "reykjavik",
                "hours": 5.0,
                "slot": _MORNING,
                "how": "circa un'ora di cammino in salita dal parcheggio, poi ci si immerge "
                       "nel fiume che scorre caldo: serve il costume sotto i vestiti, non ci sono spogliatoi",
                "tier": EXTRA,
            },
            {
                "name": "Piscine geotermali di quartiere",
                "base": "reykjavik",
                "hours": 2.0,
                "slot": _EVENING,
                "how": "a piedi o in autobus: sono le vasche calde dove va la gente del posto "
                       "la sera, a una frazione del prezzo della Blue Lagoon",
                "tier": EXTRA,
            },
        ],
        "variants": [
            {
                "days": 4,
                "title": "L'essenziale d'Islanda",
                "for_who": "Circolo d'Oro, costa sud e acque calde: i tre motivi per cui si viene qui.",
            },
            {
                "days": 6,
                "title": "Islanda oltre il Circolo d'Oro",
                "for_who": "Aggiunge Snæfellsnes e le esperienze che dipendono dalla stagione, dal ghiaccio alle balene.",
            },
        ],
    },

    # =====================================================================
    # 45 — ZANZIBAR
    # Stone Town per la storia, poi due coste diversissime: a nord si nuota
    # sempre, a sud-est la marea comanda la giornata.
    # =====================================================================
    45: {
        "bases": [
            {
                "key": "stonetown",
                "name": "Stone Town",
                "night_weight": 1,
                "max_nights": 2,
                "transfer_h": 0.0,
                "note": "Porta d'ingresso dell'isola: si arriva qui e si vede la parte storica prima del mare.",
            },
            {
                "key": "nungwi",
                "name": "Nungwi",
                "night_weight": 2,
                "max_nights": 4,
                "transfer_h": 1.5,
                "note": "Punta nord: l'unica costa dove la marea non svuota il mare e si nuota a ogni ora.",
            },
            {
                "key": "paje",
                "name": "Paje",
                "night_weight": 1.5,
                "max_nights": 4,
                "transfer_h": 2.0,
                "note": "Costa sud-est: maree ampie, vento costante e il regno dei kitesurf.",
            },
        ],
        "places": [
            {
                "name": "Stone Town",
                "base": "stonetown",
                "hours": 3.0,
                "slot": None,
                "how": "a piedi nel dedalo di vicoli della città vecchia patrimonio UNESCO, "
                       "tra le porte intagliate, la Casa delle Meraviglie e il mercato di Darajani",
                "tier": MUST,
            },
            {
                "name": "Giardini Forodhani",
                "base": "stonetown",
                "hours": 2.0,
                "slot": _EVENING,
                "how": "mercato serale di street food sul lungomare: si mangia in piedi, "
                       "arrivando poco prima del tramonto quando aprono i banchi",
                "tier": MUST,
            },
            {
                "name": "Spice tour",
                "base": "stonetown",
                "hours": 4.0,
                "slot": _MORNING,
                "how": "visita guidata a una piantagione nell'entroterra, poco fuori Stone Town: "
                       "si annusano e si assaggiano le spezie direttamente dalla pianta",
                "tier": MUST,
            },
            {
                "name": "Prison Island",
                "base": "stonetown",
                "hours": 3.5,
                "slot": None,
                "how": "in barca da Stone Town, mezz'ora di traversata: tartarughe giganti "
                       "e snorkeling sulla barriera vicino alla riva",
                "tier": EXTRA,
            },
            {
                "name": "Spiaggia di Nungwi",
                "base": "nungwi",
                "hours": 5.0,
                "slot": None,
                "how": "giornata sulla punta nord: è l'unico tratto dell'isola dove la marea "
                       "resta abbastanza alta da nuotare in qualsiasi momento",
                "tier": MUST,
            },
            {
                "name": "Snorkeling all'atollo di Mnemba",
                "base": "nungwi",
                "hours": 5.0,
                "slot": _MORNING,
                "how": "in barca dalla costa nord-est fino alla barriera dell'atollo, "
                       "partendo presto quando il mare è ancora piatto",
                "tier": MUST,
                "months": [6, 7, 8, 9, 10, 11, 12, 1, 2],
                "note": "Tra marzo e maggio le lunghe piogge rendono il mare mosso e le uscite inaffidabili.",
            },
            {
                "name": "Tramonto in dhow",
                "base": "nungwi",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "in barca a vela tradizionale, imbarco un'ora prima del tramonto: "
                       "la costa nord è l'unica esposta a ovest",
                "tier": EXTRA,
                "months": [6, 7, 8, 9, 10, 11, 12, 1, 2],
            },
            {
                "name": "Kendwa",
                "base": "nungwi",
                "hours": 3.5,
                "slot": None,
                "how": "pochi minuti a piedi lungo la costa da Nungwi: sabbia più larga "
                       "e acqua più calma, la spiaggia dove si sta tutto il giorno",
                "tier": EXTRA,
            },
            {
                "name": "Cena di pesce sulla spiaggia di Nungwi",
                "label": "Nungwi",
                "base": "nungwi",
                "hours": 2.5,
                "slot": _EVENING,
                "how": "nei ristoranti che aprono direttamente sulla sabbia: il pescato "
                       "si sceglie esposto sul ghiaccio prima di sedersi",
                "tier": EXTRA,
            },
            {
                "name": "Notte in un beach bar di Kendwa",
                "label": "Kendwa",
                "base": "nungwi",
                "hours": 3.0,
                "slot": _EVENING,
                "how": "è la zona dove si concentra la vita notturna dell'isola, "
                       "a piedi lungo la spiaggia dai resort di Nungwi",
                "tier": EXTRA,
            },
            {
                "name": "Cena vista laguna a Paje",
                "label": "Paje",
                "base": "paje",
                "hours": 2.0,
                "slot": _EVENING,
                "how": "sul fronte spiaggia, quando i kite rientrano e la marea risale: "
                       "cucina swahili, piatti a base di cocco e spezie dell'isola",
                "tier": EXTRA,
            },
            {
                "name": "Foresta di Jozani",
                "base": "paje",
                "hours": 3.0,
                "slot": _MORNING,
                "how": "sulla strada che scende a sud-est, si visita con guida su passerelle "
                       "di legno: è l'unico posto al mondo dove vive il colobo rosso di Zanzibar",
                "tier": MUST,
            },
            {
                "name": "Spiaggia di Paje",
                "base": "paje",
                "hours": 5.0,
                "slot": None,
                "how": "con la bassa marea il mare si ritira per centinaia di metri e si cammina "
                       "sul fondale; con l'alta arriva il vento ed è il momento dei kite",
                "tier": MUST,
            },
            {
                "name": "The Rock",
                "base": "paje",
                "hours": 2.0,
                "slot": None,
                "how": "il ristorante sullo scoglio davanti a Pingwe: si raggiunge a piedi "
                       "con la bassa marea e in barca con l'alta, va prenotato",
                "tier": EXTRA,
            },
            {
                "name": "Grotta di Kuza",
                "base": "paje",
                "hours": 2.5,
                "slot": _AFTERNOON,
                "how": "poco nell'entroterra da Paje: una cavità di corallo allagata da acqua "
                       "dolce trasparente, in cui si fa il bagno",
                "tier": EXTRA,
            },
            {"name": "Cattedrale anglicana e memoriale degli schiavi",
             "label": "Memoriale degli schiavi", "base": "stonetown", "hours": 2.0,
             "slot": None,
             "how": "costruita sul sito dell'ultimo mercato di schiavi dell'Africa orientale: "
                    "l'altare sorge dove stava il palo delle fustigazioni, e sotto "
                    "si visitano le celle di detenzione", "tier": MUST},
            {"name": "Casa delle Meraviglie e fronte mare", "label": "Casa delle Meraviglie",
             "base": "stonetown", "hours": 1.5, "slot": None,
             "how": "il palazzo ottocentesco del sultano sul lungomare, primo edificio "
                    "dell'isola ad avere elettricità e ascensore", "tier": EXTRA},
            {"name": "Cantiere dei dhow a Nungwi", "label": "Cantiere dei dhow",
             "base": "nungwi", "hours": 2.0, "slot": _MORNING,
             "how": "sulla spiaggia si costruiscono ancora le barche a mano, senza progetti "
                    "su carta: si guarda da vicino, e i maestri d'ascia lo permettono",
             "tier": EXTRA},
            {"name": "Acquario naturale di Nungwi", "label": "Tartarughe", "base": "nungwi",
             "hours": 1.5, "slot": None,
             "how": "una laguna di marea trasformata in centro di recupero: si nuota "
                    "con le tartarughe verdi salvate dalle reti", "tier": EXTRA},
            {"name": "Laguna blu di Michamvi", "label": "Michamvi", "base": "paje",
             "hours": 3.5, "slot": None,
             "how": "sulla punta della penisola a nord di Paje: è l'unico tratto "
                    "della costa est rivolto a ovest, quindi qui il sole tramonta sul mare",
             "tier": EXTRA},
        ],
        "variants": [
            {
                "days": 7,
                "title": "Storia e nord dell'isola",
                "for_who": "Stone Town, le spezie e la costa dove si nuota a qualsiasi ora di marea.",
            },
            {
                "days": 10,
                "title": "Zanzibar da nord a sud-est",
                "for_who": "Aggiunge la foresta di Jozani e la costa dei kite, con le sue maree spettacolari.",
            },
        ],
    },

    # =====================================================================
    # 2 — FIRENZE
    # =====================================================================
    2: {
        "bases": [
            {"key": "firenze", "name": "Firenze", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro compattissimo: dal Duomo all'Oltrarno sono quindici minuti a piedi."},
        ],
        "places": [
            {"name": "Galleria degli Uffizi", "base": "firenze", "hours": 3.0, "slot": _MORNING,
             "how": "biglietto a orario prefissato, preso online: senza prenotazione la coda "
                    "si porta via mezza mattinata", "tier": MUST},
            {"name": "Duomo e cupola del Brunelleschi", "label": "Duomo", "base": "firenze",
             "hours": 3.0, "slot": _MORNING,
             "how": "la salita alla cupola si prenota a orario ed è obbligatoria: 463 gradini "
                    "senza ascensore, in un passaggio stretto tra le due volte", "tier": MUST},
            {"name": "Ponte Vecchio e Oltrarno", "base": "firenze", "hours": 2.5, "slot": None,
             "how": "a piedi oltre il fiume, tra le botteghe artigiane di Santo Spirito "
                    "e San Frediano: la parte di città rimasta viva", "tier": MUST},
            {"name": "Tramonto da Piazzale Michelangelo", "base": "firenze", "hours": 1.5,
             "slot": _EVENING,
             "how": "si sale a piedi dalle rampe o in autobus, arrivando un'ora prima del "
                    "tramonto per prendere posto sulla balaustra", "tier": MUST},
            {"name": "Galleria dell'Accademia", "base": "firenze", "hours": 1.5, "slot": None,
             "how": "prenotazione a orario; la visita è breve perché di fatto si entra per il David",
             "tier": EXTRA},
            {"name": "Mercato Centrale e San Lorenzo", "base": "firenze", "hours": 2.0,
             "slot": _MORNING,
             "how": "a piedi tra i banchi storici al piano terra e le cucine al primo piano, "
                    "dove si pranza in piedi", "tier": EXTRA},
            {"name": "Palazzo Pitti e Giardino di Boboli", "base": "firenze", "hours": 3.0,
             "slot": None,
             "how": "biglietto unico museo più giardino: il Boboli è in salita e si gira "
                    "tutto a piedi, meglio non nelle ore centrali d'estate", "tier": EXTRA},
            {"name": "Cena in trattoria in Oltrarno", "label": "Oltrarno", "base": "firenze",
             "hours": 2.5, "slot": _EVENING,
             "how": "dieci minuti a piedi dal centro: è la zona dove si mangia bene "
                    "a prezzi ancora normali", "tier": EXTRA},
            {"name": "Basilica di Santa Croce", "base": "firenze", "hours": 1.5, "slot": None,
             "how": "a piedi dal centro: dentro ci sono le tombe di Michelangelo, Galileo e Machiavelli",
             "tier": EXTRA},
            {"name": "Fiesole", "base": "firenze", "hours": 3.5, "slot": None,
             "how": "venti minuti di autobus dal centro, per il teatro romano e la vista "
                    "sulla città dall'alto", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Firenze in un weekend",
             "for_who": "Il Rinascimento essenziale: Uffizi, cupola e Oltrarno, senza corse."},
            {"days": 4, "title": "Firenze e dintorni",
             "for_who": "Aggiunge Pitti, i mercati e una salita a Fiesole per vedere la città da fuori."},
        ],
    },

    # =====================================================================
    # 3 — VENEZIA
    # Si gira solo a piedi e in vaporetto: qui la logistica è il vaporetto,
    # e i luoghi migliori sono quelli fuori dall'asse Rialto-San Marco.
    # =====================================================================
    3: {
        "bases": [
            {"key": "venezia", "name": "Venezia", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Dormire in centro storico cambia il viaggio: la città al mattino presto "
                     "e dopo cena è un'altra cosa rispetto a quella delle gite in giornata."},
        ],
        "places": [
            {"name": "Basilica di San Marco e Palazzo Ducale", "label": "San Marco",
             "base": "venezia", "hours": 3.5, "slot": _MORNING,
             "how": "due ingressi separati, entrambi a orario prenotato: presto la mattina "
                    "la piazza è ancora quasi vuota", "tier": MUST},
            {"name": "Cannaregio e il Ghetto", "base": "venezia", "hours": 2.5, "slot": None,
             "how": "a piedi lontano dall'asse turistico: è il sestiere dove Venezia è "
                    "ancora abitata, con le fondamenta lungo i canali", "tier": MUST},
            {"name": "Rialto e il mercato del pesce", "label": "Rialto", "base": "venezia",
             "hours": 2.0, "slot": _MORNING,
             "how": "il mercato lavora presto e smonta verso mezzogiorno, ed è chiuso "
                    "la domenica e il lunedì: va incastrato in una mattina", "tier": MUST},
            {"name": "Canal Grande in vaporetto", "base": "venezia", "hours": 1.5,
             "slot": _EVENING,
             "how": "linea 1 da Piazzale Roma a San Marco, seduti a prua verso il tramonto: "
                    "costa come un biglietto ordinario, non come una gondola", "tier": MUST},
            {"name": "Murano e Burano", "base": "venezia", "hours": 5.0, "slot": _MORNING,
             "how": "in vaporetto dalle Fondamente Nove: servono entrambe mezza giornata piena, "
                    "Burano è a quaranta minuti di navigazione", "tier": EXTRA},
            {"name": "Gallerie dell'Accademia", "base": "venezia", "hours": 2.0, "slot": None,
             "how": "a piedi dal ponte omonimo: la pittura veneziana tutta in un posto solo",
             "tier": EXTRA},
            {"name": "Giro dei bacari", "base": "venezia", "hours": 2.5, "slot": _EVENING,
             "how": "in piedi da un bacaro all'altro tra Rialto e San Polo, cicchetti "
                    "e ombra di vino: è così che si cena a Venezia", "tier": EXTRA},
            {"name": "Basilica di Santa Maria della Salute", "base": "venezia", "hours": 1.5,
             "slot": None,
             "how": "in traghetto da San Marco o a piedi dall'Accademia, sulla punta "
                    "della Dogana affacciata sul bacino", "tier": EXTRA},
            {"name": "Squero di San Trovaso", "base": "venezia", "hours": 1.0, "slot": None,
             "how": "si guarda dall'altra riva del rio: è uno degli ultimi cantieri "
                    "dove si costruiscono e riparano le gondole", "tier": EXTRA},
            {"name": "Lido di Venezia", "base": "venezia", "hours": 4.0, "slot": None,
             "how": "in vaporetto dal centro: l'unica spiaggia raggiungibile dalla città",
             "tier": EXTRA, "months": [5, 6, 7, 8, 9]},
        ],
        "variants": [
            {"days": 2, "title": "Venezia essenziale",
             "for_who": "San Marco, Rialto e i bacari: due giorni bastano se si dorme in centro."},
            {"days": 4, "title": "Venezia e la laguna",
             "for_who": "Aggiunge Murano e Burano e i sestieri dove la città vive davvero."},
        ],
    },

    # =====================================================================
    # 5 — CINQUE TERRE
    # Base unica e treno: i paesi sono collegati in pochi minuti, e la
    # macchina è più un problema che una soluzione.
    # =====================================================================
    5: {
        "bases": [
            {"key": "monterosso", "name": "Monterosso", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Base unica sul treno di linea: tutti e cinque i paesi sono a pochi minuti, "
                     "e Monterosso è l'unico con una spiaggia vera."},
        ],
        "places": [
            {"name": "Sentiero Azzurro da Monterosso a Vernazza", "label": "Sentiero Azzurro",
             "base": "monterosso", "hours": 4.0, "slot": _MORNING,
             "how": "circa due ore di cammino con saliscendi esposti al sole: serve la "
                    "Cinque Terre Card e servono scarpe da trekking, non sandali", "tier": MUST},
            {"name": "Vernazza", "base": "monterosso", "hours": 2.5, "slot": None,
             "how": "il porticciolo e la salita al castello Doria; si arriva in treno "
                    "in pochi minuti da qualunque paese", "tier": MUST},
            {"name": "Tramonto a Manarola", "label": "Manarola", "base": "monterosso",
             "hours": 2.0, "slot": _EVENING,
             "how": "dal punto panoramico di Punta Bonfiglio, pochi minuti a piedi "
                    "dalla stazione: è l'inquadratura classica delle Cinque Terre", "tier": MUST},
            {"name": "Riomaggiore e Via dell'Amore", "base": "monterosso", "hours": 2.0,
             "slot": None,
             "how": "il tratto pianeggiante verso Manarola, mezz'ora di passeggiata a picco "
                    "sul mare, compreso nella Cinque Terre Card", "tier": MUST},
            {"name": "Corniglia", "base": "monterosso", "hours": 2.0, "slot": None,
             "how": "l'unico paese non sul mare: dalla stazione si salgono i 380 scalini "
                    "della Lardarina, oppure si prende la navetta", "tier": EXTRA},
            {"name": "Giro in barca lungo la costa", "base": "monterosso", "hours": 3.5,
             "slot": _AFTERNOON,
             "how": "dal mare i cinque paesi si vedono come sono nati, aggrappati alla roccia; "
                    "le partenze dipendono dallo stato del mare", "tier": EXTRA,
             "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Spiaggia di Monterosso", "base": "monterosso", "hours": 4.0, "slot": None,
             "how": "a piedi dal centro: è l'unica spiaggia di sabbia vera delle Cinque Terre, "
                    "in parte libera e in parte attrezzata", "tier": EXTRA},
            {"name": "Portovenere", "base": "monterosso", "hours": 4.0, "slot": None,
             "how": "in barca o in bus da La Spezia: fuori dal parco ma dentro lo stesso "
                    "patrimonio UNESCO, con la chiesa sullo sperone di roccia", "tier": EXTRA},
            {"name": "Cena di pesce a Monterosso", "base": "monterosso", "hours": 2.5,
             "slot": _EVENING,
             "how": "nel paese vecchio: acciughe di Monterosso, trofie al pesto "
                    "e vino delle terrazze sopra il paese", "tier": EXTRA},
            {"name": "Aperitivo al tramonto a Vernazza", "base": "monterosso", "hours": 2.0,
             "slot": _EVENING,
             "how": "sugli scogli del porticciolo, quando i turisti in giornata "
                    "hanno già ripreso il treno", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "I cinque paesi",
             "for_who": "Un sentiero, il treno e i borghi: il modo giusto di vederle senza correre."},
            {"days": 5, "title": "Cinque Terre dal mare e dai sentieri",
             "for_who": "Aggiunge la barca, Portovenere e il tempo per stare in spiaggia."},
        ],
    },

    # =====================================================================
    # 6 — PALERMO & SICILIA OCCIDENTALE
    # Due basi: la città e la costa ovest. Sono cose diversissime e sono
    # lontane, farle dallo stesso albergo significa passare la vacanza in auto.
    # =====================================================================
    6: {
        "bases": [
            {"key": "palermo", "name": "Palermo", "night_weight": 2, "max_nights": 4,
             "transfer_h": 0.0,
             "note": "La città: mercati, arabo-normanno e street food, tutto in centro a piedi."},
            {"key": "trapani", "name": "Trapani e San Vito", "night_weight": 1, "max_nights": 3,
             "transfer_h": 1.5,
             "note": "L'estremità occidentale: riserve costiere, saline e templi, tutto in auto."},
        ],
        "places": [
            {"name": "Palazzo dei Normanni e Cappella Palatina", "label": "Palermo",
             "base": "palermo", "hours": 3.0, "slot": _MORNING,
             "how": "a piedi lungo il Cassaro; la Cappella Palatina chiude al pubblico "
                    "quando c'è seduta dell'assemblea regionale, conviene verificare prima",
             "tier": MUST},
            {"name": "Mercato di Ballarò", "base": "palermo", "hours": 2.0, "slot": _MORNING,
             "how": "a piedi tra i banchi e i friggitori: qui si pranza in strada, "
                    "pane e panelle o sfincione, non al ristorante", "tier": MUST},
            {"name": "Duomo di Monreale", "base": "palermo", "hours": 3.0, "slot": None,
             "how": "venti minuti di salita in bus o auto fuori città: i mosaici bizantini "
                    "coprono seimila metri quadrati, il chiostro si paga a parte", "tier": MUST},
            {"name": "Teatro Massimo", "base": "palermo", "hours": 1.5, "slot": None,
             "how": "visita guidata negli intervalli delle prove: è il teatro d'opera "
                    "più grande d'Italia", "tier": EXTRA},
            {"name": "Mondello", "base": "palermo", "hours": 4.0, "slot": None,
             "how": "in autobus dal centro: la spiaggia dei palermitani, con le cabine "
                    "liberty in fondo al golfo", "tier": EXTRA},
            {"name": "Cena tra i banchi della Vucciria", "label": "Vucciria", "base": "palermo",
             "hours": 2.5, "slot": _EVENING,
             "how": "in piedi in piazza Caracciolo, dove la sera i banchi del mercato "
                    "diventano cucine di strada", "tier": EXTRA},
            {"name": "Riserva dello Zingaro", "base": "trapani", "hours": 5.0, "slot": _MORNING,
             "how": "sentiero costiero tra cale, si entra da Scopello o da San Vito: "
                    "non c'è ombra e non c'è acqua lungo il percorso, si parte presto", "tier": MUST},
            {"name": "Segesta", "base": "trapani", "hours": 2.5, "slot": None,
             "how": "il tempio dorico isolato tra le colline, con il teatro greco in cima "
                    "raggiungibile a piedi o con navetta", "tier": MUST},
            {"name": "Erice", "base": "trapani", "hours": 3.0, "slot": None,
             "how": "in funivia da Trapani: borgo medievale a 750 metri, spesso dentro "
                    "la nuvola anche quando sotto c'è il sole", "tier": EXTRA},
            {"name": "Saline di Trapani", "base": "trapani", "hours": 2.5, "slot": _EVENING,
             "how": "lungo la strada per Marsala, nell'ora prima del tramonto, "
                    "quando le vasche diventano rosa e i mulini si stagliano controluce",
             "tier": EXTRA},
            {"name": "San Vito Lo Capo", "base": "trapani", "hours": 4.0, "slot": None,
             "how": "sabbia bianca e fondale basso sotto il monte Monaco: è la spiaggia "
                    "più famosa della Sicilia occidentale, e si vede", "tier": EXTRA},
            {"name": "Cena di cous cous a San Vito", "base": "trapani", "hours": 2.5,
             "slot": _EVENING,
             "how": "il cous cous di pesce trapanese, che qui è piatto di casa "
                    "e non specialità turistica", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Palermo e Monreale",
             "for_who": "La città, i mercati e l'arabo-normanno, con un assaggio di costa."},
            {"days": 6, "title": "Da Palermo all'estremo ovest",
             "for_who": "Aggiunge lo Zingaro, Segesta e le saline: la Sicilia meno battuta."},
        ],
    },

    # =====================================================================
    # 7 — TAORMINA
    # =====================================================================
    7: {
        "bases": [
            {"key": "taormina", "name": "Taormina", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Base unica sul balcone naturale sopra il mare: l'Etna e la costa "
                     "ionica sono tutte escursioni in giornata."},
        ],
        "places": [
            {"name": "Teatro Antico di Taormina", "base": "taormina", "hours": 2.0,
             "slot": _MORNING,
             "how": "a piedi dal corso, appena apre: la cavea inquadra l'Etna e il mare, "
                    "e a metà mattina è già piena di gruppi", "tier": MUST},
            {"name": "Etna", "base": "taormina", "hours": 6.0, "slot": _MORNING,
             "how": "si sale in auto o bus al Rifugio Sapienza, poi funivia e fuoristrada; "
                    "per i crateri sommitali serve la guida alpina. In quota fa freddo "
                    "e c'è vento anche ad agosto", "tier": MUST},
            {"name": "Isola Bella", "base": "taormina", "hours": 3.0, "slot": None,
             "how": "si scende in funivia da Taormina; la spiaggia è di ciottoli e "
                    "l'istmo si attraversa a piedi solo quando la marea lo permette", "tier": MUST},
            {"name": "Corso Umberto la sera", "label": "Taormina", "base": "taormina",
             "hours": 2.0, "slot": _EVENING,
             "how": "la passeggiata da Porta Messina a Porta Catania quando i pullman "
                    "sono ripartiti e il corso torna ai residenti", "tier": MUST},
            {"name": "Gole dell'Alcantara", "base": "taormina", "hours": 3.0, "slot": None,
             "how": "si scende nel canyon di basalto con scale o ascensore: l'acqua "
                    "è gelida tutto l'anno, servono scarpe che si possano bagnare",
             "tier": EXTRA, "months": [4, 5, 6, 7, 8, 9, 10],
             "note": "Con le piogge il livello del fiume sale e l'accesso alle gole viene chiuso."},
            {"name": "Cantine dell'Etna", "base": "taormina", "hours": 3.5, "slot": None,
             "how": "degustazione sul versante nord, tra Randazzo e Linguaglossa: "
                    "le viti crescono su terrazze di lava nera", "tier": EXTRA},
            {"name": "Castelmola", "base": "taormina", "hours": 2.0, "slot": None,
             "how": "in bus o a piedi in salita sopra Taormina, per il vino alla mandorla "
                    "e la vista che prende tutto il golfo", "tier": EXTRA},
            {"name": "Siracusa e Ortigia in giornata", "base": "taormina", "hours": 6.0,
             "slot": _MORNING,
             "how": "circa un'ora e mezza di autostrada: l'isola di Ortigia si gira "
                    "tutta a piedi, il parco archeologico è dall'altra parte della città",
             "tier": EXTRA},
            {"name": "Giardini Naxos", "base": "taormina", "hours": 4.0, "slot": None,
             "how": "in bus o funivia giù dalla rupe: spiaggia più lunga e più economica "
                    "di quella di Taormina", "tier": EXTRA},
            {"name": "Cena vista mare a Taormina", "base": "taormina", "hours": 2.5,
             "slot": _EVENING,
             "how": "sulle terrazze affacciate sulla baia: pasta alla Norma, pesce spada "
                    "e cannoli riempiti al momento", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Taormina e l'Etna",
             "for_who": "Il teatro, il vulcano e il mare sotto la rupe: l'essenziale della costa ionica."},
            {"days": 6, "title": "Taormina, Etna e Sicilia orientale",
             "for_who": "Aggiunge le gole, le cantine sulla lava e una giornata a Siracusa."},
        ],
    },

    # =====================================================================
    # 8 — COSTA SMERALDA (SARDEGNA)
    # =====================================================================
    8: {
        "bases": [
            {"key": "portocervo", "name": "Porto Cervo", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "Il cuore della Costa Smeralda: le spiagge più famose sono tutte "
                     "entro venti minuti d'auto."},
            {"key": "palau", "name": "Palau", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.7,
             "note": "Più a nord e molto meno caro: da qui partono le barche per La Maddalena."},
        ],
        "places": [
            {"name": "Spiaggia del Principe", "base": "portocervo", "hours": 4.0, "slot": None,
             "how": "si lascia l'auto lungo la strada e si scende a piedi per un sentiero "
                    "tra il mirto: non ci sono servizi, si porta tutto", "tier": MUST},
            {"name": "Porto Cervo e la Piazzetta", "label": "Porto Cervo",
             "base": "portocervo", "hours": 2.0, "slot": _EVENING,
             "how": "passeggiata serale tra il porto vecchio e le vetrine: si guarda "
                    "più che comprare, ed è gratis", "tier": MUST},
            {"name": "Cala Capriccioli", "base": "portocervo", "hours": 4.0, "slot": None,
             "how": "due calette gemelle separate dalle rocce di granito, con vista "
                    "sull'arcipelago: fondale basso, buona anche con bambini", "tier": EXTRA},
            {"name": "Spiaggia di Liscia Ruja", "base": "portocervo", "hours": 4.0, "slot": None,
             "how": "la baia più ampia della costa, sabbia chiara e riparo dal maestrale: "
                    "l'alternativa quando il vento chiude le altre", "tier": EXTRA},
            {"name": "Cena di pesce a Cannigione", "base": "portocervo", "hours": 2.5,
             "slot": _EVENING,
             "how": "sul porticciolo fuori dal circuito di Porto Cervo, dove si mangia "
                    "lo stesso pesce a metà prezzo", "tier": EXTRA},
            {"name": "Arcipelago della Maddalena in barca", "label": "La Maddalena",
             "base": "palau", "hours": 6.0, "slot": _MORNING,
             "how": "in gommone o in barca condivisa dal porto di Palau, tra Spargi, "
                    "Santa Maria e le acque di Budelli, dove si naviga ma non si sbarca",
             "tier": MUST, "months": [5, 6, 7, 8, 9, 10],
             "note": "Le uscite in barca funzionano solo nella stagione estiva e saltano col maestrale."},
            {"name": "Capo d'Orso", "base": "palau", "hours": 2.0, "slot": None,
             "how": "breve salita a piedi sopra Palau fino alla roccia scolpita dal vento, "
                    "meglio nel tardo pomeriggio quando il granito diventa arancione", "tier": EXTRA},
            {"name": "Spiaggia di Baja Sardinia", "base": "palau", "hours": 3.5, "slot": None,
             "how": "insenatura attrezzata e riparata, con acqua bassa a lungo: "
                    "è la spiaggia comoda della zona", "tier": EXTRA},
            {"name": "Tramonto a Porto Rafael", "base": "palau", "hours": 2.0, "slot": _EVENING,
             "how": "borgo pedonale affacciato sull'arcipelago, si lascia l'auto fuori "
                    "e si scende a piedi alla piazzetta sul mare", "tier": EXTRA},
            {"name": "Tomba dei Giganti di Coddu Vecchiu", "label": "Nuraghi",
             "base": "palau", "hours": 2.0, "slot": None,
             "how": "nell'entroterra verso Arzachena: il monumento funerario nuragico "
                    "meglio conservato della Gallura", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Le spiagge della Costa Smeralda",
             "for_who": "Le cale di granito e una giornata in barca: il minimo per non stare sempre nello stesso posto."},
            {"days": 8, "title": "Gallura tra mare e granito",
             "for_who": "Aggiunge La Maddalena, i borghi a nord e l'entroterra nuragico."},
        ],
    },

    # =====================================================================
    # 9 — CORTINA D'AMPEZZO (DOLOMITI)
    # La stagione qui non cambia il ritmo, cambia proprio la meta: d'inverno
    # la strada delle Tre Cime è chiusa, d'estate gli impianti sono fermi.
    # =====================================================================
    9: {
        "bases": [
            {"key": "cortina", "name": "Cortina d'Ampezzo", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Conca circondata da pareti: quasi tutto è a mezz'ora d'auto, "
                     "ma d'inverno alcune strade di passo chiudono."},
        ],
        "places": [
            {"name": "Tre Cime di Lavaredo", "base": "cortina", "hours": 6.0, "slot": _MORNING,
             "how": "si sale con la strada a pedaggio fino al Rifugio Auronzo (circa 30 € "
                    "ad auto) oppure in bus da Cortina, poi il giro ad anello a piedi "
                    "in circa tre ore", "tier": MUST,
             "months": [6, 7, 8, 9, 10],
             "note": "La strada a pedaggio è chiusa dall'autunno alla primavera: fuori stagione "
                     "si sale solo a piedi o con le ciaspole."},
            {"name": "Lago di Braies", "base": "cortina", "hours": 4.0, "slot": _MORNING,
             "how": "un'ora d'auto in Val Pusteria; in alta stagione l'accesso in auto è "
                    "regolato e conviene la navetta. Il giro del lago a piedi è un'ora scarsa",
             "tier": MUST},
            {"name": "Rifugio Lagazuoi in funivia", "label": "Lagazuoi", "base": "cortina",
             "hours": 4.0, "slot": _MORNING,
             "how": "funivia dal Passo Falzarego fino a 2.750 metri, con le gallerie "
                    "della Grande Guerra scavate nella roccia e la terrazza sulle Dolomiti",
             "tier": MUST},
            {"name": "Giornata sulle piste", "label": "Sci", "base": "cortina", "hours": 6.0,
             "slot": _MORNING,
             "how": "impianti collegati al carosello Dolomiti Superski: skipass unico "
                    "e rientro a valle senza togliersi gli sci", "tier": MUST,
             "months": [12, 1, 2, 3, 4],
             "note": "Gli impianti da sci sono aperti solo nella stagione invernale."},
            {"name": "Corso Italia e il centro di Cortina", "label": "Cortina",
             "base": "cortina", "hours": 2.0, "slot": _EVENING,
             "how": "la passeggiata serale sotto il campanile, tra le botteghe storiche: "
                    "a Cortina è un rito, non un giro turistico", "tier": MUST},
            {"name": "Cinque Torri", "base": "cortina", "hours": 4.0, "slot": None,
             "how": "seggiovia e poi museo all'aperto della Grande Guerra tra le trincee "
                    "restaurate: il giro delle torri è facile e adatto a tutti", "tier": EXTRA,
             "months": [6, 7, 8, 9, 10]},
            {"name": "Lago di Sorapis", "base": "cortina", "hours": 6.0, "slot": _MORNING,
             "how": "sentiero 215 dal Passo Tre Croci, circa quattro ore andata e ritorno "
                    "con tratti esposti e cavi: il lago è azzurro latte per la roccia disciolta",
             "tier": EXTRA, "months": [6, 7, 8, 9, 10],
             "note": "Fuori dall'estate il sentiero è innevato ed espone a rischio valanghe."},
            {"name": "Cena in rifugio", "base": "cortina", "hours": 3.0, "slot": _EVENING,
             "how": "si sale in gatto delle nevi al tramonto e si scende a piedi o in slitta "
                    "dopo cena: canederli, casunziei e strudel", "tier": EXTRA,
             "months": [12, 1, 2, 3]},
            {"name": "Passo Giau", "base": "cortina", "hours": 2.5, "slot": _EVENING,
             "how": "venti minuti di tornanti da Cortina: è il punto da cui si fotografa "
                    "il Ra Gusela quando la roccia si accende di rosa al tramonto",
             "tier": EXTRA, "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Terme di Bagni di Bormio o spa in paese", "label": "Wellness",
             "base": "cortina", "hours": 3.0, "slot": _AFTERNOON,
             "how": "pomeriggio di saune e vasche calde all'aperto, con la neve o la roccia "
                    "intorno: il modo locale di chiudere una giornata in montagna", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Cuore delle Dolomiti",
             "for_who": "Le Tre Cime, Braies e una salita in quota: le immagini per cui si viene qui."},
            {"days": 6, "title": "Dolomiti con calma",
             "for_who": "Aggiunge i laghi alpini, la Grande Guerra e il tempo per le terrazze in quota."},
        ],
    },

    # =====================================================================
    # 10 — BOLZANO & MERCATINI DI NATALE
    # =====================================================================
    10: {
        "bases": [
            {"key": "bolzano", "name": "Bolzano", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città piccola e camminabile, con le funivie che partono dal centro "
                     "e salgono sugli altipiani in pochi minuti."},
        ],
        "places": [
            {"name": "Mercatino di Natale di Piazza Walther", "label": "Mercatini",
             "base": "bolzano", "hours": 2.5, "slot": _EVENING,
             "how": "a piedi in centro dopo il tramonto, quando si accendono le luci: "
                    "è il più antico d'Italia, si mangia in piedi tra le casette",
             "tier": MUST, "months": [11, 12, 1],
             "note": "I mercatini aprono a fine novembre e chiudono nei primi giorni di gennaio."},
            {"name": "Museo Archeologico e Ötzi", "label": "Ötzi", "base": "bolzano",
             "hours": 2.0, "slot": _MORNING,
             "how": "a piedi dal centro: la mummia del Similaun è conservata in una cella "
                    "refrigerata visibile da un oblò", "tier": MUST},
            {"name": "Altopiano del Renon in funivia", "label": "Renon", "base": "bolzano",
             "hours": 4.0, "slot": _MORNING,
             "how": "funivia dal centro di Bolzano in dodici minuti, poi il trenino "
                    "storico tra i masi e le piramidi di terra", "tier": MUST},
            {"name": "Portici e centro storico di Bolzano", "label": "Bolzano",
             "base": "bolzano", "hours": 2.0, "slot": None,
             "how": "a piedi sotto i portici medievali e nel mercato di Piazza Erbe, "
                    "dove si comprano speck e formaggi di malga", "tier": MUST},
            {"name": "Castel Roncolo", "base": "bolzano", "hours": 2.5, "slot": None,
             "how": "si raggiunge a piedi lungo il fiume o con la navetta gratuita: "
                    "conserva il più ampio ciclo di affreschi profani del Medioevo", "tier": EXTRA},
            {"name": "Lago di Carezza", "base": "bolzano", "hours": 3.0, "slot": None,
             "how": "mezz'ora d'auto verso il Catinaccio: piccolo, ma riflette le pareti "
                    "di dolomia; il giro attorno è una passeggiata di venti minuti", "tier": EXTRA},
            {"name": "Alpe di Siusi", "base": "bolzano", "hours": 5.0, "slot": _MORNING,
             "how": "funivia da Siusi allo Sciliar: l'altopiano più grande d'Europa, "
                    "d'inverno si gira con gli sci di fondo o le ciaspole", "tier": EXTRA},
            {"name": "Cena di canederli in una stube", "label": "Stube", "base": "bolzano",
             "hours": 2.5, "slot": _EVENING,
             "how": "nelle sale rivestite di legno del centro: canederli, gulasch "
                    "e vino della Val d'Adige", "tier": EXTRA},
            {"name": "Strada del vino altoatesina", "label": "Strada del vino",
             "base": "bolzano", "hours": 4.0, "slot": None,
             "how": "in auto o in bici tra Caldaro e Termeno, con soste in cantina: "
                    "è la zona del Gewürztraminer", "tier": EXTRA},
            {"name": "Passeggiata del Guncina", "base": "bolzano", "hours": 2.0, "slot": None,
             "how": "sentiero panoramico che parte dal centro e sale tra i cipressi: "
                    "un'ora di cammino con la conca sotto", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Bolzano e i mercatini",
             "for_who": "Un fine settimana d'inverno tra luci, portici e speck."},
            {"days": 4, "title": "Bolzano e gli altipiani",
             "for_who": "Aggiunge il Renon, l'Alpe di Siusi e la strada del vino."},
        ],
    },

    # =====================================================================
    # 11 — MILANO
    # =====================================================================
    11: {
        "bases": [
            {"key": "milano", "name": "Milano", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città estesa ma con una metropolitana che copre tutto: "
                     "il centro si gira a piedi, il resto in pochi minuti di metrò."},
        ],
        "places": [
            {"name": "Duomo e terrazze", "base": "milano", "hours": 2.5, "slot": _MORNING,
             "how": "il biglietto per le terrazze è separato: si sale in ascensore o a piedi "
                    "e si cammina tra le guglie, non è una semplice vista dall'alto", "tier": MUST},
            {"name": "Cenacolo di Leonardo", "label": "Cenacolo", "base": "milano",
             "hours": 1.5, "slot": None,
             "how": "visita di quindici minuti in gruppi contingentati: i biglietti si "
                    "esauriscono con mesi di anticipo, senza prenotazione non si entra",
             "tier": MUST},
            {"name": "Brera e la Pinacoteca", "label": "Brera", "base": "milano",
             "hours": 3.0, "slot": None,
             "how": "a piedi tra le vie del quartiere e poi dentro la pinacoteca, "
                    "che sta nello stesso palazzo dell'Accademia", "tier": MUST},
            {"name": "Aperitivo sui Navigli", "label": "Navigli", "base": "milano",
             "hours": 2.5, "slot": _EVENING,
             "how": "lungo il Naviglio Grande dopo il tramonto: l'aperitivo qui è la cena, "
                    "non un antipasto", "tier": MUST},
            {"name": "Galleria Vittorio Emanuele II e Teatro alla Scala", "label": "Galleria",
             "base": "milano", "hours": 2.0, "slot": None,
             "how": "a piedi dal Duomo; il museo della Scala permette di affacciarsi "
                    "in un palco quando non ci sono prove", "tier": EXTRA},
            {"name": "Castello Sforzesco e Parco Sempione", "label": "Castello",
             "base": "milano", "hours": 2.5, "slot": None,
             "how": "cortili a ingresso libero e musei a pagamento, poi il parco alle spalle "
                    "fino all'Arco della Pace", "tier": EXTRA},
            {"name": "Fondazione Prada", "base": "milano", "hours": 2.5, "slot": None,
             "how": "in metrò a sud del centro: ex distilleria trasformata in spazio "
                    "per l'arte contemporanea, con la torre panoramica", "tier": EXTRA},
            {"name": "Quartiere Isola e Bosco Verticale", "label": "Isola", "base": "milano",
             "hours": 2.0, "slot": None,
             "how": "a piedi da Porta Nuova: il contrasto tra le case di ringhiera "
                    "e i grattacieli è tutto in due isolati", "tier": EXTRA},
            {"name": "Cena in una trattoria milanese", "base": "milano", "hours": 2.5,
             "slot": _EVENING,
             "how": "risotto giallo, cotoletta e cassoeula nelle trattorie storiche "
                    "fuori dal quadrilatero", "tier": EXTRA},
            {"name": "Quadrilatero della moda", "base": "milano", "hours": 2.0,
             "slot": _AFTERNOON,
             "how": "a piedi tra Montenapoleone e Della Spiga: si guardano le vetrine "
                    "anche senza comprare, ed è parte dell'esperienza della città", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Milano in un weekend",
             "for_who": "Duomo, Brera e Navigli: la città in due giorni pieni."},
            {"days": 4, "title": "Milano oltre il Duomo",
             "for_who": "Aggiunge il Cenacolo, l'arte contemporanea e i quartieri nuovi."},
        ],
    },

    # =====================================================================
    # 12 — TORINO
    # =====================================================================
    12: {
        "bases": [
            {"key": "torino", "name": "Torino", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro a scacchiera con diciotto chilometri di portici: "
                     "si gira tutto a piedi, anche quando piove."},
        ],
        "places": [
            {"name": "Museo Egizio", "base": "torino", "hours": 3.0, "slot": _MORNING,
             "how": "biglietto a orario: è la seconda collezione egizia al mondo dopo "
                    "il Cairo, e servono almeno tre ore per non correre", "tier": MUST},
            {"name": "Mole Antonelliana e Museo del Cinema", "label": "Mole",
             "base": "torino", "hours": 3.0, "slot": None,
             "how": "l'ascensore panoramico sale nel vuoto della cupola in un minuto; "
                    "il museo si sviluppa a spirale lungo la rampa", "tier": MUST},
            {"name": "Piazza San Carlo e i caffè storici", "label": "Centro storico",
             "base": "torino", "hours": 2.0, "slot": None,
             "how": "a piedi sotto i portici tra le piazze auliche, con sosta per il bicerin "
                    "nei caffè ottocenteschi", "tier": MUST},
            {"name": "Aperitivo torinese", "base": "torino", "hours": 2.5, "slot": _EVENING,
             "how": "nel quartiere San Salvario o in piazza Vittorio: il vermouth è nato "
                    "qui e l'aperitivo con buffet pure", "tier": MUST},
            {"name": "Luci d'Artista", "base": "torino", "hours": 2.0, "slot": _EVENING,
             "how": "giro a piedi tra le installazioni luminose d'autore sparse per le vie "
                    "del centro, diverse ogni anno", "tier": EXTRA,
             "months": [11, 12, 1],
             "note": "Le installazioni restano accese solo tra fine autunno e gennaio."},
            {"name": "Basilica di Superga", "label": "Superga", "base": "torino",
             "hours": 3.0, "slot": None,
             "how": "si sale con la tranvia a dentiera da Sassi: dalla terrazza "
                    "si vede tutto l'arco alpino nelle giornate limpide", "tier": EXTRA},
            {"name": "Palazzo Reale e Armeria", "base": "torino", "hours": 2.5, "slot": None,
             "how": "biglietto unico dei Musei Reali, che comprende anche la Galleria "
                    "Sabauda e i giardini", "tier": EXTRA},
            {"name": "Mercato di Porta Palazzo", "label": "Porta Palazzo", "base": "torino",
             "hours": 2.0, "slot": _MORNING,
             "how": "a piedi tra i banchi del più grande mercato all'aperto d'Europa, "
                    "la mattina presto quando lavora davvero", "tier": EXTRA},
            {"name": "Reggia di Venaria", "base": "torino", "hours": 4.0, "slot": _MORNING,
             "how": "in bus o treno fuori città: la Galleria Grande e i giardini "
                    "richiedono mezza giornata piena", "tier": EXTRA},
            {"name": "Cena di cucina piemontese", "base": "torino", "hours": 2.5,
             "slot": _EVENING,
             "how": "agnolotti del plin, vitello tonnato e Barbera nelle piole del centro",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Torino in due giorni",
             "for_who": "Egizio, Mole e portici: la città regia in un fine settimana."},
            {"days": 4, "title": "Torino e le residenze reali",
             "for_who": "Aggiunge Venaria, Superga e i mercati, con tempo per gli aperitivi."},
        ],
    },

    # =====================================================================
    # 13 — SALENTO (PUGLIA)
    # Due coste diverse a mezz'ora l'una dall'altra: adriatica a est,
    # ionica a ovest. La base cambia quale delle due hai sotto casa.
    # =====================================================================
    13: {
        "bases": [
            {"key": "lecce", "name": "Lecce", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.0,
             "note": "La città d'arte del Salento: si dorme qui per il barocco e la sera, "
                     "non per il mare."},
            {"key": "otranto", "name": "Otranto", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.8,
             "note": "Sulla costa adriatica: da qui si raggiungono in auto sia le grotte "
                     "a nord sia Leuca a sud."},
        ],
        "places": [
            {"name": "Centro barocco di Lecce", "label": "Lecce", "base": "lecce",
             "hours": 3.0, "slot": None,
             "how": "a piedi tra Santa Croce, il Duomo e l'anfiteatro romano: "
                    "la pietra leccese è tenera, ed è per questo che è così scolpita",
             "tier": MUST},
            {"name": "Cena di cucina salentina a Lecce", "base": "lecce", "hours": 2.5,
             "slot": _EVENING,
             "how": "nelle corti del centro: ciceri e tria, pittule e rustico leccese, "
                    "con il primitivo del posto", "tier": MUST},
            {"name": "Museo Faggiano", "base": "lecce", "hours": 1.5, "slot": None,
             "how": "una casa privata scavata per caso durante dei lavori idraulici: "
                    "sotto ci sono duemila anni di città, si visita su più livelli",
             "tier": EXTRA},
            {"name": "Otranto e il mosaico della cattedrale", "label": "Otranto",
             "base": "otranto", "hours": 2.5, "slot": None,
             "how": "a piedi nel borgo murato; nella cattedrale il pavimento è un unico "
                    "mosaico del XII secolo con l'albero della vita", "tier": MUST},
            {"name": "Grotta della Poesia", "base": "otranto", "hours": 3.0, "slot": None,
             "how": "piscina naturale scavata nella roccia a Roca Vecchia, "
                    "si scende dagli scogli: non ci sono servizi né ombra", "tier": MUST,
             "months": [5, 6, 7, 8, 9, 10],
             "note": "Fuori stagione il mare mosso rende l'accesso alla grotta pericoloso."},
            {"name": "Spiaggia di Punta Prosciutto", "label": "Punta Prosciutto",
             "base": "otranto", "hours": 5.0, "slot": None,
             "how": "sulla costa ionica, circa un'ora d'auto: dune, sabbia bianca "
                    "e acqua bassa a lungo, la più caraibica del Salento", "tier": MUST},
            {"name": "Santa Maria di Leuca", "label": "Leuca", "base": "otranto",
             "hours": 4.0, "slot": None,
             "how": "la punta estrema del tacco, dove i due mari si incontrano: "
                    "il faro, la basilica e le grotte marine in barca", "tier": EXTRA},
            {"name": "Gallipoli e il centro storico sull'isola", "label": "Gallipoli",
             "base": "otranto", "hours": 4.0, "slot": None,
             "how": "il borgo vecchio sta su un'isola collegata da un ponte: "
                    "si gira a piedi e si mangia il pesce crudo al mercato", "tier": EXTRA},
            {"name": "Tramonto a Torre Sant'Andrea", "base": "otranto", "hours": 2.0,
             "slot": _EVENING,
             "how": "faraglioni di roccia bianca a nord di Otranto: si arriva in auto "
                    "e si scende a piedi sugli scogli", "tier": EXTRA},
            {"name": "Cena di pesce a Otranto", "base": "otranto", "hours": 2.5,
             "slot": _EVENING,
             "how": "sul lungomare del porto: crudi, ricci in stagione e frittura, "
                    "guardando il castello aragonese illuminato", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Salento tra barocco e mare",
             "for_who": "Lecce, Otranto e le due coste: il giro classico senza fretta."},
            {"days": 8, "title": "Tutto il tacco",
             "for_who": "Aggiunge Leuca, Gallipoli e il tempo per stare in spiaggia davvero."},
        ],
    },

    # =====================================================================
    # 14 — LAGO DI COMO
    # =====================================================================
    14: {
        "bases": [
            {"key": "varenna", "name": "Varenna", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Sul ramo di Lecco, con la stazione dei treni e il traghetto per Bellagio "
                     "e Menaggio: è il punto da cui il lago si gira senza auto."},
        ],
        "places": [
            {"name": "Bellagio", "base": "varenna", "hours": 3.0, "slot": None,
             "how": "in traghetto da Varenna in quindici minuti: il borgo sale in scalinate "
                    "dal porto, e si gira solo a piedi", "tier": MUST},
            {"name": "Villa del Balbianello", "base": "varenna", "hours": 3.5, "slot": None,
             "how": "si arriva in barca da Lenno oppure a piedi in venti minuti di sentiero; "
                    "i giardini a terrazza scendono fino all'acqua", "tier": MUST,
             "months": [3, 4, 5, 6, 7, 8, 9, 10, 11],
             "note": "La villa e i giardini chiudono nei mesi invernali."},
            {"name": "Villa Monastero e passeggiata degli innamorati", "label": "Varenna",
             "base": "varenna", "hours": 2.5, "slot": None,
             "how": "a piedi dal porto lungo la passerella a filo d'acqua, poi il giardino "
                    "botanico della villa affacciato sul lago", "tier": MUST},
            {"name": "Cena sul lungolago", "base": "varenna", "hours": 2.5, "slot": _EVENING,
             "how": "ai tavoli sull'acqua dopo che i battelli hanno smesso: "
                    "pesce di lago, missoltini e risotto con il pesce persico", "tier": MUST},
            {"name": "Funicolare di Brunate", "label": "Brunate", "base": "varenna",
             "hours": 3.0, "slot": None,
             "how": "sette minuti di funicolare da Como: dall'alto si vede tutto "
                    "il primo bacino, e si può proseguire a piedi fino al faro", "tier": EXTRA},
            {"name": "Como e il Duomo", "label": "Como", "base": "varenna", "hours": 3.0,
             "slot": None,
             "how": "in treno o battello: il centro murato si gira a piedi in un paio d'ore, "
                    "con il Duomo che mescola gotico e rinascimento", "tier": EXTRA},
            {"name": "Giro in barca privata sul ramo di Como", "label": "Giro in barca",
             "base": "varenna", "hours": 2.5, "slot": _EVENING,
             "how": "taxi boat condiviso al tramonto tra le ville storiche, "
                    "che dall'acqua si vedono come sono state pensate", "tier": EXTRA,
             "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Villa Carlotta", "base": "varenna", "hours": 2.5, "slot": None,
             "how": "in traghetto a Tremezzo: il parco botanico è il pezzo forte, "
                    "spettacolare quando fioriscono azalee e rododendri", "tier": EXTRA,
             "months": [3, 4, 5, 6, 7, 8, 9, 10, 11]},
            {"name": "Abbazia di Piona", "base": "varenna", "hours": 2.0, "slot": None,
             "how": "in fondo al ramo di Lecco, su una penisola silenziosa: "
                    "il chiostro romanico e i liquori dei monaci", "tier": EXTRA},
            {"name": "Sentiero del Viandante", "base": "varenna", "hours": 4.0,
             "slot": _MORNING,
             "how": "antico percorso a mezza costa sopra il lago: si cammina tra i borghi "
                    "e si torna in treno dalla tappa dove ci si ferma", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Il lago in un weekend",
             "for_who": "Bellagio, Varenna e una villa: il triangolo classico via traghetto."},
            {"days": 4, "title": "Como tra ville e sentieri",
             "for_who": "Aggiunge Como, i giardini storici e una camminata sopra il lago."},
        ],
    },

    # =====================================================================
    # 15 — UMBRIA (ASSISI E PERUGIA)
    # =====================================================================
    15: {
        "bases": [
            {"key": "perugia", "name": "Perugia", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.0,
             "note": "Il capoluogo sul colle: base per i borghi a nord e per il Trasimeno."},
            {"key": "assisi", "name": "Assisi", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.6,
             "note": "Mezz'ora da Perugia: la sera, quando i pullman se ne vanno, "
                     "il borgo resta vuoto e silenzioso."},
        ],
        "places": [
            {"name": "Centro storico di Perugia e Rocca Paolina", "label": "Perugia",
             "base": "perugia", "hours": 3.0, "slot": None,
             "how": "si sale dal parcheggio con le scale mobili che attraversano la città "
                    "medievale sepolta sotto la rocca, poi a piedi fino al Corso Vannucci",
             "tier": MUST},
            {"name": "Galleria Nazionale dell'Umbria", "base": "perugia", "hours": 2.0,
             "slot": None,
             "how": "dentro il Palazzo dei Priori sul corso: Perugino e Pinturicchio "
                    "nella città dove hanno lavorato", "tier": EXTRA},
            {"name": "Cena umbra a Perugia", "base": "perugia", "hours": 2.5, "slot": _EVENING,
             "how": "torta al testo, strangozzi al tartufo e Sagrantino nelle osterie "
                    "dentro le mura etrusche", "tier": MUST},
            {"name": "Lago Trasimeno e Isola Maggiore", "label": "Trasimeno",
             "base": "perugia", "hours": 4.0, "slot": None,
             "how": "traghetto da Passignano o Tuoro fino all'isola, che si gira "
                    "a piedi in un'ora tra le case dei merlettai", "tier": EXTRA,
             "months": [3, 4, 5, 6, 7, 8, 9, 10]},
            {"name": "Gubbio e la funivia del Monte Ingino", "label": "Gubbio",
             "base": "perugia", "hours": 4.0, "slot": None,
             "how": "quaranta minuti d'auto; si sale al santuario con le ceste aperte "
                    "della funivia, in piedi e appesi a un cavo", "tier": EXTRA},
            {"name": "Basilica di San Francesco", "label": "Assisi", "base": "assisi",
             "hours": 2.5, "slot": _MORNING,
             "how": "due chiese sovrapposte: sotto Cimabue, sopra il ciclo di Giotto. "
                    "Ingresso libero, ma silenzio e abbigliamento coperto sono obbligatori",
             "tier": MUST},
            {"name": "Eremo delle Carceri", "base": "assisi", "hours": 2.5, "slot": None,
             "how": "quattro chilometri sopra Assisi, in auto o a piedi nel bosco: "
                    "le grotte dove Francesco si ritirava, ancora in silenzio", "tier": MUST},
            {"name": "Rocca Maggiore", "base": "assisi", "hours": 2.0, "slot": None,
             "how": "salita ripida a piedi dal centro fino ai camminamenti: "
                    "da lassù si capisce come il borgo è appoggiato sul fianco del monte",
             "tier": EXTRA},
            {"name": "Assisi dopo il tramonto", "base": "assisi", "hours": 2.0,
             "slot": _EVENING,
             "how": "passeggiata tra i vicoli illuminati quando i pullman sono ripartiti: "
                    "è il momento in cui il paese torna ai suoi abitanti", "tier": MUST},
            {"name": "Spello", "base": "assisi", "hours": 2.5, "slot": None,
             "how": "venti minuti da Assisi: il borgo di pietra rosa, famoso per "
                    "le infiorate e per i vicoli sempre pieni di vasi", "tier": EXTRA},
            {"name": "Cascata delle Marmore", "base": "assisi", "hours": 4.0, "slot": None,
             "how": "attenzione agli orari: la cascata è alimentata da una centrale "
                    "e l'acqua viene rilasciata solo in fasce prestabilite del giorno",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Assisi e Perugia",
             "for_who": "Le due città che si guardano da una collina all'altra, senza correre."},
            {"days": 5, "title": "Cuore verde dell'Umbria",
             "for_who": "Aggiunge i borghi minori, il Trasimeno e il tempo per il silenzio."},
        ],
    },

    # =====================================================================
    # 16 — PARIGI
    # =====================================================================
    16: {
        "bases": [
            {"key": "parigi", "name": "Parigi", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Metropolitana capillare: ogni quartiere è a meno di venti minuti, "
                     "ma dentro ogni quartiere si cammina."},
        ],
        "places": [
            {"name": "Museo del Louvre", "label": "Louvre", "base": "parigi", "hours": 3.5,
             "slot": _MORNING,
             "how": "biglietto a orario prenotato; si entra dalla piramide o dal passaggio "
                    "del Carrousel, che ha quasi sempre meno coda", "tier": MUST},
            {"name": "Torre Eiffel", "base": "parigi", "hours": 2.5, "slot": _EVENING,
             "how": "salita prenotata con orario: di sera la torre scintilla per cinque "
                    "minuti all'inizio di ogni ora, e si vede meglio dal Trocadéro", "tier": MUST},
            {"name": "Île de la Cité e Notre-Dame", "label": "Notre-Dame", "base": "parigi",
             "hours": 2.0, "slot": None,
             "how": "ingresso gratuito ma con prenotazione oraria per evitare la fila; "
                    "a due passi c'è la Sainte-Chapelle, che si paga a parte", "tier": MUST},
            {"name": "Montmartre e Sacré-Cœur", "label": "Montmartre", "base": "parigi",
             "hours": 3.0, "slot": None,
             "how": "si sale con la funicolare o le scalinate; il quartiere dietro la basilica "
                    "è quello vero, place du Tertre è la parte da cartolina", "tier": MUST},
            {"name": "Musée d'Orsay", "base": "parigi", "hours": 2.5, "slot": None,
             "how": "nell'ex stazione ferroviaria sulla riva sinistra: gli impressionisti "
                    "stanno all'ultimo piano, dietro il grande orologio", "tier": EXTRA},
            {"name": "Marais", "base": "parigi", "hours": 2.5, "slot": None,
             "how": "a piedi tra place des Vosges e rue des Rosiers: è l'unico quartiere "
                    "dove molti negozi aprono anche la domenica", "tier": EXTRA},
            {"name": "Reggia di Versailles", "label": "Versailles", "base": "parigi",
             "hours": 6.0, "slot": _MORNING,
             "how": "RER C da Parigi, poi mezza giornata piena: la reggia al mattino "
                    "e i giardini nel pomeriggio, che d'estate hanno le fontane in funzione",
             "tier": EXTRA},
            {"name": "Crociera sulla Senna", "base": "parigi", "hours": 1.5, "slot": _EVENING,
             "how": "battello dal Pont Neuf al tramonto: i monumenti si accendono "
                    "mentre si naviga, ed è il modo più economico di vederli tutti", "tier": EXTRA},
            {"name": "Quartiere Latino e Panthéon", "label": "Quartiere Latino",
             "base": "parigi", "hours": 2.5, "slot": None,
             "how": "a piedi tra le librerie e i vicoli dietro la Sorbona, con il Panthéon "
                    "e i giardini del Lussemburgo a chiudere il giro", "tier": EXTRA},
            {"name": "Cena in un bistrot di quartiere", "base": "parigi", "hours": 2.5,
             "slot": _EVENING,
             "how": "fuori dal centro turistico, dove il menù è scritto a mano e cambia "
                    "ogni giorno: si prenota anche per i posti piccoli", "tier": EXTRA},
            {"name": "Cimitero di Père-Lachaise", "base": "parigi", "hours": 2.0, "slot": None,
             "how": "si entra gratis e si prende la mappa all'ingresso: è un parco collinare "
                    "più che un cimitero, e ci si perde facilmente", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Parigi la prima volta",
             "for_who": "Louvre, Torre Eiffel e Montmartre: le cose che non si possono saltare."},
            {"days": 5, "title": "Parigi per quartieri",
             "for_who": "Aggiunge Versailles, i musei minori e il tempo per vivere i quartieri."},
        ],
    },

    # =====================================================================
    # 17 — LONDRA
    # =====================================================================
    17: {
        "bases": [
            {"key": "londra", "name": "Londra", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città enorme ma con la metropolitana più capillare d'Europa: "
                     "conviene una travelcard giornaliera invece dei biglietti singoli."},
        ],
        "places": [
            {"name": "British Museum", "base": "londra", "hours": 3.0, "slot": _MORNING,
             "how": "ingresso gratuito, si entra senza biglietto ma con controllo borse: "
                    "conviene scegliere due o tre sale invece di provare a vederlo tutto",
             "tier": MUST},
            {"name": "Westminster e Abbazia", "label": "Westminster", "base": "londra",
             "hours": 3.0, "slot": None,
             "how": "a piedi lungo il Tamigi dal Big Ben; l'abbazia si paga e la visita "
                    "con audioguida richiede un'ora e mezza abbondante", "tier": MUST},
            {"name": "Torre di Londra e Tower Bridge", "label": "Tower of London",
             "base": "londra", "hours": 3.5, "slot": _MORNING,
             "how": "biglietto online; il tour con le guardie Yeoman è compreso e parte "
                    "a orari fissi, ed è la parte migliore della visita", "tier": MUST},
            {"name": "Covent Garden e Soho", "label": "Soho", "base": "londra", "hours": 2.5,
             "slot": _EVENING,
             "how": "a piedi tra i teatri e gli artisti di strada, poi cena nei vicoli "
                    "di Soho: è la zona che resta viva più tardi", "tier": MUST},
            {"name": "National Gallery e Trafalgar Square", "label": "National Gallery",
             "base": "londra", "hours": 2.5, "slot": None,
             "how": "gratuita come quasi tutti i musei nazionali; si affaccia direttamente "
                    "su Trafalgar Square, quindi si incastra in mezza giornata", "tier": EXTRA},
            {"name": "Borough Market", "base": "londra", "hours": 2.0, "slot": _MORNING,
             "how": "sotto le arcate della ferrovia a London Bridge: si pranza in piedi "
                    "tra i banchi, ed è chiuso la domenica", "tier": EXTRA},
            {"name": "Camden Market", "base": "londra", "hours": 2.5, "slot": None,
             "how": "in metropolitana a nord: mercato di bancarelle lungo il canale, "
                    "si può proseguire a piedi fino a Regent's Park", "tier": EXTRA},
            {"name": "Hyde Park e Kensington", "base": "londra", "hours": 2.5, "slot": None,
             "how": "a piedi dai Kensington Gardens fino a Speaker's Corner: il parco "
                    "attraversa mezza città e collega quartieri diversissimi", "tier": EXTRA},
            {"name": "Musical nel West End", "base": "londra", "hours": 3.0, "slot": _EVENING,
             "how": "biglietti last minute al botteghino di Leicester Square il giorno stesso, "
                    "spesso a metà prezzo rispetto all'online", "tier": EXTRA},
            {"name": "Pub tradizionale", "base": "londra", "hours": 2.0, "slot": _EVENING,
             "how": "si ordina al bancone e si paga subito: nei pub storici si beve "
                    "in piedi anche fuori, sul marciapiede", "tier": EXTRA},
            {"name": "Greenwich e il meridiano", "label": "Greenwich", "base": "londra",
             "hours": 4.0, "slot": None,
             "how": "in battello sul Tamigi invece che in metro: si arriva dal fiume, "
                    "si sale al parco e si sta a cavallo del meridiano zero", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Londra classica",
             "for_who": "Musei gratuiti, Westminster e la Torre: la città iconica in tre giorni."},
            {"days": 5, "title": "Londra per mercati e quartieri",
             "for_who": "Aggiunge i mercati, i parchi, Greenwich e una serata a teatro."},
        ],
    },

    # =====================================================================
    # 18 — BARCELLONA
    # =====================================================================
    18: {
        "bases": [
            {"key": "barcellona", "name": "Barcellona", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Dall'Eixample al mare si cammina; per Park Güell e Montjuïc "
                     "conviene la metro, sono entrambi in salita."},
        ],
        "places": [
            {"name": "Sagrada Família", "base": "barcellona", "hours": 2.5, "slot": _MORNING,
             "how": "biglietto a orario, esaurito con settimane di anticipo in alta stagione; "
                    "la salita alle torri si prenota a parte ed è con ascensore", "tier": MUST},
            {"name": "Park Güell", "base": "barcellona", "hours": 2.5, "slot": None,
             "how": "la zona monumentale ha ingresso contingentato a orario; si sale "
                    "con la metro più le scale mobili, non è una passeggiata piana", "tier": MUST},
            {"name": "Barri Gòtic", "base": "barcellona", "hours": 2.5, "slot": None,
             "how": "a piedi nel dedalo medievale dietro la cattedrale, dove le vie "
                    "sono troppo strette perché ci passino le auto", "tier": MUST},
            {"name": "Cena di tapas al Born", "label": "El Born", "base": "barcellona",
             "hours": 2.5, "slot": _EVENING,
             "how": "in piedi al bancone da un locale all'altro: qui si cena tardi, "
                    "prima delle nove i posti sono vuoti", "tier": MUST},
            {"name": "Casa Batlló e Casa Milà", "label": "Modernismo", "base": "barcellona",
             "hours": 2.5, "slot": None,
             "how": "a piedi lungo il Passeig de Gràcia: si possono vedere anche solo "
                    "dall'esterno, ma gli interni di Gaudí sono il motivo per entrare",
             "tier": EXTRA},
            {"name": "Mercato della Boqueria", "label": "Boqueria", "base": "barcellona",
             "hours": 1.5, "slot": _MORNING,
             "how": "sulla Rambla, ma i banchi buoni sono in fondo: la mattina presto "
                    "ci sono ancora i clienti del quartiere, chiuso la domenica", "tier": EXTRA},
            {"name": "Montjuïc", "base": "barcellona", "hours": 3.5, "slot": None,
             "how": "in funivia dal porto o funicolare dalla metro: castello, giardini "
                    "e la Fondazione Miró, tutto sulla stessa collina", "tier": EXTRA},
            {"name": "Spiaggia della Barceloneta", "label": "Barceloneta",
             "base": "barcellona", "hours": 4.0, "slot": None,
             "how": "a piedi dal Born in venti minuti: è la spiaggia cittadina, comoda "
                    "e affollata, con i chiringuiti lungo la sabbia", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Bunkers del Carmel al tramonto", "label": "Bunkers del Carmel",
             "base": "barcellona", "hours": 2.0, "slot": _EVENING,
             "how": "vecchie postazioni antiaeree su una collina: si sale in bus più "
                    "una salita a piedi, ed è la vista a 360 gradi sulla città", "tier": EXTRA},
            {"name": "Museo Picasso", "base": "barcellona", "hours": 2.0, "slot": None,
             "how": "nel Born, dentro cinque palazzi medievali comunicanti: raccoglie "
                    "soprattutto le opere giovanili, quelle del periodo barcellonese", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Barcellona di Gaudí",
             "for_who": "Sagrada Família, Park Güell e il Gotico: l'essenziale in tre giorni."},
            {"days": 5, "title": "Barcellona tra mare e collina",
             "for_who": "Aggiunge Montjuïc, la spiaggia, i mercati e le serate nel Born."},
        ],
    },

    # =====================================================================
    # 19 — LISBONA
    # =====================================================================
    19: {
        "bases": [
            {"key": "lisbona", "name": "Lisbona", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città di sette colli: si cammina molto e sempre in salita, "
                     "gli ascensori e le funicolari pubbliche sono parte dei trasporti."},
        ],
        "places": [
            {"name": "Belém: Torre e Monastero dos Jerónimos", "label": "Belém",
             "base": "lisbona", "hours": 3.5, "slot": _MORNING,
             "how": "in tram 15 dal centro; si visitano insieme e a due passi c'è la "
                    "pasticceria storica dei pastéis, dove si mangia in piedi al bancone",
             "tier": MUST},
            {"name": "Alfama e tram 28", "label": "Alfama", "base": "lisbona", "hours": 3.0,
             "slot": None,
             "how": "il 28 attraversa i vicoli più stretti: si prende al capolinea "
                    "per trovare posto, altrimenti si sale in piedi e stretti", "tier": MUST},
            {"name": "Serata di fado ad Alfama", "label": "Fado", "base": "lisbona",
             "hours": 2.5, "slot": _EVENING,
             "how": "nelle case di fado si cena e si ascolta: si prenota, le luci si "
                    "abbassano e durante il canto non si parla e non si fotografa", "tier": MUST},
            {"name": "Sintra", "base": "lisbona", "hours": 6.0, "slot": _MORNING,
             "how": "quaranta minuti di treno da Rossio, poi bus o tuk-tuk in salita: "
                    "il Palácio da Pena e la Quinta da Regaleira si prenotano a orario "
                    "e in un giorno solo si fanno a fatica entrambi", "tier": MUST},
            {"name": "Tramonto da un miradouro", "label": "Miradouro", "base": "lisbona",
             "hours": 1.5, "slot": _EVENING,
             "how": "Senhora do Monte o Santa Catarina: si arriva un'ora prima con "
                    "qualcosa da bere, perché i posti a sedere finiscono subito", "tier": MUST},
            {"name": "Castelo de São Jorge", "base": "lisbona", "hours": 2.0, "slot": None,
             "how": "si sale a piedi da Alfama o con l'ascensore pubblico: dalle mura "
                    "si vede tutta la città e l'estuario", "tier": EXTRA},
            {"name": "Time Out Market", "base": "lisbona", "hours": 2.0, "slot": None,
             "how": "nel vecchio mercato di Cais do Sodré: banchi di cuochi noti "
                    "e tavoli in comune, si mangia bene in fretta", "tier": EXTRA},
            {"name": "LX Factory", "base": "lisbona", "hours": 2.5, "slot": None,
             "how": "ex complesso industriale sotto il ponte 25 de Abril, oggi librerie, "
                    "botteghe e caffè: si arriva in tram o in autobus", "tier": EXTRA},
            {"name": "Cascais", "base": "lisbona", "hours": 4.0, "slot": None,
             "how": "in treno lungo la costa da Cais do Sodré, quaranta minuti con il mare "
                    "dal finestrino: borgo di pescatori diventato località balneare",
             "tier": EXTRA, "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Cena di pesce a Cais do Sodré", "base": "lisbona", "hours": 2.5,
             "slot": _EVENING,
             "how": "bacalhau, sardine alla griglia e vinho verde nelle tasche "
                    "del quartiere del porto", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Lisbona e Sintra",
             "for_who": "Belém, Alfama e una giornata a Sintra: il minimo indispensabile."},
            {"days": 5, "title": "Lisbona con calma",
             "for_who": "Aggiunge i mercati, la costa e le sere di fado nei quartieri alti."},
        ],
    },

    # =====================================================================
    # 20 — MADEIRA
    # Isola verticale: quasi tutto è un sentiero, e la differenza la fa
    # se si cammina lungo una levada o su una cresta esposta.
    # =====================================================================
    20: {
        "bases": [
            {"key": "funchal", "name": "Funchal", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Base unica sulla costa sud: serve un'auto a noleggio, perché i bus "
                     "arrivano agli imbocchi dei sentieri con orari che non tornano."},
        ],
        "places": [
            {"name": "Pico do Arieiro - Pico Ruivo (PR1)", "label": "Pico Ruivo",
             "base": "funchal", "hours": 7.0, "slot": _MORNING,
             "how": "traversata di cresta tra le due cime più alte, con gallerie scavate "
                    "nella roccia e scalinate esposte: serve una torcia e si parte all'alba, "
                    "perché a metà mattina le nuvole salgono e coprono tutto", "tier": MUST},
            {"name": "Levada das 25 Fontes", "base": "funchal", "hours": 5.0, "slot": _MORNING,
             "how": "si cammina lungo il canale d'irrigazione dentro la foresta di laurisilva "
                    "fino alla cascata: il parcheggio di Rabaçal è contingentato "
                    "e conviene arrivare presto", "tier": MUST},
            {"name": "Ponta de São Lourenço", "base": "funchal", "hours": 4.0, "slot": None,
             "how": "la punta orientale, brulla e ventosa: sentiero panoramico tra scogliere "
                    "di basalto, senza un metro d'ombra su tutto il percorso", "tier": MUST},
            {"name": "Funivia di Monte e discesa in slitta", "label": "Monte",
             "base": "funchal", "hours": 3.0, "slot": None,
             "how": "funivia da Funchal fino al giardino tropicale di Monte, poi la discesa "
                    "sui cesti di vimini spinti da due carreiros in bianco", "tier": MUST},
            {"name": "Mercado dos Lavradores", "base": "funchal", "hours": 1.5,
             "slot": _MORNING,
             "how": "a piedi nel centro di Funchal: frutti tropicali dell'isola e il banco "
                    "del pesce con gli espada neri degli abissi", "tier": EXTRA},
            {"name": "Levada do Caldeirão Verde", "base": "funchal", "hours": 6.0,
             "slot": _MORNING,
             "how": "dal parco delle Queimadas, quasi nove chilometri per senso di marcia "
                    "lungo il canale, con quattro gallerie da attraversare con la torcia",
             "tier": EXTRA},
            {"name": "Cabo Girão e Câmara de Lobos", "label": "Cabo Girão",
             "base": "funchal", "hours": 3.0, "slot": None,
             "how": "la piattaforma di vetro sospesa sulla falesia a quasi 600 metri, "
                    "poi il porticciolo di pescatori dove si beve la poncha", "tier": EXTRA},
            {"name": "Piscine naturali di Porto Moniz", "label": "Porto Moniz",
             "base": "funchal", "hours": 4.0, "slot": None,
             "how": "sulla punta nord-ovest: vasche di roccia lavica riempite dall'oceano, "
                    "attrezzate con scalette e bagnini", "tier": EXTRA},
            {"name": "Avvistamento cetacei", "base": "funchal", "hours": 3.5, "slot": None,
             "how": "in catamarano dalla marina di Funchal: al largo di Madeira i delfini "
                    "si vedono quasi tutto l'anno, le balene sono più stagionali", "tier": EXTRA},
            {"name": "Cena di espetada a Funchal", "base": "funchal", "hours": 2.5,
             "slot": _EVENING,
             "how": "spiedi di manzo su alloro serviti appesi al tavolo, con il bolo do caco "
                    "all'aglio e un bicchiere di vino Madeira", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Madeira dei sentieri",
             "for_who": "Le levade, la cresta dei picchi e la punta est: l'isola come si cammina."},
            {"days": 7, "title": "Madeira completa",
             "for_who": "Aggiunge il nord, l'oceano e il tempo per Funchal e i suoi mercati."},
        ],
    },

    # =====================================================================
    # 21 — PRAGA
    # =====================================================================
    21: {
        "bases": [
            {"key": "praga", "name": "Praga", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro storico compatto ai due lati del fiume: si gira a piedi, "
                     "il tram serve solo per salire al castello."},
        ],
        "places": [
            {"name": "Castello di Praga e Vicolo d'Oro", "label": "Castello",
             "base": "praga", "hours": 3.5, "slot": _MORNING,
             "how": "si sale in tram 22 e si scende a piedi: biglietto unico per la cattedrale, "
                    "il palazzo e il vicolo, che al pomeriggio è pieno di gruppi", "tier": MUST},
            {"name": "Ponte Carlo all'alba", "label": "Ponte Carlo", "base": "praga",
             "hours": 1.5, "slot": _MORNING,
             "how": "presto la mattina è vuoto e le statue si vedono davvero: a metà "
                    "giornata è una fila continua di persone da una riva all'altra", "tier": MUST},
            {"name": "Città Vecchia e orologio astronomico", "label": "Città Vecchia",
             "base": "praga", "hours": 2.5, "slot": None,
             "how": "l'orologio suona allo scoccare di ogni ora ed è una cosa di un minuto: "
                    "vale più salire sulla torre del municipio per vedere i tetti", "tier": MUST},
            {"name": "Birreria tradizionale", "base": "praga", "hours": 2.5, "slot": _EVENING,
             "how": "nelle birrerie storiche si siede ai tavoli in comune e la birra "
                    "arriva senza ordinarla finché non si copre il bicchiere", "tier": MUST},
            {"name": "Mercatini di Natale", "base": "praga", "hours": 2.5, "slot": _EVENING,
             "how": "in Piazza della Città Vecchia e in Piazza San Venceslao, dopo il tramonto: "
                    "si mangia in piedi tra le casette, con vin brulé e trdelník",
             "tier": MUST, "months": [11, 12, 1],
             "note": "I mercatini aprono a fine novembre e chiudono nei primi giorni di gennaio."},
            {"name": "Quartiere ebraico di Josefov", "label": "Josefov", "base": "praga",
             "hours": 2.5, "slot": None,
             "how": "biglietto unico per le sinagoghe e il vecchio cimitero, dove le lapidi "
                    "sono accatastate su dodici strati per mancanza di spazio", "tier": EXTRA},
            {"name": "Collina di Petřín", "base": "praga", "hours": 2.5, "slot": None,
             "how": "funicolare da Malá Strana e poi la torre panoramica: dall'alto "
                    "si capisce come il fiume divide la città in due", "tier": EXTRA},
            {"name": "Vyšehrad", "base": "praga", "hours": 2.5, "slot": None,
             "how": "la seconda fortezza, a sud e quasi senza turisti: mura, cimitero "
                    "monumentale e affaccio sulla Moldava", "tier": EXTRA},
            {"name": "Crociera sulla Moldava", "base": "praga", "hours": 2.0, "slot": _EVENING,
             "how": "battello dal molo sotto il Ponte Carlo: la città illuminata "
                    "si vede da sotto i ponti", "tier": EXTRA},
            {"name": "Isola di Kampa e muro di John Lennon", "label": "Kampa",
             "base": "praga", "hours": 1.5, "slot": None,
             "how": "sotto il Ponte Carlo, dalla parte di Malá Strana: un'isoletta "
                    "con il mulino, i salici e il muro ridipinto in continuazione", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Praga in un weekend",
             "for_who": "Castello, Ponte Carlo e Città Vecchia: la città d'oro in due giorni."},
            {"days": 4, "title": "Praga oltre il centro",
             "for_who": "Aggiunge Josefov, le colline e i quartieri dove non arrivano i gruppi."},
        ],
    },

    # =====================================================================
    # 22 — VIENNA
    # =====================================================================
    22: {
        "bases": [
            {"key": "vienna", "name": "Vienna", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro dentro il Ring, girabile a piedi; il resto con una metropolitana "
                     "puntuale al minuto."},
        ],
        "places": [
            {"name": "Reggia di Schönbrunn", "label": "Schönbrunn", "base": "vienna",
             "hours": 4.0, "slot": _MORNING,
             "how": "biglietto a orario per gli appartamenti; il parco è gratuito e sale "
                    "fino alla Gloriette, da cui si vede tutta la città", "tier": MUST},
            {"name": "Hofburg e Tesoro imperiale", "label": "Hofburg", "base": "vienna",
             "hours": 3.0, "slot": None,
             "how": "a piedi in centro: appartamenti di Sissi, museo e Schatzkammer "
                    "con le insegne del Sacro Romano Impero, biglietti separati", "tier": MUST},
            {"name": "Duomo di Santo Stefano", "label": "Santo Stefano", "base": "vienna",
             "hours": 2.0, "slot": None,
             "how": "la torre sud si sale a piedi con 343 gradini, quella nord in ascensore: "
                    "sono viste diverse e si pagano separatamente", "tier": MUST},
            {"name": "Caffè storico viennese", "label": "Caffè viennese", "base": "vienna",
             "hours": 1.5, "slot": None,
             "how": "ci si siede e si resta: il caffè si ordina per nome (melange, einspänner) "
                    "e arriva sempre con un bicchiere d'acqua", "tier": MUST},
            {"name": "Mercatini di Natale davanti al Municipio", "label": "Mercatini",
             "base": "vienna", "hours": 2.5, "slot": _EVENING,
             "how": "il Rathausplatz diventa un villaggio illuminato: punch caldo, "
                    "pista di ghiaccio tra gli alberi del parco", "tier": MUST,
             "months": [11, 12, 1],
             "note": "I mercatini vanno da metà novembre alle feste; alcuni chiudono già dopo Natale."},
            {"name": "Belvedere e il Bacio di Klimt", "label": "Belvedere", "base": "vienna",
             "hours": 2.5, "slot": None,
             "how": "nel palazzo superiore, in una sala sola: la fila si concentra "
                    "davanti a un quadro, il resto del museo è quasi vuoto", "tier": EXTRA},
            {"name": "Naschmarkt", "base": "vienna", "hours": 2.0, "slot": _MORNING,
             "how": "mercato lungo più di un chilometro: banchi di spezie e cucine "
                    "del mondo, il sabato si aggiunge il mercatino dell'usato", "tier": EXTRA},
            {"name": "Concerto di musica classica", "base": "vienna", "hours": 2.5,
             "slot": _EVENING,
             "how": "dalla Musikverein alle chiese del centro: i posti in piedi "
                    "all'Opera di Stato si comprano il giorno stesso e costano pochissimo",
             "tier": EXTRA},
            {"name": "Prater e ruota panoramica", "label": "Prater", "base": "vienna",
             "hours": 2.5, "slot": None,
             "how": "la ruota di fine Ottocento gira lentamente in cabine chiuse di legno; "
                    "attorno c'è un parco enorme dove i viennesi corrono e vanno in bici",
             "tier": EXTRA},
            {"name": "MuseumsQuartier", "base": "vienna", "hours": 2.5, "slot": None,
             "how": "ex scuderie imperiali diventate poli museali: nei cortili ci si siede "
                    "sui divani colorati anche senza entrare nei musei", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Vienna imperiale",
             "for_who": "Schönbrunn, Hofburg e i caffè: la capitale asburgica in tre giorni."},
            {"days": 5, "title": "Vienna tra musei e musica",
             "for_who": "Aggiunge Klimt, i mercati, un concerto e il tempo per i quartieri."},
        ],
    },

    # =====================================================================
    # 23 — BUDAPEST
    # =====================================================================
    23: {
        "bases": [
            {"key": "budapest", "name": "Budapest", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Due città divise dal Danubio: Pest è piana e si cammina, "
                     "Buda è in collina e conviene salirci con la funicolare o il bus."},
        ],
        "places": [
            {"name": "Bagni termali Széchenyi", "label": "Terme Széchenyi",
             "base": "budapest", "hours": 3.0, "slot": None,
             "how": "vasche all'aperto calde anche d'inverno, quando esce il vapore: "
                    "si porta ciabatte e accappatoio, o si noleggiano all'ingresso", "tier": MUST},
            {"name": "Parlamento ungherese", "label": "Parlamento", "base": "budapest",
             "hours": 2.0, "slot": None,
             "how": "visita guidata a orario, da prenotare: si entra solo con il gruppo "
                    "e si vedono la scalinata e la Sacra Corona", "tier": MUST},
            {"name": "Bastione dei Pescatori e quartiere del castello", "label": "Buda",
             "base": "budapest", "hours": 3.0, "slot": _MORNING,
             "how": "si sale con la funicolare dal Ponte delle Catene: dalle terrazze bianche "
                    "si guarda il Parlamento dall'altra parte del fiume", "tier": MUST},
            {"name": "Serata in un ruin bar", "label": "Ruin bar", "base": "budapest",
             "hours": 2.5, "slot": _EVENING,
             "how": "nel quartiere ebraico: palazzi abbandonati riempiti di mobili "
                    "scompagnati, si entra gratis e si gira di stanza in stanza", "tier": MUST},
            {"name": "Crociera sul Danubio", "base": "budapest", "hours": 1.5,
             "slot": _EVENING,
             "how": "dopo il tramonto, quando il Parlamento e i ponti si accendono: "
                    "la linea pubblica dei battelli costa una frazione dei tour", "tier": EXTRA},
            {"name": "Mercato Centrale", "base": "budapest", "hours": 1.5, "slot": _MORNING,
             "how": "tre piani in una struttura di ferro e vetro: paprika e salumi sotto, "
                    "banchi di lángos da mangiare in piedi al primo piano", "tier": EXTRA},
            {"name": "Basilica di Santo Stefano", "base": "budapest", "hours": 1.5,
             "slot": None,
             "how": "si sale alla cupola in ascensore più una rampa di scale, "
                    "per il giro panoramico sui tetti di Pest", "tier": EXTRA},
            {"name": "Isola Margherita", "base": "budapest", "hours": 2.5, "slot": None,
             "how": "in mezzo al Danubio, senza auto: si gira a piedi o con i risciò, "
                    "e c'è la fontana musicale all'estremità sud", "tier": EXTRA},
            {"name": "Mercatini di Natale in Vörösmarty tér", "label": "Mercatini",
             "base": "budapest", "hours": 2.0, "slot": _EVENING,
             "how": "il mercatino principale nella piazza centrale di Pest, con i banchi "
                    "di kürtőskalács cotti sulla brace", "tier": EXTRA,
             "months": [11, 12, 1]},
            {"name": "Cena di cucina ungherese", "base": "budapest", "hours": 2.5,
             "slot": _EVENING,
             "how": "gulyás come zuppa e non come spezzatino, pörkölt e vino di Eger "
                    "nelle trattorie fuori dalle vie centrali", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Budapest in un weekend",
             "for_who": "Terme, Parlamento e ruin bar: la città in due giorni pieni."},
            {"days": 4, "title": "Budapest tra le due rive",
             "for_who": "Aggiunge Buda, i mercati e le serate sul Danubio."},
        ],
    },

    # =====================================================================
    # 24 — BERLINO
    # =====================================================================
    24: {
        "bases": [
            {"key": "berlino", "name": "Berlino", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città vastissima e a bassa densità: senza S-Bahn e U-Bahn "
                     "si perde metà giornata negli spostamenti."},
        ],
        "places": [
            {"name": "Porta di Brandeburgo e Memoriale dell'Olocausto", "label": "Mitte",
             "base": "berlino", "hours": 2.5, "slot": None,
             "how": "a piedi tra i due, sono a trecento metri: il memoriale si attraversa "
                    "camminando tra le stele, e sotto c'è il centro di documentazione",
             "tier": MUST},
            {"name": "Memoriale del Muro alla Bernauer Strasse", "label": "Muro di Berlino",
             "base": "berlino", "hours": 2.5, "slot": None,
             "how": "l'unico tratto conservato con la striscia della morte e la torretta: "
                    "è qui che si capisce il Muro, non a Checkpoint Charlie", "tier": MUST},
            {"name": "Isola dei Musei", "label": "Isola dei Musei", "base": "berlino",
             "hours": 3.5, "slot": _MORNING,
             "how": "cinque musei su un'isola sulla Sprea: con il biglietto cumulativo "
                    "conviene sceglierne due, il Pergamon è in restauro a rotazione", "tier": MUST},
            {"name": "East Side Gallery", "base": "berlino", "hours": 2.0, "slot": None,
             "how": "un chilometro e mezzo di Muro rimasto in piedi e dipinto: "
                    "si cammina lungo il fiume da Ostbahnhof al ponte Oberbaum", "tier": MUST},
            {"name": "Cupola del Reichstag", "label": "Reichstag", "base": "berlino",
             "hours": 1.5, "slot": _EVENING,
             "how": "ingresso gratuito ma solo con registrazione anticipata e documento: "
                    "la rampa a spirale sale dentro la cupola di vetro, bella al tramonto",
             "tier": EXTRA},
            {"name": "Kreuzberg e la scena turca", "label": "Kreuzberg", "base": "berlino",
             "hours": 2.5, "slot": None,
             "how": "a piedi lungo il canale e per Oranienstrasse: il mercato turco "
                    "sul Maybachufer c'è il martedì e il venerdì", "tier": EXTRA},
            {"name": "Tempelhofer Feld", "label": "Tempelhof", "base": "berlino",
             "hours": 2.5, "slot": None,
             "how": "l'ex aeroporto trasformato in parco: si cammina e si va in bici "
                    "sulle piste di decollo, senza niente intorno", "tier": EXTRA},
            {"name": "Serata a Friedrichshain", "label": "Friedrichshain", "base": "berlino",
             "hours": 3.0, "slot": _EVENING,
             "how": "bar e locali attorno a Boxhagener Platz: qui si esce tardi, "
                    "e nei club veri non si entra prima dell'una", "tier": EXTRA},
            {"name": "Mercatini di Natale a Gendarmenmarkt", "label": "Mercatini",
             "base": "berlino", "hours": 2.0, "slot": _EVENING,
             "how": "nella piazza tra i due duomi: è a pagamento, ma è il più curato "
                    "dei tanti mercatini sparsi in città", "tier": EXTRA,
             "months": [11, 12, 1]},
            {"name": "Cena di street food a Markthalle Neun", "label": "Markthalle Neun",
             "base": "berlino", "hours": 2.5, "slot": _EVENING,
             "how": "mercato coperto storico a Kreuzberg: il giovedì sera è la serata "
                    "dedicata allo street food, con decine di cucine diverse", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Berlino e il Novecento",
             "for_who": "Muro, memoriali e Isola dei Musei: la città che racconta il secolo."},
            {"days": 5, "title": "Berlino per quartieri",
             "for_who": "Aggiunge Kreuzberg, i parchi, i mercati e le notti lunghe."},
        ],
    },

    # =====================================================================
    # 25 — AMSTERDAM
    # =====================================================================
    25: {
        "bases": [
            {"key": "amsterdam", "name": "Amsterdam", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Tutto entro gli anelli dei canali: si gira a piedi o in bici, "
                     "e la bici qui è un mezzo di trasporto, non un'attrazione."},
        ],
        "places": [
            {"name": "Rijksmuseum", "base": "amsterdam", "hours": 3.0, "slot": _MORNING,
             "how": "biglietto a orario: la Ronda di notte è nella galleria d'onore "
                    "all'ultimo piano, dove si concentra quasi tutta la folla", "tier": MUST},
            {"name": "Museo Van Gogh", "base": "amsterdam", "hours": 2.5, "slot": None,
             "how": "a orario prenotato, spesso esaurito con giorni di anticipo: "
                    "la collezione è in ordine cronologico su quattro piani", "tier": MUST},
            {"name": "Casa di Anna Frank", "label": "Casa di Anna Frank",
             "base": "amsterdam", "hours": 2.0, "slot": None,
             "how": "solo con biglietto nominativo comprato online settimane prima: "
                    "non si entra in nessun altro modo, non c'è biglietteria in loco",
             "tier": MUST},
            {"name": "Giro in barca sui canali", "base": "amsterdam", "hours": 1.5,
             "slot": _EVENING,
             "how": "battelli coperti che passano sotto i ponti stretti: al tramonto "
                    "le case dei canali si illuminano e i vetri non riflettono", "tier": MUST},
            {"name": "Jordaan", "base": "amsterdam", "hours": 2.5, "slot": None,
             "how": "a piedi tra i canali stretti e le corti nascoste: è il quartiere "
                    "dove Amsterdam è rimasta di quartiere, con i caffè bruni storici",
             "tier": MUST},
            {"name": "Keukenhof", "base": "amsterdam", "hours": 5.0, "slot": _MORNING,
             "how": "in bus diretto da Schiphol o dalla città: sette milioni di bulbi "
                    "in fiore in un parco che apre solo per la stagione dei tulipani",
             "tier": EXTRA, "months": [3, 4, 5],
             "note": "Il parco apre solo da fine marzo a metà maggio, per la fioritura."},
            {"name": "Mercato Albert Cuyp e De Pijp", "label": "De Pijp",
             "base": "amsterdam", "hours": 2.0, "slot": _MORNING,
             "how": "il mercato di strada più lungo dei Paesi Bassi, aperto tutti i giorni "
                    "tranne la domenica: si mangiano le stroopwafel appena fatte", "tier": EXTRA},
            {"name": "Vondelpark in bici", "label": "Vondelpark", "base": "amsterdam",
             "hours": 2.5, "slot": None,
             "how": "si noleggia una bici e si entra nel parco dalla parte dei musei: "
                    "è il modo in cui la città lo usa davvero", "tier": EXTRA},
            {"name": "Serata in un brown café", "label": "Brown café", "base": "amsterdam",
             "hours": 2.0, "slot": _EVENING,
             "how": "i caffè storici col legno scurito dal fumo di due secoli: "
                    "birra, bitterballen e conversazione, niente musica alta", "tier": EXTRA},
            {"name": "Zaanse Schans", "base": "amsterdam", "hours": 4.0, "slot": None,
             "how": "venti minuti di treno a nord: i mulini a vento ancora funzionanti "
                    "lungo il fiume, con le case di legno verdi", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Amsterdam dei musei e dei canali",
             "for_who": "Rijksmuseum, Van Gogh, Anna Frank e una barca: l'essenziale."},
            {"days": 5, "title": "Amsterdam come i locali",
             "for_who": "Aggiunge la bici, i mercati, i brown café e una gita fuori città."},
        ],
    },

    # =====================================================================
    # 26 — COPENAGHEN
    # =====================================================================
    26: {
        "bases": [
            {"key": "copenaghen", "name": "Copenaghen", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città piatta e pensata per le biciclette: noleggiarne una "
                     "cambia completamente le distanze."},
        ],
        "places": [
            {"name": "Nyhavn", "base": "copenaghen", "hours": 2.0, "slot": None,
             "how": "il canale con le case colorate: da qui partono i battelli "
                    "che girano il porto, ed è a piedi dalla via pedonale Strøget", "tier": MUST},
            {"name": "Christiania", "base": "copenaghen", "hours": 2.5, "slot": None,
             "how": "la città libera autogestita: si entra a piedi, e in alcune zone "
                    "è vietato fotografare — i cartelli lo dicono chiaramente", "tier": MUST},
            {"name": "Giro in bici per la città", "label": "Bici", "base": "copenaghen",
             "hours": 3.0, "slot": None,
             "how": "piste ciclabili separate e semafori dedicati: si va da Nørrebro "
                    "al porto in venti minuti, come fanno tutti qui", "tier": MUST},
            {"name": "Cena di smørrebrød", "label": "Smørrebrød", "base": "copenaghen",
             "hours": 2.0, "slot": _EVENING,
             "how": "le tartine aperte di segale con aringa, gamberetti o roast beef: "
                    "si ordinano più portate e si mangiano con coltello e forchetta",
             "tier": MUST},
            {"name": "Giardini di Tivoli", "label": "Tivoli", "base": "copenaghen",
             "hours": 3.5, "slot": _EVENING,
             "how": "parco storico in pieno centro, accanto alla stazione: la sera "
                    "si accendono migliaia di lampadine tra le giostre di legno",
             "tier": MUST, "months": [4, 5, 6, 7, 8, 9, 10, 11, 12],
             "note": "Tivoli chiude tra gennaio e marzo, tranne brevi riaperture stagionali."},
            {"name": "Castello di Rosenborg", "label": "Rosenborg", "base": "copenaghen",
             "hours": 2.0, "slot": None,
             "how": "nel giardino del re, in centro: nel sotterraneo ci sono i gioielli "
                    "della corona danese, ancora in uso", "tier": EXTRA},
            {"name": "Torvehallerne", "base": "copenaghen", "hours": 1.5, "slot": _MORNING,
             "how": "mercato coperto in due padiglioni di vetro: caffè, pesce affumicato "
                    "e banchi da pranzo, chiuso la domenica pomeriggio", "tier": EXTRA},
            {"name": "Museo Louisiana", "label": "Louisiana", "base": "copenaghen",
             "hours": 4.0, "slot": None,
             "how": "quaranta minuti di treno a nord: arte moderna in un edificio basso "
                    "affacciato sull'Øresund, con il parco di sculture sul mare", "tier": EXTRA},
            {"name": "Nørrebro", "base": "copenaghen", "hours": 2.5, "slot": None,
             "how": "in bici o a piedi lungo il lago: il quartiere multiculturale "
                    "con il cimitero-parco di Assistens e i locali di Jægersborggade",
             "tier": EXTRA},
            {"name": "Torre della Borsa e Christiansborg", "label": "Christiansborg",
             "base": "copenaghen", "hours": 2.0, "slot": None,
             "how": "la torre del parlamento si sale gratis e ha la vista più alta "
                    "del centro; sotto ci sono le rovine dei castelli precedenti", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Copenaghen in bici",
             "for_who": "Nyhavn, Christiania e i quartieri: la città come la vivono i danesi."},
            {"days": 5, "title": "Copenaghen e dintorni",
             "for_who": "Aggiunge i musei, i mercati e una giornata sull'Øresund."},
        ],
    },

    # =====================================================================
    # 28 — TROMSØ
    # Sopra il circolo polare: qui la stagione non sposta il programma,
    # lo ribalta. D'inverno buio e aurora, d'estate sole a mezzanotte.
    # =====================================================================
    28: {
        "bases": [
            {"key": "tromso", "name": "Tromsø", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Isola collegata da ponti: il centro si gira a piedi in mezz'ora, "
                     "tutto il resto sono escursioni che partono da qui."},
        ],
        "places": [
            {"name": "Caccia all'aurora boreale", "label": "Aurora", "base": "tromso",
             "hours": 5.0, "slot": _EVENING,
             "how": "si parte in minibus e si insegue il cielo sereno anche per centinaia "
                    "di chilometri, a volte fino alla Finlandia: si rientra a notte fonda",
             "tier": MUST, "months": [9, 10, 11, 12, 1, 2, 3],
             "note": "Serve buio: da maggio a luglio il sole non tramonta e l'aurora è invisibile."},
            {"name": "Slitta trainata dai cani", "label": "Cani da slitta",
             "base": "tromso", "hours": 4.0, "slot": None,
             "how": "si guida la slitta a turno o si sta seduti nel cesto; tuta termica "
                    "e stivali sono forniti dal campo", "tier": MUST,
             "months": [12, 1, 2, 3, 4],
             "note": "Serve neve compatta: fuori stagione i cani si incontrano ma con carrello su ruote."},
            {"name": "Funivia Fjellheisen", "label": "Fjellheisen", "base": "tromso",
             "hours": 2.5, "slot": _EVENING,
             "how": "quattro minuti di cabinovia fino a 420 metri: da lassù si vede "
                    "l'isola intera, ed è anche un punto per l'aurora senza uscire dalla città",
             "tier": MUST},
            {"name": "Cattedrale artica", "label": "Cattedrale artica", "base": "tromso",
             "hours": 1.5, "slot": None,
             "how": "sull'altra sponda del ponte, si raggiunge a piedi o in bus: "
                    "la vetrata dietro l'altare è tra le più grandi d'Europa", "tier": MUST},
            {"name": "Crociera nei fiordi", "label": "Fiordi", "base": "tromso",
             "hours": 5.0, "slot": _MORNING,
             "how": "catamarano ibrido silenzioso tra le pareti dei fiordi: d'inverno "
                    "si esce per le orche e le megattere che seguono le aringhe", "tier": MUST},
            {"name": "Campo sami e renne", "label": "Renne", "base": "tromso", "hours": 4.0,
             "slot": None,
             "how": "si dà da mangiare alle renne e si ascolta lo joik dentro il lavvu, "
                    "la tenda tradizionale: l'allevamento è ancora un mestiere vero qui",
             "tier": EXTRA, "months": [11, 12, 1, 2, 3, 4]},
            {"name": "Sole di mezzanotte", "label": "Sole di mezzanotte",
             "base": "tromso", "hours": 3.0, "slot": _EVENING,
             "how": "si sale in funivia o si esce in barca verso mezzanotte: il sole "
                    "sfiora l'orizzonte senza tramontare e la luce resta dorata per ore",
             "tier": EXTRA, "months": [5, 6, 7],
             "note": "Il sole resta sopra l'orizzonte solo tra maggio e luglio."},
            {"name": "Museo polare", "base": "tromso", "hours": 1.5, "slot": None,
             "how": "in una casa di legno sul porto: la storia delle spedizioni artiche "
                    "e dei cacciatori di foche, raccontata senza retorica", "tier": EXTRA},
            {"name": "Birrificio artico", "base": "tromso", "hours": 2.0, "slot": _EVENING,
             "how": "il birrificio più a nord del mondo, in centro: si beve al bancone "
                    "con i pescatori appena rientrati", "tier": EXTRA},
            {"name": "Ciaspolata sull'isola di Kvaløya", "label": "Kvaløya",
             "base": "tromso", "hours": 4.0, "slot": _MORNING,
             "how": "mezz'ora d'auto dalla città: ciaspole ai piedi su altopiani "
                    "affacciati sul mare, con luce blu per gran parte della giornata",
             "tier": EXTRA, "months": [12, 1, 2, 3, 4]},
        ],
        "variants": [
            {"days": 4, "title": "Tromsø e l'aurora",
             "for_who": "Cielo notturno, cani da slitta e fiordi: l'inverno artico in quattro giorni."},
            {"days": 6, "title": "Artico completo",
             "for_who": "Aggiunge i sami, le isole intorno e il tempo per aspettare il cielo giusto."},
        ],
    },

    # =====================================================================
    # 29 — ROVANIEMI (LAPPONIA)
    # =====================================================================
    29: {
        "bases": [
            {"key": "rovaniemi", "name": "Rovaniemi", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Tutto passa da escursioni organizzate: i campi husky e le renne "
                     "sono fuori città e non sono raggiungibili da soli."},
        ],
        "places": [
            {"name": "Villaggio di Babbo Natale", "label": "Villaggio di Babbo Natale",
             "base": "rovaniemi", "hours": 4.0, "slot": _MORNING,
             "how": "in bus di linea dal centro: si attraversa il Circolo Polare Artico "
                    "segnato per terra, e l'incontro con Babbo Natale è gratuito", "tier": MUST},
            {"name": "Safari con gli husky", "label": "Husky", "base": "rovaniemi",
             "hours": 4.0, "slot": None,
             "how": "si guida la propria slitta in coppia, alternandosi: al campo "
                    "danno tuta termica, stivali e guanti", "tier": MUST,
             "months": [12, 1, 2, 3, 4]},
            {"name": "Fattoria delle renne", "label": "Renne", "base": "rovaniemi",
             "hours": 3.0, "slot": None,
             "how": "giro in slitta trainata dalle renne, molto più lento degli husky, "
                    "e patente ufficiale da conducente di renne alla fine", "tier": MUST,
             "months": [12, 1, 2, 3, 4]},
            {"name": "Caccia all'aurora in motoslitta", "label": "Aurora",
             "base": "rovaniemi", "hours": 4.0, "slot": _EVENING,
             "how": "si esce dalla città verso i laghi ghiacciati, lontano dalle luci: "
                    "si guida la motoslitta in fila indiana e si aspetta al buio",
             "tier": MUST, "months": [9, 10, 11, 12, 1, 2, 3],
             "note": "Da maggio ad agosto il cielo non si fa mai abbastanza buio."},
            {"name": "Museo Arktikum", "label": "Arktikum", "base": "rovaniemi",
             "hours": 2.5, "slot": None,
             "how": "a piedi dal centro, sotto una galleria di vetro puntata a nord: "
                    "racconta la vita artica e la cultura sami senza folklore", "tier": MUST},
            {"name": "Sauna finlandese e bagno nel ghiaccio", "label": "Sauna",
             "base": "rovaniemi", "hours": 2.5, "slot": _EVENING,
             "how": "si alterna la sauna bollente al tuffo nel buco aperto nel lago "
                    "ghiacciato: dura pochi secondi ed è il rito nazionale", "tier": EXTRA,
             "months": [12, 1, 2, 3]},
            {"name": "Ranua Wildlife Park", "label": "Ranua", "base": "rovaniemi",
             "hours": 5.0, "slot": _MORNING,
             "how": "un'ora di bus a sud: gli animali artici in ampi recinti nel bosco, "
                    "con orsi polari, ghiottoni e alci", "tier": EXTRA},
            {"name": "Ciaspolata nella foresta innevata", "label": "Ciaspole",
             "base": "rovaniemi", "hours": 3.0, "slot": None,
             "how": "si esce dal bordo città e si cammina tra gli abeti piegati dalla neve, "
                    "in un silenzio totale", "tier": EXTRA,
             "months": [12, 1, 2, 3, 4]},
            {"name": "Cena lappone", "base": "rovaniemi", "hours": 2.5, "slot": _EVENING,
             "how": "zuppa di renna affumicata, salmone cotto accanto al fuoco "
                    "e frutti di bosco artici, spesso dentro un lavvu", "tier": EXTRA},
            {"name": "Discesa in gommone sul fiume Ounasjoki", "label": "Ounasjoki",
             "base": "rovaniemi", "hours": 3.0, "slot": None,
             "how": "d'estate il fiume che attraversa la città si scende in gommone "
                    "o in canoa, con la luce che non finisce mai", "tier": EXTRA,
             "months": [6, 7, 8]},
        ],
        "variants": [
            {"days": 3, "title": "Lapponia in tre giorni",
             "for_who": "Babbo Natale, husky e aurora: il concentrato dell'inverno artico."},
            {"days": 5, "title": "Lapponia con calma",
             "for_who": "Aggiunge renne, sauna sul lago ghiacciato e più notti per il cielo."},
        ],
    },

    # =====================================================================
    # 30 — ZERMATT
    # Paese senza auto: si arriva in treno da Täsch e ci si muove a piedi,
    # in navetta elettrica o con gli impianti.
    # =====================================================================
    30: {
        "bases": [
            {"key": "zermatt", "name": "Zermatt", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Il paese è chiuso alle auto: si lascia la macchina a Täsch e si sale "
                     "in treno navetta, poi ci si muove a piedi o con i taxi elettrici."},
        ],
        "places": [
            {"name": "Gornergrat", "base": "zermatt", "hours": 4.0, "slot": _MORNING,
             "how": "trenino a cremagliera da Zermatt fino a 3.089 metri, quaranta minuti: "
                    "sedersi a destra salendo, il Cervino resta in vista tutto il tempo",
             "tier": MUST},
            {"name": "Matterhorn Glacier Paradise", "label": "Ghiacciaio", "base": "zermatt",
             "hours": 4.0, "slot": _MORNING,
             "how": "la funivia più alta d'Europa, fino a 3.883 metri: in cima c'è il palazzo "
                    "di ghiaccio e si sente l'altitudine, si sale con calma", "tier": MUST},
            {"name": "Il Cervino dal ponte di Zermatt", "label": "Zermatt", "base": "zermatt",
             "hours": 2.0, "slot": _EVENING,
             "how": "dalla Bahnhofstrasse e dal ponticello sul torrente: al tramonto "
                    "la parete est si accende di rosa prima del resto della valle", "tier": MUST},
            {"name": "Giornata sulle piste", "label": "Sci", "base": "zermatt", "hours": 6.0,
             "slot": _MORNING,
             "how": "comprensorio collegato fino a Cervinia sul versante italiano: "
                    "si pranza in Italia e si rientra in Svizzera con gli sci", "tier": MUST,
             "months": [12, 1, 2, 3, 4],
             "note": "La stagione principale va da dicembre ad aprile; d'estate resta aperto solo lo sci sul ghiacciaio."},
            {"name": "Sentiero dei cinque laghi", "label": "Cinque laghi", "base": "zermatt",
             "hours": 5.0, "slot": _MORNING,
             "how": "si sale con la funivia a Blauherd e si scende a piedi tra i laghetti: "
                    "in tre di questi il Cervino si riflette quando non c'è vento", "tier": MUST,
             "months": [6, 7, 8, 9, 10],
             "note": "Il sentiero d'alta quota è percorribile solo d'estate, fuori dalla neve."},
            {"name": "Gola del Gorner", "label": "Gorner", "base": "zermatt", "hours": 2.0,
             "slot": None,
             "how": "passerelle di legno agganciate alla roccia sopra il torrente, "
                    "venti minuti a piedi dal paese", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Rifugio Hörnli", "label": "Hörnlihütte", "base": "zermatt",
             "hours": 6.0, "slot": _MORNING,
             "how": "dalla stazione di Schwarzsee, due ore di cammino fino a 3.260 metri, "
                    "ai piedi della cresta da cui parte la salita al Cervino", "tier": EXTRA,
             "months": [7, 8, 9]},
            {"name": "Cena di fondue o raclette", "base": "zermatt", "hours": 2.5,
             "slot": _EVENING,
             "how": "nei ristoranti di legno del paese: la raclette si serve a fette "
                    "successive e si continua finché non si dice basta", "tier": EXTRA},
            {"name": "Museo del Cervino", "label": "Matterhorn Museum", "base": "zermatt",
             "hours": 1.5, "slot": None,
             "how": "sotto la piazza principale: ricostruisce il villaggio antico e "
                    "conserva la corda spezzata della prima salita del 1865", "tier": EXTRA},
            {"name": "Sunnegga e lago Leisee", "label": "Sunnegga", "base": "zermatt",
             "hours": 3.0, "slot": None,
             "how": "funicolare sotterranea di tre minuti dal paese: terrazza al sole "
                    "e laghetto balneabile, comodo anche con bambini", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Zermatt e il Cervino",
             "for_who": "Gornergrat, ghiacciaio e la montagna da ogni angolazione."},
            {"days": 6, "title": "Zermatt in quota",
             "for_who": "Aggiunge i sentieri d'alta quota, i rifugi e le sere in paese."},
        ],
    },

    # =====================================================================
    # 31 — INNSBRUCK
    # =====================================================================
    31: {
        "bases": [
            {"key": "innsbruck", "name": "Innsbruck", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città alpina compatta: dal centro storico si prende la funicolare "
                     "e in venti minuti si è a duemila metri."},
        ],
        "places": [
            {"name": "Nordkette in funivia", "label": "Nordkette", "base": "innsbruck",
             "hours": 4.0, "slot": _MORNING,
             "how": "funicolare progettata da Zaha Hadid dal centro, poi due funivie "
                    "fino a 2.256 metri: da lì si guarda giù sulla città in verticale",
             "tier": MUST},
            {"name": "Tettuccio d'Oro e centro storico", "label": "Centro storico",
             "base": "innsbruck", "hours": 2.5, "slot": None,
             "how": "a piedi nella Altstadt: il balcone coperto da 2.657 tegole dorate "
                    "sta all'incrocio delle vie porticate medievali", "tier": MUST},
            {"name": "Mercatini di Natale nella Altstadt", "label": "Mercatini",
             "base": "innsbruck", "hours": 2.5, "slot": _EVENING,
             "how": "sotto il Tettuccio d'Oro e lungo la Maria-Theresien-Strasse, "
                    "con le montagne innevate che chiudono la prospettiva della via",
             "tier": MUST, "months": [11, 12, 1]},
            {"name": "Giornata sulle piste", "label": "Sci", "base": "innsbruck",
             "hours": 6.0, "slot": _MORNING,
             "how": "skipass unico su nove comprensori collegati da navette gratuite "
                    "dalla città: si scia e si torna a dormire in centro", "tier": MUST,
             "months": [12, 1, 2, 3, 4]},
            {"name": "Trampolino di Bergisel", "label": "Bergisel", "base": "innsbruck",
             "hours": 2.0, "slot": None,
             "how": "si sale con la funicolare interna alla torre fino alla piattaforma "
                    "di partenza dei saltatori: si guarda giù dal punto in cui si lanciano",
             "tier": EXTRA},
            {"name": "Castello di Ambras", "label": "Ambras", "base": "innsbruck",
             "hours": 2.5, "slot": None,
             "how": "in bus dal centro: la camera delle meraviglie rinascimentale "
                    "è rimasta esattamente come la immaginò l'arciduca Ferdinando", "tier": EXTRA},
            {"name": "Mondi di Cristallo Swarovski", "label": "Swarovski",
             "base": "innsbruck", "hours": 3.0, "slot": None,
             "how": "venti minuti di navetta a Wattens: percorso di installazioni "
                    "dentro la collina, più giardino con la nuvola di cristallo", "tier": EXTRA},
            {"name": "Cena tirolese", "base": "innsbruck", "hours": 2.5, "slot": _EVENING,
             "how": "nelle stube del centro: knödel, gulasch e strudel, con la birra "
                    "servita in boccali da mezzo litro", "tier": EXTRA},
            {"name": "Ghiacciaio dello Stubai", "label": "Stubai", "base": "innsbruck",
             "hours": 5.0, "slot": _MORNING,
             "how": "quaranta minuti di bus e poi funivia fino a 3.210 metri, "
                    "con la passerella panoramica sospesa sul ghiacciaio", "tier": EXTRA},
            {"name": "Gola dell'Sill e passeggiata sull'Inn", "label": "Lungofiume",
             "base": "innsbruck", "hours": 2.0, "slot": None,
             "how": "a piedi lungo l'argine con le case colorate riflesse nel fiume: "
                    "è l'immagine simbolo della città, e non costa niente", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Innsbruck tra città e montagna",
             "for_who": "Centro storico e duemila metri nello stesso giorno."},
            {"days": 5, "title": "Innsbruck e il Tirolo",
             "for_who": "Aggiunge castelli, ghiacciai e le valli intorno alla città."},
        ],
    },

    # =====================================================================
    # 32 — EDIMBURGO
    # =====================================================================
    32: {
        "bases": [
            {"key": "edimburgo", "name": "Edimburgo", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città vecchia in salita e città nuova georgiana in piano: "
                     "si gira tutta a piedi, ma con parecchio dislivello."},
        ],
        "places": [
            {"name": "Castello di Edimburgo", "label": "Castello", "base": "edimburgo",
             "hours": 3.0, "slot": _MORNING,
             "how": "in cima alla rocca vulcanica in fondo al Royal Mile: biglietto "
                    "a orario, e a mezzogiorno spara il cannone tutti i giorni tranne la domenica",
             "tier": MUST},
            {"name": "Royal Mile e Old Town", "label": "Royal Mile", "base": "edimburgo",
             "hours": 2.5, "slot": None,
             "how": "a piedi in discesa dal castello a Holyrood, infilandosi nei close, "
                    "i vicoli coperti che scendono ripidi ai lati", "tier": MUST},
            {"name": "Arthur's Seat", "base": "edimburgo", "hours": 3.0, "slot": _MORNING,
             "how": "un vulcano spento dentro la città: un'ora di salita a piedi "
                    "dal parco di Holyrood, con vento quasi sempre in cima", "tier": MUST},
            {"name": "Degustazione di whisky", "label": "Whisky", "base": "edimburgo",
             "hours": 2.0, "slot": _EVENING,
             "how": "nei bar storici della Old Town: si assaggia per regioni, "
                    "dai torbati di Islay ai più dolci dello Speyside", "tier": MUST},
            {"name": "Dean Village e Water of Leith", "label": "Dean Village",
             "base": "edimburgo", "hours": 2.0, "slot": None,
             "how": "dieci minuti a piedi dalla città nuova: antico borgo di mulini "
                    "sul fiume, e da lì il sentiero lungo l'acqua fino a Stockbridge",
             "tier": EXTRA},
            {"name": "Calton Hill", "base": "edimburgo", "hours": 1.5, "slot": _EVENING,
             "how": "salita breve e facile dal centro: monumenti neoclassici incompiuti "
                    "e la vista che prende castello, mare e città nuova insieme", "tier": EXTRA},
            {"name": "Palazzo di Holyroodhouse", "label": "Holyrood", "base": "edimburgo",
             "hours": 2.0, "slot": None,
             "how": "in fondo al Royal Mile: residenza ufficiale in Scozia, chiude "
                    "quando la famiglia reale è in città", "tier": EXTRA},
            {"name": "Mercatino di Natale in Princes Street Gardens", "label": "Mercatini",
             "base": "edimburgo", "hours": 2.5, "slot": _EVENING,
             "how": "nei giardini sotto il castello, con la ruota panoramica: "
                    "il castello illuminato fa da fondale a tutto il mercato", "tier": EXTRA,
             "months": [11, 12, 1]},
            {"name": "Edinburgh Festival Fringe", "label": "Fringe", "base": "edimburgo",
             "hours": 3.0, "slot": _EVENING,
             "how": "il festival di teatro e comicità più grande del mondo: si compra "
                    "all'ultimo o si guardano gli spettacoli gratuiti per strada",
             "tier": EXTRA, "months": [8],
             "note": "Il Fringe occupa tutto agosto: fuori da quel mese la città è un'altra."},
            {"name": "Cena scozzese in un pub", "base": "edimburgo", "hours": 2.5,
             "slot": _EVENING,
             "how": "haggis con neeps and tatties e musica dal vivo: nei pub della Old Town "
                    "si suona quasi ogni sera senza biglietto", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Edimburgo essenziale",
             "for_who": "Castello, Royal Mile e la salita ad Arthur's Seat."},
            {"days": 5, "title": "Edimburgo tra colline e whisky",
             "for_who": "Aggiunge i borghi sul fiume, le colline panoramiche e le serate nei pub."},
        ],
    },

    # =====================================================================
    # 33 — DUBLINO
    # =====================================================================
    33: {
        "bases": [
            {"key": "dublino", "name": "Dublino", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro raccolto ai due lati del Liffey: si cammina ovunque, "
                     "e le gite fuori partono tutte dalla stessa zona."},
        ],
        "places": [
            {"name": "Trinity College e Book of Kells", "label": "Trinity College",
             "base": "dublino", "hours": 2.5, "slot": _MORNING,
             "how": "biglietto a orario: si vede il manoscritto miniato e poi si sale "
                    "nella Long Room, la sala di legno con duecentomila volumi", "tier": MUST},
            {"name": "Guinness Storehouse", "label": "Guinness", "base": "dublino",
             "hours": 2.5, "slot": None,
             "how": "sette piani nel vecchio magazzino della fabbrica: in cima "
                    "si beve la pinta compresa nel biglietto, con la città a 360 gradi",
             "tier": MUST},
            {"name": "Musica dal vivo in un pub", "label": "Musica dal vivo",
             "base": "dublino", "hours": 2.5, "slot": _EVENING,
             "how": "nelle session tradizionali i musicisti si siedono al tavolo "
                    "e suonano senza palco: non si paga, si consuma e si sta zitti", "tier": MUST},
            {"name": "Kilmainham Gaol", "base": "dublino", "hours": 2.0, "slot": None,
             "how": "solo con visita guidata prenotata online: il carcere dove furono "
                    "giustiziati i capi della rivolta del 1916, è il luogo che spiega l'Irlanda",
             "tier": MUST},
            {"name": "Scogliere di Moher in giornata", "label": "Cliffs of Moher",
             "base": "dublino", "hours": 10.0, "slot": _MORNING,
             "how": "escursione lunghissima in bus attraverso l'isola: si parte all'alba "
                    "e si rientra a sera, con soste al Burren lungo la strada", "tier": EXTRA},
            {"name": "Temple Bar", "base": "dublino", "hours": 2.0, "slot": _EVENING,
             "how": "il quartiere dei pub con le facciate rosse: caro e turistico, "
                    "ma la sera vale il giro, e i pub veri sono nelle vie intorno", "tier": EXTRA},
            {"name": "Phoenix Park", "base": "dublino", "hours": 2.5, "slot": None,
             "how": "il parco recintato più grande d'Europa, con i cervi che pascolano "
                    "liberi: si gira in bici noleggiata all'ingresso", "tier": EXTRA},
            {"name": "Cattedrale di San Patrizio", "label": "San Patrizio",
             "base": "dublino", "hours": 1.5, "slot": None,
             "how": "a piedi dal centro: la cattedrale nazionale, con la tomba "
                    "di Jonathan Swift che ne fu decano", "tier": EXTRA},
            {"name": "Howth", "base": "dublino", "hours": 4.0, "slot": None,
             "how": "trenino DART lungo la costa in mezz'ora: villaggio di pescatori "
                    "con il sentiero ad anello sulla scogliera e il pesce fritto al porto",
             "tier": EXTRA},
            {"name": "Cena di cucina irlandese", "base": "dublino", "hours": 2.5,
             "slot": _EVENING,
             "how": "irish stew, soda bread e ostriche di Galway nelle gastropub "
                    "fuori da Temple Bar", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Dublino e i suoi pub",
             "for_who": "Trinity, Guinness e le session di musica: la città in tre giorni."},
            {"days": 5, "title": "Dublino e la costa",
             "for_who": "Aggiunge la storia del Novecento, il mare e una giornata sulle scogliere."},
        ],
    },

    # =====================================================================
    # 34 — ATENE
    # =====================================================================
    34: {
        "bases": [
            {"key": "atene", "name": "Atene", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Il centro archeologico si gira tutto a piedi; per il mare "
                     "e Sounio serve il bus o il tram lungo la costa."},
        ],
        "places": [
            {"name": "Acropoli e Partenone", "label": "Acropoli", "base": "atene",
             "hours": 3.0, "slot": _MORNING,
             "how": "si entra all'apertura, alle otto: dopo le dieci non c'è ombra "
                    "e il marmo riflette il sole. Biglietto unico valido per più siti",
             "tier": MUST},
            {"name": "Museo dell'Acropoli", "base": "atene", "hours": 2.5, "slot": None,
             "how": "ai piedi della rocca, con il pavimento di vetro sopra gli scavi: "
                    "l'ultimo piano riproduce le proporzioni esatte del Partenone", "tier": MUST},
            {"name": "Plaka e Monastiraki", "label": "Plaka", "base": "atene", "hours": 2.5,
             "slot": None,
             "how": "a piedi tra i vicoli sotto l'Acropoli e il mercato delle pulci: "
                    "la domenica mattina i banchi occupano tutte le strade", "tier": MUST},
            {"name": "Tramonto a Capo Sounio", "label": "Capo Sounio", "base": "atene",
             "hours": 4.0, "slot": _EVENING,
             "how": "un'ora e mezza di bus lungo la costa: il tempio di Poseidone "
                    "sul promontorio, e il sole che cade dritto nel mare dietro le colonne",
             "tier": MUST},
            {"name": "Agorà antica e Tempio di Efesto", "label": "Agorà", "base": "atene",
             "hours": 2.0, "slot": None,
             "how": "compresa nel biglietto unico: il tempio dorico è il meglio conservato "
                    "di tutta la Grecia, e qui c'è ombra vera sotto gli alberi", "tier": EXTRA},
            {"name": "Collina del Licabetto", "label": "Licabetto", "base": "atene",
             "hours": 2.0, "slot": _EVENING,
             "how": "funicolare o mezz'ora di salita a piedi: è il punto più alto "
                    "della città, e da lassù l'Acropoli si vede dall'alto", "tier": EXTRA},
            {"name": "Mercato centrale di Varvakios", "label": "Mercato centrale",
             "base": "atene", "hours": 1.5, "slot": _MORNING,
             "how": "carne e pesce sotto le volte di ferro, e attorno i banchi di spezie "
                    "e olive: chiude la domenica e nel primo pomeriggio", "tier": EXTRA},
            {"name": "Cena di meze a Psiri", "label": "Psiri", "base": "atene", "hours": 2.5,
             "slot": _EVENING,
             "how": "si ordinano molti piattini da condividere e si resta a lungo: "
                    "nelle taverne del quartiere si mangia tardi e spesso c'è musica dal vivo",
             "tier": EXTRA},
            {"name": "Isola di Egina in giornata", "label": "Egina", "base": "atene",
             "hours": 6.0, "slot": _MORNING,
             "how": "traghetto veloce dal Pireo in quaranta minuti: il tempio di Afaia, "
                    "i pistacchi e il porticciolo con le barche di pescatori", "tier": EXTRA,
             "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Riviera ateniese", "label": "Riviera", "base": "atene", "hours": 4.0,
             "slot": None,
             "how": "in tram lungo la costa fino a Glyfada: spiagge attrezzate "
                    "e libere a mezz'ora dall'Acropoli", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
        ],
        "variants": [
            {"days": 3, "title": "Atene classica",
             "for_who": "Acropoli, musei e Plaka: l'antichità in tre giorni, con un tramonto a Sounio."},
            {"days": 5, "title": "Atene tra rovine e mare",
             "for_who": "Aggiunge le isole vicine, la riviera e le serate nei quartieri."},
        ],
    },

    # =====================================================================
    # 35 — SANTORINI
    # =====================================================================
    35: {
        "bases": [
            {"key": "fira", "name": "Fira", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.0,
             "note": "Il capoluogo sulla caldera: più centrale e più economico, "
                     "con i bus per tutta l'isola che partono da qui."},
            {"key": "oia", "name": "Oia", "night_weight": 1, "max_nights": 4,
             "transfer_h": 0.5,
             "note": "L'estremità nord: il tramonto famoso, ma anche i prezzi più alti "
                     "dell'isola e la folla serale."},
        ],
        "places": [
            {"name": "Sentiero da Fira a Oia", "label": "Sentiero della caldera",
             "base": "fira", "hours": 4.0, "slot": _MORNING,
             "how": "dieci chilometri sul bordo della caldera, tra tre e quattro ore: "
                    "quasi senza ombra, si parte all'alba e si torna in bus", "tier": MUST},
            {"name": "Sito archeologico di Akrotiri", "label": "Akrotiri", "base": "fira",
             "hours": 2.5, "slot": None,
             "how": "una città minoica sepolta dall'eruzione e scavata sotto una copertura: "
                    "si cammina su passerelle e si sta all'ombra, buono nelle ore calde",
             "tier": MUST},
            {"name": "Fira e il bordo della caldera", "label": "Fira", "base": "fira",
             "hours": 2.5, "slot": _EVENING,
             "how": "a piedi lungo il ciglio, tra le terrazze affacciate sul vuoto: "
                    "la sera si accendono le luci fino a Imerovigli", "tier": MUST},
            {"name": "Escursione in barca al vulcano", "label": "Vulcano", "base": "fira",
             "hours": 5.0, "slot": _MORNING,
             "how": "in caicco dal porto vecchio: si sale a piedi sul cratere di Nea Kameni "
                    "e ci si bagna nelle sorgenti termali di Palea Kameni", "tier": MUST,
             "months": [4, 5, 6, 7, 8, 9, 10],
             "note": "Le escursioni in barca sulla caldera funzionano solo nella stagione turistica."},
            {"name": "Tramonto a Oia", "label": "Oia", "base": "oia", "hours": 2.5,
             "slot": _EVENING,
             "how": "bisogna prendere posto almeno un'ora prima sui gradini del castello, "
                    "oppure guardarlo da Imerovigli dove c'è molta meno gente", "tier": MUST},
            {"name": "Amoudi Bay", "base": "oia", "hours": 3.0, "slot": None,
             "how": "trecento gradini sotto Oia, o in auto per la strada tornante: "
                    "taverne di pesce sull'acqua e il salto dagli scogli dell'isolotto",
             "tier": MUST},
            {"name": "Degustazione di vini dell'isola", "label": "Cantine", "base": "oia",
             "hours": 2.5, "slot": None,
             "how": "le viti crescono attorcigliate a canestro per terra, per resistere "
                    "al vento: si assaggia l'assyrtiko con vista sulla caldera", "tier": EXTRA},
            {"name": "Spiaggia Rossa", "label": "Red Beach", "base": "fira", "hours": 3.0,
             "slot": None,
             "how": "sotto una falesia di lava rossa vicino ad Akrotiri: si scende "
                    "per un sentiero breve ma instabile, meglio scarpe chiuse", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Perissa e le spiagge nere", "label": "Perissa", "base": "fira",
             "hours": 4.0, "slot": None,
             "how": "sul lato opposto dell'isola: sabbia vulcanica nera che scotta "
                    "a mezzogiorno, con lettini e taverne lungo tutta la spiaggia", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Cena vista caldera", "base": "oia", "hours": 2.5, "slot": _EVENING,
             "how": "si prenota con settimane di anticipo per i tavoli sul bordo: "
                    "fava, pomodorini dell'isola e pesce alla griglia", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Santorini e la caldera",
             "for_who": "Il sentiero sul bordo, il vulcano e il tramonto di Oia."},
            {"days": 6, "title": "Santorini oltre la cartolina",
             "for_who": "Aggiunge le spiagge nere, l'archeologia minoica e le cantine."},
        ],
    },

    # =====================================================================
    # 37 — MALTA
    # =====================================================================
    37: {
        "bases": [
            {"key": "valletta", "name": "La Valletta", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "L'isola è piccola: da La Valletta si raggiunge qualsiasi punto "
                     "in meno di un'ora con i bus pubblici."},
        ],
        "places": [
            {"name": "La Valletta e la Concattedrale di San Giovanni", "label": "La Valletta",
             "base": "valletta", "hours": 3.0, "slot": _MORNING,
             "how": "a piedi nella capitale fortificata: dentro la concattedrale ci sono "
                    "due Caravaggio, e il pavimento è fatto di lapidi dei cavalieri", "tier": MUST},
            {"name": "Mdina", "base": "valletta", "hours": 2.5, "slot": None,
             "how": "la città silenziosa sulla collina, chiusa alle auto: si visita "
                    "meglio la sera, quando i pullman se ne sono andati", "tier": MUST},
            {"name": "Blue Lagoon a Comino", "label": "Blue Lagoon", "base": "valletta",
             "hours": 5.0, "slot": _MORNING,
             "how": "traghetto da Ċirkewwa: l'acqua è trasparente ma l'isolotto è minuscolo "
                    "e in agosto è pieno, conviene la prima corsa del mattino", "tier": MUST,
             "months": [4, 5, 6, 7, 8, 9, 10],
             "note": "I collegamenti per Comino funzionano solo nella stagione balneare."},
            {"name": "Tramonto sulle mura di Mdina", "label": "Mura di Mdina",
             "base": "valletta", "hours": 2.0, "slot": _EVENING,
             "how": "dai bastioni si vede metà isola fino al mare: si arriva in bus "
                    "e si resta per la cena in uno dei pochi ristoranti dentro le mura",
             "tier": MUST},
            {"name": "Le Tre Città", "label": "Tre Città", "base": "valletta", "hours": 3.0,
             "slot": None,
             "how": "si attraversa il Grand Harbour in barchetta tradizionale in cinque minuti: "
                    "Vittoriosa e Senglea sono più vissute e meno turistiche della capitale",
             "tier": EXTRA},
            {"name": "Templi di Ħaġar Qim", "label": "Ħaġar Qim", "base": "valletta",
             "hours": 2.5, "slot": None,
             "how": "templi megalitici più antichi delle piramidi, protetti da una tensostruttura "
                    "sulla scogliera meridionale", "tier": EXTRA},
            {"name": "Gozo", "base": "valletta", "hours": 6.0, "slot": _MORNING,
             "how": "traghetto da Ċirkewwa in venticinque minuti, poi serve un mezzo: "
                    "la cittadella di Victoria, le saline e la baia di Ramla", "tier": EXTRA},
            {"name": "Mercato di Marsaxlokk", "label": "Marsaxlokk", "base": "valletta",
             "hours": 3.0, "slot": _MORNING,
             "how": "la domenica mattina il porto dei pescatori si riempie di banchi, "
                    "con le barche luzzu dagli occhi dipinti sulla prua", "tier": EXTRA},
            {"name": "Grotta Azzurra", "label": "Grotta Azzurra", "base": "valletta",
             "hours": 2.0, "slot": _MORNING,
             "how": "in barchetta da Wied iż-Żurrieq, venti minuti tra le grotte: "
                    "si esce solo col mare calmo, e la luce migliore è la mattina presto",
             "tier": EXTRA, "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Cena maltese a Valletta", "base": "valletta", "hours": 2.5,
             "slot": _EVENING,
             "how": "coniglio in umido, pastizzi e vino locale nei ristoranti "
                    "delle vie strette dietro la Strada Reale", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Malta dei cavalieri",
             "for_who": "La Valletta, Mdina e le Tre Città: la storia dell'isola in tre giorni."},
            {"days": 5, "title": "Malta e le isole",
             "for_who": "Aggiunge Gozo, Comino e i templi preistorici sulla costa sud."},
        ],
    },

    # =====================================================================
    # 38 — TENERIFE (CANARIE)
    # Due isole in una: il sud secco e balneare, il nord verde e umido.
    # =====================================================================
    38: {
        "bases": [
            {"key": "adeje", "name": "Costa Adeje", "night_weight": 2, "max_nights": 5,
             "transfer_h": 0.0,
             "note": "Il sud: sole quasi garantito tutto l'anno, spiagge attrezzate "
                     "e le partenze per le escursioni in mare."},
            {"key": "laguna", "name": "Puerto de la Cruz", "night_weight": 1, "max_nights": 3,
             "transfer_h": 1.2,
             "note": "Il nord: più verde e più nuvoloso, ma da qui il Teide e Anaga "
                     "sono molto più vicini."},
        ],
        "places": [
            {"name": "Parco Nazionale del Teide", "label": "Teide", "base": "adeje",
             "hours": 6.0, "slot": _MORNING,
             "how": "si sale in auto fino ai 2.356 metri della funivia; per l'ultimo tratto "
                    "fino al cratere serve un permesso gratuito da prenotare online "
                    "con settimane di anticipo, e senza quello ci si ferma alla stazione alta",
             "tier": MUST},
            {"name": "Avvistamento di balene e delfini", "label": "Cetacei", "base": "adeje",
             "hours": 3.5, "slot": None,
             "how": "in catamarano da Puerto Colón: al largo del sud vivono globicefali "
                    "stanziali, quindi gli avvistamenti sono quasi certi tutto l'anno",
             "tier": MUST},
            {"name": "Masca", "base": "adeje", "hours": 4.0, "slot": None,
             "how": "borgo isolato in fondo a una gola, si arriva per una strada di tornanti "
                    "strettissimi con navetta obbligatoria in alta stagione", "tier": MUST},
            {"name": "Playa de las Américas e Costa Adeje", "label": "Spiagge del sud",
             "base": "adeje", "hours": 4.0, "slot": None,
             "how": "sabbia scura vulcanica e sabbia importata chiara, tutte attrezzate: "
                    "il sud è riparato dagli alisei e resta caldo anche d'inverno", "tier": MUST},
            {"name": "Cena di pesce a Los Abrigos", "label": "Los Abrigos", "base": "adeje",
             "hours": 2.5, "slot": _EVENING,
             "how": "villaggio di pescatori a est: si sceglie il pesce a peso in vetrina "
                    "e si mangia con le papas arrugadas e il mojo", "tier": EXTRA},
            {"name": "San Cristóbal de La Laguna", "label": "La Laguna", "base": "laguna",
             "hours": 2.5, "slot": None,
             "how": "a piedi nel centro coloniale patrimonio UNESCO: è la città universitaria, "
                    "quindi viva anche fuori stagione", "tier": MUST},
            {"name": "Massiccio di Anaga", "label": "Anaga", "base": "laguna", "hours": 5.0,
             "slot": _MORNING,
             "how": "foresta di alloro perenne avvolta nella nebbia, con sentieri fitti "
                    "e strade a tornanti: è il posto più diverso dell'isola", "tier": MUST},
            {"name": "Garachico", "base": "laguna", "hours": 3.0, "slot": None,
             "how": "piscine naturali scavate nella colata lavica che distrusse il porto "
                    "nel Settecento: si nuota tra le rocce nere quando il mare è calmo",
             "tier": EXTRA},
            {"name": "Playa de las Teresitas", "label": "Las Teresitas", "base": "laguna",
             "hours": 3.5, "slot": None,
             "how": "vicino a Santa Cruz: sabbia chiara portata dal Sahara e una barriera "
                    "che tiene l'acqua ferma, è la spiaggia di famiglia dei tinerfeñi",
             "tier": EXTRA},
            {"name": "Valle de La Orotava", "label": "La Orotava", "base": "laguna",
             "hours": 2.5, "slot": None,
             "how": "case con i balconi di legno canario e i giardini terrazzati, "
                    "con il Teide che chiude la valle sullo sfondo", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Tenerife tra vulcano e mare",
             "for_who": "Il Teide, le balene e le spiagge del sud: l'isola in cinque giorni."},
            {"days": 8, "title": "Tutta Tenerife",
             "for_who": "Aggiunge il nord verde, Anaga e i borghi coloniali."},
        ],
    },

    # =====================================================================
    # 39 — CRACOVIA
    # =====================================================================
    39: {
        "bases": [
            {"key": "cracovia", "name": "Cracovia", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro medievale racchiuso dal parco anulare delle vecchie mura: "
                     "tutto a piedi, tranne le due grandi escursioni fuori città."},
        ],
        "places": [
            {"name": "Piazza del Mercato e Basilica di Santa Maria", "label": "Rynek",
             "base": "cracovia", "hours": 2.5, "slot": None,
             "how": "la piazza medievale più grande d'Europa: ogni ora dalla torre "
                    "un trombettiere suona e si interrompe a metà, come da tradizione",
             "tier": MUST},
            {"name": "Collina e Castello del Wawel", "label": "Wawel", "base": "cracovia",
             "hours": 3.0, "slot": _MORNING,
             "how": "biglietti separati per cattedrale, appartamenti e tesoro, "
                    "contingentati a orario: la collina e i cortili si girano gratis", "tier": MUST},
            {"name": "Auschwitz-Birkenau", "base": "cracovia", "hours": 7.0, "slot": _MORNING,
             "how": "un'ora e mezza di bus, e la visita guidata va prenotata online "
                    "con largo anticipo: sono due campi distinti, e servono almeno "
                    "tre ore e mezza per entrambi", "tier": MUST},
            {"name": "Kazimierz", "base": "cracovia", "hours": 2.5, "slot": _EVENING,
             "how": "l'ex quartiere ebraico, oggi la zona dei locali: si cena tra le sinagoghe "
                    "e i cortili industriali riconvertiti", "tier": MUST},
            {"name": "Miniera di sale di Wieliczka", "label": "Wieliczka", "base": "cracovia",
             "hours": 4.0, "slot": _MORNING,
             "how": "si scendono oltre trecento gradini fino a 135 metri sottoterra: "
                    "gallerie, laghi salati e una cattedrale intera scavata nel sale",
             "tier": MUST},
            {"name": "Fabbrica di Schindler", "label": "Fabbrica di Schindler",
             "base": "cracovia", "hours": 2.0, "slot": None,
             "how": "museo sull'occupazione nazista dentro la fabbrica vera, "
                    "con biglietti a orario che finiscono presto", "tier": EXTRA},
            {"name": "Mercatini di Natale nel Rynek", "label": "Mercatini",
             "base": "cracovia", "hours": 2.0, "slot": _EVENING,
             "how": "banchi di legno attorno al Panno di Tessuto: si mangia oscypek, "
                    "il formaggio di pecora affumicato dei monti Tatra, alla griglia",
             "tier": EXTRA, "months": [11, 12, 1]},
            {"name": "Quartiere di Nowa Huta", "label": "Nowa Huta", "base": "cracovia",
             "hours": 3.0, "slot": None,
             "how": "in tram dal centro: la città operaia costruita dai sovietici "
                    "negli anni Cinquanta, con i viali monumentali e i palazzi in fila",
             "tier": EXTRA},
            {"name": "Cena polacca", "base": "cracovia", "hours": 2.5, "slot": _EVENING,
             "how": "pierogi, żurek nel pane e vodka gelata nelle taverne del centro: "
                    "si mangia molto bene spendendo poco", "tier": EXTRA},
            {"name": "Tumulo di Kościuszko", "label": "Kopiec Kościuszki",
             "base": "cracovia", "hours": 2.0, "slot": None,
             "how": "collinetta artificiale a ovest della città: si sale a spirale "
                    "fino in cima per la vista su Cracovia e sulla valle della Vistola",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Cracovia in un weekend",
             "for_who": "Rynek, Wawel e Kazimierz: la città vecchia in due giorni."},
            {"days": 4, "title": "Cracovia e la memoria",
             "for_who": "Aggiunge Auschwitz e la miniera di sale, le due escursioni che non si dimenticano."},
        ],
    },

    # =====================================================================
    # 40 — STOCCOLMA
    # =====================================================================
    40: {
        "bases": [
            {"key": "stoccolma", "name": "Stoccolma", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città su quattordici isole collegate da ponti: si cammina molto "
                     "e i battelli pubblici sono parte del trasporto urbano."},
        ],
        "places": [
            {"name": "Gamla Stan", "base": "stoccolma", "hours": 2.5, "slot": None,
             "how": "a piedi nella città vecchia su un'isola: il vicolo più stretto "
                    "mista novanta centimetri, e il cambio della guardia al palazzo "
                    "è a mezzogiorno", "tier": MUST},
            {"name": "Museo Vasa", "label": "Vasa", "base": "stoccolma", "hours": 2.5,
             "slot": _MORNING,
             "how": "il vascello del Seicento affondato al varo e recuperato intero "
                    "dopo tre secoli: è conservato in penombra e umidità controllata",
             "tier": MUST},
            {"name": "Skansen", "base": "stoccolma", "hours": 3.5, "slot": None,
             "how": "il primo museo all'aperto del mondo: case svedesi rimontate pezzo "
                    "per pezzo su una collina, con animali nordici in recinti ampi", "tier": MUST},
            {"name": "Arcipelago in battello", "label": "Arcipelago", "base": "stoccolma",
             "hours": 6.0, "slot": _MORNING,
             "how": "battello da Strandvägen verso Vaxholm o Grinda: trentamila isole, "
                    "e in estate si può scendere su una e prendere il battello dopo",
             "tier": MUST, "months": [5, 6, 7, 8, 9],
             "note": "Le linee turistiche dell'arcipelago funzionano solo nella stagione estiva."},
            {"name": "Fika in un caffè storico", "label": "Fika", "base": "stoccolma",
             "hours": 1.5, "slot": None,
             "how": "non è una pausa caffè, è un'istituzione: caffè e kanelbullar "
                    "alla cannella, seduti e senza fretta", "tier": MUST},
            {"name": "Fotografiska", "base": "stoccolma", "hours": 2.5, "slot": _EVENING,
             "how": "museo di fotografia in un ex magazzino doganale sul porto, "
                    "aperto fino a tarda sera: il bar all'ultimo piano ha la vista migliore",
             "tier": EXTRA},
            {"name": "Djurgården in bici", "label": "Djurgården", "base": "stoccolma",
             "hours": 3.0, "slot": None,
             "how": "l'isola-parco reale: si gira in bici tra boschi, musei e "
                    "canali, ed è a venti minuti a piedi dal centro", "tier": EXTRA},
            {"name": "Municipio e Sala Blu", "label": "Stadshuset", "base": "stoccolma",
             "hours": 2.0, "slot": None,
             "how": "solo con visita guidata: è la sala dove si tiene il banchetto "
                    "del Nobel, e si può salire sulla torre di mattoni", "tier": EXTRA},
            {"name": "Södermalm", "base": "stoccolma", "hours": 2.5, "slot": _EVENING,
             "how": "l'isola sud, più giovane e meno formale: negozi vintage, "
                    "locali e le terrazze di Monteliusvägen sulla città", "tier": EXTRA},
            {"name": "Metropolitana come galleria d'arte", "label": "Metro d'arte",
             "base": "stoccolma", "hours": 1.5, "slot": None,
             "how": "con un solo biglietto si scende in una stazione dopo l'altra: "
                    "novanta fermate sono decorate da artisti, alcune scavate nella roccia viva",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Stoccolma sull'acqua",
             "for_who": "Gamla Stan, il Vasa e le isole del centro: la capitale in tre giorni."},
            {"days": 5, "title": "Stoccolma e l'arcipelago",
             "for_who": "Aggiunge le isole, i quartieri sud e i musei meno ovvi."},
        ],
    },

    # =====================================================================
    # 41 — BRUGES
    # =====================================================================
    41: {
        "bases": [
            {"key": "bruges", "name": "Bruges", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Centro medievale minuscolo e pedonale: dormire dentro le mura "
                     "vuol dire avere la città vuota la mattina presto e dopo cena."},
        ],
        "places": [
            {"name": "Markt e Belfort", "label": "Markt", "base": "bruges", "hours": 2.0,
             "slot": _MORNING,
             "how": "366 gradini stretti fino in cima al campanile, con accesso "
                    "contingentato: si sale presto perché la fila si forma subito", "tier": MUST},
            {"name": "Giro in barca sui canali", "label": "Canali", "base": "bruges",
             "hours": 1.0, "slot": None,
             "how": "mezz'ora su barchette scoperte che passano sotto i ponti bassi: "
                    "cinque imbarcaderi, stesso prezzo, si paga in contanti", "tier": MUST,
             "months": [3, 4, 5, 6, 7, 8, 9, 10, 11],
             "note": "I battelli sui canali non navigano nei mesi invernali."},
            {"name": "Beghinaggio e Minnewater", "label": "Beghinaggio", "base": "bruges",
             "hours": 1.5, "slot": None,
             "how": "cortile bianco di case basse attorno a un prato di narcisi, "
                    "dove vige il silenzio: si entra a piedi dal lago dell'amore", "tier": MUST},
            {"name": "Mercatini di Natale sul Markt", "label": "Mercatini", "base": "bruges",
             "hours": 2.0, "slot": _EVENING,
             "how": "la piazza si riempie di casette e di una pista di pattinaggio, "
                    "con le facciate a gradoni illuminate intorno", "tier": MUST,
             "months": [11, 12, 1]},
            {"name": "Basilica del Sacro Sangue", "label": "Sacro Sangue", "base": "bruges",
             "hours": 1.0, "slot": None,
             "how": "due cappelle sovrapposte, romanica sotto e gotica sopra, "
                    "in un angolo della piazza del Burg", "tier": EXTRA},
            {"name": "Birreria storica e degustazione", "label": "Birreria", "base": "bruges",
             "hours": 2.0, "slot": _EVENING,
             "how": "le trappiste e le birre d'abbazia si bevono nel bicchiere dedicato "
                    "a ogni marca: nei locali storici la carta ha centinaia di etichette",
             "tier": MUST},
            {"name": "Museo Groeninge", "label": "Groeninge", "base": "bruges", "hours": 2.0,
             "slot": None,
             "how": "i primitivi fiamminghi, Van Eyck e Memling, in un museo piccolo "
                    "che si visita in un'ora e mezza senza stancarsi", "tier": EXTRA},
            {"name": "Mulini a vento sui bastioni", "label": "Mulini", "base": "bruges",
             "hours": 1.5, "slot": None,
             "how": "passeggiata sull'argine a nord-est, dove restano quattro mulini "
                    "in piedi: è la parte di città senza turisti", "tier": EXTRA},
            {"name": "Cena di cozze e patatine", "base": "bruges", "hours": 2.0,
             "slot": _EVENING,
             "how": "cozze in pentola con birra e patatine fritte due volte, servite "
                    "con la maionese: è il piatto nazionale, non un cliché", "tier": EXTRA},
            {"name": "Cioccolaterie artigianali", "label": "Cioccolato", "base": "bruges",
             "hours": 1.5, "slot": None,
             "how": "nelle botteghe si vede fare la praline dietro il vetro: "
                    "si comprano sfuse a peso, scegliendo una per una", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Bruges in un weekend",
             "for_who": "Il campanile, i canali e il beghinaggio: la città in due giorni lenti."},
            {"days": 3, "title": "Bruges senza fretta",
             "for_who": "Aggiunge i musei, i mulini e il tempo per birra e cioccolato."},
        ],
    },

    # =====================================================================
    # 42 — MARRAKECH
    # =====================================================================
    42: {
        "bases": [
            {"key": "medina", "name": "Medina di Marrakech", "night_weight": 1,
             "max_nights": 10, "transfer_h": 0.0,
             "note": "Dormire in un riad dentro le mura cambia tutto: la medina è un labirinto "
                     "in cui le auto non entrano, e di notte è silenziosa."},
        ],
        "places": [
            {"name": "Piazza Jemaa el-Fna", "label": "Jemaa el-Fna", "base": "medina",
             "hours": 2.5, "slot": _EVENING,
             "how": "al tramonto la piazza cambia mestiere: spariscono i banchi del giorno "
                    "e arrivano le cucine su ruote, si mangia in piedi tra il fumo", "tier": MUST},
            {"name": "Souk della medina", "label": "Souk", "base": "medina", "hours": 3.0,
             "slot": None,
             "how": "a piedi, senza mappa che tenga: si contratta sempre, partendo "
                    "da circa un terzo del prezzo chiesto, e senza fretta", "tier": MUST},
            {"name": "Palazzo della Bahia", "label": "Bahia", "base": "medina", "hours": 2.0,
             "slot": _MORNING,
             "how": "a piedi nella medina sud: centocinquanta stanze attorno a cortili "
                    "di marmo e zellige, si visita presto perché all'ombra ci sono i gruppi",
             "tier": MUST},
            {"name": "Giardino Majorelle e Museo YSL", "label": "Majorelle", "base": "medina",
             "hours": 2.5, "slot": _MORNING,
             "how": "fuori le mura, nel quartiere Gueliz: biglietto a orario, e il blu "
                    "cobalto del giardino si fotografa meglio nella prima ora", "tier": MUST},
            {"name": "Madrasa Ben Youssef", "label": "Ben Youssef", "base": "medina",
             "hours": 1.5, "slot": None,
             "how": "l'antica scuola coranica con il cortile di stucco e cedro intagliato, "
                    "e le celle minuscole degli studenti al piano di sopra", "tier": EXTRA},
            {"name": "Hammam tradizionale", "label": "Hammam", "base": "medina", "hours": 2.0,
             "slot": _AFTERNOON,
             "how": "sapone nero, guanto kessa e risciacquo a secchiate: negli hammam "
                    "di quartiere si va tra locali, in quelli dei riad si paga il triplo",
             "tier": MUST},
            {"name": "Valle dell'Ourika", "label": "Ourika", "base": "medina", "hours": 6.0,
             "slot": _MORNING,
             "how": "un'ora d'auto verso l'Alto Atlante: villaggi berberi lungo il fiume "
                    "e una camminata fino alle cascate, con guida locale al parcheggio",
             "tier": MUST},
            {"name": "Cena nel deserto di Agafay", "label": "Agafay", "base": "medina",
             "hours": 5.0, "slot": _EVENING,
             "how": "quaranta minuti dalla città: deserto di pietra e non di sabbia, "
                    "con cena sotto le tende e il tramonto sull'Atlante", "tier": EXTRA},
            {"name": "Tombe Saadiane", "base": "medina", "hours": 1.5, "slot": None,
             "how": "murate e dimenticate per due secoli, riaperte nel Novecento: "
                    "la sala delle dodici colonne è piccola e la fila scorre lenta",
             "tier": EXTRA},
            {"name": "Corso di cucina marocchina", "label": "Corso di cucina",
             "base": "medina", "hours": 4.0, "slot": _MORNING,
             "how": "si parte dal mercato per la spesa e si torna a cucinare la tajine "
                    "sul braciere, poi si mangia quello che si è preparato", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Marrakech e la medina",
             "for_who": "Souk, palazzi e Jemaa el-Fna: la città rossa senza uscire dalle mura."},
            {"days": 6, "title": "Marrakech e l'Atlante",
             "for_who": "Aggiunge le valli berbere, il deserto di pietra e i riti dell'hammam."},
        ],
    },

    # =====================================================================
    # 43 — DUBAI
    # =====================================================================
    43: {
        "bases": [
            {"key": "dubai", "name": "Dubai", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città lunghissima lungo la costa: la metropolitana copre l'asse "
                     "principale, per tutto il resto servono i taxi, che costano poco."},
        ],
        "places": [
            {"name": "Burj Khalifa", "base": "dubai", "hours": 2.5, "slot": _EVENING,
             "how": "biglietto a orario preso online: al tramonto costa di più ma si vede "
                    "la città di giorno e di notte con la stessa salita", "tier": MUST},
            {"name": "Dubai Mall e Dubai Fountain", "label": "Dubai Mall", "base": "dubai",
             "hours": 3.0, "slot": _EVENING,
             "how": "le fontane danzanti partono ogni mezz'ora dopo il tramonto: "
                    "si guardano gratis dalla passerella sul lago", "tier": MUST},
            {"name": "Safari nel deserto", "label": "Deserto", "base": "dubai", "hours": 6.0,
             "slot": _AFTERNOON,
             "how": "fuoristrada sulle dune nel pomeriggio, poi cena nel campo beduino "
                    "con falconeria e danze: si viene presi in hotel", "tier": MUST},
            {"name": "Dubai Creek e i souk", "label": "Creek", "base": "dubai", "hours": 3.0,
             "slot": _MORNING,
             "how": "si attraversa il canale sulle barche abra per pochi centesimi, "
                    "tra il souk dell'oro e quello delle spezie: è la Dubai di prima",
             "tier": MUST},
            {"name": "Quartiere storico di Al Fahidi", "label": "Al Fahidi", "base": "dubai",
             "hours": 2.0, "slot": _MORNING,
             "how": "vicoli di case in corallo e gesso con le torri del vento, "
                    "il sistema di aria condizionata di duecento anni fa", "tier": MUST},
            {"name": "Palm Jumeirah e The View", "label": "Palm Jumeirah", "base": "dubai",
             "hours": 3.0, "slot": None,
             "how": "monorotaia lungo il tronco della palma, con l'osservatorio "
                    "da cui si capisce la forma dell'isola artificiale", "tier": EXTRA},
            {"name": "Spiaggia di JBR", "label": "JBR", "base": "dubai", "hours": 3.5,
             "slot": None,
             "how": "spiaggia pubblica attrezzata con la passeggiata di ristoranti alle spalle "
                    "e i grattacieli della Marina dietro", "tier": EXTRA},
            {"name": "Museum of the Future", "base": "dubai", "hours": 2.5, "slot": None,
             "how": "l'anello d'acciaio con la calligrafia araba traforata: biglietti "
                    "nominativi che si esauriscono giorni prima", "tier": EXTRA},
            {"name": "Global Village", "base": "dubai", "hours": 4.0, "slot": _EVENING,
             "how": "padiglioni di decine di paesi con mercatini e cucine, all'aperto: "
                    "si gira per ore camminando", "tier": EXTRA,
             "months": [10, 11, 12, 1, 2, 3, 4],
             "note": "Apre solo nella stagione fresca, da ottobre a primavera."},
            {"name": "Miracle Garden", "base": "dubai", "hours": 2.5, "slot": _MORNING,
             "how": "milioni di fiori disposti in strutture gigantesche: si visita "
                    "la mattina presto, perché è tutto all'aperto e senza ombra", "tier": EXTRA,
             "months": [11, 12, 1, 2, 3, 4, 5],
             "note": "Chiude nei mesi estivi, quando il caldo ucciderebbe le piante."},
        ],
        "variants": [
            {"days": 4, "title": "Dubai in verticale",
             "for_who": "Burj Khalifa, deserto e la città vecchia sul Creek: i contrasti in quattro giorni."},
            {"days": 6, "title": "Dubai tra futuro e tradizione",
             "for_who": "Aggiunge le isole artificiali, i musei e le spiagge."},
        ],
    },

    # =====================================================================
    # 44 — MUSCAT (OMAN)
    # =====================================================================
    44: {
        "bases": [
            {"key": "muscat", "name": "Muscat", "night_weight": 2, "max_nights": 5,
             "transfer_h": 0.0,
             "note": "La capitale distesa tra il mare e le montagne: base per i wadi "
                     "della costa e per le escursioni giornaliere."},
            {"key": "nizwa", "name": "Nizwa e le montagne", "night_weight": 1,
             "max_nights": 3, "transfer_h": 1.8,
             "note": "L'interno: forti, oasi e le montagne dell'Hajar, dove la temperatura "
                     "scende di parecchi gradi rispetto alla costa."},
        ],
        "places": [
            {"name": "Grande Moschea del Sultano Qaboos", "label": "Grande Moschea",
             "base": "muscat", "hours": 2.0, "slot": _MORNING,
             "how": "aperta ai non musulmani solo la mattina nei giorni feriali: "
                    "spalle e gambe coperte, e le donne devono coprire i capelli", "tier": MUST},
            {"name": "Souk di Mutrah", "label": "Mutrah", "base": "muscat", "hours": 2.5,
             "slot": _EVENING,
             "how": "sul lungomare della città vecchia, apre nel tardo pomeriggio: "
                    "incenso, argento e khanjar, i pugnali ricurvi tradizionali", "tier": MUST},
            {"name": "Wadi Shab", "base": "muscat", "hours": 6.0, "slot": _MORNING,
             "how": "due ore d'auto a sud, poi barchetta e quarantacinque minuti di cammino "
                    "tra le rocce, e infine si nuota fino alla grotta con la cascata: "
                    "si va con lo zaino impermeabile", "tier": MUST},
            {"name": "Voragine di Bimmah", "label": "Bimmah", "base": "muscat", "hours": 2.0,
             "slot": None,
             "how": "una dolina di acqua turchese a pochi passi dalla strada costiera: "
                    "si scendono le scale e ci si tuffa, è attrezzata a parco", "tier": EXTRA},
            {"name": "Cena omanita sul lungomare", "base": "muscat", "hours": 2.5,
             "slot": _EVENING,
             "how": "shuwa, pesce alla griglia e datteri con il caffè al cardamomo, "
                    "servito prima del pasto e non dopo", "tier": EXTRA},
            {"name": "Forte e mercato di Nizwa", "label": "Nizwa", "base": "nizwa",
             "hours": 3.0, "slot": _MORNING,
             "how": "la torre circolare si sale a spirale; il mercato delle capre "
                    "si tiene solo il venerdì mattina presto, ed è uno spettacolo a sé",
             "tier": MUST},
            {"name": "Jebel Shams", "base": "nizwa", "hours": 6.0, "slot": _MORNING,
             "how": "la montagna più alta dell'Oman: si sale in fuoristrada fino al bordo "
                    "del canyon, e il sentiero balcone corre a picco sul vuoto", "tier": MUST},
            {"name": "Deserto di Wahiba Sands", "label": "Wahiba", "base": "nizwa",
             "hours": 8.0, "slot": _MORNING,
             "how": "dune arancioni alte fino a cento metri: si entra solo in fuoristrada "
                    "sgonfiando le gomme, e si dorme nei campi tendati", "tier": MUST},
            {"name": "Villaggio di Misfat al Abriyeen", "label": "Misfat", "base": "nizwa",
             "hours": 3.0, "slot": None,
             "how": "villaggio di fango e pietra aggrappato alla roccia, con i canali falaj "
                    "che irrigano i palmeti a terrazza sotto le case", "tier": EXTRA},
            {"name": "Wadi Bani Khalid", "base": "nizwa", "hours": 4.0, "slot": None,
             "how": "piscine naturali smeraldo raggiungibili in auto normale, "
                    "poi pochi minuti a piedi: è il wadi più accessibile del paese",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Oman tra mare e wadi",
             "for_who": "Muscat, la moschea e le piscine naturali della costa."},
            {"days": 8, "title": "Oman completo",
             "for_who": "Aggiunge le montagne dell'Hajar, i forti dell'interno e una notte nel deserto."},
        ],
    },

    # =====================================================================
    # 46 — PHUKET & KRABI
    # =====================================================================
    46: {
        "bases": [
            {"key": "phuket", "name": "Phuket", "night_weight": 1, "max_nights": 5,
             "transfer_h": 0.0,
             "note": "L'isola grande, con l'aeroporto e la vita notturna: base "
                     "per le uscite in barca verso ovest e nord."},
            {"key": "krabi", "name": "Krabi e Ao Nang", "night_weight": 2, "max_nights": 8,
             "transfer_h": 2.5,
             "note": "Sulla terraferma, tra le falesie calcaree: da qui si raggiungono "
                     "Railay e le isole del sud, tutte in longtail."},
        ],
        "places": [
            {"name": "Vecchia Phuket Town", "label": "Phuket Town", "base": "phuket",
             "hours": 2.5, "slot": None,
             "how": "a piedi tra le case sino-portoghesi colorate di Thalang Road: "
                    "la domenica sera la via diventa mercato pedonale", "tier": MUST},
            {"name": "Isole Phi Phi in barca", "label": "Phi Phi", "base": "phuket",
             "hours": 8.0, "slot": _MORNING,
             "how": "in speedboat da Phuket: Maya Bay si visita con ingresso contingentato "
                    "e non è più consentito nuotare in tutta la baia", "tier": MUST},
            {"name": "Baia di Phang Nga e James Bond Island", "label": "Phang Nga",
             "base": "phuket", "hours": 8.0, "slot": _MORNING,
             "how": "in barca tra i pinnacoli calcarei, con il giro in canoa dentro "
                    "le grotte allagate che si apre solo con la marea giusta", "tier": MUST},
            {"name": "Big Buddha", "base": "phuket", "hours": 2.5, "slot": None,
             "how": "in scooter o taxi su per la collina: quarantacinque metri di marmo "
                    "bianco con la vista su entrambe le coste dell'isola", "tier": EXTRA},
            {"name": "Cena di street food ai mercati notturni", "label": "Mercato notturno",
             "base": "phuket", "hours": 2.5, "slot": _EVENING,
             "how": "si mangia camminando tra i banchi: pad thai, mango sticky rice "
                    "e frullati, pagando cifre irrisorie", "tier": MUST},
            {"name": "Railay Beach", "label": "Railay", "base": "krabi", "hours": 5.0,
             "slot": None,
             "how": "raggiungibile solo in longtail da Ao Nang, dieci minuti: "
                    "una penisola chiusa dalle falesie, dove si arrampica sul calcare",
             "tier": MUST},
            {"name": "Isole di Koh Hong e delle Quattro Isole", "label": "Quattro Isole",
             "base": "krabi", "hours": 6.0, "slot": _MORNING,
             "how": "in longtail da Ao Nang: laguna interna a Koh Hong e la lingua "
                    "di sabbia che con la bassa marea unisce tre isole", "tier": MUST},
            {"name": "Tempio della Grotta della Tigre", "label": "Tiger Cave",
             "base": "krabi", "hours": 3.5, "slot": _MORNING,
             "how": "1.260 gradini ripidissimi fino al Buddha in cima: si sale all'alba "
                    "per evitare il caldo, e non è una passeggiata", "tier": MUST},
            {"name": "Isole Similan", "label": "Similan", "base": "phuket", "hours": 10.0,
             "slot": _MORNING,
             "how": "in speedboat dal nord di Phuket: le acque migliori della Thailandia "
                    "per lo snorkeling, con granito bianco e barriera intatta", "tier": EXTRA,
             "months": [10, 11, 12, 1, 2, 3, 4, 5],
             "note": "Il parco nazionale chiude durante la stagione dei monsoni, da metà maggio a metà ottobre."},
            {"name": "Sorgenti termali ed Emerald Pool", "label": "Emerald Pool",
             "base": "krabi", "hours": 5.0, "slot": _MORNING,
             "how": "nell'entroterra di Krabi: una pozza verde nella foresta e poco più in là "
                    "le cascate calde in cui ci si siede come in una vasca", "tier": EXTRA},
            {"name": "Wat Chalong", "base": "phuket", "hours": 2.0, "slot": None,
             "how": "il tempio più venerato dell'isola: chi vede esaudito un voto "
                    "fa scoppiare i petardi nel forno di mattoni all'ingresso", "tier": EXTRA},
            {"name": "Capo Promthep al tramonto", "label": "Promthep", "base": "phuket",
             "hours": 2.0, "slot": _EVENING,
             "how": "la punta sud dell'isola: si arriva mezz'ora prima perché "
                    "il parcheggio si riempie, e il sole cade dritto nell'Andamane",
             "tier": EXTRA},
            {"name": "Spiagge di Kata e Karon", "label": "Kata e Karon", "base": "phuket",
             "hours": 4.0, "slot": None,
             "how": "le due baie più larghe della costa ovest: mare piatto in inverno, "
                    "onde e bandiere rosse durante il monsone", "tier": EXTRA},
            {"name": "Incontro di muay thai", "label": "Muay thai", "base": "phuket",
             "hours": 2.5, "slot": _EVENING,
             "how": "combattimenti veri con la musica dal vivo che accelera a ogni ripresa: "
                    "i biglietti si comprano allo stadio la sera stessa", "tier": EXTRA},
            {"name": "Cena di pesce a Rawai", "label": "Rawai", "base": "phuket",
             "hours": 2.5, "slot": _EVENING,
             "how": "si sceglie il pesce vivo alle vasche del mercato sul molo e lo si porta "
                    "a un ristorante accanto, che lo cucina per una cifra simbolica",
             "tier": EXTRA},
            {"name": "Ao Nang la sera", "label": "Ao Nang", "base": "krabi", "hours": 2.0,
             "slot": _EVENING,
             "how": "il lungomare si riempie di banchi di frutta tagliata, massaggi "
                    "sul marciapiede e bar con le sedie rivolte verso il mare", "tier": EXTRA},
            {"name": "Koh Lanta in giornata", "label": "Koh Lanta", "base": "krabi",
             "hours": 8.0, "slot": _MORNING,
             "how": "traghetto da Krabi: isola lunga e tranquilla, con le spiagge del sud "
                    "quasi vuote e il vecchio quartiere cinese sul porto", "tier": EXTRA},
            {"name": "Spiagge di Tubkaek e Klong Muang", "label": "Tubkaek",
             "base": "krabi", "hours": 4.0, "slot": None,
             "how": "venti minuti a nord di Ao Nang: sabbia più fine e nessun venditore, "
                    "con le isole calcaree davanti", "tier": EXTRA},
            {"name": "Mangrovie di Krabi in longtail", "label": "Mangrovie", "base": "krabi",
             "hours": 3.0, "slot": None,
             "how": "si naviga tra le radici aeree fino alle grotte con le conchiglie "
                    "fossili di quaranta milioni di anni", "tier": EXTRA},
            {"name": "Mercato notturno di Krabi Town", "label": "Krabi Town",
             "base": "krabi", "hours": 2.5, "slot": _EVENING,
             "how": "nel fine settimana lungo il fiume: è il mercato dove mangiano i thailandesi, "
                    "con i prezzi di chi non vive di turismo", "tier": EXTRA},
        ],
        "variants": [
            {"days": 9, "title": "Andamane classiche",
             "for_who": "Phuket, Phi Phi e Railay: le isole simbolo con il tempo di goderle."},
            {"days": 13, "title": "Sud della Thailandia completo",
             "for_who": "Aggiunge le Similan, l'entroterra e le isole meno battute di Krabi."},
        ],
    },

    # =====================================================================
    # 47 — BANGKOK
    # =====================================================================
    47: {
        "bases": [
            {"key": "bangkok", "name": "Bangkok", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Traffico pesantissimo: si usano lo skytrain, la metro e i battelli "
                     "sul fiume, mai il taxi nelle ore di punta."},
        ],
        "places": [
            {"name": "Grande Palazzo e Wat Phra Kaew", "label": "Grande Palazzo",
             "base": "bangkok", "hours": 3.0, "slot": _MORNING,
             "how": "si entra all'apertura per il caldo: spalle e ginocchia coperte "
                    "obbligatoriamente, altrimenti non si passa il controllo", "tier": MUST},
            {"name": "Wat Pho e il Buddha sdraiato", "label": "Wat Pho", "base": "bangkok",
             "hours": 2.0, "slot": None,
             "how": "a piedi dal Grande Palazzo: quarantasei metri di Buddha dorato, "
                    "e nel complesso c'è la scuola di massaggio thailandese più antica",
             "tier": MUST},
            {"name": "Wat Arun al tramonto", "label": "Wat Arun", "base": "bangkok",
             "hours": 2.0, "slot": _EVENING,
             "how": "si attraversa il fiume col traghetto pubblico per pochi baht: "
                    "il tempio si illumina e si vede meglio dalla riva opposta", "tier": MUST},
            {"name": "Street food a Chinatown", "label": "Chinatown", "base": "bangkok",
             "hours": 3.0, "slot": _EVENING,
             "how": "Yaowarat Road si accende dopo le sette: si mangia in piedi "
                    "o ai tavolini di plastica, scegliendo i banchi con la fila di locali",
             "tier": MUST},
            {"name": "Giro in longtail sui khlong", "label": "Khlong", "base": "bangkok",
             "hours": 2.5, "slot": _MORNING,
             "how": "in barca a coda lunga nei canali di Thonburi: case su palafitte "
                    "e templi che si affacciano sull'acqua, lontano dai grattacieli",
             "tier": MUST},
            {"name": "Mercato del fine settimana di Chatuchak", "label": "Chatuchak",
             "base": "bangkok", "hours": 3.5, "slot": _MORNING,
             "how": "ottomila bancarelle in un labirinto di corridoi: apre solo "
                    "il sabato e la domenica, e serve mezza giornata piena", "tier": EXTRA},
            {"name": "Ayutthaya in giornata", "label": "Ayutthaya", "base": "bangkok",
             "hours": 8.0, "slot": _MORNING,
             "how": "un'ora e mezza di treno a nord: l'antica capitale in rovina, "
                    "si gira in bici tra i templi e la testa di Buddha tra le radici",
             "tier": EXTRA},
            {"name": "Mercato galleggiante di Damnoen Saduak", "label": "Mercato galleggiante",
             "base": "bangkok", "hours": 6.0, "slot": _MORNING,
             "how": "un'ora e mezza fuori città e bisogna arrivare prestissimo: "
                    "verso le nove è già solo un mercato per turisti", "tier": EXTRA},
            {"name": "Rooftop bar", "base": "bangkok", "hours": 2.0, "slot": _EVENING,
             "how": "sui tetti dei grattacieli lungo il fiume: c'è dress code, "
                    "niente infradito né canottiere, e si paga il panorama", "tier": EXTRA},
            {"name": "Massaggio thailandese tradizionale", "label": "Massaggio",
             "base": "bangkok", "hours": 1.5, "slot": _AFTERNOON,
             "how": "non è un massaggio rilassante: si viene piegati e stirati, "
                    "vestiti, su un materasso a terra", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Bangkok essenziale",
             "for_who": "Templi, fiume e street food: la capitale in quattro giorni."},
            {"days": 7, "title": "Bangkok e dintorni",
             "for_who": "Aggiunge i mercati, le rovine di Ayutthaya e i canali."},
        ],
    },

    # =====================================================================
    # 48 — BALI
    # =====================================================================
    48: {
        "bases": [
            {"key": "ubud", "name": "Ubud", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "L'entroterra tra risaie e templi: base per i vulcani, le cascate "
                     "e tutto quello che non è mare."},
            {"key": "canggu", "name": "Canggu", "night_weight": 2, "max_nights": 6,
             "transfer_h": 1.5,
             "note": "La costa sud-ovest: surf, tramonti e locali, con le spiagge "
                     "di sabbia scura vulcanica."},
        ],
        "places": [
            {"name": "Risaie di Tegallalang", "label": "Tegallalang", "base": "ubud",
             "hours": 3.0, "slot": _MORNING,
             "how": "terrazze a gradoni pochi chilometri a nord di Ubud: si scende "
                    "nel mezzo per un sentiero, e all'ingresso si lascia un'offerta",
             "tier": MUST},
            {"name": "Alba sul Monte Batur", "label": "Monte Batur", "base": "ubud",
             "hours": 8.0, "slot": _MORNING,
             "how": "partenza alle due di notte e due ore di salita con guida obbligatoria: "
                    "si arriva in vetta per l'alba sopra il lago e le nuvole", "tier": MUST},
            {"name": "Tempio di Tirta Empul", "label": "Tirta Empul", "base": "ubud",
             "hours": 2.5, "slot": None,
             "how": "il tempio della purificazione: si entra in acqua col sarong "
                    "e ci si mette sotto le fontane in fila, una dopo l'altra", "tier": MUST},
            {"name": "Foresta delle scimmie", "label": "Monkey Forest", "base": "ubud",
             "hours": 2.0, "slot": None,
             "how": "a piedi dal centro di Ubud: i macachi rubano occhiali e bottiglie, "
                    "quindi si entra con le tasche vuote e senza cibo", "tier": EXTRA},
            {"name": "Cascate di Tegenungan e Tibumana", "label": "Cascate", "base": "ubud",
             "hours": 4.0, "slot": None,
             "how": "in scooter o con autista: si scendono lunghe scalinate fino "
                    "alle pozze, e ci si bagna sotto il getto", "tier": EXTRA},
            {"name": "Cena balinese e danza tradizionale", "label": "Danza balinese",
             "base": "ubud", "hours": 2.5, "slot": _EVENING,
             "how": "spettacolo di legong o kecak al palazzo reale di Ubud, "
                    "preceduto dal babi guling o dal bebek betutu", "tier": MUST},
            {"name": "Tempio di Uluwatu e danza kecak", "label": "Uluwatu",
             "base": "canggu", "hours": 4.0, "slot": _EVENING,
             "how": "il tempio sulla falesia a settanta metri sul mare: la danza kecak "
                    "si tiene all'aperto proprio al tramonto, i biglietti si esauriscono",
             "tier": MUST},
            {"name": "Tanah Lot", "base": "canggu", "hours": 3.0, "slot": _EVENING,
             "how": "il tempio sullo scoglio, raggiungibile a piedi solo con la bassa marea: "
                    "con l'alta si guarda dalla riva ed è comunque lo scatto classico",
             "tier": MUST},
            {"name": "Lezione di surf a Canggu", "label": "Surf", "base": "canggu",
             "hours": 3.0, "slot": _MORNING,
             "how": "onde regolari e fondo sabbioso a Batu Bolong: è uno dei posti "
                    "migliori al mondo per imparare, con scuole ovunque sulla spiaggia",
             "tier": EXTRA},
            {"name": "Nusa Penida in giornata", "label": "Nusa Penida", "base": "canggu",
             "hours": 10.0, "slot": _MORNING,
             "how": "traghetto veloce da Sanur e poi scooter o autista sull'isola: "
                    "le strade sono pessime e le scogliere di Kelingking richiedono "
                    "una discesa ripida e faticosa", "tier": EXTRA},
            {"name": "Tempio Ulun Danu Beratan", "label": "Lago Bratan", "base": "ubud",
             "hours": 4.0, "slot": None,
             "how": "a 1.200 metri sul lago Bratan, dove fa davvero fresco: "
                    "quando il livello dell'acqua è alto il tempio sembra galleggiare",
             "tier": EXTRA},
            {"name": "Cascata di Sekumpul", "label": "Sekumpul", "base": "ubud",
             "hours": 6.0, "slot": _MORNING,
             "how": "la più alta di Bali, nel nord dell'isola: si scendono centinaia "
                    "di gradini e si guada il fiume, si torna bagnati e stanchi", "tier": EXTRA},
            {"name": "Campuhan Ridge Walk", "label": "Campuhan", "base": "ubud",
             "hours": 2.0, "slot": _MORNING,
             "how": "sentiero di cresta tra due valli, parte dal centro di Ubud: "
                    "si va all'alba, perché è tutto esposto e dalle nove è un forno",
             "tier": EXTRA},
            {"name": "Mercato d'arte di Ubud", "label": "Mercato di Ubud", "base": "ubud",
             "hours": 1.5, "slot": _MORNING,
             "how": "di fronte al palazzo reale: la mattina presto è ancora mercato "
                    "vero per i balinesi, dopo le nove diventa souvenir e si contratta",
             "tier": EXTRA},
            {"name": "Massaggio balinese", "label": "Massaggio", "base": "ubud", "hours": 1.5,
             "slot": _AFTERNOON,
             "how": "pressione profonda con olio di cocco, molto più intenso del thai: "
                    "nelle spa di Ubud costa una frazione che in Europa", "tier": EXTRA},
            {"name": "Cena di babi guling", "label": "Babi guling", "base": "ubud",
             "hours": 2.0, "slot": _EVENING,
             "how": "il maialino allo spiedo con le spezie: i locali storici finiscono "
                    "le porzioni entro il primo pomeriggio, quelli serali sono più turistici",
             "tier": EXTRA},
            {"name": "Tramonto a Seminyak", "label": "Seminyak", "base": "canggu",
             "hours": 3.0, "slot": _EVENING,
             "how": "beach club con i lettini sulla sabbia nera: si prenota il posto "
                    "per il tramonto, altrimenti alle cinque è tutto occupato", "tier": EXTRA},
            {"name": "Cena di pesce a Jimbaran", "label": "Jimbaran", "base": "canggu",
             "hours": 2.5, "slot": _EVENING,
             "how": "tavoli apparecchiati direttamente sulla sabbia con le lampade: "
                    "si sceglie il pesce a peso e lo grigliano sui gusci di cocco", "tier": EXTRA},
            {"name": "Alba a Sanur", "label": "Sanur", "base": "canggu", "hours": 2.0,
             "slot": _MORNING,
             "how": "l'unica costa rivolta a est: qui il sole sorge dal mare invece "
                    "di tramontarci, e la passeggiata lungomare è tutta pedonale", "tier": EXTRA},
            {"name": "Spiagge di Padang Padang e Bingin", "label": "Padang Padang",
             "base": "canggu", "hours": 4.0, "slot": None,
             "how": "cale incastrate sotto le falesie di Uluwatu: si scende per scalinate "
                    "strette nella roccia, e con l'alta marea la sabbia sparisce", "tier": EXTRA},
        ],
        "variants": [
            {"days": 9, "title": "Bali tra risaie e mare",
             "for_who": "Ubud, i templi e la costa del surf: l'isola in due basi."},
            {"days": 13, "title": "Bali senza fretta",
             "for_who": "Aggiunge i vulcani, le isole vicine e il tempo per il ritmo balinese."},
        ],
    },

    # =====================================================================
    # 49 — VIETNAM (HANOI, HA LONG, HOI AN)
    # Tre tappe lontanissime tra loro: tra il nord e il centro si vola,
    # non si guida.
    # =====================================================================
    49: {
        "bases": [
            {"key": "hanoi", "name": "Hanoi", "night_weight": 2, "max_nights": 5,
             "transfer_h": 0.0,
             "note": "La capitale del nord: base per la baia di Ha Long e per l'entroterra."},
            {"key": "halong", "name": "Baia di Ha Long", "night_weight": 1, "max_nights": 2,
             "transfer_h": 2.5,
             "note": "Si dorme a bordo della giunca: è l'unico modo di vedere la baia "
                     "all'alba, quando i battelli in giornata non sono ancora arrivati."},
            {"key": "hoian", "name": "Hoi An", "night_weight": 2, "max_nights": 6,
             "transfer_h": 3.5,
             "note": "Nel centro del paese: ci si arriva in aereo su Da Nang, "
                     "poi mezz'ora d'auto fino alla città vecchia."},
        ],
        "places": [
            {"name": "Città vecchia di Hanoi", "label": "Hanoi", "base": "hanoi",
             "hours": 3.0, "slot": None,
             "how": "a piedi nelle 36 vie delle corporazioni, dove ogni strada "
                    "vende ancora una merce sola: si attraversa camminando piano "
                    "e senza fermarsi, e i motorini scansano", "tier": MUST},
            {"name": "Mausoleo di Ho Chi Minh e Tempio della Letteratura", "label": "Ho Chi Minh",
             "base": "hanoi", "hours": 3.0, "slot": _MORNING,
             "how": "il mausoleo apre solo la mattina e chiude alcuni mesi l'anno "
                    "per manutenzione; abbigliamento coperto e silenzio obbligatori",
             "tier": MUST},
            {"name": "Cena di street food ad Hanoi", "label": "Street food",
             "base": "hanoi", "hours": 2.5, "slot": _EVENING,
             "how": "seduti su sgabelli di plastica sul marciapiede: pho, bun cha "
                    "e bia hoi, la birra alla spina servita fresca ogni giorno", "tier": MUST},
            {"name": "Spettacolo delle marionette sull'acqua", "label": "Marionette",
             "base": "hanoi", "hours": 1.5, "slot": _EVENING,
             "how": "un teatro con la scena allagata: i burattinai stanno immersi "
                    "dietro un paravento di bambù, e l'orchestra suona dal vivo", "tier": EXTRA},
            {"name": "Crociera nella baia di Ha Long", "label": "Ha Long", "base": "halong",
             "hours": 8.0, "slot": _MORNING,
             "how": "giunca con notte a bordo: si naviga tra i pinnacoli calcarei, "
                    "si entra in kayak nelle grotte e si dorme in mezzo alla baia",
             "tier": MUST},
            {"name": "Grotta Sung Sot", "label": "Grotte di Ha Long", "base": "halong",
             "hours": 2.5, "slot": None,
             "how": "si sbarca e si salgono scalinate umide dentro l'isola: "
                    "tre camere enormi illuminate, con il soffitto a decine di metri",
             "tier": EXTRA},
            {"name": "Città vecchia di Hoi An", "label": "Hoi An", "base": "hoian",
             "hours": 3.0, "slot": _EVENING,
             "how": "al tramonto si accendono migliaia di lanterne di seta e le auto "
                    "sono vietate: si cammina e si mandano le candele sul fiume", "tier": MUST},
            {"name": "Ponte giapponese e case dei mercanti", "label": "Ponte giapponese",
             "base": "hoian", "hours": 2.5, "slot": _MORNING,
             "how": "biglietto cumulativo che dà accesso a cinque monumenti a scelta "
                    "nella città vecchia, comprese le case di famiglia ancora abitate",
             "tier": MUST},
            {"name": "Spiaggia di An Bang", "label": "An Bang", "base": "hoian", "hours": 4.0,
             "slot": None,
             "how": "quindici minuti di bicicletta dalla città vecchia: sabbia larga "
                    "e chiringuiti di bambù, il pomeriggio libero classico di Hoi An",
             "tier": MUST},
            {"name": "Sartoria su misura a Hoi An", "label": "Sartoria", "base": "hoian",
             "hours": 2.0, "slot": None,
             "how": "si sceglie il tessuto, si prende la misura e in ventiquattro ore "
                    "l'abito è pronto: conviene ordinare il primo giorno di permanenza",
             "tier": EXTRA},
            {"name": "Santuario di My Son", "label": "My Son", "base": "hoian", "hours": 5.0,
             "slot": _MORNING,
             "how": "un'ora d'auto nell'entroterra: templi cham in mattoni rossi "
                    "nella giungla, si va all'alba per il caldo e per la luce", "tier": EXTRA},
            {"name": "Lago Hoan Kiem e tempio Ngoc Son", "label": "Hoan Kiem",
             "base": "hanoi", "hours": 2.0, "slot": _MORNING,
             "how": "alle sei del mattino gli anziani fanno tai chi lungo la riva: "
                    "al tempio sull'isolotto si arriva per il ponte rosso di legno",
             "tier": EXTRA},
            {"name": "Prigione di Hoa Lo", "label": "Hoa Lo", "base": "hanoi", "hours": 2.0,
             "slot": None,
             "how": "carcere coloniale francese e poi prigione dei piloti americani: "
                    "il racconto è dichiaratamente di parte, e vale anche per questo",
             "tier": EXTRA},
            {"name": "Ninh Binh in giornata", "label": "Ninh Binh", "base": "hanoi",
             "hours": 8.0, "slot": _MORNING,
             "how": "due ore a sud: si naviga in barca a remi tra i pinnacoli calcarei "
                    "che escono dalle risaie, e le rematrici usano i piedi", "tier": EXTRA},
            {"name": "Caffè all'uovo", "label": "Ca phe trung", "base": "hanoi", "hours": 1.0,
             "slot": None,
             "how": "tuorlo montato con latte condensato sopra il caffè bollente: "
                    "si beve nei locali storici nascosti in fondo a corridoi stretti",
             "tier": EXTRA},
            {"name": "Alba sul ponte della giunca", "label": "Alba a Ha Long",
             "base": "halong", "hours": 1.5, "slot": _MORNING,
             "how": "si sale in coperta verso le sei per il tai chi e per la foschia "
                    "che si alza tra i pinnacoli: è il motivo per cui si dorme a bordo",
             "tier": EXTRA},
            {"name": "Villaggio galleggiante di Cua Van", "label": "Cua Van",
             "base": "halong", "hours": 2.0, "slot": None,
             "how": "in barca a remi tra le case galleggianti dei pescatori, "
                    "con la scuola e il centro culturale costruiti sull'acqua", "tier": EXTRA},
            {"name": "Villaggio di erbe di Tra Que", "label": "Tra Que", "base": "hoian",
             "hours": 3.0, "slot": _MORNING,
             "how": "in bici da Hoi An tra gli orti: si zappa e si annaffia con i contadini "
                    "usando i bilancieri, e poi si cucina quello che si è raccolto",
             "tier": EXTRA},
            {"name": "Barca delle lanterne sul Thu Bon", "label": "Lanterne sul fiume",
             "base": "hoian", "hours": 1.5, "slot": _EVENING,
             "how": "mezz'ora in barca a remi dopo il tramonto: si compra una candela "
                    "di carta e la si lascia andare sulla corrente", "tier": EXTRA},
            {"name": "Passo di Hai Van e Da Nang", "label": "Hai Van", "base": "hoian",
             "hours": 5.0, "slot": None,
             "how": "la strada di montagna a picco sul mare verso nord, con i bunker "
                    "in cima al passo; sulla via c'è il Ponte d'Oro sorretto dalle mani giganti",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 9, "title": "Vietnam dal nord al centro",
             "for_who": "Hanoi, una notte in giunca a Ha Long e le lanterne di Hoi An."},
            {"days": 13, "title": "Vietnam con calma",
             "for_who": "Aggiunge i templi cham, le spiagge e il tempo per i mercati."},
        ],
    },

    # =====================================================================
    # 50 — SRI LANKA (COLOMBO, ELLA, MIRISSA)
    # =====================================================================
    50: {
        "bases": [
            {"key": "kandy", "name": "Kandy", "night_weight": 1, "max_nights": 3,
             "transfer_h": 0.0,
             "note": "Nel centro dell'isola: la città sacra e il punto da cui parte "
                     "il treno panoramico verso le montagne."},
            {"key": "ella", "name": "Ella", "night_weight": 1, "max_nights": 4,
             "transfer_h": 3.0,
             "note": "Sugli altopiani a 1.000 metri: fa fresco anche in piena stagione, "
                     "e si arriva col treno più bello del paese."},
            {"key": "mirissa", "name": "Mirissa", "night_weight": 2, "max_nights": 6,
             "transfer_h": 3.5,
             "note": "Sulla costa sud: spiagge, surf e le uscite per le balene."},
        ],
        "places": [
            {"name": "Tempio del Dente di Buddha", "label": "Kandy", "base": "kandy",
             "hours": 2.5, "slot": _EVENING,
             "how": "si entra a piedi nudi e coperti, durante una delle tre puja "
                    "quotidiane, quando si apre la teca della reliquia", "tier": MUST},
            {"name": "Giardini botanici di Peradeniya", "label": "Peradeniya",
             "base": "kandy", "hours": 3.0, "slot": None,
             "how": "poco fuori Kandy in tuk-tuk: sessanta ettari con l'avenue di palme "
                    "e il ficus gigante, si gira lentamente all'ombra", "tier": EXTRA},
            {"name": "Rocca di Sigiriya", "label": "Sigiriya", "base": "kandy", "hours": 6.0,
             "slot": _MORNING,
             "how": "1.200 gradini su una rocca alta duecento metri: si sale all'apertura, "
                    "alle sette, perché dopo il caldo sulle scale di metallo è insopportabile",
             "tier": MUST},
            {"name": "Treno panoramico da Kandy a Ella", "label": "Treno per Ella",
             "base": "ella", "hours": 7.0, "slot": _MORNING,
             "how": "sette ore tra le piantagioni di tè, seduti sulla porta aperta: "
                    "i posti in seconda classe riservata si comprano con giorni di anticipo",
             "tier": MUST},
            {"name": "Nine Arches Bridge", "label": "Nine Arches", "base": "ella",
             "hours": 2.5, "slot": _MORNING,
             "how": "venti minuti a piedi dal paese tra le piantagioni: si aspetta "
                    "il passaggio del treno sul viadotto di pietra, gli orari sono affissi in stazione",
             "tier": MUST},
            {"name": "Little Adam's Peak", "label": "Little Adam's Peak", "base": "ella",
             "hours": 3.0, "slot": _MORNING,
             "how": "un'ora di salita facile con vista sulla gola di Ella: "
                    "si parte all'alba per trovare il cielo libero dalle nuvole", "tier": MUST},
            {"name": "Fabbrica del tè di Ceylon", "label": "Piantagione di tè",
             "base": "ella", "hours": 2.5, "slot": None,
             "how": "visita alla lavorazione e degustazione: si vedono le raccoglitrici "
                    "al lavoro sui pendii con le ceste sulla schiena", "tier": EXTRA},
            {"name": "Avvistamento balene a Mirissa", "label": "Balene", "base": "mirissa",
             "hours": 5.0, "slot": _MORNING,
             "how": "si esce all'alba dal porto: al largo passano le balenottere azzurre, "
                    "il mare si alza presto quindi si rientra a metà mattina", "tier": MUST,
             "months": [11, 12, 1, 2, 3, 4],
             "note": "La stagione delle balene sulla costa sud va da novembre ad aprile; "
                     "negli altri mesi il monsone chiude le uscite."},
            {"name": "Spiaggia di Mirissa", "base": "mirissa", "hours": 5.0, "slot": None,
             "how": "baia a mezzaluna con la collina delle palme all'estremità: "
                    "la corrente è forte, si nuota nella parte riparata", "tier": MUST},
            {"name": "Galle e le mura olandesi", "label": "Galle", "base": "mirissa",
             "hours": 4.0, "slot": None,
             "how": "quaranta minuti lungo la costa: il forte coloniale si gira "
                    "camminando sui bastioni, meglio nel tardo pomeriggio", "tier": MUST},
            {"name": "Cena di rice and curry", "base": "mirissa", "hours": 2.0,
             "slot": _EVENING,
             "how": "non è un piatto ma dieci ciotoline attorno al riso: si mangia "
                    "con la mano destra, mescolando poco alla volta", "tier": EXTRA},
            {"name": "Tempio d'oro di Dambulla", "label": "Dambulla", "base": "kandy",
             "hours": 3.0, "slot": None,
             "how": "cinque grotte scavate nella roccia con centocinquanta statue "
                    "di Buddha e soffitti dipinti: si sale una scalinata e si entra scalzi",
             "tier": MUST},
            {"name": "Spettacolo di danza kandyana", "label": "Danza kandyana",
             "base": "kandy", "hours": 1.5, "slot": _EVENING,
             "how": "tamburi, maschere e la camminata finale sui carboni ardenti: "
                    "gli spettacoli iniziano nel tardo pomeriggio e durano un'ora", "tier": EXTRA},
            {"name": "Parco nazionale di Minneriya", "label": "Minneriya", "base": "kandy",
             "hours": 5.0, "slot": _AFTERNOON,
             "how": "safari nel pomeriggio quando gli elefanti scendono al bacino: "
                    "nella stagione secca se ne radunano anche trecento insieme", "tier": EXTRA,
             "months": [6, 7, 8, 9, 10],
             "note": "Il grande raduno avviene solo nella stagione secca, quando il lago si ritira."},
            {"name": "Ella Rock", "base": "ella", "hours": 4.0, "slot": _MORNING,
             "how": "quattro ore tra andata e ritorno camminando prima sui binari "
                    "e poi nella foresta: il sentiero non è segnato, conviene una guida",
             "tier": EXTRA},
            {"name": "Cascata Ravana", "label": "Ravana", "base": "ella", "hours": 1.5,
             "slot": None,
             "how": "si vede dalla strada che scende da Ella: ci si ferma in piazzola "
                    "e si scende agli scogli, ma le rocce sono scivolose", "tier": EXTRA},
            {"name": "Cena vista gola a Ella", "label": "Ella", "base": "ella", "hours": 2.0,
             "slot": _EVENING,
             "how": "i ristoranti sono affacciati sulla valle e la sera si accendono "
                    "le luci nelle piantagioni: si mangia kottu preparato a colpi di lama",
             "tier": EXTRA},
            {"name": "Coconut Tree Hill", "base": "mirissa", "hours": 1.5, "slot": _EVENING,
             "how": "il promontorio di palme all'estremità della baia: si arriva a piedi "
                    "in dieci minuti, ed è il posto del tramonto per tutti", "tier": EXTRA},
            {"name": "Surf a Weligama", "label": "Weligama", "base": "mirissa", "hours": 3.0,
             "slot": _MORNING,
             "how": "baia riparata con onde lente e fondo sabbioso: è dove impara "
                    "chi non ha mai preso una tavola, e le scuole sono sulla spiaggia",
             "tier": EXTRA},
            {"name": "Safari nel parco di Yala", "label": "Yala", "base": "mirissa",
             "hours": 8.0, "slot": _MORNING,
             "how": "partenza prima dell'alba in jeep: è il parco con la più alta densità "
                    "di leopardi al mondo, ma restano animali selvatici e non si garantisce nulla",
             "tier": EXTRA, "months": [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12],
             "note": "Il settore principale del parco chiude per manutenzione durante il mese di settembre."},
        ],
        "variants": [
            {"days": 9, "title": "Sri Lanka dal centro al sud",
             "for_who": "Kandy, il treno per Ella e la costa: l'isola in tre tappe."},
            {"days": 13, "title": "Sri Lanka completo",
             "for_who": "Aggiunge Sigiriya, le piantagioni e il tempo per il mare."},
        ],
    },

    # =====================================================================
    # 51 — MALDIVE
    # Qui non ci sono itinerari: c'è un'isola e quello che ci si fa dentro.
    # =====================================================================
    51: {
        "bases": [
            {"key": "atollo", "name": "Isola-resort", "night_weight": 1, "max_nights": 14,
             "transfer_h": 0.0,
             "note": "Si resta sulla stessa isola per tutto il soggiorno: le escursioni "
                     "si prenotano al desk e partono dal molo del resort."},
        ],
        "places": [
            {"name": "Snorkeling sulla barriera di casa", "label": "House reef",
             "base": "atollo", "hours": 3.0, "slot": None,
             "how": "si entra in acqua direttamente dalla spiaggia: la barriera del resort "
                    "comincia a pochi metri e non serve barca", "tier": MUST},
            {"name": "Uscita con le mante", "label": "Mante", "base": "atollo", "hours": 4.0,
             "slot": _MORNING,
             "how": "in dhoni fino ai punti di pulizia dove le mante si fermano: "
                    "si nuota in superficie senza toccarle e senza inseguirle", "tier": MUST},
            {"name": "Immersione o snorkeling con gli squali balena", "label": "Squali balena",
             "base": "atollo", "hours": 5.0, "slot": _MORNING,
             "how": "escursione più lunga verso gli atolli dove passano: sono innocui "
                    "e filtrano plancton, ma si resta a distanza per non stressarli",
             "tier": MUST},
            {"name": "Tramonto in dhoni", "label": "Dhoni al tramonto", "base": "atollo",
             "hours": 2.0, "slot": _EVENING,
             "how": "in barca tradizionale di legno, spesso con avvistamento di delfini "
                    "che seguono la prua", "tier": MUST},
            {"name": "Cena sulla sabbia", "label": "Cena in spiaggia", "base": "atollo",
             "hours": 2.5, "slot": _EVENING,
             "how": "tavolo apparecchiato sulla battigia con le lanterne: si prenota "
                    "al mattino, e nei resort è il classico regalo per gli anniversari",
             "tier": MUST},
            {"name": "Spa sull'acqua", "label": "Spa", "base": "atollo", "hours": 2.5,
             "slot": _AFTERNOON,
             "how": "cabine sospese sulla laguna col pavimento di vetro: si guarda "
                    "il fondale mentre si sta sdraiati", "tier": EXTRA},
            {"name": "Banco di sabbia deserto", "label": "Sandbank", "base": "atollo",
             "hours": 4.0, "slot": None,
             "how": "si viene lasciati in barca su una lingua di sabbia in mezzo al nulla "
                    "e ripresi dopo qualche ora: non c'è ombra, serve tutto da casa",
             "tier": EXTRA},
            {"name": "Visita a un'isola locale", "label": "Isola locale", "base": "atollo",
             "hours": 4.0, "slot": None,
             "how": "in barca fino a un villaggio abitato: qui valgono le regole locali, "
                    "niente bikini fuori dalla bikini beach e niente alcol", "tier": EXTRA},
            {"name": "Kayak trasparente sulla laguna", "label": "Kayak", "base": "atollo",
             "hours": 2.0, "slot": None,
             "how": "compreso nella maggior parte dei resort: sul fondo di vetro "
                    "si vedono le razze passare sotto lo scafo", "tier": EXTRA},
            {"name": "Plancton bioluminescente", "label": "Mare stellato", "base": "atollo",
             "hours": 1.5, "slot": _EVENING,
             "how": "in certe notti senza luna la battigia si illumina di puntini blu "
                    "quando l'onda si rompe: non è garantito, dipende dalle correnti",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Maldive essenziali",
             "for_who": "Barriera, laguna e tramonti: il soggiorno breve senza spostarsi mai."},
            {"days": 8, "title": "Maldive tra oceano e atolli",
             "for_who": "Aggiunge le escursioni ai grandi pelagici e le isole abitate."},
        ],
    },

    # =====================================================================
    # 52 — NEW YORK
    # =====================================================================
    52: {
        "bases": [
            {"key": "manhattan", "name": "Manhattan", "night_weight": 1, "max_nights": 14,
             "transfer_h": 0.0,
             "note": "Metropolitana 24 ore su 24: conviene una MetroCard settimanale, "
                     "ma tra una attrazione e l'altra spesso si cammina."},
        ],
        "places": [
            {"name": "Central Park", "base": "manhattan", "hours": 3.0, "slot": _MORNING,
             "how": "si entra da Columbus Circle e si esce dal Met: quattro chilometri "
                    "a piedi tra i laghi, o in bici noleggiata agli ingressi", "tier": MUST},
            {"name": "Top of the Rock o Empire State Building", "label": "Skyline dall'alto",
             "base": "manhattan", "hours": 2.0, "slot": _EVENING,
             "how": "il Rockefeller ha il vantaggio di inquadrare l'Empire State "
                    "nella foto; biglietti a orario, e il tramonto si esaurisce per primo",
             "tier": MUST},
            {"name": "Statua della Libertà ed Ellis Island", "label": "Statua della Libertà",
             "base": "manhattan", "hours": 5.0, "slot": _MORNING,
             "how": "traghetto da Battery Park con controlli come in aeroporto: "
                    "per salire nella corona serve un biglietto a parte, mesi prima",
             "tier": MUST},
            {"name": "Ponte di Brooklyn a piedi", "label": "Brooklyn Bridge",
             "base": "manhattan", "hours": 2.5, "slot": _EVENING,
             "how": "si attraversa da Brooklyn verso Manhattan per avere lo skyline "
                    "davanti: la passerella pedonale è sopra il traffico", "tier": MUST},
            {"name": "Times Square e Broadway", "label": "Times Square", "base": "manhattan",
             "hours": 2.5, "slot": _EVENING,
             "how": "i biglietti dei musical scontati si comprano allo stand TKTS "
                    "in piazza il giorno stesso, mettendosi in fila nel pomeriggio",
             "tier": MUST},
            {"name": "Metropolitan Museum", "label": "Met", "base": "manhattan", "hours": 3.5,
             "slot": None,
             "how": "il biglietto è a offerta libera per i residenti dello stato, "
                    "a prezzo pieno per gli altri: in un giorno si vede un'ala, non tutto",
             "tier": EXTRA},
            {"name": "High Line e Chelsea Market", "label": "High Line", "base": "manhattan",
             "hours": 2.5, "slot": None,
             "how": "ex ferrovia sopraelevata trasformata in giardino lineare: "
                    "si cammina sopra le strade e si scende dentro il mercato coperto",
             "tier": EXTRA},
            {"name": "Memoriale dell'11 settembre", "label": "Ground Zero",
             "base": "manhattan", "hours": 2.5, "slot": None,
             "how": "le due vasche sono all'aperto e gratuite; il museo sotterraneo "
                    "si paga e richiede almeno due ore", "tier": EXTRA},
            {"name": "Williamsburg", "base": "manhattan", "hours": 3.0, "slot": None,
             "how": "una fermata di metro sotto l'East River: negozi vintage, murales "
                    "e la vista migliore su Manhattan dai moli di Domino Park", "tier": EXTRA},
            {"name": "Pista di pattinaggio e vetrine di Natale", "label": "Natale a New York",
             "base": "manhattan", "hours": 2.5, "slot": _EVENING,
             "how": "l'albero del Rockefeller Center, le vetrine animate dei grandi magazzini "
                    "sulla Fifth Avenue e le piste di pattinaggio nei parchi", "tier": EXTRA,
             "months": [11, 12, 1],
             "note": "Albero, vetrine e piste all'aperto ci sono solo tra fine novembre e inizio gennaio."},
        ],
        "variants": [
            {"days": 5, "title": "New York la prima volta",
             "for_who": "Skyline, Central Park, Statua della Libertà: le icone in cinque giorni."},
            {"days": 8, "title": "New York per quartieri",
             "for_who": "Aggiunge i musei, Brooklyn e il tempo per vivere i quartieri."},
        ],
    },

    # =====================================================================
    # 53 — MIAMI
    # =====================================================================
    53: {
        "bases": [
            {"key": "southbeach", "name": "South Beach", "night_weight": 1, "max_nights": 14,
             "transfer_h": 0.0,
             "note": "Sulla penisola di Miami Beach: si cammina lungo l'oceano, "
                     "ma per la città e le Everglades serve l'auto."},
        ],
        "places": [
            {"name": "South Beach e il distretto Art Déco", "label": "Art Déco",
             "base": "southbeach", "hours": 3.0, "slot": _MORNING,
             "how": "a piedi su Ocean Drive tra gli hotel anni Trenta: la visita guidata "
                    "del centro Art Déco parte ogni mattina e spiega cosa si sta guardando",
             "tier": MUST},
            {"name": "Wynwood Walls", "label": "Wynwood", "base": "southbeach", "hours": 3.0,
             "slot": None,
             "how": "ex quartiere industriale coperto di murales: si gira a piedi "
                    "tra i magazzini, ed è pieno di birrifici e caffè", "tier": MUST},
            {"name": "Little Havana e Calle Ocho", "label": "Little Havana",
             "base": "southbeach", "hours": 2.5, "slot": None,
             "how": "a piedi lungo la Calle Ocho: si beve il cafecito al bancone "
                    "e si guardano i vecchi giocare a domino nel parco", "tier": MUST},
            {"name": "Everglades in airboat", "label": "Everglades", "base": "southbeach",
             "hours": 5.0, "slot": _MORNING,
             "how": "un'ora d'auto a ovest: idroscivolante tra le erbe di sawgrass "
                    "per vedere gli alligatori, e si esce presto per il caldo", "tier": MUST},
            {"name": "Serata a Ocean Drive", "label": "Ocean Drive", "base": "southbeach",
             "hours": 2.5, "slot": _EVENING,
             "how": "le insegne al neon si accendono e la strada diventa una passerella: "
                    "si mangia meglio nelle vie interne che sul lungomare", "tier": MUST},
            {"name": "Vizcaya Museum and Gardens", "label": "Vizcaya", "base": "southbeach",
             "hours": 2.5, "slot": None,
             "how": "villa italiana costruita da un industriale americano sulla baia, "
                    "con i giardini all'italiana che scendono all'acqua", "tier": EXTRA},
            {"name": "Key Biscayne", "base": "southbeach", "hours": 4.0, "slot": None,
             "how": "si attraversa il ponte a pedaggio: spiagge molto più tranquille "
                    "di South Beach, con il faro all'estremità dell'isola", "tier": EXTRA},
            {"name": "Design District", "base": "southbeach", "hours": 2.0, "slot": None,
             "how": "boutique, gallerie e installazioni all'aperto: si guarda anche "
                    "solo camminando, e l'architettura è parte dell'attrazione", "tier": EXTRA},
            {"name": "Key Largo in giornata", "label": "Key Largo", "base": "southbeach",
             "hours": 7.0, "slot": _MORNING,
             "how": "un'ora e mezza a sud sull'Overseas Highway: snorkeling sulla barriera "
                    "corallina del parco statale, l'unica viva degli Stati Uniti continentali",
             "tier": EXTRA},
            {"name": "Cena cubana", "base": "southbeach", "hours": 2.5, "slot": _EVENING,
             "how": "ropa vieja, tostones e mojito nei ristoranti di Little Havana, "
                    "spesso con musica dal vivo dopo cena", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Miami tra spiagge e murales",
             "for_who": "Art Déco, Wynwood e Little Havana: la città in cinque giorni."},
            {"days": 8, "title": "Miami e la Florida del sud",
             "for_who": "Aggiunge le Everglades, le Keys e le isole della baia."},
        ],
    },

    # =====================================================================
    # 54 — CITTÀ DEL MESSICO
    # =====================================================================
    54: {
        "bases": [
            {"key": "cdmx", "name": "Città del Messico", "night_weight": 1, "max_nights": 14,
             "transfer_h": 0.0,
             "note": "Megalopoli a 2.240 metri: si dorme nei quartieri Roma o Condesa "
                     "e ci si muove in metro, evitando l'auto nelle ore di punta."},
        ],
        "places": [
            {"name": "Zócalo e Templo Mayor", "label": "Centro storico", "base": "cdmx",
             "hours": 3.5, "slot": _MORNING,
             "how": "la piazza enorme con la cattedrale che sprofonda lentamente, "
                    "e accanto le rovine del tempio azteco scoperte scavando per la metro",
             "tier": MUST},
            {"name": "Teotihuacán", "base": "cdmx", "hours": 6.0, "slot": _MORNING,
             "how": "un'ora di autobus a nord: si percorre a piedi la Calzada dei Morti "
                    "tra le due piramidi, e alle nove il sole è già forte", "tier": MUST},
            {"name": "Museo Nazionale di Antropologia", "label": "Antropologia",
             "base": "cdmx", "hours": 3.5, "slot": None,
             "how": "nel parco di Chapultepec: è enorme, conviene concentrarsi sulle sale "
                    "azteca e maya, dove c'è la pietra del sole", "tier": MUST},
            {"name": "Casa Azul di Frida Kahlo", "label": "Frida Kahlo", "base": "cdmx",
             "hours": 2.5, "slot": None,
             "how": "a Coyoacán, biglietto nominativo online che va comprato con settimane "
                    "di anticipo: si visita la casa dove ha vissuto e lo studio", "tier": MUST},
            {"name": "Xochimilco", "base": "cdmx", "hours": 4.0, "slot": None,
             "how": "sui canali si affittano le trajineras colorate a ore: si va in gruppo, "
                    "e le barche dei mariachi si accostano per suonare a pagamento",
             "tier": MUST},
            {"name": "Coyoacán", "base": "cdmx", "hours": 2.5, "slot": None,
             "how": "a piedi tra le case coloniali e il mercato: si mangiano le tostadas "
                    "al banco e si beve l'agua fresca del giorno", "tier": EXTRA},
            {"name": "Cena di tacos al pastor", "label": "Tacos", "base": "cdmx",
             "hours": 2.0, "slot": _EVENING,
             "how": "in piedi alla taqueria, dove la carne gira sul trompo e l'ananas "
                    "viene tagliato al volo sopra il taco", "tier": MUST},
            {"name": "Palacio de Bellas Artes", "label": "Bellas Artes", "base": "cdmx",
             "hours": 2.0, "slot": None,
             "how": "i murales di Rivera e Siqueiros ai piani alti; dal bar del palazzo "
                    "postale di fronte si fotografa la cupola dall'alto", "tier": EXTRA},
            {"name": "Lucha libre", "base": "cdmx", "hours": 3.0, "slot": _EVENING,
             "how": "all'Arena México nelle sere di combattimento: si tifa, si urla "
                    "e non si fotografano i lottatori senza maschera", "tier": EXTRA},
            {"name": "Día de Muertos", "label": "Día de Muertos", "base": "cdmx",
             "hours": 4.0, "slot": _EVENING,
             "how": "altari nelle piazze, sfilata in centro e cimiteri illuminati "
                    "di candele: la città si trasforma completamente", "tier": EXTRA,
             "months": [10, 11],
             "note": "Le celebrazioni si concentrano tra il 31 ottobre e il 2 novembre."},
            {"name": "Castello di Chapultepec", "label": "Chapultepec", "base": "cdmx",
             "hours": 2.5, "slot": None,
             "how": "si sale a piedi per la rampa nel bosco: è l'unico castello reale "
                    "delle Americhe, e la terrazza guarda dritta sul Paseo de la Reforma",
             "tier": MUST},
            {"name": "Basilica di Guadalupe", "label": "Guadalupe", "base": "cdmx",
             "hours": 3.0, "slot": _MORNING,
             "how": "il santuario più visitato dell'America Latina: davanti al manto "
                    "si passa su un tappeto mobile, perché nessuno possa fermarsi",
             "tier": EXTRA},
            {"name": "Torre Latinoamericana", "label": "Torre Latinoamericana",
             "base": "cdmx", "hours": 1.5, "slot": _EVENING,
             "how": "il grattacielo che ha resistito a tutti i terremoti: dal mirador "
                    "all'ultimo piano si vede quanto è sterminata questa città", "tier": EXTRA},
            {"name": "Quartieri Roma e Condesa", "label": "Roma e Condesa", "base": "cdmx",
             "hours": 2.5, "slot": None,
             "how": "a piedi tra i viali alberati e le case liberty: è la zona "
                    "delle librerie, dei caffè e dei ristoranti di ricerca", "tier": MUST},
            {"name": "Mercato di San Juan", "label": "San Juan", "base": "cdmx", "hours": 2.0,
             "slot": _MORNING,
             "how": "il mercato gastronomico storico: formaggi, insetti commestibili "
                    "e banchi dove ti preparano il panino con quello che scegli", "tier": EXTRA},
            {"name": "Museo Soumaya", "label": "Soumaya", "base": "cdmx", "hours": 2.0,
             "slot": None,
             "how": "l'edificio rivestito di esagoni d'alluminio a Polanco: ingresso "
                    "gratuito, e la rampa a spirale sale fino alla collezione Rodin", "tier": EXTRA},
            {"name": "Cantina storica del centro", "label": "Cantina", "base": "cdmx",
             "hours": 2.0, "slot": _EVENING,
             "how": "le cantinas del centro servono la botana gratis finché si beve: "
                    "si prova il mezcal accompagnato da arancia e sale di verme", "tier": EXTRA},
            {"name": "Cena di mole a San Ángel", "label": "San Ángel", "base": "cdmx",
             "hours": 2.5, "slot": _EVENING,
             "how": "quartiere coloniale a sud con le case in pietra vulcanica: "
                    "il mole poblano ha decine di ingredienti e si cuoce per ore", "tier": EXTRA},
            {"name": "Puebla e Cholula in giornata", "label": "Puebla", "base": "cdmx",
             "hours": 9.0, "slot": _MORNING,
             "how": "due ore di autobus a est: il centro barocco rivestito di azulejos "
                    "e la piramide di Cholula, la più grande al mondo per volume", "tier": EXTRA},
            {"name": "Museo Anahuacalli", "label": "Anahuacalli", "base": "cdmx",
             "hours": 2.0, "slot": None,
             "how": "il museo di pietra lavica che Diego Rivera costruì per la sua "
                    "collezione precolombiana: buio, silenzioso e quasi senza visitatori",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 6, "title": "Città del Messico essenziale",
             "for_who": "Centro storico, Teotihuacán e Frida: la capitale in sei giorni."},
            {"days": 9, "title": "Città del Messico a fondo",
             "for_who": "Aggiunge i quartieri coloniali, i canali e le serate di lucha libre."},
        ],
    },

    # =====================================================================
    # 55 — L'AVANA (CUBA)
    # =====================================================================
    55: {
        "bases": [
            {"key": "avana", "name": "L'Avana", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "Si dorme in casa particular, non in hotel: è più economico "
                     "ed è l'unico modo di stare davvero dentro la città."},
            {"key": "vinales", "name": "Viñales", "night_weight": 1, "max_nights": 3,
             "transfer_h": 2.5,
             "note": "Due ore e mezza a ovest: la valle del tabacco, con i mogotes "
                     "e i ritmi di campagna."},
        ],
        "places": [
            {"name": "Habana Vieja", "label": "Habana Vieja", "base": "avana", "hours": 3.0,
             "slot": _MORNING,
             "how": "a piedi tra le quattro piazze coloniali restaurate: appena si esce "
                    "dal perimetro UNESCO la città cambia completamente faccia", "tier": MUST},
            {"name": "Malecón al tramonto", "label": "Malecón", "base": "avana", "hours": 2.0,
             "slot": _EVENING,
             "how": "otto chilometri di muretto sul mare dove l'Avana si siede la sera: "
                    "si cammina e basta, ed è gratis", "tier": MUST},
            {"name": "Giro in auto americana d'epoca", "label": "Auto d'epoca",
             "base": "avana", "hours": 2.0, "slot": None,
             "how": "cabriolet degli anni Cinquanta con autista: si contratta il prezzo "
                    "prima di salire, e il giro classico tocca Vedado e Plaza de la Revolución",
             "tier": MUST},
            {"name": "Serata di musica dal vivo", "label": "Son cubano", "base": "avana",
             "hours": 2.5, "slot": _EVENING,
             "how": "nelle case de la música e nei bar della Habana Vieja si suona son "
                    "e salsa dal vivo tutte le sere, spesso senza biglietto d'ingresso",
             "tier": MUST},
            {"name": "Fusterlandia", "base": "avana", "hours": 2.0, "slot": None,
             "how": "un intero quartiere periferico rivestito di mosaici da un solo artista: "
                    "si arriva in taxi e si gira a piedi tra le case decorate", "tier": EXTRA},
            {"name": "Fortezza del Morro e cañonazo", "label": "El Morro", "base": "avana",
             "hours": 3.0, "slot": _EVENING,
             "how": "dall'altra parte della baia: ogni sera alle nove i soldati in divisa "
                    "settecentesca sparano il colpo di cannone, come da tre secoli", "tier": EXTRA},
            {"name": "Valle di Viñales", "label": "Viñales", "base": "vinales", "hours": 5.0,
             "slot": _MORNING,
             "how": "a cavallo o in bici tra i campi di tabacco e i mogotes, "
                    "le colline a pan di zucchero: si visita una casa del tabacco "
                    "e si vede arrotolare il sigaro a mano", "tier": MUST},
            {"name": "Grotta dell'Indio", "label": "Cueva del Indio", "base": "vinales",
             "hours": 2.0, "slot": None,
             "how": "si entra a piedi e si esce in barca lungo il fiume sotterraneo, "
                    "pochi minuti di navigazione dentro la roccia", "tier": EXTRA},
            {"name": "Cayo Jutías", "base": "vinales", "hours": 5.0, "slot": None,
             "how": "un'ora di strada dalla valle: spiaggia bianca su una lingua di terra, "
                    "quasi senza costruzioni e con pochissimi servizi", "tier": EXTRA},
            {"name": "Cena in paladar", "label": "Paladar", "base": "vinales", "hours": 2.5,
             "slot": _EVENING,
             "how": "i ristoranti privati di famiglia: si mangia molto meglio che nei locali "
                    "statali, spesso in terrazza e con quello che c'è quel giorno", "tier": EXTRA},
            {"name": "Vedado e Plaza de la Revolución", "label": "Vedado", "base": "avana",
             "hours": 2.5, "slot": None,
             "how": "il quartiere delle ville anni Cinquanta e dei grandi viali: "
                    "in piazza ci sono i profili in ferro di Che Guevara e Cienfuegos",
             "tier": MUST},
            {"name": "Callejón de Hamel", "base": "avana", "hours": 1.5, "slot": None,
             "how": "un vicolo interamente dipinto con i simboli della santería: "
                    "la domenica pomeriggio c'è la rumba suonata dal vivo in strada",
             "tier": EXTRA},
            {"name": "Museo della Rivoluzione", "label": "Museo della Rivoluzione",
             "base": "avana", "hours": 2.5, "slot": None,
             "how": "nell'ex palazzo presidenziale, con i fori dei proiettili lasciati "
                    "nelle pareti: fuori è esposto lo yacht Granma", "tier": EXTRA},
            {"name": "Fabbrica di sigari", "label": "Sigari", "base": "avana", "hours": 2.0,
             "slot": _MORNING,
             "how": "visita guidata mentre si lavora: c'è ancora il lettore che legge "
                    "ad alta voce ai torcedores per tutto il turno", "tier": EXTRA},
            {"name": "Playas del Este", "base": "avana", "hours": 4.0, "slot": None,
             "how": "venti minuti a est della città: sabbia bianca e chioschi, "
                    "è la spiaggia dove vanno gli abitanti dell'Avana nel fine settimana",
             "tier": EXTRA},
            {"name": "Cena in paladar all'Avana", "label": "Paladar dell'Avana",
             "base": "avana", "hours": 2.5, "slot": _EVENING,
             "how": "nelle case private di Habana Vieja e Vedado: si prenota il giorno prima "
                    "perché comprano gli ingredienti in base a chi ha riservato", "tier": MUST},
            {"name": "Spettacolo di cabaret", "label": "Cabaret", "base": "avana",
             "hours": 3.0, "slot": _EVENING,
             "how": "il varietà con orchestra dal vivo e piume, all'aperto: "
                    "si prenota e si arriva presto per i tavoli davanti", "tier": EXTRA},
            {"name": "Mirador Los Jazmines", "label": "Los Jazmines", "base": "vinales",
             "hours": 1.5, "slot": _EVENING,
             "how": "la terrazza sopra la valle da cui si vedono i mogotes allineati "
                    "nella foschia: al tramonto il fondovalle si riempie di nebbia",
             "tier": MUST},
            {"name": "Cavalcata nella valle di Viñales", "label": "A cavallo",
             "base": "vinales", "hours": 4.0, "slot": _MORNING,
             "how": "si attraversano i campi di tabacco al passo, fermandosi nelle case "
                    "dei contadini: è il modo in cui ci si muove davvero qui", "tier": EXTRA},
            {"name": "Cayo Levisa", "base": "vinales", "hours": 6.0, "slot": _MORNING,
             "how": "traghetto da Palma Rubia verso il cayo: barriera corallina "
                    "a pochi metri dalla riva e una sola struttura sull'isola", "tier": EXTRA},
        ],
        "variants": [
            {"days": 7, "title": "L'Avana e Viñales",
             "for_who": "La capitale coloniale e la valle del tabacco: due Cube molto diverse."},
            {"days": 10, "title": "Cuba occidentale",
             "for_who": "Aggiunge le spiagge del nord, le grotte e il tempo per la musica."},
        ],
    },

    # =====================================================================
    # 56 — PUNTA CANA
    # =====================================================================
    56: {
        "bases": [
            {"key": "puntacana", "name": "Bávaro-Punta Cana", "night_weight": 1,
             "max_nights": 14, "transfer_h": 0.0,
             "note": "Costa di resort all-inclusive: si sta in struttura e le escursioni "
                     "partono dalla hall, non serve mezzo proprio."},
        ],
        "places": [
            {"name": "Spiaggia di Bávaro", "label": "Bávaro", "base": "puntacana",
             "hours": 5.0, "slot": None,
             "how": "chilometri di sabbia bianca e palme, con la barriera al largo "
                    "che tiene il mare piatto: è la spiaggia davanti ai resort", "tier": MUST},
            {"name": "Isola Saona", "label": "Saona", "base": "puntacana", "hours": 8.0,
             "slot": _MORNING,
             "how": "catamarano e motoscafo dentro il parco nazionale dell'Est, "
                    "con sosta alla piscina naturale dove si sta in piedi in mezzo al mare",
             "tier": MUST},
            {"name": "Cenote di Hoyo Azul", "label": "Hoyo Azul", "base": "puntacana",
             "hours": 3.0, "slot": None,
             "how": "dentro il parco Scape Park: si scende un sentiero fino alla pozza "
                    "turchese ai piedi di una falesia, e ci si tuffa", "tier": MUST},
            {"name": "Isla Catalina", "label": "Catalina", "base": "puntacana", "hours": 8.0,
             "slot": _MORNING,
             "how": "in barca verso ovest: uno dei migliori punti di snorkeling "
                    "e immersione del paese, con il muro di corallo che scende a picco",
             "tier": EXTRA},
            {"name": "Cena su una terrazza a Bávaro", "label": "Cena caraibica",
             "base": "puntacana", "hours": 2.5, "slot": _EVENING,
             "how": "fuori dal resort, nei ristoranti sulla spiaggia: pesce alla griglia, "
                    "mofongo e rum locale", "tier": MUST},
            {"name": "Buggy tra le piantagioni", "label": "Buggy", "base": "puntacana",
             "hours": 4.0, "slot": None,
             "how": "fuoristrada sulle strade sterrate dell'entroterra tra canna da zucchero "
                    "e cacao: si torna pieni di polvere rossa, vestiti vecchi obbligatori",
             "tier": EXTRA},
            {"name": "Osservazione delle megattere a Samaná", "label": "Megattere",
             "base": "puntacana", "hours": 10.0, "slot": _MORNING,
             "how": "escursione lunga verso nord-ovest: nella baia di Samaná le balene "
                    "arrivano a partorire, e si osservano da barche autorizzate", "tier": EXTRA,
             "months": [1, 2, 3],
             "note": "Le megattere sono nella baia di Samaná solo tra gennaio e marzo."},
            {"name": "Serata di merengue e bachata", "label": "Merengue", "base": "puntacana",
             "hours": 2.5, "slot": _EVENING,
             "how": "lezione e ballo nei locali della zona: qui si balla in coppia "
                    "e si impara in una sera, la bachata è più lenta del merengue", "tier": EXTRA},
            {"name": "Snorkeling sulla barriera", "label": "Snorkeling", "base": "puntacana",
             "hours": 3.0, "slot": None,
             "how": "in barca a fondo trasparente fino alla barriera davanti alla costa: "
                    "acqua bassa e calma, adatta anche a chi non ha mai provato", "tier": EXTRA},
            {"name": "Kitesurf a Cabeza de Toro", "label": "Kitesurf", "base": "puntacana",
             "hours": 3.5, "slot": _AFTERNOON,
             "how": "il vento entra regolare nel pomeriggio: le scuole sono sulla spiaggia "
                    "e affittano tutta l'attrezzatura", "tier": EXTRA},
            {"name": "Spiaggia di Macao", "label": "Macao", "base": "puntacana", "hours": 4.0,
             "slot": None,
             "how": "una delle poche spiagge pubbliche non occupata dai resort: "
                    "onde più grosse, scuole di surf e chioschi di pesce fritto", "tier": MUST},
            {"name": "Laguna Bavaro e Indigenous Eyes", "label": "Indigenous Eyes",
             "base": "puntacana", "hours": 2.5, "slot": None,
             "how": "riserva ecologica con dodici lagune d'acqua dolce nella foresta: "
                    "si cammina su sentieri ombreggiati e si nuota in alcune", "tier": EXTRA},
            {"name": "Altos de Chavón", "label": "Altos de Chavón", "base": "puntacana",
             "hours": 5.0, "slot": None,
             "how": "un villaggio in stile mediterraneo costruito negli anni Settanta "
                    "sopra il fiume Chavón, con l'anfiteatro affacciato sul canyon",
             "tier": EXTRA},
            {"name": "Santo Domingo coloniale in giornata", "label": "Santo Domingo",
             "base": "puntacana", "hours": 9.0, "slot": _MORNING,
             "how": "due ore e mezza a ovest: la prima città europea delle Americhe, "
                    "con la cattedrale più antica del continente e la Zona Colonial a piedi",
             "tier": EXTRA},
            {"name": "Battesimo subacqueo", "label": "Immersione", "base": "puntacana",
             "hours": 3.0, "slot": None,
             "how": "prima prova in acque protette e poi uscita in barca: "
                    "acqua a ventisette gradi e visibilità alta quasi tutto l'anno",
             "tier": EXTRA},
            {"name": "Zipline nella foresta", "label": "Zipline", "base": "puntacana",
             "hours": 3.0, "slot": None,
             "how": "cavi tesi sopra le chiome e i corsi d'acqua dell'entroterra: "
                    "si va con imbragatura e istruttore, adatto anche ai ragazzi", "tier": EXTRA},
            {"name": "Golf sui campi affacciati sull'oceano", "label": "Golf",
             "base": "puntacana", "hours": 5.0, "slot": _MORNING,
             "how": "diversi percorsi hanno buche a picco sul mare: si prenota "
                    "il tee time e si gioca presto, prima che si alzi il vento", "tier": EXTRA},
            {"name": "Serata di rum e sigari", "label": "Rum e sigari", "base": "puntacana",
             "hours": 2.0, "slot": _EVENING,
             "how": "degustazione guidata dei rum invecchiati dominicani, spesso "
                    "con l'arrotolatura del sigaro fatta davanti al tavolo", "tier": EXTRA},
            {"name": "Basilica di Higüey", "label": "Higüey", "base": "puntacana",
             "hours": 3.0, "slot": None,
             "how": "quaranta minuti nell'entroterra: la basilica di cemento con gli archi "
                    "parabolici e, attorno, il mercato della città vera", "tier": EXTRA},
            {"name": "Cena sulla spiaggia a Cap Cana", "label": "Cap Cana",
             "base": "puntacana", "hours": 2.5, "slot": _EVENING,
             "how": "nella marina a sud: ristoranti sull'acqua dove si mangia "
                    "il pesce appena sbarcato dai pescherecci ormeggiati davanti", "tier": EXTRA},
        ],
        "variants": [
            {"days": 7, "title": "Caraibi in resort",
             "for_who": "Spiaggia, isole e un paio di escursioni: la vacanza senza pensieri."},
            {"days": 10, "title": "Punta Cana oltre la spiaggia",
             "for_who": "Aggiunge l'entroterra, le barriere e le escursioni più lontane."},
        ],
    },

    # =====================================================================
    # 57 — CAPPADOCIA
    # =====================================================================
    57: {
        "bases": [
            {"key": "goreme", "name": "Göreme", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Il paese al centro della regione: si dorme negli hotel scavati "
                     "nella roccia, e da qui partono tutte le escursioni."},
        ],
        "places": [
            {"name": "Volo in mongolfiera all'alba", "label": "Mongolfiera",
             "base": "goreme", "hours": 4.0, "slot": _MORNING,
             "how": "sveglia alle quattro e mezza e volo di un'ora sopra i camini di fata: "
                    "si prenota con largo anticipo, ma i decolli vengono annullati "
                    "con il vento forte, quindi conviene tenersi giorni di margine", "tier": MUST},
            {"name": "Museo all'aperto di Göreme", "label": "Göreme", "base": "goreme",
             "hours": 2.5, "slot": _MORNING,
             "how": "a piedi tra le chiese rupestri bizantine con gli affreschi: "
                    "la Chiesa Scura si paga a parte ma è quella meglio conservata",
             "tier": MUST},
            {"name": "Valle dell'Amore e Valle Rosa", "label": "Valli", "base": "goreme",
             "hours": 4.0, "slot": _EVENING,
             "how": "sentieri tra i pinnacoli di tufo: si cammina nel tardo pomeriggio "
                    "e si resta per il tramonto, quando la roccia diventa rossa", "tier": MUST},
            {"name": "Città sotterranea di Derinkuyu", "label": "Città sotterranea",
             "base": "goreme", "hours": 3.0, "slot": None,
             "how": "otto livelli scavati fino a sessanta metri di profondità: "
                    "i cunicoli sono bassi e stretti, non fa per chi soffre di claustrofobia",
             "tier": MUST},
            {"name": "Cena in una casa scavata nella roccia", "label": "Cena cappadoce",
             "base": "goreme", "hours": 2.5, "slot": _EVENING,
             "how": "il testi kebab arriva in un'anfora di terracotta che si rompe "
                    "davanti al tavolo, con i mezze turchi prima", "tier": MUST},
            {"name": "Valle di Ihlara", "label": "Ihlara", "base": "goreme", "hours": 5.0,
             "slot": _MORNING,
             "how": "un canyon verde profondo cento metri: si scendono quattrocento gradini "
                    "e si cammina lungo il fiume tra le chiese scavate nelle pareti",
             "tier": EXTRA},
            {"name": "Castello di Uçhisar", "label": "Uçhisar", "base": "goreme", "hours": 2.0,
             "slot": None,
             "how": "il picco di roccia più alto della regione, tutto perforato di stanze: "
                    "si sale in cima per la vista a 360 gradi sulle valli", "tier": EXTRA},
            {"name": "Escursione a cavallo tra i camini di fata", "label": "Cavallo",
             "base": "goreme", "hours": 3.0, "slot": _EVENING,
             "how": "Cappadocia significa terra dei bei cavalli: si esce al tramonto "
                    "e si attraversano le valli dove le auto non arrivano", "tier": EXTRA},
            {"name": "Avanos e la ceramica", "label": "Avanos", "base": "goreme", "hours": 2.5,
             "slot": None,
             "how": "sul fiume rosso: nelle botteghe si prova il tornio con l'argilla "
                    "locale, che è quella che dà il colore ai vasi", "tier": EXTRA},
            {"name": "Notte in una grotta hotel", "label": "Cave hotel", "base": "goreme",
             "hours": 2.0, "slot": _EVENING,
             "how": "le stanze scavate nel tufo restano fresche d'estate e tiepide d'inverno; "
                    "le terrazze sono il posto migliore per guardare le mongolfiere all'alba",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Cappadocia essenziale",
             "for_who": "Mongolfiera, chiese rupestri e valli: il concentrato in tre giorni."},
            {"days": 5, "title": "Cappadocia a piedi",
             "for_who": "Aggiunge i canyon, le città sotterranee e i villaggi di ceramisti."},
        ],
    },

    # =====================================================================
    # 58 — ISTANBUL
    # =====================================================================
    58: {
        "bases": [
            {"key": "istanbul", "name": "Istanbul", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città su due continenti: il traghetto sul Bosforo è un mezzo "
                     "pubblico, costa come il tram e attraversa in venti minuti."},
        ],
        "places": [
            {"name": "Santa Sofia", "label": "Santa Sofia", "base": "istanbul", "hours": 2.0,
             "slot": _MORNING,
             "how": "oggi è moschea in funzione: si entra scalzi e coperti, "
                    "e il piano superiore con i mosaici ha un biglietto separato", "tier": MUST},
            {"name": "Moschea Blu e Ippodromo", "label": "Moschea Blu", "base": "istanbul",
             "hours": 2.0, "slot": None,
             "how": "a duecento metri da Santa Sofia: chiusa ai visitatori durante "
                    "le cinque preghiere quotidiane, che durano circa mezz'ora ciascuna",
             "tier": MUST},
            {"name": "Gran Bazar", "base": "istanbul", "hours": 2.5, "slot": None,
             "how": "quattromila botteghe in sessantuno strade coperte: si contratta "
                    "sempre, ed è chiuso la domenica", "tier": MUST},
            {"name": "Crociera sul Bosforo", "label": "Bosforo", "base": "istanbul",
             "hours": 2.5, "slot": _EVENING,
             "how": "il traghetto pubblico da Eminönü costa una frazione dei tour privati "
                    "e passa sotto gli stessi ponti, tra palazzi ottomani e fortezze",
             "tier": MUST},
            {"name": "Palazzo Topkapı", "label": "Topkapı", "base": "istanbul", "hours": 3.0,
             "slot": _MORNING,
             "how": "quattro cortili e l'harem, che si paga a parte ed è la parte migliore: "
                    "serve mezza giornata, e chiude il martedì", "tier": MUST},
            {"name": "Hammam storico", "label": "Hammam", "base": "istanbul", "hours": 2.0,
             "slot": _AFTERNOON,
             "how": "nei bagni ottomani del Cinquecento: marmo caldo, schiuma "
                    "e massaggio col guanto ruvido, uomini e donne separati", "tier": MUST},
            {"name": "Cisterna Basilica", "label": "Cisterna", "base": "istanbul",
             "hours": 1.5, "slot": None,
             "how": "un serbatoio sotterraneo bizantino con 336 colonne nell'acqua, "
                    "illuminato a bassa luce: fresco anche in agosto", "tier": EXTRA},
            {"name": "Quartiere di Balat", "label": "Balat", "base": "istanbul", "hours": 2.5,
             "slot": None,
             "how": "case colorate in salita lungo il Corno d'Oro, tra sinagoghe "
                    "e chiese greche: è il quartiere che sta cambiando più in fretta",
             "tier": EXTRA},
            {"name": "Mercato delle spezie e cena a Karaköy", "label": "Mercato delle spezie",
             "base": "istanbul", "hours": 2.5, "slot": _EVENING,
             "how": "il bazar egiziano vicino al ponte di Galata, poi si attraversa "
                    "a piedi tra i pescatori con le canne per cenare dall'altra parte",
             "tier": EXTRA},
            {"name": "Torre di Galata", "label": "Galata", "base": "istanbul", "hours": 1.5,
             "slot": _EVENING,
             "how": "si sale in ascensore per il ballatoio circolare: la fila si allunga "
                    "verso il tramonto, che è anche il momento migliore", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Istanbul imperiale",
             "for_who": "Santa Sofia, Topkapı e il Bosforo: le due sponde in tre giorni."},
            {"days": 5, "title": "Istanbul per quartieri",
             "for_who": "Aggiunge i bazar, gli hammam e i quartieri lungo il Corno d'Oro."},
        ],
    },

    # =====================================================================
    # 59 — CITTÀ DEL CAPO
    # =====================================================================
    59: {
        "bases": [
            {"key": "capetown", "name": "Città del Capo", "night_weight": 2, "max_nights": 8,
             "transfer_h": 0.0,
             "note": "Città distesa tra la montagna e due oceani: serve l'auto, "
                     "e le distanze verso la penisola sono più lunghe di quanto sembri."},
            {"key": "winelands", "name": "Stellenbosch", "night_weight": 1, "max_nights": 3,
             "transfer_h": 1.0,
             "note": "Le terre del vino a un'ora dalla città: valli di tenute storiche "
                     "circondate da montagne."},
        ],
        "places": [
            {"name": "Table Mountain", "label": "Table Mountain", "base": "capetown",
             "hours": 4.0, "slot": _MORNING,
             "how": "funivia con cabina rotante, oppure due ore di salita per la gola "
                    "di Platteklip: chiude col vento forte, quindi si va appena il tempo lo permette",
             "tier": MUST},
            {"name": "Capo di Buona Speranza", "label": "Cape Point", "base": "capetown",
             "hours": 7.0, "slot": _MORNING,
             "how": "giornata intera lungo la penisola: si passa da Chapman's Peak Drive, "
                    "strada a picco sull'oceano, e si sale al faro con la funicolare",
             "tier": MUST},
            {"name": "Pinguini di Boulders Beach", "label": "Boulders Beach",
             "base": "capetown", "hours": 2.0, "slot": None,
             "how": "passerelle di legno sopra la colonia di pinguini africani, "
                    "a Simon's Town: si guardano da un metro ma non si toccano", "tier": MUST},
            {"name": "Bo-Kaap", "base": "capetown", "hours": 2.0, "slot": None,
             "how": "il quartiere malese con le case dipinte a tinte forti sulla salita: "
                    "si visita a piedi, ed è educato chiedere prima di fotografare le case",
             "tier": MUST},
            {"name": "V&A Waterfront e cena sull'oceano", "label": "Waterfront",
             "base": "capetown", "hours": 2.5, "slot": _EVENING,
             "how": "il vecchio porto riconvertito: da qui partono i traghetti "
                    "per Robben Island, e la sera si mangia pesce guardando la montagna",
             "tier": MUST},
            {"name": "Robben Island", "base": "capetown", "hours": 4.0, "slot": _MORNING,
             "how": "traghetto dal Waterfront e visita guidata da ex detenuti: "
                    "si vede la cella di Mandela, e le partenze saltano col mare mosso",
             "tier": EXTRA},
            {"name": "Giardino botanico di Kirstenbosch", "label": "Kirstenbosch",
             "base": "capetown", "hours": 3.0, "slot": None,
             "how": "sul versante orientale della montagna: la passerella sospesa "
                    "tra gli alberi e i concerti all'aperto nelle sere d'estate", "tier": EXTRA},
            {"name": "Degustazione nelle tenute di Stellenbosch", "label": "Stellenbosch",
             "base": "winelands", "hours": 4.0, "slot": None,
             "how": "si gira con autista perché si assaggia in più tenute: qui nascono "
                    "i grandi rossi sudafricani e il pinotage, vitigno locale", "tier": MUST},
            {"name": "Franschhoek e il tram del vino", "label": "Franschhoek",
             "base": "winelands", "hours": 5.0, "slot": _MORNING,
             "how": "un tram-bus a cerchi collega le cantine della valle: si sale "
                    "e si scende liberamente per tutta la giornata", "tier": EXTRA},
            {"name": "Avvistamento balene a Hermanus", "label": "Balene", "base": "winelands",
             "hours": 6.0, "slot": _MORNING,
             "how": "un'ora e mezza a est: le balene franche australi si vedono "
                    "anche da terra, camminando lungo la scogliera del paese", "tier": EXTRA,
             "months": [6, 7, 8, 9, 10, 11],
             "note": "Le balene franche sostano lungo questa costa solo nell'inverno australe."},
            {"name": "Alba dal Lion's Head", "label": "Lion's Head", "base": "capetown",
             "hours": 3.0, "slot": _MORNING,
             "how": "un'ora e mezza di salita a spirale attorno alla collina, con "
                    "due tratti di catene e scalette: si parte col buio e la torcia",
             "tier": MUST},
            {"name": "Camps Bay e Clifton", "label": "Camps Bay", "base": "capetown",
             "hours": 4.0, "slot": None,
             "how": "le spiagge sotto i Dodici Apostoli: sabbia bianca e acqua "
                    "dell'Atlantico a dodici gradi, in cui quasi nessuno resta a lungo",
             "tier": MUST},
            {"name": "Tramonto da Signal Hill", "label": "Signal Hill", "base": "capetown",
             "hours": 2.0, "slot": _EVENING,
             "how": "ci si arriva in auto fino in cima: a mezzogiorno esatto sparano "
                    "il cannone, ma è al tramonto che si viene qui", "tier": MUST},
            {"name": "Zeitz MOCAA", "base": "capetown", "hours": 2.5, "slot": None,
             "how": "un vecchio silo per il grano scavato all'interno come un alveare: "
                    "è il più grande museo d'arte contemporanea africana", "tier": EXTRA},
            {"name": "Woodstock e i mercati", "label": "Woodstock", "base": "capetown",
             "hours": 2.5, "slot": None,
             "how": "ex quartiere industriale con i murales e l'Old Biscuit Mill, "
                    "che il sabato mattina diventa mercato del cibo", "tier": EXTRA},
            {"name": "Visita guidata a Langa", "label": "Township", "base": "capetown",
             "hours": 3.5, "slot": None,
             "how": "si va solo con guide che vivono nel township: si visitano progetti "
                    "sociali e si mangia in una shebeen, mai fotografando le persone senza chiedere",
             "tier": EXTRA},
            {"name": "Cena a Kloof Street", "label": "Kloof Street", "base": "capetown",
             "hours": 2.5, "slot": _EVENING,
             "how": "la via dei ristoranti sotto la montagna: cucina del Capo, "
                    "vini locali al bicchiere e prezzi bassi per gli standard europei",
             "tier": MUST},
            {"name": "Braai in una tenuta", "label": "Braai", "base": "winelands",
             "hours": 2.5, "slot": _EVENING,
             "how": "la grigliata sudafricana è un rito sociale, non una cena: "
                    "boerewors, agnello e mais arrostito, con il vino della casa", "tier": MUST},
            {"name": "Paarl e la valle del Berg", "label": "Paarl", "base": "winelands",
             "hours": 3.0, "slot": None,
             "how": "le cupole di granito sopra il paese e le tenute più antiche "
                    "della regione, meno affollate di Stellenbosch", "tier": EXTRA},
            {"name": "Mercato contadino di Stellenbosch", "label": "Mercato contadino",
             "base": "winelands", "hours": 2.0, "slot": _MORNING,
             "how": "il sabato mattina nelle tenute attorno al paese: formaggi, pane "
                    "e vino aperto alle nove, con i tavoli sotto le querce", "tier": EXTRA},
        ],
        "variants": [
            {"days": 9, "title": "Città del Capo e la penisola",
             "for_who": "Table Mountain, il Capo e i pinguini: la città e il suo oceano."},
            {"days": 13, "title": "Capo e terre del vino",
             "for_who": "Aggiunge Stellenbosch, le balene e il tempo per la costa."},
        ],
    },

    # =====================================================================
    # 60 — TOKYO
    # =====================================================================
    60: {
        "bases": [
            {"key": "tokyo", "name": "Tokyo", "night_weight": 1, "max_nights": 14,
             "transfer_h": 0.0,
             "note": "Rete ferroviaria urbana straordinaria ma complessa: conviene "
                     "una carta ricaricabile e scegliere ogni giorno un quartiere solo."},
        ],
        "places": [
            {"name": "Tempio Sensō-ji e Asakusa", "label": "Asakusa", "base": "tokyo",
             "hours": 2.5, "slot": _MORNING,
             "how": "si entra dalla porta del tuono e si percorre la via dei negozietti: "
                    "presto la mattina è quasi vuota, dalle dieci è un fiume di gente",
             "tier": MUST},
            {"name": "Incrocio di Shibuya e Shinjuku di notte", "label": "Shibuya",
             "base": "tokyo", "hours": 3.0, "slot": _EVENING,
             "how": "l'attraversamento si guarda dall'alto dalla stazione o dai caffè, "
                    "poi si prosegue nei vicoli di izakaya di Shinjuku", "tier": MUST},
            {"name": "Santuario Meiji e Harajuku", "label": "Meiji", "base": "tokyo",
             "hours": 3.0, "slot": _MORNING,
             "how": "un bosco di centomila alberi in mezzo alla città: si entra sotto "
                    "il torii gigante, e all'uscita c'è la via delle mode giovanili",
             "tier": MUST},
            {"name": "Mercato esterno di Tsukiji", "label": "Tsukiji", "base": "tokyo",
             "hours": 2.5, "slot": _MORNING,
             "how": "il mercato all'ingrosso si è spostato, ma le vie esterne restano: "
                    "si fa colazione con sushi e uova tamago ai banchi, dalle sette",
             "tier": MUST},
            {"name": "Cena in izakaya", "label": "Izakaya", "base": "tokyo", "hours": 2.5,
             "slot": _EVENING,
             "how": "si ordina poco alla volta e si beve insieme: nei vicoli di Omoide "
                    "Yokocho i locali hanno sei posti e si sta gomito a gomito", "tier": MUST},
            {"name": "Fioritura dei ciliegi", "label": "Hanami", "base": "tokyo",
             "hours": 3.0, "slot": None,
             "how": "picnic sotto gli alberi nei parchi di Ueno o lungo il fiume Meguro: "
                    "la fioritura dura poco più di una settimana e la data cambia ogni anno",
             "tier": MUST, "months": [3, 4],
             "note": "I ciliegi fioriscono a Tokyo tra fine marzo e i primi di aprile, e basta una pioggia per finirla."},
            {"name": "Quartiere di Akihabara", "label": "Akihabara", "base": "tokyo",
             "hours": 2.5, "slot": None,
             "how": "palazzi interi di elettronica, manga e sale giochi su più piani: "
                    "la domenica pomeriggio la via principale è pedonale", "tier": EXTRA},
            {"name": "Giardino Shinjuku Gyoen", "label": "Shinjuku Gyoen", "base": "tokyo",
             "hours": 2.0, "slot": None,
             "how": "tre giardini in uno, giapponese, inglese e francese: si paga "
                    "un ingresso simbolico ed è il posto più silenzioso del centro",
             "tier": EXTRA},
            {"name": "teamLab", "base": "tokyo", "hours": 2.5, "slot": None,
             "how": "installazioni digitali immersive con biglietti a orario esauriti "
                    "con settimane di anticipo: si cammina scalzi e nell'acqua in alcune sale",
             "tier": EXTRA},
            {"name": "Escursione a Nikko o Hakone", "label": "Hakone", "base": "tokyo",
             "hours": 9.0, "slot": _MORNING,
             "how": "due ore di treno: a Hakone si gira con funivia, battello sul lago "
                    "e treno a cremagliera, e col cielo sereno si vede il Fuji", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Tokyo la prima volta",
             "for_who": "Templi, incroci e izakaya: la città in cinque giorni, un quartiere al giorno."},
            {"days": 8, "title": "Tokyo a fondo",
             "for_who": "Aggiunge i giardini, i quartieri di nicchia e una gita fuori città."},
        ],
    },

    # =====================================================================
    # 61 — PORTO
    # =====================================================================
    61: {
        "bases": [
            {"key": "porto", "name": "Porto", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città verticale sul Douro: si cammina molto in salita, "
                     "e il tram storico e la funicolare aiutano più della metro."},
        ],
        "places": [
            {"name": "Ribeira e Ponte Dom Luís I", "label": "Ribeira", "base": "porto",
             "hours": 2.5, "slot": None,
             "how": "si attraversa il ponte sul livello alto, a piedi accanto al metrò: "
                    "da lì si vede tutta la Ribeira e le barche rabelo sul fiume", "tier": MUST},
            {"name": "Cantine del vino Porto a Gaia", "label": "Cantine di Gaia",
             "base": "porto", "hours": 2.5, "slot": None,
             "how": "sull'altra riva: visita alle botti e degustazione di tawny e vintage, "
                    "quasi tutte le case storiche fanno tour a orari fissi", "tier": MUST},
            {"name": "Livraria Lello", "base": "porto", "hours": 1.5, "slot": _MORNING,
             "how": "biglietto a orario da comprare online, scalabile sull'acquisto "
                    "di un libro: si entra presto perché la scala rossa è piccolissima",
             "tier": MUST},
            {"name": "Stazione di São Bento", "label": "São Bento", "base": "porto",
             "hours": 1.0, "slot": None,
             "how": "è una stazione funzionante: si entra gratis nell'atrio rivestito "
                    "da ventimila azulejos che raccontano la storia portoghese", "tier": MUST},
            {"name": "Cena di francesinha", "label": "Francesinha", "base": "porto",
             "hours": 2.0, "slot": _EVENING,
             "how": "il panino con carne, formaggio fuso e salsa piccante alla birra: "
                    "è pesantissimo, si divide in due e si accompagna con le patatine",
             "tier": MUST},
            {"name": "Crociera dei sei ponti", "label": "Douro", "base": "porto", "hours": 1.5,
             "slot": _EVENING,
             "how": "cinquanta minuti sul fiume in barca rabelo tradizionale: "
                    "si parte dalla Ribeira e si vede la città da sotto", "tier": EXTRA},
            {"name": "Torre dos Clérigos", "label": "Clérigos", "base": "porto", "hours": 1.5,
             "slot": None,
             "how": "225 gradini stretti a chiocciola fino al ballatoio: da lì si capisce "
                    "come la città scende a scalini fino al fiume", "tier": EXTRA},
            {"name": "Foz do Douro", "label": "Foz", "base": "porto", "hours": 3.0,
             "slot": _EVENING,
             "how": "in tram storico lungo il fiume fino alla foce: passeggiata sull'oceano "
                    "e tramonto sull'Atlantico, con i frangiflutti davanti", "tier": EXTRA},
            {"name": "Mercado do Bolhão", "label": "Bolhão", "base": "porto", "hours": 1.5,
             "slot": _MORNING,
             "how": "il mercato storico ristrutturato: banchi di pesce, baccalà secco "
                    "e frutta, con le tasche al piano superiore per il pranzo", "tier": EXTRA},
            {"name": "Valle del Douro in giornata", "label": "Valle del Douro",
             "base": "porto", "hours": 8.0, "slot": _MORNING,
             "how": "in treno lungo il fiume fino a Pinhão, con la ferrovia che corre "
                    "sull'acqua: le vigne terrazzate sono patrimonio UNESCO", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Porto in un weekend",
             "for_who": "Ribeira, cantine e azulejos: la città in due giorni."},
            {"days": 4, "title": "Porto e il Douro",
             "for_who": "Aggiunge l'oceano, i mercati e una giornata nella valle del vino."},
        ],
    },

    # =====================================================================
    # 62 — KYOTO
    # =====================================================================
    62: {
        "bases": [
            {"key": "kyoto", "name": "Kyoto", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "I templi sono sparsi ai bordi della conca: si usano bus e bici, "
                     "e conviene raggruppare le visite per zona invece che per importanza."},
        ],
        "places": [
            {"name": "Fushimi Inari Taisha", "label": "Fushimi Inari", "base": "kyoto",
             "hours": 3.0, "slot": _MORNING,
             "how": "migliaia di torii vermigli in salita sul monte: si entra all'alba "
                    "perché è aperto sempre e gratis, e dopo le nove non si cammina più",
             "tier": MUST},
            {"name": "Padiglione d'Oro Kinkaku-ji", "label": "Kinkaku-ji", "base": "kyoto",
             "hours": 1.5, "slot": _MORNING,
             "how": "il percorso è a senso unico e breve: si guarda il padiglione "
                    "riflesso nello stagno e si esce, non si entra dentro", "tier": MUST},
            {"name": "Foresta di bambù di Arashiyama", "label": "Arashiyama",
             "base": "kyoto", "hours": 3.5, "slot": _MORNING,
             "how": "presto la mattina, prima dei pullman: nella stessa zona ci sono "
                    "il ponte Togetsukyo e il parco delle scimmie in salita", "tier": MUST},
            {"name": "Gion e le vie delle geisha", "label": "Gion", "base": "kyoto",
             "hours": 2.5, "slot": _EVENING,
             "how": "a piedi tra le case di legno di Hanamikoji al crepuscolo: "
                    "fotografare le maiko per strada è vietato nelle vie private, e ci sono multe",
             "tier": MUST},
            {"name": "Kiyomizu-dera e Higashiyama", "label": "Kiyomizu-dera",
             "base": "kyoto", "hours": 3.0, "slot": None,
             "how": "il tempio sul terrazzamento di legno senza chiodi, e la salita "
                    "per le vie di Sannenzaka piene di botteghe di ceramica", "tier": MUST},
            {"name": "Mercato Nishiki", "label": "Nishiki", "base": "kyoto", "hours": 1.5,
             "slot": None,
             "how": "una via coperta lunga quattrocento metri: si assaggia camminando, "
                    "ma è considerato scortese mangiare in movimento, ci si ferma al banco",
             "tier": MUST},
            {"name": "Foliage autunnale nei templi", "label": "Momiji", "base": "kyoto",
             "hours": 3.0, "slot": None,
             "how": "gli aceri rossi nei giardini dei templi, con molti complessi "
                    "aperti anche di sera e illuminati apposta", "tier": EXTRA,
             "months": [11, 12],
             "note": "Il picco del foliage a Kyoto è tra metà novembre e inizio dicembre."},
            {"name": "Sentiero della Filosofia", "label": "Sentiero della Filosofia",
             "base": "kyoto", "hours": 2.0, "slot": None,
             "how": "due chilometri lungo un canale fiancheggiato da ciliegi, "
                    "da Ginkaku-ji verso sud: si cammina e basta, ed è gratuito", "tier": EXTRA},
            {"name": "Nara in giornata", "label": "Nara", "base": "kyoto", "hours": 6.0,
             "slot": _MORNING,
             "how": "quarantacinque minuti di treno: il Grande Buddha di bronzo "
                    "e i cervi liberi nel parco, che si inchinano per un biscotto", "tier": EXTRA},
            {"name": "Cerimonia del tè", "label": "Cerimonia del tè", "base": "kyoto",
             "hours": 1.5, "slot": _AFTERNOON,
             "how": "si prenota in una casa da tè: si sta seduti a terra, si gira "
                    "la ciotola due volte prima di bere e si finisce in tre sorsi", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Kyoto essenziale",
             "for_who": "Fushimi Inari, i padiglioni e Gion: i templi simbolo in tre giorni."},
            {"days": 5, "title": "Kyoto per zone",
             "for_who": "Aggiunge Arashiyama, i sentieri, Nara e i riti del tè."},
        ],
    },

    # =====================================================================
    # 63 — OSAKA
    # =====================================================================
    63: {
        "bases": [
            {"key": "osaka", "name": "Osaka", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città compatta e diretta, con la metropolitana che porta ovunque: "
                     "è anche la base più comoda per Kyoto, Nara e Himeji."},
        ],
        "places": [
            {"name": "Dotonbori", "base": "osaka", "hours": 2.5, "slot": _EVENING,
             "how": "il canale con le insegne al neon e il Glico Man: si mangia "
                    "camminando, takoyaki e okonomiyaki ai banchi lungo la via", "tier": MUST},
            {"name": "Castello di Osaka", "label": "Castello", "base": "osaka", "hours": 3.0,
             "slot": _MORNING,
             "how": "il parco attorno è gratuito e vale già la visita; dentro il torrione "
                    "c'è un museo su otto piani con ascensore fino in cima", "tier": MUST},
            {"name": "Mercato di Kuromon", "label": "Kuromon", "base": "osaka", "hours": 2.0,
             "slot": _MORNING,
             "how": "seicento metri di banchi coperti: si compra il pesce e lo grigliano "
                    "sul momento, si mangia in piedi davanti alla bancarella", "tier": MUST},
            {"name": "Shinsekai e Tsutenkaku", "label": "Shinsekai", "base": "osaka",
             "hours": 2.5, "slot": _EVENING,
             "how": "il quartiere retrò rimasto agli anni Sessanta: si mangiano "
                    "i kushikatsu fritti, e non si intinge due volte nella salsa comune",
             "tier": MUST},
            {"name": "Umeda Sky Building", "label": "Umeda Sky", "base": "osaka",
             "hours": 2.0, "slot": _EVENING,
             "how": "due torri unite da un giardino sospeso al quarantesimo piano: "
                    "si sale con una scala mobile sospesa nel vuoto", "tier": EXTRA},
            {"name": "Castello di Himeji in giornata", "label": "Himeji", "base": "osaka",
             "hours": 6.0, "slot": _MORNING,
             "how": "un'ora di treno a ovest: il castello giapponese meglio conservato, "
                    "mai distrutto, con le scale interne ripidissime da salire in calzini",
             "tier": EXTRA},
            {"name": "Santuario Sumiyoshi Taisha", "label": "Sumiyoshi Taisha",
             "base": "osaka", "hours": 2.0, "slot": None,
             "how": "uno dei santuari shintoisti più antichi del Giappone, con il ponte "
                    "rosso ad arco così ripido che si sale a gradini", "tier": EXTRA},
            {"name": "Acquario Kaiyukan", "label": "Kaiyukan", "base": "osaka", "hours": 3.0,
             "slot": None,
             "how": "il percorso scende a spirale attorno a una vasca centrale enorme "
                    "con gli squali balena: adatto anche con bambini", "tier": EXTRA},
            {"name": "Cena di okonomiyaki", "label": "Okonomiyaki", "base": "osaka",
             "hours": 2.0, "slot": _EVENING,
             "how": "la frittata di cavolo cotta sulla piastra davanti al tavolo: "
                    "a Osaka gli ingredienti si mescolano tutti insieme prima di cuocere",
             "tier": EXTRA},
            {"name": "Quartiere di Amerikamura", "label": "Amerikamura", "base": "osaka",
             "hours": 2.0, "slot": None,
             "how": "l'isolato della moda giovane, tra negozi vintage e murales: "
                    "si gira a piedi da Shinsaibashi in dieci minuti", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Osaka in due giorni",
             "for_who": "Dotonbori, castello e mercati: la capitale del cibo in un weekend."},
            {"days": 4, "title": "Osaka e il Kansai",
             "for_who": "Aggiunge Himeji, i santuari antichi e le serate nei quartieri retrò."},
        ],
    },

    # =====================================================================
    # 64 — CHIANG MAI
    # =====================================================================
    64: {
        "bases": [
            {"key": "chiangmai", "name": "Chiang Mai", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città vecchia dentro un fossato quadrato: dentro si cammina, "
                     "fuori si usano i songthaew rossi, che sono taxi collettivi."},
        ],
        "places": [
            {"name": "Wat Phra That Doi Suthep", "label": "Doi Suthep", "base": "chiangmai",
             "hours": 4.0, "slot": _MORNING,
             "how": "si sale in songthaew per la strada di montagna, poi 306 gradini "
                    "fiancheggiati dai naga: dalla terrazza si vede tutta la valle",
             "tier": MUST},
            {"name": "Templi della città vecchia", "label": "Città vecchia",
             "base": "chiangmai", "hours": 3.0, "slot": None,
             "how": "a piedi tra Wat Chedi Luang e Wat Phra Singh: nei cortili "
                    "ci sono i tavoli del monk chat, dove i novizi parlano con i visitatori",
             "tier": MUST},
            {"name": "Santuario etico degli elefanti", "label": "Elefanti",
             "base": "chiangmai", "hours": 6.0, "slot": _MORNING,
             "how": "si scelgono i centri dove non si cavalcano e non si fanno spettacoli: "
                    "si preparano il cibo, si osserva e al massimo si fa il bagno nel fiume",
             "tier": MUST},
            {"name": "Corso di cucina thailandese", "label": "Corso di cucina",
             "base": "chiangmai", "hours": 5.0, "slot": _MORNING,
             "how": "si parte dal mercato per la spesa, poi si cucinano quattro o cinque "
                    "piatti e si mangiano: le scuole vengono a prendere in hotel", "tier": MUST},
            {"name": "Mercato notturno e Sunday Walking Street", "label": "Mercato notturno",
             "base": "chiangmai", "hours": 3.0, "slot": _EVENING,
             "how": "il bazar notturno è tutte le sere; la domenica invece si chiude "
                    "la via principale della città vecchia e diventa un mercato lungo un chilometro",
             "tier": MUST},
            {"name": "Parco nazionale del Doi Inthanon", "label": "Doi Inthanon",
             "base": "chiangmai", "hours": 8.0, "slot": _MORNING,
             "how": "la vetta più alta della Thailandia, due ore d'auto: cascate, "
                    "sentiero nella foresta di muschio e le due pagode reali in quota",
             "tier": EXTRA},
            {"name": "Festival delle lanterne Yi Peng", "label": "Yi Peng",
             "base": "chiangmai", "hours": 4.0, "slot": _EVENING,
             "how": "migliaia di lanterne di carta liberate insieme nel cielo, "
                    "insieme a quelle sull'acqua del Loi Krathong", "tier": EXTRA,
             "months": [11],
             "note": "Si tiene una volta l'anno, a novembre, secondo il calendario lunare."},
            {"name": "Grand Canyon di Hang Dong", "label": "Grand Canyon", "base": "chiangmai",
             "hours": 3.0, "slot": None,
             "how": "una cava allagata diventata parco acquatico: si salta dalle pareti "
                    "e ci sono i gonfiabili, molto frequentata dai locali nel weekend",
             "tier": EXTRA},
            {"name": "Massaggio thai in centro", "label": "Massaggio", "base": "chiangmai",
             "hours": 1.5, "slot": _AFTERNOON,
             "how": "a Chiang Mai costa una frazione che altrove: molti centri sono "
                    "gestiti da programmi di reinserimento e la qualità è alta", "tier": EXTRA},
            {"name": "Cena di khao soi", "label": "Khao soi", "base": "chiangmai",
             "hours": 2.0, "slot": _EVENING,
             "how": "la zuppa di noodles al curry con la pasta fritta sopra, "
                    "piatto del nord che a Bangkok quasi non si trova", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Chiang Mai essenziale",
             "for_who": "Templi, elefanti e mercati notturni: il nord in tre giorni."},
            {"days": 5, "title": "Chiang Mai e le montagne",
             "for_who": "Aggiunge il parco nazionale, i corsi di cucina e il ritmo lento del nord."},
        ],
    },

    # =====================================================================
    # 65 — ESSAOUIRA
    # =====================================================================
    65: {
        "bases": [
            {"key": "essaouira", "name": "Essaouira", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Medina piccola e pedonale affacciata sull'Atlantico: si gira "
                     "tutta a piedi in mezz'ora, e il vento è una costante."},
        ],
        "places": [
            {"name": "Medina e bastioni di Skala", "label": "Medina", "base": "essaouira",
             "hours": 2.5, "slot": None,
             "how": "a piedi sulle mura portoghesi con i cannoni di bronzo affacciati "
                    "sull'oceano: la medina qui è ordinata e ad angolo retto, non un labirinto",
             "tier": MUST},
            {"name": "Porto dei pescatori", "label": "Porto", "base": "essaouira",
             "hours": 2.0, "slot": _MORNING,
             "how": "le barche azzurre rientrano a metà mattina: si compra il pesce "
                    "al banco e lo grigliano lì davanti su bracieri all'aperto", "tier": MUST},
            {"name": "Spiaggia e windsurf", "label": "Spiaggia", "base": "essaouira",
             "hours": 4.0, "slot": _AFTERNOON,
             "how": "il vento costante da nord-est ha reso questa baia una capitale "
                    "del windsurf: le scuole sono sulla sabbia e affittano tutto", "tier": MUST},
            {"name": "Cena di pesce sulla piazza", "label": "Cena di pesce",
             "base": "essaouira", "hours": 2.5, "slot": _EVENING,
             "how": "sardine alla griglia, tajine di pesce e tè alla menta nei ristoranti "
                    "attorno a Place Moulay Hassan", "tier": MUST},
            {"name": "Cooperativa dell'olio di argan", "label": "Argan", "base": "essaouira",
             "hours": 2.0, "slot": None,
             "how": "sulla strada per Marrakech: cooperative femminili dove si vede "
                    "la frantumazione a mano delle noci, e si compra senza intermediari",
             "tier": EXTRA},
            {"name": "Passeggiata a cammello sulla spiaggia", "label": "Cammelli",
             "base": "essaouira", "hours": 2.0, "slot": _EVENING,
             "how": "lungo la baia verso sud al tramonto: si contratta il prezzo "
                    "prima di salire, come ovunque in Marocco", "tier": EXTRA},
            {"name": "Sidi Kaouki", "base": "essaouira", "hours": 4.0, "slot": None,
             "how": "venticinque chilometri a sud: spiaggia lunghissima e quasi vuota, "
                    "con onde più grosse, è il posto dei surfisti veri", "tier": EXTRA},
            {"name": "Botteghe di ebanisteria", "label": "Legno di thuya", "base": "essaouira",
             "hours": 1.5, "slot": None,
             "how": "sotto i bastioni ci sono le botteghe dove si lavora il thuya, "
                    "il legno profumato locale: si vede intarsiare a mano", "tier": EXTRA},
            {"name": "Isole Purpuraires in barca", "label": "Isole Purpuraires",
             "base": "essaouira", "hours": 2.5, "slot": None,
             "how": "uscita breve davanti alla città verso le isole dove nidificano "
                    "i falchi di Eleonora: si sbarca solo con autorizzazione", "tier": EXTRA,
             "months": [4, 5, 6, 7, 8, 9, 10]},
            {"name": "Concerto di musica gnaoua", "label": "Gnaoua", "base": "essaouira",
             "hours": 2.0, "slot": _EVENING,
             "how": "nei caffè della medina si suona dal vivo con il guembri e i crotali "
                    "di ferro: la città è la capitale di questa musica", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Essaouira in due giorni",
             "for_who": "Medina, porto e oceano: la fuga dal caos di Marrakech."},
            {"days": 4, "title": "Essaouira e la costa",
             "for_who": "Aggiunge le spiagge a sud, l'argan e le sere di gnaoua."},
        ],
    },

    # =====================================================================
    # 66 — MERZOUGA (SAHARA)
    # =====================================================================
    66: {
        "bases": [
            {"key": "merzouga", "name": "Merzouga", "night_weight": 1, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "Ai piedi delle dune: qui non si arriva per caso, sono otto ore "
                     "d'auto da Marrakech e tutto passa da guide locali."},
        ],
        "places": [
            {"name": "Traversata in cammello all'Erg Chebbi", "label": "Erg Chebbi",
             "base": "merzouga", "hours": 3.0, "slot": _EVENING,
             "how": "si parte un'ora e mezza prima del tramonto e si entra nelle dune "
                    "in carovana: turbante e scarpe chiuse contro la sabbia", "tier": MUST},
            {"name": "Notte nel campo tendato", "label": "Campo tendato",
             "base": "merzouga", "hours": 4.0, "slot": _EVENING,
             "how": "cena sotto le tende berbere, tamburi attorno al fuoco e poi il cielo: "
                    "senza luci artificiali la Via Lattea si vede a occhio nudo", "tier": MUST},
            {"name": "Alba sulle dune", "label": "Alba nel deserto", "base": "merzouga",
             "hours": 2.0, "slot": _MORNING,
             "how": "ci si sveglia al buio e si sale a piedi sulla duna più vicina: "
                    "la sabbia cambia colore in pochi minuti, dal grigio all'arancio",
             "tier": MUST},
            {"name": "Villaggio gnaoua di Khamlia", "label": "Khamlia", "base": "merzouga",
             "hours": 2.0, "slot": None,
             "how": "pochi chilometri a sud: i discendenti dei sudanesi suonano "
                    "la musica gnaoua nella casa comune, servendo il tè", "tier": MUST},
            {"name": "Fuoristrada tra le miniere e l'oasi", "label": "Fuoristrada",
             "base": "merzouga", "hours": 4.0, "slot": _MORNING,
             "how": "giro in 4x4 fuori pista tra le vecchie miniere di kohl, "
                    "il lago stagionale e i pozzi nomadi", "tier": EXTRA},
            {"name": "Sandboard sulle dune", "label": "Sandboard", "base": "merzouga",
             "hours": 2.0, "slot": None,
             "how": "si sale a piedi affondando nella sabbia e si scende sulla tavola: "
                    "faticoso in salita, brevissimo in discesa", "tier": EXTRA},
            {"name": "Gole del Todra", "label": "Todra", "base": "merzouga", "hours": 6.0,
             "slot": _MORNING,
             "how": "due ore e mezza verso ovest: un canyon con pareti di trecento metri "
                    "che si stringono fino a dieci, con la strada che passa in mezzo",
             "tier": EXTRA},
            {"name": "Cena berbera nella kasbah", "label": "Cena berbera",
             "base": "merzouga", "hours": 2.5, "slot": _EVENING,
             "how": "tajine cotta lentamente sotto il coperchio di terracotta "
                    "e pane cotto nella sabbia calda", "tier": EXTRA},
            {"name": "Lago Dayet Srji e fenicotteri", "label": "Dayet Srji",
             "base": "merzouga", "hours": 2.0, "slot": _MORNING,
             "how": "un lago che appare solo dopo le piogge, a due passi dal villaggio: "
                    "quando c'è acqua ci si fermano i fenicotteri in migrazione",
             "tier": EXTRA, "months": [2, 3, 4, 5],
             "note": "Il lago è stagionale: si forma con le piogge di fine inverno e in estate sparisce."},
            {"name": "Oasi di palme e canali", "label": "Oasi", "base": "merzouga",
             "hours": 2.5, "slot": None,
             "how": "si cammina nel palmeto irrigato dalle khettara, i canali sotterranei "
                    "scavati secoli fa per portare l'acqua dalle montagne", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Una notte nel Sahara",
             "for_who": "Dune, cammelli e cielo stellato: l'essenziale del deserto."},
            {"days": 3, "title": "Sahara e dintorni",
             "for_who": "Aggiunge i villaggi gnaoua, le gole e le oasi attorno all'erg."},
        ],
    },

    # =====================================================================
    # 67 — COSTA BRAVA
    # =====================================================================
    67: {
        "bases": [
            {"key": "palafrugell", "name": "Calella de Palafrugell", "night_weight": 1,
             "max_nights": 10, "transfer_h": 0.0,
             "note": "Nel centro della costa: da qui si raggiungono in mezz'ora "
                     "sia le cale a nord sia Girona nell'entroterra."},
        ],
        "places": [
            {"name": "Camí de Ronda", "base": "palafrugell", "hours": 4.0, "slot": _MORNING,
             "how": "l'antico sentiero dei doganieri a picco sul mare: si cammina "
                    "da Calella a Llafranc e oltre, scendendo in cale raggiungibili solo così",
             "tier": MUST},
            {"name": "Cadaqués e Portlligat", "label": "Cadaqués", "base": "palafrugell",
             "hours": 5.0, "slot": None,
             "how": "un'ora di tornanti oltre il massiccio: paese bianco di pescatori "
                    "e la casa-museo di Dalí, che si visita solo su prenotazione",
             "tier": MUST},
            {"name": "Cap de Creus", "label": "Cap de Creus", "base": "palafrugell",
             "hours": 4.0, "slot": None,
             "how": "il punto più orientale della Spagna: rocce modellate dalla tramontana "
                    "e sentieri sul promontorio, con il faro in fondo alla strada", "tier": MUST},
            {"name": "Teatro-Museo Dalí a Figueres", "label": "Museo Dalí",
             "base": "palafrugell", "hours": 3.0, "slot": None,
             "how": "biglietto a orario: il museo è progettato dall'artista stesso "
                    "ed è la sua tomba, si comincia dal cortile con la Cadillac", "tier": MUST},
            {"name": "Cena di pesce a Llafranc", "label": "Llafranc", "base": "palafrugell",
             "hours": 2.5, "slot": _EVENING,
             "how": "sul lungomare della baia accanto: suquet de peix, arròs negre "
                    "e vino dell'Empordà", "tier": MUST},
            {"name": "Girona", "base": "palafrugell", "hours": 4.0, "slot": None,
             "how": "quaranta minuti nell'entroterra: si cammina sulle mura, "
                    "nel quartiere ebraico e sulle scalinate della cattedrale", "tier": EXTRA},
            {"name": "Tossa de Mar", "base": "palafrugell", "hours": 4.0, "slot": None,
             "how": "il borgo murato sul mare più a sud: la città vecchia è dentro "
                    "le mura medievali che scendono fino alla spiaggia", "tier": EXTRA},
            {"name": "Cale di Begur", "label": "Cale di Begur", "base": "palafrugell",
             "hours": 4.0, "slot": None,
             "how": "Sa Tuna e Aiguablava: si scende in auto per strade strette "
                    "e i parcheggi sono pochissimi, meglio arrivare presto", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Giro in kayak tra le cale", "label": "Kayak", "base": "palafrugell",
             "hours": 3.0, "slot": _MORNING,
             "how": "si pagaia lungo la costa entrando nelle grotte marine "
                    "che da terra non si raggiungono", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10]},
            {"name": "Rovine greco-romane di Empúries", "label": "Empúries",
             "base": "palafrugell", "hours": 3.0, "slot": None,
             "how": "l'unico sito in Spagna con una città greca e una romana affiancate, "
                    "affacciato direttamente sulla spiaggia", "tier": EXTRA},
        ],
        "variants": [
            {"days": 2, "title": "Costa Brava in un weekend",
             "for_who": "Il sentiero sul mare e le cale: due giorni tra roccia e acqua."},
            {"days": 4, "title": "Costa Brava e l'Empordà",
             "for_who": "Aggiunge Cadaqués, Dalí, Girona e le rovine sul mare."},
        ],
    },

    # =====================================================================
    # 68 — SAL (CAPO VERDE)
    # =====================================================================
    68: {
        "bases": [
            {"key": "santamaria", "name": "Santa Maria", "night_weight": 1, "max_nights": 12,
             "transfer_h": 0.0,
             "note": "Il paese all'estremità sud dell'isola: tutto quello che si fa "
                     "parte da qui, e il resto di Sal è deserto piatto."},
        ],
        "places": [
            {"name": "Spiaggia di Santa Maria", "label": "Santa Maria", "base": "santamaria",
             "hours": 5.0, "slot": None,
             "how": "otto chilometri di sabbia bianca con l'acqua a ventiquattro gradi "
                    "quasi tutto l'anno: il vento si alza nel pomeriggio", "tier": MUST},
            {"name": "Pontile dei pescatori", "label": "Pontile", "base": "santamaria",
             "hours": 2.0, "slot": _MORNING,
             "how": "verso le nove rientrano le barche e il pesce viene pulito sul molo, "
                    "con i pesci vela appesi e le razze che aspettano gli scarti", "tier": MUST},
            {"name": "Cratere salino di Pedra de Lume", "label": "Pedra de Lume",
             "base": "santamaria", "hours": 3.0, "slot": None,
             "how": "dentro un cratere vulcanico spento: si galleggia senza sforzo "
                    "nella salamoia, e poi bisogna sciacquarsi subito", "tier": MUST},
            {"name": "Kitesurf a Kite Beach", "label": "Kitesurf", "base": "santamaria",
             "hours": 3.5, "slot": _AFTERNOON,
             "how": "gli alisei soffiano costanti da nord-est e l'acqua è calda: "
                    "le scuole stanno tutte sulla spiaggia a est del paese", "tier": MUST,
             "months": [11, 12, 1, 2, 3, 4, 5],
             "note": "La stagione del vento va da novembre a maggio; d'estate cala molto."},
            {"name": "Cena di cachupa e musica dal vivo", "label": "Cachupa",
             "base": "santamaria", "hours": 2.5, "slot": _EVENING,
             "how": "la zuppa nazionale di mais e fagioli, e nei bar del paese "
                    "si suona morna e coladeira quasi ogni sera", "tier": MUST},
            {"name": "Buracona e l'occhio blu", "label": "Buracona", "base": "santamaria",
             "hours": 3.0, "slot": _MORNING,
             "how": "una grotta lavica sulla costa nord-ovest: verso mezzogiorno "
                    "il sole entra da una fessura e accende l'acqua di blu elettrico",
             "tier": EXTRA},
            {"name": "Osservazione delle tartarughe", "label": "Tartarughe",
             "base": "santamaria", "hours": 3.0, "slot": _EVENING,
             "how": "escursione notturna con biologi sulle spiagge di nidificazione: "
                    "si sta in silenzio e senza luci bianche, solo torce rosse", "tier": EXTRA,
             "months": [6, 7, 8, 9, 10],
             "note": "Le tartarughe caretta caretta depongono su queste spiagge solo d'estate."},
            {"name": "Escursione in quad nell'interno", "label": "Quad",
             "base": "santamaria", "hours": 3.0, "slot": None,
             "how": "l'isola è piatta e desertica: si attraversano le saline abbandonate "
                    "e i villaggi di pescatori sulla costa est", "tier": EXTRA},
            {"name": "Shark Bay", "base": "santamaria", "hours": 2.5, "slot": None,
             "how": "in acqua bassa si cammina tra i piccoli squali limone che usano "
                    "la baia come nursery: si entra solo con la guida", "tier": EXTRA},
            {"name": "Escursione in barca a vela con snorkeling", "label": "Vela",
             "base": "santamaria", "hours": 4.0, "slot": None,
             "how": "catamarano lungo la costa con soste per lo snorkeling: "
                    "spesso si vedono tartarughe verdi vicino al relitto sommerso",
             "tier": EXTRA},
            {"name": "Espargos e il mercato", "label": "Espargos", "base": "santamaria",
             "hours": 2.0, "slot": _MORNING,
             "how": "il capoluogo al centro dell'isola, dove vive la gente: "
                    "mercato di frutta e pesce, e nessun turista dopo le dieci", "tier": EXTRA},
            {"name": "Palmeira", "base": "santamaria", "hours": 2.0, "slot": None,
             "how": "il porto commerciale sul lato ovest: barche colorate tirate "
                    "in secca e una piscina naturale poco più in là", "tier": EXTRA},
            {"name": "Immersione sulle secche di Sal", "label": "Immersione",
             "base": "santamaria", "hours": 4.0, "slot": _MORNING,
             "how": "grotte laviche sommerse e branchi di barracuda: l'acqua "
                    "resta sopra i ventidue gradi tutto l'anno", "tier": EXTRA},
            {"name": "Pesca d'altura", "label": "Pesca d'altura", "base": "santamaria",
             "hours": 5.0, "slot": _MORNING,
             "how": "le acque al largo sono tra le più pescose dell'Atlantico: "
                    "si esce all'alba, e quasi tutte le barche praticano il rilascio",
             "tier": EXTRA},
            {"name": "Serata di morna e coladeira", "label": "Morna", "base": "santamaria",
             "hours": 2.5, "slot": _EVENING,
             "how": "nei bar del paese si suona dal vivo quasi ogni sera: la morna "
                    "è lenta e malinconica, la coladeira è quella su cui si balla",
             "tier": EXTRA},
            {"name": "Terra Boa e il miraggio", "label": "Terra Boa", "base": "santamaria",
             "hours": 2.0, "slot": None,
             "how": "in mezzo alla piana desertica si vede un lago che non esiste: "
                    "è un miraggio stabile, e ci si ferma lungo la strada per Espargos",
             "tier": EXTRA},
            {"name": "Costa da Fragata e Regaço", "label": "Costa da Fragata",
             "base": "santamaria", "hours": 3.5, "slot": None,
             "how": "spiagge selvagge a est, senza servizi: si arriva in fuoristrada "
                    "e il mare è troppo mosso per nuotare, ma si cammina per chilometri",
             "tier": EXTRA},
            {"name": "Boa Vista in giornata", "label": "Boa Vista", "base": "santamaria",
             "hours": 8.0, "slot": _MORNING,
             "how": "traghetto o volo interno: dune sahariane che arrivano al mare "
                    "e il relitto della Cabo Santa Maria arenato sulla spiaggia", "tier": EXTRA},
            {"name": "Ponta Preta", "base": "santamaria", "hours": 3.0, "slot": None,
             "how": "il promontorio a ovest dove si formano le onde grandi: non è "
                    "una spiaggia per nuotare, ci si va a guardare i surfisti", "tier": EXTRA},
            {"name": "Tramonto dal pontile", "label": "Tramonto", "base": "santamaria",
             "hours": 1.5, "slot": _EVENING,
             "how": "in fondo al molo di legno, quando i pescatori hanno finito: "
                    "il sole cade dritto in mare e il pontile resta illuminato", "tier": EXTRA},
        ],
        "variants": [
            {"days": 6, "title": "Sal tra spiaggia e vento",
             "for_who": "Santa Maria, il cratere salino e l'oceano: l'isola in sei giorni."},
            {"days": 9, "title": "Sal a fondo",
             "for_who": "Aggiunge le grotte, l'entroterra desertico e la vita del mare."},
        ],
    },

    # =====================================================================
    # 69 — FUERTEVENTURA
    # =====================================================================
    69: {
        "bases": [
            {"key": "corralejo", "name": "Corralejo", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "All'estremità nord, accanto alle dune e con il traghetto per Lobos: "
                     "è la base più comoda e più viva dell'isola."},
            {"key": "morrojable", "name": "Morro Jable", "night_weight": 1, "max_nights": 4,
             "transfer_h": 1.5,
             "note": "All'estremo sud, sulla penisola di Jandía: spiagge lunghissime "
                     "e l'accesso alla costa selvaggia di Cofete."},
        ],
        "places": [
            {"name": "Dune di Corralejo", "label": "Dune", "base": "corralejo", "hours": 4.0,
             "slot": None,
             "how": "un deserto di sabbia chiara che arriva fino al mare: si parcheggia "
                    "lungo la strada e si scende, ma non c'è ombra da nessuna parte",
             "tier": MUST},
            {"name": "Isola di Lobos", "label": "Lobos", "base": "corralejo", "hours": 5.0,
             "slot": _MORNING,
             "how": "traghetto di quindici minuti, con numero chiuso e permesso "
                    "da richiedere online: si gira a piedi in tre ore, senza bar né ombra",
             "tier": MUST},
            {"name": "El Cotillo e le lagune", "label": "El Cotillo", "base": "corralejo",
             "hours": 4.0, "slot": None,
             "how": "sulla costa nord-ovest: piscine naturali riparate da barriere "
                    "di roccia, con acqua ferma anche quando l'oceano è mosso", "tier": MUST},
            {"name": "Lezione di surf", "label": "Surf", "base": "corralejo", "hours": 3.5,
             "slot": _MORNING,
             "how": "le onde del nord sono costanti tutto l'anno e le scuole sono "
                    "sulla spiaggia: per i principianti si va nei punti a fondo sabbioso",
             "tier": EXTRA},
            {"name": "Cena di pesce a Corralejo", "base": "corralejo", "hours": 2.5,
             "slot": _EVENING,
             "how": "vieja e cherne alla griglia con le papas arrugadas e i due mojo, "
                    "verde e rosso, nei ristoranti del porticciolo", "tier": MUST},
            {"name": "Spiaggia di Cofete", "label": "Cofete", "base": "morrojable",
             "hours": 5.0, "slot": _MORNING,
             "how": "quattordici chilometri di sabbia selvaggia dietro la montagna: "
                    "si arriva per una pista sterrata ripida, con auto normali è vietato "
                    "e il bagno è pericoloso per le correnti", "tier": MUST},
            {"name": "Spiagge di Sotavento", "label": "Sotavento", "base": "morrojable",
             "hours": 5.0, "slot": None,
             "how": "la laguna che si forma con la marea: acqua a mezza gamba per centinaia "
                    "di metri, ed è il campo di gara mondiale di windsurf", "tier": MUST},
            {"name": "Betancuria", "base": "morrojable", "hours": 3.0, "slot": None,
             "how": "l'antica capitale nell'entroterra montuoso: case bianche, "
                    "una chiesa del Quattrocento e i mirador lungo la strada", "tier": EXTRA},
            {"name": "Grotte di Ajuy", "label": "Ajuy", "base": "morrojable", "hours": 3.0,
             "slot": None,
             "how": "si cammina venti minuti sopra la scogliera nera e si scende "
                    "nelle grotte marine: sono le rocce più antiche delle Canarie", "tier": EXTRA},
            {"name": "Caseificio di formaggio di capra", "label": "Majorero",
             "base": "morrojable", "hours": 2.0, "slot": None,
             "how": "il majorero è il formaggio dell'isola, fatto con il latte "
                    "delle capre che pascolano nel deserto: si visita e si assaggia",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Fuerteventura del nord",
             "for_who": "Dune, Lobos e le lagune: l'isola in cinque giorni con una base sola."},
            {"days": 8, "title": "Tutta Fuerteventura",
             "for_who": "Aggiunge il sud selvaggio, Cofete e l'entroterra montuoso."},
        ],
    },

    # =====================================================================
    # 70 — LANZAROTE
    # =====================================================================
    70: {
        "bases": [
            {"key": "lanzarote", "name": "Costa Teguise", "night_weight": 1, "max_nights": 12,
             "transfer_h": 0.0,
             "note": "L'isola è piccola e si gira tutta in auto da qualsiasi punto: "
                     "una base sola basta, e le distanze non superano l'ora."},
        ],
        "places": [
            {"name": "Parco Nazionale di Timanfaya", "label": "Timanfaya",
             "base": "lanzarote", "hours": 3.5, "slot": _MORNING,
             "how": "si entra solo con il bus del parco lungo la Ruta de los Volcanes: "
                    "all'arrivo mostrano il calore del sottosuolo bruciando paglia in una fossa",
             "tier": MUST},
            {"name": "Jameos del Agua", "label": "Jameos del Agua", "base": "lanzarote",
             "hours": 2.5, "slot": None,
             "how": "un tubo lavico crollato trasformato da César Manrique in auditorium "
                    "e giardino: nel lago sotterraneo vivono granchi albini ciechi", "tier": MUST},
            {"name": "La Geria", "base": "lanzarote", "hours": 3.0, "slot": None,
             "how": "le viti crescono in conche scavate nella cenere e protette "
                    "da muretti a semicerchio: si assaggia il malvasia nelle bodegas",
             "tier": MUST},
            {"name": "Spiagge di Papagayo", "label": "Papagayo", "base": "lanzarote",
             "hours": 4.5, "slot": None,
             "how": "cale di sabbia dorata a sud, si arriva per una pista sterrata "
                    "a pagamento: non ci sono servizi, si porta acqua e ombrellone",
             "tier": MUST},
            {"name": "Cena vista oceano a El Golfo", "label": "El Golfo",
             "base": "lanzarote", "hours": 2.5, "slot": _EVENING,
             "how": "nel villaggio accanto alla laguna verde: pesce fresco al tramonto, "
                    "con la falesia del cratere alle spalle", "tier": MUST},
            {"name": "Cueva de los Verdes", "label": "Cueva de los Verdes",
             "base": "lanzarote", "hours": 2.0, "slot": None,
             "how": "un chilometro di galleria lavica visitabile solo con guida, "
                    "dove gli abitanti si nascondevano dai pirati", "tier": EXTRA},
            {"name": "Mirador del Río", "base": "lanzarote", "hours": 2.0, "slot": None,
             "how": "belvedere scavato nella scogliera a 475 metri, invisibile da fuori: "
                    "guarda sull'isola della Graciosa e sullo stretto", "tier": EXTRA},
            {"name": "Fondazione César Manrique", "label": "Manrique", "base": "lanzarote",
             "hours": 2.0, "slot": None,
             "how": "la casa dell'artista costruita dentro cinque bolle di lava collegate "
                    "tra loro: è lui che ha vietato i grattacieli su tutta l'isola",
             "tier": EXTRA},
            {"name": "La Graciosa in traghetto", "label": "La Graciosa", "base": "lanzarote",
             "hours": 6.0, "slot": _MORNING,
             "how": "venticinque minuti da Órzola: sull'isola non ci sono strade asfaltate, "
                    "ci si muove in bici o in fuoristrada condiviso", "tier": EXTRA},
            {"name": "Mercato domenicale di Teguise", "label": "Teguise",
             "base": "lanzarote", "hours": 2.5, "slot": _MORNING,
             "how": "l'antica capitale si riempie di banchi la domenica mattina: "
                    "artigianato, aloe e formaggi, con la musica dal vivo in piazza",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Lanzarote vulcanica",
             "for_who": "Timanfaya, le grotte laviche e le vigne nella cenere."},
            {"days": 8, "title": "Lanzarote e le isole",
             "for_who": "Aggiunge Papagayo, La Graciosa e le opere di Manrique."},
        ],
    },

    # =====================================================================
    # 71 — HURGHADA
    # =====================================================================
    71: {
        "bases": [
            {"key": "hurghada", "name": "Hurghada", "night_weight": 1, "max_nights": 12,
             "transfer_h": 0.0,
             "note": "Costa di resort sul Mar Rosso: si sta in struttura e le escursioni "
                     "si prenotano in hotel, il centro città è a parte."},
        ],
        "places": [
            {"name": "Isola di Giftun", "label": "Giftun", "base": "hurghada", "hours": 7.0,
             "slot": _MORNING,
             "how": "in barca dal porto, con due o tre soste di snorkeling sulla barriera "
                    "e sosta sulla spiaggia di Mahmya: si parte alle otto", "tier": MUST},
            {"name": "Immersione sulla barriera", "label": "Immersione", "base": "hurghada",
             "hours": 5.0, "slot": _MORNING,
             "how": "il Mar Rosso ha visibilità altissima tutto l'anno: i centri diving "
                    "fanno battesimi in mare aperto anche senza brevetto", "tier": MUST},
            {"name": "Safari nel deserto in quad", "label": "Deserto", "base": "hurghada",
             "hours": 5.0, "slot": _AFTERNOON,
             "how": "quad tra le montagne rosse e cena in un campo beduino: "
                    "si parte nel pomeriggio per evitare le ore centrali", "tier": MUST},
            {"name": "Luxor in giornata", "label": "Luxor", "base": "hurghada", "hours": 12.0,
             "slot": _MORNING,
             "how": "quattro ore d'auto per senso di marcia: la Valle dei Re, "
                    "Karnak e il tempio di Hatshepsut. È una giornata durissima ma è l'Egitto",
             "tier": MUST},
            {"name": "Cena di cucina egiziana", "label": "Cena egiziana", "base": "hurghada",
             "hours": 2.5, "slot": _EVENING,
             "how": "koshari, ful e pesce alla griglia nei ristoranti del centro, "
                    "fuori dai buffet dei resort", "tier": MUST},
            {"name": "El Gouna", "base": "hurghada", "hours": 4.0, "slot": None,
             "how": "mezz'ora a nord: una cittadina costruita su lagune e canali, "
                    "si gira in barca-taxi tra le isole artificiali", "tier": EXTRA},
            {"name": "Mercato vecchio di Hurghada", "label": "Souk", "base": "hurghada",
             "hours": 2.0, "slot": _EVENING,
             "how": "il souk ristrutturato in centro: spezie, papiri e argento, "
                    "e si contratta su tutto senza eccezioni", "tier": EXTRA},
            {"name": "Snorkeling all'Orange Bay", "label": "Orange Bay", "base": "hurghada",
             "hours": 6.0, "slot": _MORNING,
             "how": "spiaggia bianchissima su un'isola davanti alla costa, con la barriera "
                    "che comincia a pochi metri dalla riva", "tier": EXTRA},
            {"name": "Uscita in sottomarino", "label": "Sottomarino", "base": "hurghada",
             "hours": 3.0, "slot": None,
             "how": "semi-sommergibile con oblò sotto il livello del mare: "
                    "l'unico modo di vedere la barriera senza entrare in acqua", "tier": EXTRA},
            {"name": "Kitesurf a Makadi Bay", "label": "Kitesurf", "base": "hurghada",
             "hours": 3.5, "slot": _AFTERNOON,
             "how": "vento costante e laguna poco profonda: è la zona dove imparano "
                    "quasi tutti sul Mar Rosso", "tier": EXTRA},
        ],
        "variants": [
            {"days": 5, "title": "Mar Rosso in resort",
             "for_who": "Barriera, isole e deserto: la settimana di mare senza pensieri."},
            {"days": 8, "title": "Mar Rosso ed Egitto antico",
             "for_who": "Aggiunge Luxor, le lagune e le immersioni più lontane."},
        ],
    },

    # =====================================================================
    # 72 — AQABA
    # =====================================================================
    72: {
        "bases": [
            {"key": "aqaba", "name": "Aqaba", "night_weight": 2, "max_nights": 6,
             "transfer_h": 0.0,
             "note": "L'unico sbocco sul mare della Giordania: base per le immersioni "
                     "e punto di partenza per Wadi Rum e Petra."},
            {"key": "wadirum", "name": "Wadi Rum", "night_weight": 1, "max_nights": 3,
             "transfer_h": 1.2,
             "note": "Un'ora nel deserto: si dorme nei campi beduini, e dentro la riserva "
                     "ci si muove solo con i fuoristrada delle guide locali."},
        ],
        "places": [
            {"name": "Immersione sulla barriera di Aqaba", "label": "Barriera",
             "base": "aqaba", "hours": 4.0, "slot": _MORNING,
             "how": "molti punti si raggiungono da riva senza barca: coralli intatti "
                    "e relitti affondati apposta, tra cui un aereo militare", "tier": MUST},
            {"name": "Petra in giornata", "label": "Petra", "base": "aqaba", "hours": 10.0,
             "slot": _MORNING,
             "how": "due ore d'auto a nord: si attraversa il Siq a piedi fino al Tesoro, "
                    "e per il Monastero servono 800 gradini in più. Si parte all'alba",
             "tier": MUST},
            {"name": "Snorkeling alla Japanese Garden", "label": "Snorkeling",
             "base": "aqaba", "hours": 3.0, "slot": None,
             "how": "si entra dalla spiaggia a sud della città: il giardino di coralli "
                    "molli comincia a pochi metri dalla riva", "tier": MUST},
            {"name": "Cena di mansaf o pesce sul golfo", "label": "Cena giordana",
             "base": "aqaba", "hours": 2.5, "slot": _EVENING,
             "how": "sul lungomare si vedono contemporaneamente le luci di quattro paesi: "
                    "Giordania, Israele, Egitto e Arabia Saudita", "tier": MUST},
            {"name": "Forte di Aqaba e centro città", "label": "Aqaba", "base": "aqaba",
             "hours": 2.0, "slot": None,
             "how": "a piedi tra il forte mamelucco, il museo e il souk: la città "
                    "è piccola e si gira in un pomeriggio", "tier": EXTRA},
            {"name": "Fuoristrada nel Wadi Rum", "label": "Wadi Rum", "base": "wadirum",
             "hours": 6.0, "slot": _MORNING,
             "how": "in pick-up con guida beduina tra i monoliti di arenaria, "
                    "le dune rosse e i graffiti nabatei sulle pareti", "tier": MUST},
            {"name": "Notte nel campo beduino", "label": "Campo beduino", "base": "wadirum",
             "hours": 4.0, "slot": _EVENING,
             "how": "cena zarb cotta sotto la sabbia, poi il cielo: nel deserto "
                    "di Wadi Rum non c'è nessuna luce artificiale nel raggio di chilometri",
             "tier": MUST},
            {"name": "Alba sulle dune rosse", "label": "Alba nel deserto",
             "base": "wadirum", "hours": 2.0, "slot": _MORNING,
             "how": "si sale a piedi su una duna vicino al campo prima che schiarisca: "
                    "l'arenaria passa dal viola all'arancio in venti minuti", "tier": MUST},
            {"name": "Ponte di roccia di Burrah", "label": "Burrah", "base": "wadirum",
             "hours": 3.0, "slot": None,
             "how": "arco naturale che si raggiunge con una breve arrampicata "
                    "sulla roccia: si sale senza corda ma serve passo fermo", "tier": EXTRA},
            {"name": "Mar Morto in giornata", "label": "Mar Morto", "base": "aqaba",
             "hours": 8.0, "slot": _MORNING,
             "how": "tre ore verso nord lungo la valle: si galleggia senza sforzo "
                    "e ci si copre di fango nero, ma non si mette la testa sotto", "tier": EXTRA},
            {"name": "Relitto del Cedar Pride", "label": "Cedar Pride", "base": "aqaba",
             "hours": 3.0, "slot": None,
             "how": "un mercantile affondato apposta nel 1985 e ormai ricoperto di coralli: "
                    "sta a venticinque metri, quindi serve il brevetto", "tier": EXTRA},
            {"name": "Giro in barca con fondo trasparente", "label": "Barca a fondo trasparente",
             "base": "aqaba", "hours": 3.0, "slot": None,
             "how": "si esce dal porto turistico e si guardano i coralli e il carro armato "
                    "affondato senza bagnarsi: adatto anche con bambini", "tier": EXTRA},
            {"name": "South Beach di Aqaba", "label": "South Beach", "base": "aqaba",
             "hours": 3.5, "slot": None,
             "how": "la costa a sud verso il confine saudita: qui si entra in acqua "
                    "direttamente da riva sopra la barriera, con lo snorkeling migliore",
             "tier": EXTRA},
            {"name": "Souk di Aqaba", "label": "Souk", "base": "aqaba", "hours": 1.5,
             "slot": _EVENING,
             "how": "il mercato del centro apre nel tardo pomeriggio: spezie, datteri "
                    "e caffè al cardamomo macinato davanti a te", "tier": EXTRA},
            {"name": "Canyon di Khazali", "label": "Khazali", "base": "wadirum", "hours": 2.0,
             "slot": None,
             "how": "una fenditura stretta nella roccia in cui si entra a piedi: "
                    "sulle pareti ci sono petroglifi nabatei e thamudeni", "tier": EXTRA},
            {"name": "Lawrence Spring", "label": "Lawrence Spring", "base": "wadirum",
             "hours": 2.0, "slot": None,
             "how": "una breve salita ripida fino alla sorgente citata da Lawrence d'Arabia: "
                    "dall'alto si vede tutta la piana rossa", "tier": EXTRA},
            {"name": "Tramonto dalla duna rossa", "label": "Tramonto nel deserto",
             "base": "wadirum", "hours": 2.0, "slot": _EVENING,
             "how": "si sale scalzi sulla sabbia fino in cima e ci si siede: "
                    "il sole scende dietro le montagne e la temperatura crolla subito",
             "tier": MUST},
            {"name": "Salita al Jebel Umm ad Dami", "label": "Umm ad Dami",
             "base": "wadirum", "hours": 6.0, "slot": _MORNING,
             "how": "la montagna più alta della Giordania: si arriva in fuoristrada "
                    "alla base e poi due ore di salita su roccia, con vista fino all'Arabia Saudita",
             "tier": EXTRA},
            {"name": "Wadi Rum in cammello", "label": "Cammello", "base": "wadirum",
             "hours": 2.5, "slot": None,
             "how": "il passo del cammello è il ritmo con cui i beduini attraversano "
                    "questo deserto da sempre: si va al passo, non si corre", "tier": EXTRA},
            {"name": "Mongolfiera su Wadi Rum", "label": "Mongolfiera", "base": "wadirum",
             "hours": 3.0, "slot": _MORNING,
             "how": "decollo all'alba dalla piana: un'ora sopra i monoliti, "
                    "quando la sabbia è ancora arancione", "tier": EXTRA,
             "months": [9, 10, 11, 12, 1, 2, 3, 4],
             "note": "I voli si fanno nella stagione fresca: d'estate le termiche del deserto li impediscono."},
        ],
        "variants": [
            {"days": 6, "title": "Mar Rosso e deserto",
             "for_who": "Barriera, Wadi Rum e una notte sotto le stelle."},
            {"days": 9, "title": "Giordania del sud",
             "for_who": "Aggiunge Petra, il Mar Morto e più giorni di immersione."},
        ],
    },

    # =====================================================================
    # 73 — ISOLE LOFOTEN
    # =====================================================================
    73: {
        "bases": [
            {"key": "lofoten", "name": "Reine e Moskenes", "night_weight": 1,
             "max_nights": 10, "transfer_h": 0.0,
             "note": "Si dorme nei rorbuer, le vecchie capanne rosse dei pescatori "
                     "sull'acqua. Serve l'auto: l'arcipelago è lungo centocinquanta chilometri."},
        ],
        "places": [
            {"name": "Reine e Hamnøy", "label": "Reine", "base": "lofoten", "hours": 3.0,
             "slot": None,
             "how": "i villaggi di capanne rosse sotto le pareti verticali: "
                    "la vista classica si ha dal ponte di Hamnøy, fermandosi in piazzola",
             "tier": MUST},
            {"name": "Spiaggia di Haukland", "label": "Haukland", "base": "lofoten",
             "hours": 3.0, "slot": None,
             "how": "sabbia bianca e acqua turchese sotto le montagne artiche: "
                    "sembra tropicale ma l'acqua è a otto gradi", "tier": MUST},
            {"name": "Caccia all'aurora boreale", "label": "Aurora", "base": "lofoten",
             "hours": 4.0, "slot": _EVENING,
             "how": "qui non serve un tour: si esce in auto verso una spiaggia a nord "
                    "e si aspetta, con le montagne che entrano nell'inquadratura",
             "tier": MUST, "months": [9, 10, 11, 12, 1, 2, 3],
             "note": "Serve buio: da maggio a luglio il sole non tramonta mai."},
            {"name": "Villaggio di Å", "label": "Å", "base": "lofoten", "hours": 2.5,
             "slot": None,
             "how": "l'ultimo paese della strada, dove finisce la E10: museo del merluzzo "
                    "essiccato e i telai di legno dove il pesce pende ad asciugare",
             "tier": MUST},
            {"name": "Salita al Reinebringen", "label": "Reinebringen", "base": "lofoten",
             "hours": 4.0, "slot": _MORNING,
             "how": "1.900 gradini di pietra costruiti da sherpa nepalesi: due ore "
                    "andata e ritorno, ripidissime, per la vista più famosa di Norvegia",
             "tier": MUST, "months": [6, 7, 8, 9],
             "note": "La scalinata è chiusa o pericolosa con neve e ghiaccio, quindi solo d'estate."},
            {"name": "Sole di mezzanotte", "label": "Sole di mezzanotte", "base": "lofoten",
             "hours": 3.0, "slot": _EVENING,
             "how": "si va su una spiaggia esposta a nord verso mezzanotte: "
                    "il sole scende, sfiora il mare e risale senza tramontare", "tier": MUST,
             "months": [5, 6, 7]},
            {"name": "Nusfjord", "base": "lofoten", "hours": 2.5, "slot": None,
             "how": "uno dei villaggi di pescatori meglio conservati, protetto "
                    "come museo vivente: si paga un piccolo ingresso e si gira a piedi",
             "tier": EXTRA},
            {"name": "Uscita in mare per le orche", "label": "Orche", "base": "lofoten",
             "hours": 5.0, "slot": _MORNING,
             "how": "in gommone o barca a vela quando le aringhe entrano nei fiordi "
                    "e si portano dietro orche e megattere", "tier": EXTRA,
             "months": [11, 12, 1],
             "note": "Le orche seguono le aringhe in questi fiordi solo nel tardo autunno e inizio inverno."},
            {"name": "Cena di stoccafisso e merluzzo", "label": "Cena norvegese",
             "base": "lofoten", "hours": 2.5, "slot": _EVENING,
             "how": "lo skrei fresco d'inverno, lo stoccafisso il resto dell'anno, "
                    "spesso servito nei rorbuer ristrutturati sull'acqua", "tier": EXTRA},
            {"name": "Kayak tra i fiordi", "label": "Kayak", "base": "lofoten", "hours": 4.0,
             "slot": None,
             "how": "si pagaia dentro i bracci di mare tra le pareti di granito, "
                    "con le aquile di mare che volano sopra", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9]},
        ],
        "variants": [
            {"days": 4, "title": "Lofoten essenziali",
             "for_who": "Reine, le spiagge artiche e i villaggi di pescatori."},
            {"days": 6, "title": "Lofoten da un capo all'altro",
             "for_who": "Aggiunge le salite panoramiche, il mare e le notti ad aspettare il cielo."},
        ],
    },

    # =====================================================================
    # 74 — TALLINN
    # =====================================================================
    74: {
        "bases": [
            {"key": "tallinn", "name": "Tallinn", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città vecchia medievale piccolissima e tutta pedonale: "
                     "si gira in un giorno, e il resto è a pochi minuti di tram."},
        ],
        "places": [
            {"name": "Città Vecchia e piazza del Municipio", "label": "Città Vecchia",
             "base": "tallinn", "hours": 3.0, "slot": None,
             "how": "a piedi dentro le mura: è una delle città medievali meglio conservate "
                    "d'Europa, e il municipio gotico è ancora quello originale", "tier": MUST},
            {"name": "Collina di Toompea", "label": "Toompea", "base": "tallinn", "hours": 2.0,
             "slot": _MORNING,
             "how": "si sale per la Pikk jalg fino ai due belvedere: da Kohtuotsa "
                    "si vedono i tetti rossi e le torri, ed è la foto simbolo della città",
             "tier": MUST},
            {"name": "Mercatino di Natale in Raekoja plats", "label": "Mercatini",
             "base": "tallinn", "hours": 2.0, "slot": _EVENING,
             "how": "attorno all'albero nella piazza medievale: si beve il glögi "
                    "e si mangiano le salsicce, con la neve quasi garantita", "tier": MUST,
             "months": [11, 12, 1]},
            {"name": "Telliskivi Creative City", "label": "Telliskivi", "base": "tallinn",
             "hours": 2.5, "slot": None,
             "how": "ex complesso ferroviario sovietico diventato quartiere creativo: "
                    "murales, mercato coperto e locali, dieci minuti a piedi dalle mura",
             "tier": MUST},
            {"name": "Cena estone medievale", "label": "Cena medievale", "base": "tallinn",
             "hours": 2.5, "slot": _EVENING,
             "how": "nelle taverne a lume di candela dentro la Città Vecchia: "
                    "zuppa d'orzo, selvaggina e birra scura servita in boccali di terracotta",
             "tier": MUST},
            {"name": "Palazzo e parco di Kadriorg", "label": "Kadriorg", "base": "tallinn",
             "hours": 2.5, "slot": None,
             "how": "in tram dal centro: palazzo barocco fatto costruire da Pietro il Grande, "
                    "con il museo d'arte estone nel parco accanto", "tier": EXTRA},
            {"name": "Porto degli idrovolanti", "label": "Lennusadam", "base": "tallinn",
             "hours": 2.5, "slot": None,
             "how": "un hangar di cemento del 1917 con dentro un sottomarino "
                    "in cui si entra: è il museo marittimo, ottimo anche con bambini",
             "tier": EXTRA},
            {"name": "Mura e torri di Tallinn", "label": "Mura", "base": "tallinn",
             "hours": 1.5, "slot": None,
             "how": "si sale sui camminamenti di ronda e si passa da una torre all'altra: "
                    "restano quasi due chilometri di cinta e venti torri", "tier": EXTRA},
            {"name": "Quartiere di Kalamaja", "label": "Kalamaja", "base": "tallinn",
             "hours": 2.0, "slot": None,
             "how": "case di legno colorate a due piani vicino al mare: era il quartiere "
                    "dei pescatori, oggi è dove si mangia meglio spendendo poco", "tier": EXTRA},
            {"name": "Sauna estone", "label": "Sauna", "base": "tallinn", "hours": 2.0,
             "slot": _EVENING,
             "how": "la sauna qui è un rito sociale: si alterna il calore secco "
                    "al tuffo nell'acqua fredda, e ci si frusta con rami di betulla",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Tallinn medievale",
             "for_who": "Le mura, i tetti rossi e le taverne: la città vecchia in tre giorni."},
            {"days": 5, "title": "Tallinn oltre le mura",
             "for_who": "Aggiunge i quartieri creativi, il mare e i palazzi imperiali."},
        ],
    },

    # =====================================================================
    # 75 — TBILISI
    # =====================================================================
    75: {
        "bases": [
            {"key": "tbilisi", "name": "Tbilisi", "night_weight": 2, "max_nights": 7,
             "transfer_h": 0.0,
             "note": "Città vecchia stretta nella gola del fiume: si cammina molto "
                     "in salita, e la funivia sostituisce mezz'ora di scalinate."},
            {"key": "kazbegi", "name": "Kazbegi", "night_weight": 1, "max_nights": 3,
             "transfer_h": 3.0,
             "note": "Tre ore a nord lungo la Strada Militare Georgiana, fino al confine "
                     "russo: alta montagna vera, con il Caucaso a cinquemila metri."},
        ],
        "places": [
            {"name": "Bagni sulfurei di Abanotubani", "label": "Bagni sulfurei",
             "base": "tbilisi", "hours": 2.0, "slot": _AFTERNOON,
             "how": "cupole di mattoni sopra le sorgenti calde: si affitta una stanza "
                    "privata a ore, e il massaggio con il guanto ruvido si paga a parte",
             "tier": MUST},
            {"name": "Fortezza di Narikala in funivia", "label": "Narikala",
             "base": "tbilisi", "hours": 2.5, "slot": _EVENING,
             "how": "la cabinovia parte dal parco Rike e costa quanto un biglietto "
                    "del bus: dall'alto si vede la città vecchia stretta nella gola",
             "tier": MUST},
            {"name": "Città vecchia e case con i balconi", "label": "Città vecchia",
             "base": "tbilisi", "hours": 3.0, "slot": None,
             "how": "a piedi tra le case con i ballatoi di legno intagliato, "
                    "molte ancora fatiscenti: è la Tbilisi che sta sparendo in fretta",
             "tier": MUST},
            {"name": "Cena georgiana con khinkali e khachapuri", "label": "Cena georgiana",
             "base": "tbilisi", "hours": 2.5, "slot": _EVENING,
             "how": "i khinkali si prendono con le mani per il ciuffo, si morde "
                    "e si beve il brodo dentro: il ciuffo non si mangia", "tier": MUST},
            {"name": "Degustazione di vini in anfora", "label": "Vino in qvevri",
             "base": "tbilisi", "hours": 2.0, "slot": None,
             "how": "la Georgia fa vino da ottomila anni fermentandolo in anfore "
                    "interrate: i bianchi macerati escono ambrati", "tier": MUST},
            {"name": "Fabrika", "base": "tbilisi", "hours": 2.0, "slot": _EVENING,
             "how": "ex fabbrica sovietica di cucito diventata ostello e cortile "
                    "di bar: è il centro della vita notturna giovane della città", "tier": EXTRA},
            {"name": "Mtskheta", "base": "tbilisi", "hours": 4.0, "slot": None,
             "how": "mezz'ora fuori città: l'antica capitale con la cattedrale Svetitskhoveli "
                    "e il monastero di Jvari sulla collina sopra la confluenza dei fiumi",
             "tier": MUST},
            {"name": "Chiesa della Trinità di Gergeti", "label": "Gergeti",
             "base": "kazbegi", "hours": 5.0, "slot": _MORNING,
             "how": "la chiesa isolata a 2.170 metri sotto il monte Kazbek: "
                    "si sale a piedi in due ore o in fuoristrada per la pista sterrata",
             "tier": MUST},
            {"name": "Strada Militare Georgiana", "label": "Strada Militare",
             "base": "kazbegi", "hours": 4.0, "slot": None,
             "how": "la strada storica verso il Caucaso, con la fortezza di Ananuri "
                    "sul lago e il monumento sovietico dell'amicizia sul passo", "tier": MUST},
            {"name": "Valle di Truso", "label": "Truso", "base": "kazbegi", "hours": 6.0,
             "slot": _MORNING,
             "how": "una gola con sorgenti minerali che colorano la roccia di arancione "
                    "e villaggi abbandonati: si cammina in piano per ore", "tier": EXTRA,
             "months": [5, 6, 7, 8, 9, 10],
             "note": "La valle è raggiungibile solo nella stagione senza neve."},
        ],
        "variants": [
            {"days": 4, "title": "Tbilisi e i suoi bagni",
             "for_who": "Città vecchia, bagni sulfurei e cucina georgiana."},
            {"days": 7, "title": "Georgia dal Caucaso alla capitale",
             "for_who": "Aggiunge le montagne di Kazbegi, i monasteri e le cantine."},
        ],
    },

    # =====================================================================
    # 76 — YEREVAN
    # =====================================================================
    76: {
        "bases": [
            {"key": "yerevan", "name": "Yerevan", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città bassa e ordinata di tufo rosa: il centro si gira a piedi, "
                     "e tutte le grandi visite sono escursioni in giornata."},
        ],
        "places": [
            {"name": "Cascade e Piazza della Repubblica", "label": "Cascade",
             "base": "yerevan", "hours": 2.5, "slot": _EVENING,
             "how": "una scalinata monumentale con sculture e scale mobili interne: "
                    "in cima si vede il monte Ararat, e alla base le fontane danzanti "
                    "della piazza si accendono dopo il tramonto", "tier": MUST},
            {"name": "Monasteri di Garni e Geghard", "label": "Garni e Geghard",
             "base": "yerevan", "hours": 6.0, "slot": _MORNING,
             "how": "un'ora a est: un tempio ellenistico sulla gola e, poco oltre, "
                    "un monastero scavato dentro la roccia dove i canti risuonano",
             "tier": MUST},
            {"name": "Monastero di Khor Virap", "label": "Khor Virap", "base": "yerevan",
             "hours": 4.0, "slot": _MORNING,
             "how": "sulla pianura al confine turco: è il punto da cui l'Ararat "
                    "si vede più vicino, e si scende nella fossa dove fu imprigionato "
                    "Gregorio l'Illuminatore", "tier": MUST},
            {"name": "Memoriale del genocidio Tsitsernakaberd", "label": "Tsitsernakaberd",
             "base": "yerevan", "hours": 2.5, "slot": None,
             "how": "il memoriale sulla collina e il museo sotterraneo: si entra "
                    "gratuitamente, ed è il luogo che spiega l'Armenia contemporanea",
             "tier": MUST},
            {"name": "Cena armena e degustazione di brandy", "label": "Cena armena",
             "base": "yerevan", "hours": 2.5, "slot": _EVENING,
             "how": "dolma, khorovats alla brace e lavash cotto nel tonir; il brandy "
                    "armeno si assaggia in fabbrica con visita guidata", "tier": MUST},
            {"name": "Mercato Vernissage", "label": "Vernissage", "base": "yerevan",
             "hours": 2.0, "slot": None,
             "how": "mercato all'aperto attivo nel fine settimana: tappeti, "
                    "scacchi intagliati, argenteria sovietica e strumenti musicali",
             "tier": EXTRA},
            {"name": "Matenadaran", "base": "yerevan", "hours": 2.0, "slot": None,
             "how": "l'istituto dei manoscritti antichi in cima al viale: miniature "
                    "e codici armeni, alcuni del quinto secolo", "tier": EXTRA},
            {"name": "Lago Sevan", "label": "Sevan", "base": "yerevan", "hours": 5.0,
             "slot": None,
             "how": "un'ora a nord-est, a 1.900 metri: si sale alla penisola con "
                    "i due monasteri e si mangia il pesce ishkhan del lago", "tier": EXTRA},
            {"name": "Monastero di Tatev e funivia", "label": "Tatev", "base": "yerevan",
             "hours": 10.0, "slot": _MORNING,
             "how": "quattro ore a sud, e poi la funivia più lunga del mondo "
                    "che attraversa la gola in dodici minuti: giornata lunghissima",
             "tier": EXTRA},
            {"name": "Mercato coperto GUM e degustazione di frutta secca",
             "label": "Mercato GUM", "base": "yerevan", "hours": 1.5, "slot": _MORNING,
             "how": "i banchi di albicocche secche, sujuk di noci e spezie: "
                    "si assaggia tutto prima di comprare, ed è previsto", "tier": EXTRA},
        ],
        "variants": [
            {"days": 4, "title": "Yerevan e i monasteri",
             "for_who": "La capitale rosa, Garni, Geghard e l'Ararat all'orizzonte."},
            {"days": 7, "title": "Armenia oltre la capitale",
             "for_who": "Aggiunge il lago Sevan, Tatev e le valli del sud."},
        ],
    },

    # =====================================================================
    # 77 — TIRANA
    # =====================================================================
    77: {
        "bases": [
            {"key": "tirana", "name": "Tirana", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Capitale piccola e in trasformazione continua: il centro "
                     "si gira a piedi, e la montagna è a quindici minuti di funivia."},
        ],
        "places": [
            {"name": "Piazza Skanderbeg", "label": "Piazza Skanderbeg", "base": "tirana",
             "hours": 2.0, "slot": None,
             "how": "la piazza pedonale con il pavimento fatto di pietre da tutta "
                    "l'Albania, la moschea ottomana e la torre dell'orologio", "tier": MUST},
            {"name": "Bunk'Art", "base": "tirana", "hours": 3.0, "slot": None,
             "how": "un bunker antiatomico di cinque piani costruito da Hoxha e riaperto "
                    "come museo: dentro si cammina nei corridoi originali, fa freddo",
             "tier": MUST},
            {"name": "Funivia Dajti Express", "label": "Dajti", "base": "tirana", "hours": 3.5,
             "slot": None,
             "how": "quindici minuti di cabinovia fino a 1.100 metri: dall'alto "
                    "si vede tutta la piana fino al mare nelle giornate limpide", "tier": MUST},
            {"name": "Serata nel quartiere Blloku", "label": "Blloku", "base": "tirana",
             "hours": 2.5, "slot": _EVENING,
             "how": "era la zona riservata alla nomenklatura e vietata ai cittadini, "
                    "oggi è il quartiere dei bar e dei ristoranti", "tier": MUST},
            {"name": "Cena albanese", "label": "Cena albanese", "base": "tirana",
             "hours": 2.5, "slot": _EVENING,
             "how": "tavë kosi, byrek e fërgesë, con il raki servito prima "
                    "e non dopo il pasto", "tier": MUST},
            {"name": "Museo Storico Nazionale", "label": "Museo Nazionale", "base": "tirana",
             "hours": 2.0, "slot": None,
             "how": "sotto il grande mosaico della facciata in piazza: la sezione "
                    "sul periodo comunista è la più impressionante", "tier": EXTRA},
            {"name": "Piramide di Tirana", "label": "Piramide", "base": "tirana",
             "hours": 1.5, "slot": None,
             "how": "il mausoleo di Hoxha abbandonato per decenni e riconvertito "
                    "in centro giovanile: ci si sale sopra per le rampe esterne", "tier": EXTRA},
            {"name": "Kruja", "base": "tirana", "hours": 4.0, "slot": None,
             "how": "quaranta minuti a nord: il castello di Skanderbeg sulla montagna "
                    "e il vecchio bazar di legno con i tappeti e le antichità", "tier": MUST},
            {"name": "Casa delle Foglie", "label": "Casa delle Foglie", "base": "tirana",
             "hours": 1.5, "slot": None,
             "how": "il museo della sorveglianza nell'ex sede della polizia segreta: "
                    "microfoni, schede e fascicoli lasciati come erano", "tier": EXTRA},
            {"name": "Lago artificiale e parco", "label": "Parco del lago",
             "base": "tirana", "hours": 2.0, "slot": _MORNING,
             "how": "a piedi dal centro: è dove i tiranesi corrono e passeggiano "
                    "la mattina presto, con i chioschi di caffè lungo la riva", "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Tirana e il suo passato",
             "for_who": "Bunker, piazze e Blloku: la capitale che sta cambiando faccia."},
            {"days": 5, "title": "Tirana e dintorni",
             "for_who": "Aggiunge Kruja, la montagna e i musei del periodo comunista."},
        ],
    },

    # =====================================================================
    # 78 — OHRID
    # =====================================================================
    78: {
        "bases": [
            {"key": "ohrid", "name": "Ohrid", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città vecchia in salita sopra il lago: si gira tutta a piedi, "
                     "e le barche per i monasteri partono dal porticciolo."},
        ],
        "places": [
            {"name": "Chiesa di San Giovanni a Kaneo", "label": "Kaneo", "base": "ohrid",
             "hours": 2.0, "slot": _EVENING,
             "how": "la chiesetta sulla scogliera a picco sul lago: si arriva a piedi "
                    "lungo la passerella di legno sull'acqua, ed è l'immagine simbolo "
                    "della Macedonia del Nord", "tier": MUST},
            {"name": "Fortezza di Samuele", "label": "Fortezza", "base": "ohrid", "hours": 2.0,
             "slot": None,
             "how": "si sale a piedi dal centro tra le case ottomane: dalle mura "
                    "si vede il lago fino alla riva albanese", "tier": MUST},
            {"name": "Città vecchia e Bazar", "label": "Città vecchia", "base": "ohrid",
             "hours": 2.5, "slot": None,
             "how": "a piedi tra le case a sbalzo con i piani superiori più larghi: "
                    "nel bazar si vendono ancora le perle di Ohrid fatte con le squame di pesce",
             "tier": MUST},
            {"name": "Monastero di San Naum", "label": "San Naum", "base": "ohrid",
             "hours": 5.0, "slot": _MORNING,
             "how": "in barca lungo il lago o in bus fino al confine albanese: "
                    "il monastero è sulla scogliera, e accanto ci sono le sorgenti "
                    "che si visitano in barca a remi", "tier": MUST},
            {"name": "Cena di pesce sul lago", "label": "Cena sul lago", "base": "ohrid",
             "hours": 2.5, "slot": _EVENING,
             "how": "la trota di Ohrid è una specie endemica e la pesca è regolata: "
                    "si mangia nei ristoranti sull'acqua con il vino macedone", "tier": MUST},
            {"name": "Teatro antico", "label": "Teatro antico", "base": "ohrid", "hours": 1.0,
             "slot": None,
             "how": "un teatro ellenistico incastrato tra le case della città vecchia: "
                    "d'estate ci si tengono ancora i concerti del festival", "tier": EXTRA},
            {"name": "Baia delle Ossa", "label": "Baia delle Ossa", "base": "ohrid",
             "hours": 3.0, "slot": None,
             "how": "un villaggio palafitticolo preistorico ricostruito sull'acqua "
                    "come era: si cammina sulle passerelle sopra il lago", "tier": EXTRA},
            {"name": "Spiagge del lago", "label": "Spiagge", "base": "ohrid", "hours": 4.0,
             "slot": None,
             "how": "il lago è balneabile e l'acqua è trasparente: le spiagge attrezzate "
                    "stanno lungo la strada verso San Naum", "tier": EXTRA,
             "months": [6, 7, 8, 9]},
            {"name": "Chiesa di Santa Sofia", "label": "Santa Sofia", "base": "ohrid",
             "hours": 1.5, "slot": None,
             "how": "affreschi bizantini dell'undicesimo secolo sopravvissuti sotto "
                    "l'intonaco del periodo ottomano, quando era una moschea", "tier": EXTRA},
            {"name": "Parco nazionale di Galičica", "label": "Galičica", "base": "ohrid",
             "hours": 5.0, "slot": _MORNING,
             "how": "la montagna che separa il lago di Ohrid da quello di Prespa: "
                    "dalla strada di crinale si vedono i due laghi contemporaneamente",
             "tier": EXTRA, "months": [5, 6, 7, 8, 9, 10]},
        ],
        "variants": [
            {"days": 3, "title": "Ohrid e il suo lago",
             "for_who": "La città vecchia, le chiese bizantine e il lago in barca."},
            {"days": 5, "title": "Ohrid e la Macedonia del sud",
             "for_who": "Aggiunge i monasteri lontani, il parco nazionale e le spiagge."},
        ],
    },

    # =====================================================================
    # 79 — SARAJEVO
    # =====================================================================
    79: {
        "bases": [
            {"key": "sarajevo", "name": "Sarajevo", "night_weight": 1, "max_nights": 10,
             "transfer_h": 0.0,
             "note": "Città stretta in una valle: si cammina lungo un asse solo, "
                     "e in venti minuti si passa dall'Oriente ottomano all'Austria-Ungheria."},
        ],
        "places": [
            {"name": "Baščaršija", "base": "sarajevo", "hours": 2.5, "slot": None,
             "how": "il bazar ottomano con le botteghe dei ramai: al centro c'è "
                    "la fontana Sebilj, e da lì partono i vicoli degli artigiani", "tier": MUST},
            {"name": "Tunnel della Speranza", "label": "Tunnel della Speranza",
             "base": "sarajevo", "hours": 3.0, "slot": None,
             "how": "vicino all'aeroporto: il cunicolo scavato a mano sotto la pista "
                    "che teneva in vita la città durante l'assedio, se ne percorre un tratto",
             "tier": MUST},
            {"name": "Ponte Latino e Museo 1878-1918", "label": "Ponte Latino",
             "base": "sarajevo", "hours": 1.5, "slot": None,
             "how": "l'angolo dove fu ucciso Francesco Ferdinando: il museo accanto "
                    "è piccolo e racconta l'attentato e il periodo austro-ungarico",
             "tier": MUST},
            {"name": "Tramonto dalla Fortezza Gialla", "label": "Fortezza Gialla",
             "base": "sarajevo", "hours": 2.0, "slot": _EVENING,
             "how": "si sale a piedi dal bazar passando accanto al cimitero bianco: "
                    "al tramonto partono i richiami alla preghiera da tutte le moschee "
                    "della valle insieme", "tier": MUST},
            {"name": "Cena di ćevapi", "label": "Ćevapi", "base": "sarajevo", "hours": 2.0,
             "slot": _EVENING,
             "how": "polpettine di carne servite nel pane somun con la cipolla cruda "
                    "e il kajmak: si mangia in piedi o ai tavoli comuni nel bazar",
             "tier": MUST},
            {"name": "Pista da bob olimpica di Trebević", "label": "Trebević",
             "base": "sarajevo", "hours": 3.5, "slot": None,
             "how": "si sale con la funivia dal centro: la pista del 1984 è abbandonata "
                    "nel bosco e ricoperta di murales, si cammina dentro le curve",
             "tier": MUST},
            {"name": "Moschea di Gazi Husrev-beg", "label": "Gazi Husrev-beg",
             "base": "sarajevo", "hours": 1.5, "slot": None,
             "how": "la principale moschea ottomana della città, ancora in funzione: "
                    "si entra fuori dagli orari di preghiera, scalzi e coperti", "tier": EXTRA},
            {"name": "Museo ebraico e sinagoga", "label": "Museo ebraico",
             "base": "sarajevo", "hours": 1.5, "slot": None,
             "how": "nella più antica sinagoga della Bosnia: racconta i sefarditi "
                    "arrivati qui dopo la cacciata dalla Spagna", "tier": EXTRA},
            {"name": "Sorgenti di Vrelo Bosne", "label": "Vrelo Bosne", "base": "sarajevo",
             "hours": 3.0, "slot": None,
             "how": "alla periferia ovest: si percorre un viale alberato di tre chilometri "
                    "a piedi o in carrozza fino alle sorgenti del fiume Bosna", "tier": EXTRA},
            {"name": "Caffè bosniaco in un kafana", "label": "Caffè bosniaco",
             "base": "sarajevo", "hours": 1.5, "slot": None,
             "how": "servito nel bricco di rame con il rahat lokum e una zolletta "
                    "da tenere in bocca: si beve lentamente, è un rito di conversazione",
             "tier": EXTRA},
        ],
        "variants": [
            {"days": 3, "title": "Sarajevo tra Oriente e Occidente",
             "for_who": "Il bazar, l'assedio e le due anime della città in tre giorni."},
            {"days": 5, "title": "Sarajevo a fondo",
             "for_who": "Aggiunge la montagna olimpica, le sorgenti e i musei della memoria."},
        ],
    },
}


def has_curated_places(dest_id: Any) -> bool:
    """True se la meta ha contenuto curato e puo' avere itinerari con nomi
    propri. Le altre restano sul motore generico."""
    try:
        return int(dest_id) in CURATED
    except (TypeError, ValueError):
        return False


def curated_entry(dest_id: Any) -> dict[str, Any] | None:
    try:
        return CURATED.get(int(dest_id))
    except (TypeError, ValueError):
        return None


def in_season(place_list: list[dict[str, Any]], months: list[int] | None) -> list[dict[str, Any]]:
    """I luoghi visitabili nel periodo scelto.

    Un luogo con `months` esce dalla lista se NESSUNO dei mesi richiesti e'
    compatibile: proporre le Gole di Samaria a dicembre, quando il sentiero
    e' chiuso, sarebbe un errore piu' grave del restare sul generico."""
    if not months:
        return list(place_list)
    return [
        p for p in place_list
        if not p.get("months") or any(m in p["months"] for m in months)
    ]


def out_of_season(place_list: list[dict[str, Any]], months: list[int] | None) -> list[dict[str, Any]]:
    """I luoghi tagliati dalla stagione, con la ragione: vanno detti, non
    nascosti — "Samaria non c'e' perche' a dicembre e' chiusa" e'
    informazione utile quanto l'itinerario stesso."""
    if not months:
        return []
    return [
        p for p in place_list
        if p.get("months") and not any(m in p["months"] for m in months)
    ]


