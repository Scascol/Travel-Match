# ✈️ TravelMatch

**Dove dovresti andare davvero in vacanza?**

App di travel matching che aiuta a scegliere la meta giusta rispondendo a un
questionario — offline, senza AI generativa, senza chiamate di rete. Il
dataset (79 destinazioni reali) e il motore di scoring sono scritti a mano;
Streamlit fa solo da interfaccia.

Funziona per **qualunque periodo dell'anno**: weekend, stagioni, o le feste
di Natale/Capodanno. Il periodo scelto dà solo un piccolo boost coerente
quando è esplicitamente festivo (vedi §3) — mai un bias di default.

Oltre alle **singole destinazioni**, TravelMatch è anche un **Trip Builder**:
propone itinerari di 2-3 tappe (es. "Istanbul & Cappadocia") solo quando sono
davvero fattibili, mai solo perché il punteggio è alto (§6).

Ogni meta e ogni viaggio combinato hanno un **itinerario giorno per giorno con
luoghi reali** — 911 luoghi curati con base logistica, modalità di visita e
stagionalità, non nomi generati (§8).

---

## Indice

1. [Installazione e struttura](#1-installazione-e-struttura)
2. [Architettura](#2-architettura)
3. [Il Travel Match Score](#3-il-travel-match-score)
4. [Travel DNA](#4-travel-dna)
5. [Costi: scenari, dati statici, stagionalità](#5-costi-scenari-dati-statici-stagionalità)
6. [Trip Builder — viaggi combinati](#6-trip-builder--viaggi-combinati)
7. [Dettagli di ogni meta](#7-dettagli-di-ogni-meta)
8. [Itinerari giorno per giorno](#8-itinerari-giorno-per-giorno)
9. [Modalità di ricerca](#9-modalità-di-ricerca)
10. [Confronto e "I miei viaggi"](#10-confronto-e-i-miei-viaggi)
11. [Export e condivisione](#11-export-e-condivisione)
12. [Interfaccia](#12-interfaccia)
13. [Estendere il dataset](#13-estendere-il-dataset)
14. [Note di robustezza](#14-note-di-robustezza)

---

## 1. Installazione e struttura

Requisiti: **Python 3.11+**. Le librerie in `requirements.txt` sono bloccate
sulle versioni con cui l'app è stata provata (Streamlit 1.58.0, pandas 3.0.3,
reportlab 5.0.1, Pillow 12.2.0): così Streamlit Cloud installa esattamente
quelle, invece delle più recenti. Per aggiornarle si cambia il numero, si
riprova tutto in locale e solo dopo si carica.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Si apre su `http://localhost:8501`. Il motore non fa chiamate di rete: il
dataset è locale (`destinations.py`). Solo le foto delle mete arrivano da
internet, caricate dal browser del visitatore; senza connessione al loro posto
resta un gradiente, mai un'immagine rotta.

```text
travelmatch/
├── app.py                  # interfaccia Streamlit (UI, stato, pagine) — nessuna logica di scoring
├── recommender.py          # motore di scoring per singola destinazione (zero dipendenze da Streamlit)
├── trip_builder.py         # motore Trip Builder (itinerari multi-tappa) + confronto viaggi
├── trip_routes.py          # rotte tra destinazioni + trip template curati a mano
├── trip_presentation.py    # spiegazioni, timeline ed export testuale dei viaggi combinati
├── destinations.py         # dataset locale (79 destinazioni) + ritmo/stagionalità derivati
├── places.py               # luoghi curati per meta (911 voci): basi, durate, modalità, stagionalità
├── catalog.py              # scheda vetrina di ogni meta: slug per i link, foto con crediti, zona, descrizione
├── travel_estimates.py     # come arrivarci da Milano/Bergamo/Roma: aereo, treno, auto, auto+traghetto
├── insights.py             # Travel Style, DNA vs meta, giorno tipo, avvisi, anti-FOMO, facilità organizzativa
├── itinerary.py            # itinerari giorno per giorno (curati e generici), mobilità, zone, prenotazioni
├── checklist.py            # checklist di viaggio (cosa portare/lasciare a casa, documenti, consigli)
├── utils.py                # costanti del questionario, Travel DNA, formattazione, scenari di costo
├── export.py               # export testo/PDF/"stories" di destinazioni e viaggi combinati
├── social_card.py          # immagine + didascalia "social" condivisibile
├── requirements.txt
└── .streamlit/config.toml  # tema colori nativo Streamlit
```

---

## 2. Architettura

Quattro livelli indipendenti:

- **`destinations.py` — dati.** Ogni destinazione è un dizionario a schema
  fisso (~35 campi autorati + colonne derivate come `pace_score` e
  `seasonal_profile`, calcolate da `load_destinations_df()`). Aggiungere una
  meta non richiede toccare il motore.
- **`places.py` — dati, secondo livello.** I luoghi con nome proprio di ogni
  meta, con base logistica, durata, modalità di visita e stagionalità. È
  separato da `destinations.py` perché serve solo agli itinerari e perché
  cresce con una granularità diversa: una meta ha ~35 campi, ma dai 10 ai 20
  luoghi.
- **`catalog.py` — vetrina.** Come si presenta una meta fuori dal
  questionario: slug stabile per i link (`?meta=creta`), foto Wikimedia con
  autore e licenza, zona del mondo, descrizione di una riga. È pensato come
  base dati anche per un futuro sito con dominio proprio.
- **`recommender.py` / `trip_builder.py` — motore.** Puro Python + pandas,
  **zero dipendenze da Streamlit**: testabile in isolamento, riusabile in
  un'API o un altro frontend.
- **`utils.py`, `insights.py`, `itinerary.py`, `checklist.py`, `export.py`,
  `social_card.py` — presentazione.** Leggono dati già calcolati dal motore e
  li trasformano in testo/immagini per l'utente. Non alterano mai uno score.
- **`app.py` — interfaccia.** Orchestrazione delle pagine via
  `st.session_state`, rendering delle card, CSS. Chiama gli altri moduli,
  non contiene logica propria di scoring.

Regola pratica: se una modifica cambia *quanto* una meta matcha, va in
`recommender.py`/`trip_builder.py`. Se cambia solo *come viene raccontata*,
va in uno dei moduli di presentazione.

---

## 3. Il Travel Match Score

Ogni destinazione riceve uno score 0-100, media pesata di componenti già
0-100 ciascuna. Pesi centralizzati in `recommender.DEFAULT_WEIGHTS`:

```python
DEFAULT_WEIGHTS = {
    "budget": 0.19, "mood": 0.17, "climate": 0.13, "season": 0.10,
    "duration": 0.10, "social": 0.09, "comfort": 0.05, "distance": 0.09,
    "pace": 0.08,
}
```

| Componente | Cosa confronta |
|---|---|
| **budget** | Il budget indicato vs lo scenario **Economico** della meta (`total_cost_min`, "da X €" corretto per stagione — §5). Mai la media o lo scenario Elevato: un budget contenuto non deve escludere mete raggiungibili scegliendo l'alloggio giusto. |
| **mood** | Affinità con i mood scelti + overlap dei tag speciali. |
| **climate** | Clima tipico della meta vs quello richiesto. |
| **season** | Sovrapposizione con `best_months`. Solo per Natale/Capodanno si somma un bonus festivo (mercatini/neve o fuga al caldo) — mai per gli altri periodi. |
| **duration** | Sovrapposizione tra giorni desiderati e durata consigliata. |
| **social** | Distanza tra lo slider di socialità e il livello sociale tipico della meta. |
| **comfort** | Distanza tra il comfort desiderato e il `comfort_level` della meta. |
| **distance** | Ore di viaggio col mezzo scelto (`travel_hours`) vs limite scelto; senza città di partenza, ore di volo. |
| **pace** | Il ritmo della meta (`pace_score`, formula in §6) vs l'intensità richiesta nel questionario. |

Componenti secondarie a peso zero (romantic, adventure, relax, food, luxury,
snow, warm) si attivano solo con i pulsanti di raffinamento rapido
(`apply_refinement()`), senza ripetere il questionario. Lo score resta
sempre normalizzato 0-100 sulla somma dei pesi effettivamente attivi.

**Hard constraint**: oltre allo score continuo, `_meets_strict_criteria`
verifica budget (≤ scenario Economico + 15%), volo, durata e periodo. Se
meno di 5 mete rispettano tutti i criteri, l'app lo dichiara e completa con
le migliori alternative, segnalando in ogni card quale criterio è stato
ammorbidito ("Piccolo compromesso su: budget").

**Spiegazione del match**: `explain_match()` individua le componenti che si
discostano di più (in positivo) da un valore neutro — non semplicemente le
più alte, per non "spiegare" ogni risultato con ciò che è sempre alto per
costruzione. In UI questa frase è il fallback di `narrative_explanation()`
(§7), usata quando non c'è abbastanza materiale per una spiegazione più ricca.

**🎲 Sorprendimi**: `surprise_me()` filtra le mete con match ≥ 65% (soglia
che scende se il pool è vuoto), esclude quelle già mostrate, e sceglie con
un bias verso posizioni meno scontate del ranking — coerente ma raramente
banale. **Sorpresa controllata** (§9) è la variante con vincoli duri
espliciti invece delle preferenze complete.

---

## 4. Travel DNA

`utils.compute_travel_dna` calcola **solo dalle preferenze** (non dal
dataset) 10 tratti 0-100 — Adventure, Nature, Food, Social, Relax, Luxury,
Culture, Romance, Snow, Warmth — con una descrizione automatica. Sempre
visibile in sidebar, si aggiorna a ogni cambio di preferenze.

**DNA vs meta** (`insights.dna_vs_destination`): confronto tratto per
tratto tra il profilo utente e quello della destinazione, con tre stati —
*in linea* (scarto ≤ 18 punti), *offre di più*, *offre meno di quanto
cerchi*. In UI due barre sovrapposte per tratto, mostrate solo se almeno un
valore supera 25 (altrimenti righe quasi vuote senza informazione).

---

## 5. Costi: scenari, dati statici, stagionalità

Nel questionario il budget è **esplicitamente per persona o totale per il
gruppo** : se scelto "totale", viene diviso per il
numero di persone (`utils.PEOPLE_HEADCOUNT`) prima di entrare nello scoring — internamente il motore
lavora sempre e solo con un budget per persona.

**Tre scenari** (`utils.cost_scenarios`), letti dallo stesso range
min/max già nel dataset:

| Scenario | Cosa rappresenta | Nello score? |
|---|---|---|
| 🟢 Economico | hostel/1-2★, il minimo del range — il "da X €" mostrato ovunque | **Sì**, unico scenario usato da scoring e hard constraint (§3) |
| 🟡 Medio | 3★/B&B, punto medio | No — solo informativo, avviso soft se sfora il budget oltre il 15% |
| 🔴 Elevato | 4-5★, massimo maggiorato del 15% | No — solo informativo |

**Dati statici realistici**: i range (volo da Italia + hotel + cibo +
attività, per la durata consigliata) sono stime calibrate su medie di
mercato 2023-2025, non aggiornate dinamicamente (nessuna API).

**Stagionalità** (`destinations.py`): i range restano una media annua; un
fattore per mese la corregge secondo il profilo della meta —

| Profilo | Curva | Esempio |
|---|---|---|
| `beach` | picco lug-ago, minimo inverno | Mediterraneo (Creta, Santorini) |
| `winter_sun` | opposta a `beach`: picco dic-feb, minimo giu-set | Canarie, Mar Rosso, Golfo, Caraibi |
| `tropical` | picco lug-ago + festività | Bali, Thailandia |
| `ski` | picco festività + alta stagione neve, minimo estate | Zermatt, Dolomiti |
| `city` | quasi stabile, lieve picco primavera/autunno/feste | città d'arte |

`_seasonal_profile()` assegna il profilo dai punteggi già nel dataset (neve
prima di tutto, poi `warm_score`/`relax_score`/`best_months` per distinguere
sole-d'inverno da mare mediterraneo da città calda). `seasonal_cost_factor()`
restituisce **1.0 senza un periodo scelto** — retro-compatibilità piena, chi
non indica quando parte vede i valori medi di sempre. Usata da
`recommender.seasonal_cost_min` e `trip_builder.seasonal_trip_cost_min`, così
destinazioni e itinerari non possono contraddirsi sullo stesso mese.

---

### Come arrivarci: città di partenza e mezzo (`travel_estimates.py`)

Nel questionario si sceglie **da dove si parte** (Milano, Bergamo, Roma o
"altro") e **come si preferisce viaggiare** (💡 il più conveniente, ✈️ aereo,
🚆 treno, 🚗 auto). Per ogni meta `travel_options()` stima i mezzi sensati,
con tempo **porta a porta, solo andata** e costo **a persona, andata e
ritorno**:

| Mezzo | Da dove vengono i numeri |
|---|---|
| ✈️ Aereo | Volo del dataset corretto per aeroporto (Roma hub intercontinentale, Bergamo low cost; da Bergamo i voli lunghi partono da Malpensa), + accesso all'aeroporto, 1h45 prima del volo e il tragitto dall'aeroporto d'arrivo. Per le mete italiane solo dove un volo ha senso (`_ITALY_FLIGHTS`). |
| 🚆 Treno | Tabella scritta a mano di collegamenti reali (`_TRAIN`): tempi e prezzi tipici, max ~14 ore (anche notturni). Da Bergamo si passa da Milano se non c'è un collegamento dedicato. |
| 🚗 Auto | Distanza in linea d'aria × fattore strada, con passaggi obbligati (Stretto di Messina, Nizza per la Spagna, Trieste per i Balcani). 100 km/h medi più le soste, max 13 ore di guida. Carburante e pedaggi **divisi tra chi viaggia** (5 posti per auto), più gli extra noti: Stretto, trafori alpini, Eurotunnel, vignette. |
| ⛴️ Auto + traghetto | Rotte reali (`_FERRY_ROUTES`): Genova/Civitavecchia–Olbia, –Palermo, –Barcellona, Bari–Durazzo, Ancona/Bari–Patrasso, Pozzallo–Malta. Auto fino al porto + imbarco + traversata. |

"Il più conveniente" confronta il costo medio a persona più 12 € per ogni
ora di viaggio (`VALUE_OF_HOUR`): senza il valore del tempo vincerebbe
sempre l'opzione da 20 ore che costa 10 € in meno. Ogni opzione riceve le
etichette "il più conveniente", "più economico", "più veloce".

**Nel motore** `apply_travel()` restituisce il dataset di sempre, con il
costo del volo sostituito da quello del mezzo scelto (così budget, costi
totali e viaggi combinati lo usano senza modifiche) e le colonne
`travel_mode`, `travel_hours`, `travel_door_hours`, `travel_available`.
`flight_hours` resta la durata del volo, perché altrove vuol dire "quanto è
lontana" (profilo stagionale, avvisi per le famiglie). Scegliendo treno o
auto **cambiano anche i consigli**: `keep_reachable()` lascia solo le mete
raggiungibili così, e i viaggi combinati con un volo interno vengono
scartati. La città di partenza non viene mai proposta come meta. Pagina
meta, vetrina ed Esplora invece mostrano sempre tutte le mete
(`_travel_df_for` senza filtri); se una meta è fuori dai consigli per come
si vuole viaggiare, la pagina lo spiega.

**In interfaccia** la sezione "Come arrivarci" di ogni meta mette i mezzi a
confronto in schede; città e numero di persone si cambiano lì sul posto,
quindi il confronto funziona anche per chi arriva da un link condiviso.

---

## 6. Trip Builder — viaggi combinati

**Principio guida: più destinazioni non significa viaggio migliore.**
`trip_builder.py` genera itinerari di 2-3 tappe solo quando sono
geograficamente sensati, compatibili con la durata, con trasferimenti che
non "mangiano" il viaggio. Riusa lo scoring per singola destinazione
(`recommender.py`), non lo duplica.

**Come nascono le combinazioni**: `trip_routes.py` contiene solo i
collegamenti realmente utili (non una rotta per ogni coppia possibile) —
è anche il meccanismo che evita combinazioni assurde (es. Reykjavik + Bali:
senza una rotta autorata, non viene generata). 7 trip template curati
arricchiscono con nome/descrizione le combinazioni che coincidono, ma il
motore ne genera liberamente altre dalle rotte disponibili.

**Tre punteggi calcolati separatamente**:

1. **Trip Match Score** — `avg_stop×0.40 + min_stop×0.20 + mood_coverage×0.25
   + efficiency×0.15`. `mood_coverage` prende il **meglio** tra le tappe per
   ogni mood (non la media): un itinerario complementare (una tappa forte su
   cultura, l'altra su avventura) viene premiato, non penalizzato.
2. **Feasibility Score** (interno, mai mostrato in UI) — geographic_coherence
   25% + transport_feasibility 25% + time_feasibility 25% +
   budget_feasibility 15% + season_compatibility 10%. Solo itinerari ≥ 75
   competono (soglia 60 come compromesso, con avviso).
3. **Travel Efficiency Score** — giorni di esplorazione / (esplorazione +
   giorni-equivalenti di trasferimento) × 100.

Il costo assume un solo volo internazionale verso la tappa d'ingresso + i
trasferimenti locali, non un volo per tappa. Linee guida durata→tappe (non
regole assolute, influenzano solo il punteggio):

| Durata | Tappe consigliate |
|---|---|
| 2-4 giorni | 1 (zero viaggi combinati è il comportamento atteso) |
| 5-7 giorni | 1-2 |
| 8-10 giorni | 2-3, solo se sensate |
| 11-14 giorni | 2-4, solo con logistica molto buona |
| 15+ giorni | itinerari più articolati |

**Ritmo** (`pace_score`, in `destinations.py`): mescola `activity_level`,
`adventure_score` e l'inverso di `relax_score` — il solo `activity_level`
avrebbe dato gruppi inutili (42 destinazioni su 79 valgono 2). Etichetta
(`pace_label_for_score`) su tre soglie: 32 Rilassato / 35 Dinamico / 12
Intenso sul dataset attuale. Per un itinerario è la media del `pace_score`
delle tappe, con le stesse soglie condivise.

**Raffinamento**: "Meno spostamenti", "Più destinazioni", "Più
rilassato/intenso", "Ottimizza il tempo" modificano pesi/penalità interne
(`apply_trip_refinement`), senza ripetere il questionario. 🎲 Sorprendimi è
condiviso tra destinazioni e viaggi (scelta pesata verso le destinazioni).

**Itinerario giorno per giorno**: ogni viaggio combinato ha anche il suo
itinerario con luoghi reali, costruito trattando le tappe come basi — vedi
[§8](#8-itinerari-giorno-per-giorno).

---

## 7. Dettagli di ogni meta

Contenuto delle card, tutto derivato da dati già presenti — nessun nuovo
campo dataset, nessuna fonte esterna:

- **Spiegazione narrativa** (`insights.narrative_explanation`) — 2-3 frasi
  costruite su mood coperti, stagione, margine di budget e Travel DNA.
  Fallback su `explain_match` (§3) se manca materiale.
- **Giornata tipo** (`typical_day`) — mattina/pomeriggio/sera dedotti dai
  tag, più un'esperienza WOW curata a mano per la sera. Non è un
  itinerario: è un assaggio di atmosfera.
- **Cosa ti porti a casa** (`emotional_takeaways`) — 3 highlight emotivi dai
  tratti sopra 65, contraltare della checklist pratica.
- **Stagionalità visuale** (`seasonality_months`, `seasonality_note`) —
  striscia dei 12 mesi con i migliori evidenziati e il mese scelto
  contornato.
- **Travel Style** (`travel_style_scores`) — 5 barre (Avventura, Relax,
  Cultura, Social, Lusso) che descrivono la *meta* — diverso dal Travel DNA,
  che descrive l'utente (§4).
- **Avvisi contestuali** (`destination_warnings` / `trip_warnings`) —
  trasferimento lungo, affollamento nel periodo festivo scelto, esperienza
  meteo-dipendente, sforamento budget: un solo box consolidato, tono non
  allarmistico.
- **Avvisi per modalità viaggiatore** (`traveller_mode_warnings`) — solo/
  coppia/gruppo/famiglia (§9) cambiano quali avvisi hanno senso (es. meta
  poco social per chi viaggia solo, volo lungo con bambini).
- **Checklist smart** (`checklist.py`) — 🎒 Cosa portare, 📄 Documenti, 🚫
  Cosa lasciare a casa, 🤦 Cose che si dimenticano spesso, 💡 Consigli
  pratici; dipende da clima, comfort, durata, area, e aggiunge una sezione
  dedicata per il primo viaggio da solo/a.
- **Facilità organizzativa** (`organizational_ease`, 1-5) — da area
  geografica, ore di volo, comfort_level. Per i viaggi combinati: il minimo
  tra le tappe meno una penalità per ogni tappa oltre la prima. Filtrabile
  nel questionario ("quanto vuoi che sia semplice da organizzare").
- **Anti-FOMO** (`discarded_destination_alternatives` /
  `discarded_trip_alternatives`) — 1-2 alternative valutate ma non mostrate,
  con la ragione onesta e specifica del perché.
- **Alternative accessibili** (`accessible_alternatives`) — per ogni meta
  fuori budget, 1-2 ripieghi nello stesso cluster/mood con un costo
  Economico più basso o un volo più corto, e quanto si risparmia.

---

## 8. Itinerari giorno per giorno

`itinerary.py` costruisce un itinerario **standard** (non personalizzato sulle
preferenze) giorno per giorno, in mattina / pomeriggio / sera. Risponde alla
domanda "cosa ci faccio in N giorni", che viene prima di "è la meta giusta".

**Dove:** expander **"🗺️ Itinerario classico"** nel dettaglio della card
destinazione, subito dopo la Giornata tipo. Per i viaggi combinati, expander
**"🗺️ Itinerario giorno per giorno"** nella card del viaggio.

Ci sono **due motori**, con lo stesso codice di riempimento delle giornate:

| | Motore curato | Motore generico |
|---|---|---|
| Attinge da | `places.py` — luoghi con nome proprio | tag della meta |
| Copertura | tutte e 79 le mete | fallback per mete senza contenuto curato |
| Esempio di riga | "Laguna di Balos — in barca da Kissamos" | "Cala o tratto di costa raggiungibile in giornata" |

`build_curated_itinerary()` restituisce `None` se la meta non è coperta, e
`app.py` ricade su `build_standard_itinerary()`. Il generico non è stato
rimosso: resta la rete di sicurezza quando i luoghi curati di una giornata
finiscono, e serve subito se si aggiungono destinazioni nuove al dataset.

### Cosa è curato e cosa è calcolato

Il principio non è cambiato: **niente dati di viaggio inventati.** Quello che
è cambiato è che i luoghi ora ci sono davvero invece di essere aggirati.

| Elemento | Origine |
|---|---|
| Luoghi delle giornate | `places.py` — nome proprio, base, durata, slot, tier (★ = imperdibile) |
| Modalità di visita | Curata (`how`): "in barca da Kissamos", "306 gradini fiancheggiati dai naga", "prenotazione obbligatoria a orario" |
| Base logistica | Curata: dove si dorme ogni notte, e quando ci si sposta |
| Stagionalità | Curata (`months` + `note`), solo dove è **strutturale**: una gola chiusa d'inverno, i traghetti fermi, il sole di mezzanotte. Mai orari o prezzi, che invecchiano |
| Riempimento residuo | Blocchi generici derivati dai tag, filtrati per stagione |
| Durate e ritmo | **Calcolati**: ore di luce per latitudine e stagione, tetto dello stile, tempi di trasferimento |
| Mobilità e zone | Descritte per **categoria** (a piedi / mezzi / serve l'auto / resort / tour) |

Il dataset curato oggi: **911 luoghi su 79 mete** (da 10 a 20 per meta), 102
basi logistiche, 228 attività serali, 93 luoghi con un vincolo stagionale.

### Basi: dove si dorme

È il pezzo che il motore generico non può avere, perché richiede di sapere
*dove stanno* le cose. A Creta, Cnosso e Samaria sono a tre ore d'auto: un
itinerario che le mette in giornate consecutive senza spostare la base è
sbagliato anche se "sta" nel budget orario. Quindi:

- ogni meta dichiara le sue basi con un peso e un tetto di notti;
- `_allocate_nights()` distribuisce le notti in proporzione, rispettando i
  tetti (a Rethymno si dorme una volta sola, il resto delle notti va a Chania);
- nei giorni di trasferimento si può ancora attingere alla base che si sta
  lasciando — è così che il Giorno 1 di Creta fa Cnosso di mattina e Rethymno
  la sera;
- sulle mete a base unica la riga sparisce: "Notte a Roma centro" ripetuto per
  cinque giorni non è informazione.

### Vincoli di tempo rispettati

- **Max un'attività per slot** → 2 attività principali di giorno + una serale.
- **Ore di luce reali**: `DAYLIGHT_HOURS` per banda di latitudine × mese. A
  Rovaniemi a dicembre ci sono 3.5 ore di luce e l'itinerario lo dichiara.
  Il pavimento a 4.5h evita di svuotare la giornata: sotto il circolo polare
  d'inverno le attività (aurora, slitte, saune) si fanno al buio o al chiuso.
- **Gli spostamenti contano**: quelli tra basi sono curati, quelli interni
  sono già dentro le ore del luogo (Elafonissi vale 6 ore, non 4, perché
  include la strada da Chania).
- **Mezza giornata dichiarata**: un'attività ≥ 4h occupa mattina *e*
  pomeriggio, invece di impilarci sopra dell'altro.
- **I `must` si piazzano comunque**, anche sforando il tetto orario. In stile
  Relax il tetto è 5.5h ed Elafonissi ne vale 6: rispettarlo significherebbe
  proporre Creta senza la spiaggia rosa, che non è un ritmo più lento, è
  un'altra vacanza.

### Stagionalità

Un luogo fuori stagione **esce dall'itinerario e viene dichiarato**, con il
motivo: "Gole di Samaria non è in programma: il sentiero è percorribile solo
da maggio a ottobre". Vale anche per il riempimento generico —
`_FILLER_TAG_MONTHS` impedisce che a luglio, dopo aver escluso l'aurora vera,
comparisse un generico "uscita a caccia di aurora".

### Varianti per durata e per stile

Due selettori in cima all'expander:

- **Durata** — due varianti curate per meta, ciascuna con un titolo e una riga
  di posizionamento ("Il meglio del Nord-Ovest — ideale per chi visita l'isola
  per la prima volta"). Le durate rispettano `days_min`-`days_max`.
- **Stile** — Standard · Relax · Intenso · Foodie · Con bambini. Cambiano tetto
  orario, numero di attività e quota di pause: *Intenso* aggiunge il Museo
  Archeologico e le Gole di Samaria, *Relax* li toglie. "Intenso" ha un tetto a
  10 ore: oltre non è intenso, è una giornata che non regge.

### Itinerari dei viaggi combinati

Un viaggio combinato è già una sequenza di tappe con trasferimenti in mezzo:
la stessa struttura che il motore usa per le basi. `build_trip_itinerary()`
riusa lo stesso codice trattando **ogni tappa come una base**, con i luoghi
curati di quella meta nel suo pool e i tempi di trasferimento presi dagli
archi calcolati dal Trip Builder invece che da una stima.

Le basi interne di una meta collassano in una: dentro una tappa di un viaggio
combinato non si cambia albergo. Il peso di ogni tappa è il suo `days_min`,
così una città che si vede in due giorni non si prende tre notti.

Se anche **una sola tappa** non ha contenuto curato, l'itinerario non compare
e resta la sola timeline: un percorso metà con nomi propri e metà generico
sarebbe peggio che non proporlo. Oggi non accade mai, ma la regola protegge se
si aggiungono destinazioni nuove.

### Confronto pratico

**Dove:** pagina Confronto, sotto radar e tabelle → expander **"🗺️ Cosa farei
negli stessi giorni, qui vs lì"**. Itinerari della **stessa durata** affiancati
(anche fuori dal range consigliato della meta — è il senso della domanda), con
l'avviso esplicito quando quella durata non è adatta.

---

## 9. Modalità di ricerca

- **Quick start** — scorciatoie in home che precompilano il questionario
  (es. "Voglio staccare e stare al caldo") senza toccare lo scoring.
- **Primo viaggio da solo/a** — area Europa, volo max 3h, comfort/socialità
  medi come default; sblocca checklist e avvisi dedicati (§7) e un
  suggerimento di alloggio in linea con la modalità.
- **Modalità viaggiatore** (Solo / Coppia / Gruppo / Famiglia, derivata da
  "Con chi parti?") — influenza avvisi e suggerimento di alloggio, mai lo
  scoring di base.
- **Regalo/Sorpresa** — nasconde una destinazione dietro "Scopri il regalo";
  rivelata, resta fissa in sessione (non si rigenera ad ogni click).
- **Sorpresa controllata** — l'utente fissa 2-3 vincoli **duri** (budget
  massimo, volo massimo, esclusioni tassative come "niente neve") che
  filtrano il pool *prima* della pesca, poi il motore sceglie una meta
  coerente ma meno ovvia. Diversa da 🎲 Sorprendimi: qui i vincoli sono
  espliciti e pochi, non le preferenze complete del questionario.

---

## 10. Confronto e "I miei viaggi"

- **Confronto destinazioni/viaggi** — fino a 3 destinazioni o 2 viaggi
  affiancati: un **radar SVG inline** dei Travel Style (nessuna libreria di
  grafici aggiunta) più una tabella numerica.
- **I miei viaggi** — pagina dedicata ai preferiti (❤️ dalle card), con lo
  stesso radar di confronto e una tabella costi/ritmo/durata affiancata.
  Non richiede un account: vive in `st.session_state` + il file `.json`
  scaricabile.

---

## 11. Export e condivisione

- **Riepilogo testuale** (`export.py`, `trip_presentation.py`) — pronto per
  WhatsApp/Telegram, per destinazioni e viaggi combinati.
- **PDF** — via `reportlab`; se non installato, fallback silenzioso al solo
  testo (mai un errore).
- **Versione "stories"** (`export_destination_as_stories`) — testo
  cortissimo per storie/status, diverso sia dal riepilogo (da leggere) sia
  dalla didascalia social (accompagna un'immagine).
- **Card social** (`social_card.py`) — immagine PNG verticale con nome,
  match %, un'esperienza WOW e il costo, generata con Pillow (fallback alla
  sola didascalia se non disponibile). Senza una ricerca alle spalle il badge
  diventa "IDEA DI VIAGGIO".
- **Link condivisibile** — ogni meta ha una pagina sua,
  `…/?meta=<slug>&giorni=<N>`: riquadro con il link da copiare e pulsanti
  WhatsApp/Telegram/Email. Il link entra anche nel riepilogo testuale, nella
  versione stories e nella didascalia social. L'indirizzo pubblico è
  `PUBLIC_APP_URL` in `app.py`: va aggiornato se l'app cambia sottodominio.

---

## 12. Interfaccia

Palette "cielo" applicata a `.streamlit/config.toml` e al CSS globale in
`app.py` (`inject_css`):

| Ruolo | Colore |
|---|---|
| Primary | `#4A90E2` |
| Primary light (sfondi) | `#E3F2FD` |
| Accent (bottoni, focus) | `#1E88E5` |
| Testo principale | `#1A237E` |
| Testo secondario | `#546E7A` |
| Success / Warning | `#43A047` / `#FB8C00` |

- **Home**: hero centrato con CTA singola e un aereo che decolla in loop
  (solo CSS, animato con `transform`/`opacity`; fermo per chi ha attivato
  "riduci movimento"). Sotto, una riga sola: 🎲 Sorprendimi, 🧳 Primo viaggio
  da solo/a e il menu a tendina "✨ Altre idee di viaggio" con le altre
  scorciatoie (`QUICK_START_FEATURED` in `utils.py` decide quali restano fuori).
  Poi la vetrina, per chi non vuole ancora rispondere a domande:
  - **Dove andare a [mese]**: 8 mete per il mese corrente (o quello scelto
    con i pulsanti dei mesi), da `catalog.month_picks` — solo mete per cui è
    un mese migliore, prima le più stagionali, alternando le zone del mondo.
  - **Che viaggio cerchi?** (8 stili, `MOOD_SHOWCASE`) ed **Esplora per zona**
    (`ZONE_SHOWCASE`): ogni tessera apre Esplora con quel filtro.
  - **Come funziona** in 3 passi, una striscia di fiducia (numero di mete,
    luoghi curati, niente sponsor, `DATA_REVIEWED`) e le **domande frequenti**.
  Le tessere sono foto con un pulsante Streamlit invisibile steso sopra: tutta
  la foto è cliccabile senza ricaricare l'app. Su telefono ogni riga diventa
  una fila da scorrere col dito. Usano la foto a 500 px (`Photo.tile`).
- **Esplora** (`stage = "explore"`, anche dalla sidebar): tutte le mete con
  filtri per mese, stile, zona, budget e durata, ordinate "di stagione" o per
  prezzo, 12 alla volta. I filtri restano salvati in `ex_filters` quando si
  apre una meta e si torna indietro (Streamlit cancellerebbe lo stato dei
  widget non disegnati).
- **Questionario**: 8 domande in card distinte e numerate ("Domanda X di 8"),
  dentro un unico form (non un wizard multi-step).
- **Risultati**: vista compatta di default — pro/contro, breakdown costi,
  timeline e checklist dietro expander; prima cosa visibile è la foto della
  meta con match % e poi "Da X €". I viaggi combinati mostrano una striscia
  con le foto delle tappe.
- **Pagina meta** (`stage = "destination"`): foto grande, numeri chiave
  (costo, durata, volo, periodo migliore), itinerario già aperto, riquadro di
  condivisione e lo stesso dettaglio delle card. Ci si arriva da un link o dal
  pulsante "Apri la pagina della meta" di ogni card; "Indietro" riporta da
  dove si era partiti. Chi arriva da un link senza aver fatto il questionario
  vede un invito a farlo al posto del match.
- **Foto**: Wikimedia Commons, scelte a mano e verificate, 1280 px per la
  pagina e 960 px per le card, come sfondo CSS con un gradiente sotto (se non
  si caricano non si vede un'immagine rotta). Autore e licenza sono sempre
  visibili sulla foto, con link alla pagina Commons.
- Card individuate via un marcatore invisibile (`span` con classe dedicata,
  primo figlio del container) anziché le classi auto-generate di Streamlit,
  che cambiano hash a ogni build.

---

## 13. Estendere il dataset

Per una nuova destinazione: aggiungi un elemento a `RAW_DESTINATIONS` in
`destinations.py` con l'helper `_d(...)`, più una riga in `CLUSTER_BY_ID` se
deve partecipare a itinerari combinati. `pace_score` e `seasonal_profile` si
calcolano da soli — non serve autorarli. Nessuna modifica al motore:
`recommender.py` legge le colonne del DataFrame, non destinazioni hardcoded.

Per nuove combinazioni multi-tappa: aggiungi una rotta in `trip_routes.py`
(`RAW_ROUTES`) — senza rotta autorata, il Trip Builder non le combinerà mai.
Un trip template curato si aggiunge a `RAW_TRIP_TEMPLATES`.

Per la vetrina (`catalog.py`): se una meta non va mostrata nella sezione
del mese in alcuni periodi (nome o foto stagionali), una voce in
`_SHOWCASE_ONLY_IN`. Una foto in `PHOTOS` con autore e licenza
esatti della pagina Commons (obbligatori per CC BY / CC BY-SA), il paese in
`_ZONE_BY_COUNTRY` se è nuovo e, se il nome è lungo o ha parentesi, uno slug
in `_SLUG_OVERRIDES`. **Uno slug pubblicato non si cambia più**: i link già
condivisi smetterebbero di funzionare. `build_slug_index` si ferma con un
errore se due mete finiscono con lo stesso slug.

### Aggiungere i luoghi curati di una meta

Una voce in `places.py`, indicizzata per id di destinazione, con `bases`,
`places` e `variants`. Senza, la meta funziona lo stesso e ricade sul motore
generico. Regole imparate scrivendo le 79 esistenti:

- **`how` è obbligatoria ed è il valore aggiunto.** Come ci si arriva e in che
  modo si vive il posto — "in barca da Kissamos", "306 gradini", "prenotazione
  a orario". È ciò che distingue un itinerario utile da un elenco di nomi.
- **Servono 2-3 luoghi serali** (`slot: _EVENING`), altrimenti le sere
  diventano un muro di "Cena tranquilla e rientro senza fretta".
- **Attenzione alle attività da 4 ore o più**: occupano mattina e pomeriggio, e
  non possono mai finire in un pomeriggio. Un'escursione da mezza giornata a
  4.0h non entrerà da nessuna parte; a 3.5h riempie il pomeriggio.
- **Circa 10 luoghi bastano fino a 6 giorni; per varianti da 9-14 servono 20.**
  Sotto quella soglia metà degli slot torna generico.
- **`months` solo per la stagionalità strutturale** (sentiero chiuso, traghetti
  fermi, sole di mezzanotte), mai per orari o prezzi.
- **Niente contenuto incerto**: se non si conosce la modalità reale di un
  luogo, meglio non inserirlo e lasciare il blocco generico, che è vago ma
  non è sbagliato.

---

## 14. Note di robustezza

- **Prestazioni.** Il dataset (`_cached_destinations`, `_prepared_df_for`) è in
  `st.cache_data`; immagini social e PDF sono in `lru_cache` nei rispettivi
  moduli, che restano indipendenti da Streamlit. Prima venivano ricostruiti a
  ogni clic — i PDF e le immagini anche con l'expander "Esporta" chiuso. Con
  la cache un rerun della pagina risultati è sceso da ~1,4 s a ~0,8 s in locale.

- Budget, durata, clima o tag mancanti non causano errori: ogni componente
  ha un valore neutro di fallback.
- Zero destinazioni entro i criteri stretti → l'app mostra comunque le
  migliori alternative con il compromesso spiegato.
- Il Trip Builder non genera mai eccezioni se non esistono itinerari
  fattibili: mostra un messaggio che spiega perché una meta singola è la
  scelta migliore in quel caso.
- Salvataggio via file `.json` scaricabile (sidebar) e ricaricabile in
  home — resta sul dispositivo del visitatore, mai sul server: su una
  versione online condivisa da più persone, un salvataggio unico lato
  server finirebbe sovrascritto a ogni utente.
- Filtro di facilità organizzativa (§7): se azzera i risultati viene
  ignorato invece di mostrare una pagina vuota.
- **Rete di sicurezza** (`safe_block` / `safe_render` in `app.py`): se una
  scheda o una sezione si rompe, al suo posto compare un avviso gentile e il
  resto della pagina funziona; se si rompe una pagina intera, una pagina di
  errore con "Torna alla home" (`render_error_page`). L'errore finisce nei
  log (Manage app → Logs). Con la variabile d'ambiente
  `TRAVELMATCH_STRICT=1` gli errori riemergono: serve ai test automatici.
  `st.rerun()` e `st.stop()` non vengono intercettati (sono BaseException).
- **Ricerche salvate** caricate da file: `_sanitize_saved_prefs` ricostruisce
  le preferenze campo per campo, tenendo solo chiavi note con valori validi.
  Un file vecchio, ritoccato a mano o non JSON dà un messaggio, mai un errore.
- **Itinerari lunghi**: quando il viaggio supera la somma dei `max_nights`
  delle basi (13 giorni a Bali con due basi da 6 notti), la notte in più va
  alla base principale. Prima andava persa e l'itinerario usciva con un giorno
  in meno di quelli richiesti (Bali, L'Avana, Città del Capo).
- **Commenti e segnalazioni**: `FEEDBACK_URL` in `app.py`. Se è vuoto il link
  non compare; con l'indirizzo di un modulo (es. Modulo Google) compare in
  fondo a home, risultati, pagina meta, Esplora, nella sidebar e nella pagina
  di errore.
- **Link rotti o manomessi** (`?meta=pippo`, `&giorni=99`, testo a caso)
  non causano mai errori: meta sconosciuta → home con un avviso; durata
  inesistente → itinerario standard. Maiuscole, spazi e accenti nello slug
  vengono normalizzati (`?meta=Città del Capo` funziona).
- Merzouga (Sahara) aveva volo a 0 € e 0 ore: risultava "da 120 €" e passava
  il filtro dei voli brevi. Ora ha il volo su Marrakech più il trasferimento
  su strada (130-350 €, ~3h10 di volo).
- La sorpresa di "🎲 Sorprendimi" viene scelta una volta sola: prima veniva
  ripescata a ogni clic, e cambiare la durata dell'itinerario la sostituiva
  con un'altra meta.
