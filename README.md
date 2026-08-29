# ✈️ TravelMatch

**Dove dovresti andare davvero in vacanza?**

TravelMatch è una piccola app da viaggio "vera" — ispirata a WeRoad, G Adventures e
Intrepid Travel — che ti aiuta a scegliere la meta giusta per la tua prossima
vacanza, con un occhio speciale a **Natale 2026 / Capodanno 2027**. Funziona
interamente offline, con un dataset locale di 79 destinazioni reali e un motore
di raccomandazione scritto da zero (nessuna chiamata a servizi esterni, nessuna AI
generativa: solo un buon algoritmo di scoring).

Oltre a suggerire **singole destinazioni**, TravelMatch è anche un **Trip
Builder**: propone itinerari realistici di 2-3 tappe (es. "Istanbul & Cappadocia",
"Tokyo, Kyoto & Osaka") solo quando sono davvero fattibili — mai solo perché il
punteggio è alto. Vedi la sezione 7 per i dettagli.

---

## 1. Installazione e avvio

Requisiti: Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'app si apre automaticamente nel browser su `http://localhost:8501`. Non serve
nessuna connessione internet dopo l'installazione delle dipendenze: il dataset è
locale (`destinations.py`) e non ci sono chiamate di rete.

### Struttura del progetto

```text
travelmatch/
├── app.py                  # interfaccia Streamlit (UI, stato, pagine)
├── recommender.py          # motore di raccomandazione per singola destinazione
├── trip_builder.py         # motore Trip Builder (itinerari multi-tappa) + confronto viaggi
├── trip_presentation.py    # spiegazioni, timeline ed export testuale dei viaggi combinati
├── destinations.py         # dataset locale (79 destinazioni)
├── trip_routes.py          # rotte tra destinazioni + trip template validati
├── utils.py                # costanti del questionario, Travel DNA, formattazione, salvataggio
├── insights.py             # Travel Style, avvisi contestuali, facilità organizzativa, anti-FOMO
├── checklist.py            # checklist pratica automatica (cosa portare, documenti, consigli)
├── export.py               # export testo/PDF di destinazioni e viaggi combinati
├── social_card.py          # immagine e didascalia "social" condivisibili
├── requirements.txt
└── README.md
```

---

## 2. Architettura

Il progetto è diviso in quattro livelli indipendenti, così com'era richiesto:

- **`destinations.py` — dati.** Ogni destinazione è un dizionario con uno schema
  fisso (~35 campi: punteggi 0-100 per mood/clima/atmosfera natalizia, costi a
  range, durata di volo, mesi consigliati, esperienze WOW, pro/contro, consigli
  pratici...). Aggiungere una destinazione nuova (o arrivare a 100+) significa
  solo aggiungere un dizionario in più: **nessuna modifica al motore è
  necessaria**, perché il recommender lavora sulle colonne del DataFrame, non su
  singole destinazioni hardcoded.

- **`recommender.py` — motore.** Puro Python + pandas, **zero dipendenze da
  Streamlit**. Espone funzioni testabili in isolamento: `get_recommendations`,
  `surprise_me`, `get_christmas_categories`, `compare_destinations`,
  `apply_refinement`. Può essere riusato in futuro in un'API, in un notebook o
  in un altro frontend senza modifiche.

- **`utils.py` — utility.** Costanti del questionario (fasce di budget, mood,
  tag...), calcolo del Travel DNA, formattazione di prezzi/temperature/emoji,
  salvataggio/caricamento locale in JSON. Anche questo modulo non dipende da
  Streamlit.

- **`app.py` — interfaccia.** Orchestrazione delle pagine (landing →
  questionario → risultati) tramite `st.session_state`, rendering delle card,
  gestione dei pulsanti di raffinamento e confronto. Non contiene logica di
  scoring: si limita a chiamare `recommender.py` e mostrare il risultato.

Questa separazione è quella richiesta esplicitamente dal progetto: puoi far
crescere il dataset a 100+ destinazioni, o sostituire Streamlit con un'altra UI,
senza toccare il motore.

---

## 3. Il Travel Match Score — come funziona

Ogni destinazione riceve un punteggio da 0 a 100 calcolato come **media pesata**
di componenti, ciascuna già espressa su scala 0-100:

```python
DEFAULT_WEIGHTS = {
    "budget":   0.20,
    "mood":     0.20,
    "climate":  0.15,
    "season":   0.10,
    "duration": 0.10,
    "social":   0.10,
    "comfort":  0.05,
    "distance": 0.10,
}
```

I pesi sono **centralizzati** in `recommender.py` (`DEFAULT_WEIGHTS` /
`DEFAULT_BOOSTS`) e possono essere modificati in un unico punto per cambiare il
comportamento di tutta l'app.

Ogni componente confronta le preferenze dell'utente con i dati della
destinazione:

- **budget** — quanto il costo totale stimato (volo+hotel+cibo+attività) sta
  dentro (o fuori) al budget indicato. Restare comodamente sotto budget dà un
  punteggio alto; sforare oltre ~15% lo fa crollare rapidamente (vedi hard
  constraint sotto).
- **mood** — media tra affinità mood (natura, città, romantico...) e overlap
  dei tag speciali selezionati (mercatini di Natale, trekking, aurora
  boreale...).
- **climate** — quanto il clima tipico della destinazione (caldo/temperato/
  freddo/neve) corrisponde a quello richiesto.
- **season** — la destinazione è "nella sua stagione migliore" nel periodo
  richiesto? Per Natale/Capodanno si somma anche un bonus per atmosfera
  natalizia (mercatini, neve) **oppure** per essere una buona fuga al caldo:
  è così che il motore rappresenta le due anime "☀️ Fuga al caldo" e
  "🎄 Winter Wonderland" senza penalizzare l'una a favore dell'altra.
- **duration** — sovrapposizione tra i giorni desiderati e la durata
  consigliata per quella meta.
- **social** — distanza tra lo slider di socialità (0-100) e il livello
  sociale tipico della destinazione.
- **comfort** — distanza tra il comfort desiderato (backpacker → luxury) e il
  comfort_level della meta.
- **distance** — quanto le ore di volo restano sotto (o superano) il limite
  scelto.

A queste si affiancano **componenti secondarie a peso zero di default**
(romantic, adventure, relax, food, luxury, snow, warm — i punteggi grezzi
della destinazione), che si attivano quando l'utente preme un pulsante di
raffinamento rapido (vedi sotto). Il punteggio finale è sempre normalizzato
sulla somma dei pesi effettivamente attivi, quindi resta comparabile 0-100
anche dopo molti raffinamenti.

### Spiegazione del match

Per ogni destinazione, `explain_match()` individua le componenti che si
discostano di più (in positivo) da un valore neutro di riferimento — non
semplicemente quelle con il valore più alto, per evitare di "spiegare" ogni
risultato con componenti che sono sempre alte per costruzione (es. "nessun
limite di volo"). Il risultato è la frase "Perché fa per te" mostrata in ogni
card.

### Hard constraint e compromessi

Oltre allo score continuo, il motore verifica dei **criteri stretti**
(`_meets_strict_criteria`): budget non sforato oltre il 15%, volo entro il
limite, durata compatibile, mese richiesto tra i `best_months` della meta. Se
meno di 5 destinazioni rispettano tutti i criteri, l'app lo dichiara
esplicitamente e completa i risultati con le migliori alternative disponibili,
spiegando in ogni card **quale** criterio è stato ammorbidito ("Piccolo
compromesso su: budget").

### Raffinamento rapido

I pulsanti "💰 Più economico", "☀️ Più caldo", ecc. **non ripetono il
questionario**: chiamano `apply_refinement()`, che aumenta un peso esistente
(es. "Più social" → `weights["social"] += 0.12`) e/o attiva un bonus
secondario (es. "Più romantico" → `boosts["romantic"] += 0.16`, che inietta
direttamente il `romantic_score` della destinazione nel calcolo). I pesi
restano clampati per evitare che troppi click consecutivi sbilancino lo score
fuori scala.

### 🎲 Sorprendimi

`surprise_me()` filtra le destinazioni con match ≥ 65% (soglia che si abbassa
gradualmente se il pool è vuoto), esclude quelle già mostrate in top 5, e
sceglie **con un bias verso posizioni meno scontate** del ranking (non il
podio assoluto), così la meta proposta è sempre coerente ma raramente banale.

---

## 4. Travel DNA

Il Travel DNA (`utils.compute_travel_dna`) è calcolato **solo dalle
preferenze**, non dal dataset: combina mood selezionati, intensità, slider di
socialità, comfort e clima in 10 tratti (Adventure, Nature, Food, Social,
Relax, Luxury, Culture, Romance, Snow, Warmth) su scala 0-100, con una
descrizione generata automaticamente a partire dai tratti più (e meno) marcati.
Si aggiorna automaticamente ogni volta che le preferenze cambiano.

---

## 5. Note di robustezza

- Budget, durata, clima o tag mancanti non causano errori: ogni componente ha
  un valore neutro di fallback.
- Se zero destinazioni rispettano tutti i criteri, l'app mostra comunque le
  migliori alternative disponibili con la spiegazione del compromesso.
- Le "Date personalizzate" vengono convertite in mesi coperti dal viaggio e
  usate per il match di stagionalità come le altre opzioni di periodo.
- Il salvataggio è opzionale e non richiede alcun database: usa
  `st.session_state` durante la sessione, più un file `.json` scaricabile
  ("💾 Scarica questa ricerca" nella sidebar) e ricaricabile in seguito
  ("📂 Carica una ricerca salvata" nella home) per la persistenza tra sessioni.
  Il file resta sul dispositivo del visitatore, mai sul server: importante
  per una versione online condivisa da più persone, dove un salvataggio unico
  lato server finirebbe sovrascritto (e visibile) a ogni utente.
- Il Trip Builder non genera mai eccezioni se non esistono itinerari fattibili
  per la durata/preferenze scelte: la sezione "✈️ Viaggi combinati" mostra
  semplicemente un messaggio che spiega perché una destinazione singola è la
  scelta migliore in quel caso, invece di forzare una combinazione scadente.

---

## 7. Trip Builder — viaggi combinati

**Principio guida: più destinazioni non significa viaggio migliore.**
`trip_builder.py` genera itinerari di 2-3 tappe, ma solo quando sono
**davvero fattibili** — geograficamente sensati, compatibili con la durata
scelta, con trasferimenti che non "mangiano" il viaggio. Riusa lo scoring per
singola destinazione di `recommender.py` (non lo duplica) per valutare ogni
tappa, e aggiunge sopra tre livelli di analisi specifici per gli itinerari.

### Come nascono le combinazioni

`trip_routes.py` contiene un dataset "leggero" di rotte tra destinazioni
(`origin_id, destination_id, transport_mode, travel_time, transport_cost,
convenience_score`) — **non una rotta per ogni coppia possibile**, solo i
collegamenti realmente utili. Questo è anche il meccanismo con cui il motore
evita combinazioni geograficamente assurde: se non esiste una rotta tra due
destinazioni (es. Reykjavik + Bali), quella combinazione non può essere
generata, indipendentemente da quanto siano simili i punteggi. Ogni
destinazione ha anche un `cluster` (in `destinations.py`, `CLUSTER_BY_ID`) che
raggruppa mete vicine (es. "Veneto-Dolomiti", "Giappone", "Grecia") — usato
come ulteriore segnale di coerenza geografica, non come unico criterio.

7 **trip template** validati a mano (Istanbul+Cappadocia, Lisbona+Porto,
Tokyo+Kyoto+Osaka, Bangkok+Chiang Mai, Marrakech+Sahara+Essaouira,
Vienna+Budapest, Barcellona+Costa Brava) arricchiscono con nome e descrizione
curati le combinazioni generate quando coincidono, ma **non sono le uniche
possibili**: il motore genera liberamente altre coppie/triple sensate dalle
rotte disponibili (es. Firenze+Cinque Terre, Atene+Santorini+Creta).

### I tre punteggi

Per ogni itinerario vengono calcolati **separatamente**:

1. **Trip Match Score** — non è una media delle singole destinazioni: è
   `avg_stop*0.40 + min_stop*0.20 + mood_coverage*0.25 + efficiency*0.15`. Il
   pezzo chiave è `mood_coverage`: per ogni mood richiesto prende il **meglio**
   tra le tappe (non la media), così un itinerario complementare (una tappa
   forte su cultura/food, l'altra su avventura) viene premiato invece di
   essere penalizzato perché nessuna singola tappa eccelle su tutto.
2. **Feasibility Score** (pesi centralizzati in `FEASIBILITY_WEIGHTS`):
   `geographic_coherence 25% + transport_feasibility 25% + time_feasibility
   25% + budget_feasibility 15% + season_compatibility 10%`, con penalità
   aggiuntive se i trasferimenti superano il 30-35% del tempo ideale di
   viaggio o se il numero di tappe eccede le linee guida per la durata scelta.
   Solo itinerari con Feasibility ≥ 75 vengono usati per selezionare i
   risultati (soglia che scende a 60 come compromesso se non ce ne sono
   abbastanza, con avviso esplicito) — **resta un dettaglio puramente
   interno del motore**: il punteggio numerico non compare mai nell'interfaccia
   (card, confronti, export, PDF), solo l'effetto delle sue scelte.
3. **Travel Efficiency Score** — `giorni di esplorazione / (giorni di
   esplorazione + giorni-equivalenti di trasferimento) × 100`.

Il costo totale stimato assume **un solo volo internazionale** andata/ritorno
verso la tappa d'ingresso più i trasferimenti locali (andata e ritorno)
verso le tappe successive — non un volo separato per ogni tappa, che
gonfierebbe artificialmente il costo di itinerari con una tappa finale meno
connessa (es. Cappadocia).

### Linee guida su durata → numero di tappe

Non sono regole assolute ma influenzano il punteggio (penalità se il numero
di tappe eccede la linea guida per la durata scelta):

| Durata | Tappe consigliate |
|---|---|
| 2-4 giorni | 1 |
| 5-7 giorni | 1-2 |
| 8-10 giorni | 2-3, solo se sensate |
| 11-14 giorni | 2-4, solo con logistica molto buona |
| 15+ giorni | itinerari più articolati |

Per un viaggio di 2-3 giorni, il Trip Builder mostrerà correttamente **zero**
viaggi combinati: è il comportamento atteso, non un errore — una destinazione
sola ben vissuta batte sempre una combinazione forzata.

### Raffinamento dei viaggi combinati

I pulsanti "🧳 Meno spostamenti", "🗺️ Più destinazioni", "🧘 Più rilassato",
"⚡ Più intenso", "⏱️ Ottimizza il tempo" modificano pesi e penalità interne
del motore (`apply_trip_refinement()` in `trip_builder.py`), non ripetono il
questionario — stesso principio del raffinamento per singola destinazione.

### 🎲 Sorprendimi (unificato)

Lo stesso pulsante "🎲 SORPRENDIMI" può restituire **sia** una destinazione
singola **sia** un viaggio combinato (scelta casuale pesata verso le
destinazioni), coerente con l'obiettivo del match ma volutamente meno ovvio
del podio principale.

---

## 8. Estendere il dataset

Per aggiungere una destinazione, apri `destinations.py` e aggiungi un nuovo
elemento a `RAW_DESTINATIONS` usando la funzione helper `_d(...)` con lo
stesso schema delle altre voci, più una riga in `CLUSTER_BY_ID` se vuoi che
partecipi a itinerari combinati. Non serve toccare `recommender.py`: il
motore legge le colonne del DataFrame generato da `load_destinations_df()`,
quindi scala naturalmente a 100+ destinazioni.

Per abilitare nuove combinazioni multi-tappa, aggiungi una rotta in
`trip_routes.py` (`RAW_ROUTES`) tra le destinazioni interessate — senza una
rotta autorata, il Trip Builder non le combinerà mai. Un nuovo trip template
curato si aggiunge invece a `RAW_TRIP_TEMPLATES`.

---

## 9. Fase 1 — export, costi, spiegazioni, timeline

Obiettivo: rendere l'app più completa e rassicurante senza toccare lo
scoring. Ogni feature è un modulo leggero che legge dati già calcolati.

- **Export itinerario** (`export.py`, `trip_presentation.py`)
  - Testo pronto per WhatsApp/Telegram (emoji, struttura chiara) per destinazioni e viaggi combinati.
  - PDF scaricabile via `reportlab`; se non è installato, fallback silenzioso al solo testo (mai un errore).
  - Stesso contenuto in entrambi i formati: il PDF è solo un layer di formattazione sopra il testo, non una fonte separata.

- **Breakdown costi a 3 scenari + avviso budget** (`utils.cost_scenarios`, `budget_warning_message`)
  - Economico (minimo del range) · Medio (punto medio) · Comodo (massimo maggiorato del 15%).
  - Avviso amichevole se lo scenario Medio sfora il budget di oltre il 15%.
  - Per i viaggi combinati il totale include già i trasferimenti (nessun calcolo separato).

- **Spiegazione "Perché questa combinazione"** (`trip_presentation.generate_trip_explanation`)
  - 2-4 frasi generate dai dati reali dell'itinerario: tempo di trasferimento, Travel Efficiency, mood coverage, cluster geografico, punteggi per tappa.
  - Segnala un compromesso onesto quando una tappa pesa meno delle altre sul match.

- **Toggle modalità risultati + empty state curati**
  - Selettore 🌍 Solo destinazioni / ✈️ Solo viaggi combinati / 🔀 Entrambi.
  - Empty state positivo ("una destinazione ben vissuta resta la scelta migliore") invece di un messaggio tecnico quando un viaggio combinato non aggiunge valore.

- **Timeline visuale semplice** (`trip_presentation.generate_timeline_segments`)
  - Blocchi colorati distinti per giorni di esplorazione e giorni di trasferimento, con icona del mezzo (✈️/🚄/🚌/⛴️).

---

## 10. Tier 2 — Travel Style, avvisi, confronto viaggi

- **Travel Style bars** (`insights.travel_style_scores` / `travel_style_scores_for_stops`)
  - 5 barre (Avventura, Relax, Cultura, Social, Lusso) lette dai punteggi già presenti nel dataset — non è il Travel DNA (quello descrive l'utente, questo la meta).
  - Per i viaggi combinati: media tra le tappe, per descrivere il carattere complessivo dell'itinerario.

- **Avvisi contestuali intelligenti** (`insights.destination_warnings` / `trip_warnings`)
  - Trasferimento lungo (> 4.5h), meta molto gettonata nel periodo scelto (`christmas_score`/`new_year_score`), esperienza dipendente dal meteo (es. mongolfiera, aurora boreale), sforamento budget.
  - Un solo box consolidato per card, tono non allarmistico.

- **Confronto tra viaggi combinati** (`trip_builder.compare_trips`)
  - Stesso principio del confronto destinazioni già esistente, esteso ai viaggi (fino a 2 alla volta).
  - Legge dall'intero pool di candidati generati, non solo dal Top N mostrato in pagina.

---

## 11. Tier 3 — checklist, modalità speciali, condivisione social, anti-FOMO

- **Checklist pratica automatica** (`checklist.py`)
  - 🎒 Cosa portare (da temperature min/max e tag come neve/spiaggia/trekking), 📄 Documenti tipici (per area geografica), 💡 Consigli pratici rapidi (riusa i `practical_tips` già curati nel dataset + una nota se il periodo è natalizio).
  - Per i viaggi combinati aggrega clima, area più "esigente" e consigli di tutte le tappe.

- **Modalità "Primo viaggio da solo" e "Regalo/Sorpresa"** (`app.py`, `handle_quick_start` / `render_gift_surprise`)
  - "🧳 Primo viaggio da solo/a": precompila il questionario con area Europa, volo max 3h, comfort medio, socialità media — facilità logistica alta senza toccare lo scoring.
  - "🎁 Regalo/Sorpresa": nasconde una destinazione dietro un bottone "Scopri il regalo"; una volta rivelata resta fissa in sessione (non si rigenera ad ogni click successivo).

- **Card viaggio/destinazione condivisibile** (`social_card.py`)
  - Immagine PNG (formato verticale, gradiente sul brand dell'app) con nome, match %, un'esperienza WOW e il costo, generata con Pillow.
  - Didascalia testuale breve e curata per i social, volutamente diversa dal riepilogo dettagliato di `export.py` (quello è un itinerario da leggere, questa è un teaser da postare).
  - Se Pillow non è disponibile, fallback automatico alla sola didascalia testuale.

- **Anti-FOMO leggero** (`insights.discarded_destination_alternatives` / `discarded_trip_alternatives`)
  - 1-2 alternative valutate ma non mostrate, con una frase onesta e specifica sul perché (budget, distanza di volo, durata, periodo, o la componente di Feasibility più debole per i viaggi).
  - Riusa dati già calcolati (`compromise_reasons`, componenti di Feasibility): nessun nuovo criterio di scoring introdotto.

- **Facilità organizzativa (1-5)** (`insights.organizational_ease` / `trip_organizational_ease`)
  - Calcolata (non un nuovo campo nel dataset) da area geografica, ore di volo e `comfort_level`.
  - Per i viaggi combinati: il minimo tra le tappe (la più complessa "detta il ritmo"), con una piccola penalità per ogni tappa oltre la prima.
