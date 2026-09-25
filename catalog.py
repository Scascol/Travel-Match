"""
Catalogo di TravelMatch: la "scheda vetrina" di ogni meta.

Qui vive tutto ciò che serve a presentare una meta fuori dal questionario:
un indirizzo breve e stabile (slug) per i link condivisibili, la foto con i
suoi crediti, la zona del mondo e una descrizione di una riga. Oggi lo usano
la pagina meta dell'app e le card dei risultati; domani, se servirà un sito
con dominio proprio indicizzato da Google, le stesse schede diventeranno le
sue pagine senza rifare nulla: gli slug restano gli stessi, così un link
condiviso oggi continuerà a valere anche lì.

Nessuna dipendenza da Streamlit e nessuna chiamata di rete: le foto sono
indirizzi fissi di Wikimedia Commons (licenze libere, scelte e verificate a
mano), caricati dal browser del visitatore e non dal server.

Regole per chi aggiunge una meta:
- lo slug si ricava da solo dal nome; se il nome è lungo o ha parentesi,
  aggiungere una voce a _SLUG_OVERRIDES. Uno slug, una volta pubblicato,
  non va più cambiato (i link già condivisi smetterebbero di funzionare).
- la foto va aggiunta a PHOTOS con autore e licenza esatti della pagina
  Commons: sono obbligatori per le licenze CC BY / CC BY-SA.
- il paese va aggiunto a _ZONE_BY_COUNTRY se è nuovo.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, NamedTuple

from utils import MONTH_SHORT, MOOD_OPTIONS, format_price


class Photo(NamedTuple):
    hero: str      # 1280 px: testata della pagina meta
    card: str      # 960 px: card dei risultati, dove basta molto meno
    author: str
    license: str
    source: str    # pagina Commons con licenza e autore completi

    @property
    def tile(self) -> str:
        """500 px per le tessere della home e di Esplora: una ventina di foto
        in pagina a 960 px peserebbero ~4 MB, troppo per un telefono."""
        return self.card.replace("/960px-", "/500px-")


def _p(hero: str, card: str, author: str, license: str, source: str) -> Photo:
    return Photo(hero, card, author, license, source)


# ---------------------------------------------------------------------------
# Foto (id destinazione -> Photo)
# ---------------------------------------------------------------------------

PHOTOS: dict[int, Photo] = {
    1: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d8/Colosseum_in_Rome-April_2007-1-_copie_2B.jpg/1280px-Colosseum_in_Rome-April_2007-1-_copie_2B.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d8/Colosseum_in_Rome-April_2007-1-_copie_2B.jpg/960px-Colosseum_in_Rome-April_2007-1-_copie_2B.jpg',
        'Diliff', 'CC BY-SA 2.5',
        'https://commons.wikimedia.org/wiki/File:Colosseum_in_Rome-April_2007-1-_copie_2B.jpg',
    ),
    2: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/44/Florence_panorama_as_seen_from_The_Piazza_Michelangelo.jpg/1280px-Florence_panorama_as_seen_from_The_Piazza_Michelangelo.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/44/Florence_panorama_as_seen_from_The_Piazza_Michelangelo.jpg/960px-Florence_panorama_as_seen_from_The_Piazza_Michelangelo.jpg',
        'Ray in Manila', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Florence_panorama_as_seen_from_The_Piazza_Michelangelo.jpg',
    ),
    3: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6e/Gondola_on_the_Grand_Canal%2C_Venice%2C_Italy.jpg/1280px-Gondola_on_the_Grand_Canal%2C_Venice%2C_Italy.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6e/Gondola_on_the_Grand_Canal%2C_Venice%2C_Italy.jpg/960px-Gondola_on_the_Grand_Canal%2C_Venice%2C_Italy.jpg',
        'Peter K Burian', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Gondola_on_the_Grand_Canal,_Venice,_Italy.jpg',
    ),
    4: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bd/Positano_%28Italy%29_03.jpg/1280px-Positano_%28Italy%29_03.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bd/Positano_%28Italy%29_03.jpg/960px-Positano_%28Italy%29_03.jpg',
        'Bernard Gagnon', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Positano_(Italy)_03.jpg',
    ),
    5: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e9/Manarola_NW_Cinque_Terre_Sep23_A7C_07233.jpg/1280px-Manarola_NW_Cinque_Terre_Sep23_A7C_07233.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e9/Manarola_NW_Cinque_Terre_Sep23_A7C_07233.jpg/960px-Manarola_NW_Cinque_Terre_Sep23_A7C_07233.jpg',
        'Timothy A. Gonsalves', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Manarola_NW_Cinque_Terre_Sep23_A7C_07233.jpg',
    ),
    6: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/83/Sea_houses_viewed_from_the_sea%2C_Cefalu%2C_Sicily%2C_Italy_%289452625422%29.jpg/1280px-Sea_houses_viewed_from_the_sea%2C_Cefalu%2C_Sicily%2C_Italy_%289452625422%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/83/Sea_houses_viewed_from_the_sea%2C_Cefalu%2C_Sicily%2C_Italy_%289452625422%29.jpg/960px-Sea_houses_viewed_from_the_sea%2C_Cefalu%2C_Sicily%2C_Italy_%289452625422%29.jpg',
        'l0da_ralta', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Sea_houses_viewed_from_the_sea,_Cefalu,_Sicily,_Italy_(9452625422).jpg',
    ),
    7: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/45/Etna_from_Taormina_2006.jpg/1280px-Etna_from_Taormina_2006.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/45/Etna_from_Taormina_2006.jpg/960px-Etna_from_Taormina_2006.jpg',
        'Victor M. Vicente Selvas', 'Public domain',
        'https://commons.wikimedia.org/wiki/File:Etna_from_Taormina_2006.jpg',
    ),
    8: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fe/Spiaggia_del_Principe.jpg/1280px-Spiaggia_del_Principe.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fe/Spiaggia_del_Principe.jpg/960px-Spiaggia_del_Principe.jpg',
        'Ökologix', 'CC0',
        'https://commons.wikimedia.org/wiki/File:Spiaggia_del_Principe.jpg',
    ),
    9: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/02/Faloria_Cortina_d%27Ampezzo_7.jpg/1280px-Faloria_Cortina_d%27Ampezzo_7.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/02/Faloria_Cortina_d%27Ampezzo_7.jpg/960px-Faloria_Cortina_d%27Ampezzo_7.jpg',
        'kallerna', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Faloria_Cortina_d%27Ampezzo_7.jpg',
    ),
    10: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a0/Bolzano_%28Rathaus%29_-_panoramio.jpg/1280px-Bolzano_%28Rathaus%29_-_panoramio.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a0/Bolzano_%28Rathaus%29_-_panoramio.jpg/960px-Bolzano_%28Rathaus%29_-_panoramio.jpg',
        'Michael Paraskevas', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Bolzano_(Rathaus)_-_panoramio.jpg',
    ),
    11: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/10/Milano%2C_Duomo_with_Milan_Cathedral_and_Galleria_Vittorio_Emanuele_II%2C_2016.jpg/1280px-Milano%2C_Duomo_with_Milan_Cathedral_and_Galleria_Vittorio_Emanuele_II%2C_2016.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/10/Milano%2C_Duomo_with_Milan_Cathedral_and_Galleria_Vittorio_Emanuele_II%2C_2016.jpg/960px-Milano%2C_Duomo_with_Milan_Cathedral_and_Galleria_Vittorio_Emanuele_II%2C_2016.jpg',
        'Steffen Schmitz', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Milano,_Duomo_with_Milan_Cathedral_and_Galleria_Vittorio_Emanuele_II,_2016.jpg',
    ),
    12: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bf/Turin_banner1.jpg/1280px-Turin_banner1.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bf/Turin_banner1.jpg/960px-Turin_banner1.jpg',
        'Hpnx9420, Massimo Telò', 'CC BY 3.0',
        'https://commons.wikimedia.org/wiki/File:Turin_banner1.jpg',
    ),
    13: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Torre_dell%27orso_-_Caletta.JPG/1280px-Torre_dell%27orso_-_Caletta.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Torre_dell%27orso_-_Caletta.JPG/960px-Torre_dell%27orso_-_Caletta.JPG',
        'Psymark', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Torre_dell%27orso_-_Caletta.JPG',
    ),
    14: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e7/Town_of_Bellagio_%28Lake_Como%29_seen_from_the_lake_%2836722979021%29.jpg/1280px-Town_of_Bellagio_%28Lake_Como%29_seen_from_the_lake_%2836722979021%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e7/Town_of_Bellagio_%28Lake_Como%29_seen_from_the_lake_%2836722979021%29.jpg/960px-Town_of_Bellagio_%28Lake_Como%29_seen_from_the_lake_%2836722979021%29.jpg',
        'Ray Swi-hymn from Sijhih-Taipei, Taiwan', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Town_of_Bellagio_(Lake_Como)_seen_from_the_lake_(36722979021).jpg',
    ),
    15: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/83/Basilica_di_San_Francesco_%28Upper_Lawn_1%29.jpg/1280px-Basilica_di_San_Francesco_%28Upper_Lawn_1%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/83/Basilica_di_San_Francesco_%28Upper_Lawn_1%29.jpg/960px-Basilica_di_San_Francesco_%28Upper_Lawn_1%29.jpg',
        'Chris Light', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Basilica_di_San_Francesco_(Upper_Lawn_1).jpg',
    ),
    16: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/de/Eiffel_Tower_and_Pont_Alexandre_III_at_night.jpg/1280px-Eiffel_Tower_and_Pont_Alexandre_III_at_night.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/de/Eiffel_Tower_and_Pont_Alexandre_III_at_night.jpg/960px-Eiffel_Tower_and_Pont_Alexandre_III_at_night.jpg',
        'Getfunky Paris', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Eiffel_Tower_and_Pont_Alexandre_III_at_night.jpg',
    ),
    17: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5f/Tower_Bridge_London_Dusk_Feb_2006.jpg/1280px-Tower_Bridge_London_Dusk_Feb_2006.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5f/Tower_Bridge_London_Dusk_Feb_2006.jpg/960px-Tower_Bridge_London_Dusk_Feb_2006.jpg',
        'Diliff', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Tower_Bridge_London_Dusk_Feb_2006.jpg',
    ),
    18: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ee/Sagrada_Familia_01.jpg/1280px-Sagrada_Familia_01.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ee/Sagrada_Familia_01.jpg/960px-Sagrada_Familia_01.jpg',
        'Bernard Gagnon', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Sagrada_Familia_01.jpg',
    ),
    19: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Trams_in_Lisbon_-a.jpg/1280px-Trams_in_Lisbon_-a.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Trams_in_Lisbon_-a.jpg/960px-Trams_in_Lisbon_-a.jpg',
        'Jorge Franganillo from Barcelona, Spain', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Trams_in_Lisbon_-a.jpg',
    ),
    20: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e7/Cliffs_and_houses_of_the_coast_of_Faial%2C_Santana%2C_Madeira%2C_2023_May.jpg/1280px-Cliffs_and_houses_of_the_coast_of_Faial%2C_Santana%2C_Madeira%2C_2023_May.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e7/Cliffs_and_houses_of_the_coast_of_Faial%2C_Santana%2C_Madeira%2C_2023_May.jpg/960px-Cliffs_and_houses_of_the_coast_of_Faial%2C_Santana%2C_Madeira%2C_2023_May.jpg',
        'Ximonic (Simo Räsänen)', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Cliffs_and_houses_of_the_coast_of_Faial,_Santana,_Madeira,_2023_May.jpg',
    ),
    21: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/90/Prague_Castle_and_Charles_Bridge%2C_Czech_Republic_-_Diliff.jpg/1280px-Prague_Castle_and_Charles_Bridge%2C_Czech_Republic_-_Diliff.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/90/Prague_Castle_and_Charles_Bridge%2C_Czech_Republic_-_Diliff.jpg/960px-Prague_Castle_and_Charles_Bridge%2C_Czech_Republic_-_Diliff.jpg',
        'Diliff', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Prague_Castle_and_Charles_Bridge,_Czech_Republic_-_Diliff.jpg',
    ),
    22: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c4/Schloss_Sch%C3%B6nbrunn_Wien_2014_%28Zuschnitt_1%29.jpg/1280px-Schloss_Sch%C3%B6nbrunn_Wien_2014_%28Zuschnitt_1%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c4/Schloss_Sch%C3%B6nbrunn_Wien_2014_%28Zuschnitt_1%29.jpg/960px-Schloss_Sch%C3%B6nbrunn_Wien_2014_%28Zuschnitt_1%29.jpg',
        'Thomas Wolf, www.foto-tw.de', 'CC BY-SA 3.0 de',
        'https://commons.wikimedia.org/wiki/File:Schloss_Sch%C3%B6nbrunn_Wien_2014_(Zuschnitt_1).jpg',
    ),
    23: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/65/Hungarian_Parliament_Building_2023-9.jpg/1280px-Hungarian_Parliament_Building_2023-9.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/65/Hungarian_Parliament_Building_2023-9.jpg/960px-Hungarian_Parliament_Building_2023-9.jpg',
        'Pierre Blaché', 'CC0',
        'https://commons.wikimedia.org/wiki/File:Hungarian_Parliament_Building_2023-9.jpg',
    ),
    24: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Brandenburger_Tor_nachts.jpg/1280px-Brandenburger_Tor_nachts.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Brandenburger_Tor_nachts.jpg/960px-Brandenburger_Tor_nachts.jpg',
        'Thomas Wolf, www.foto-tw.de', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Brandenburger_Tor_nachts.jpg',
    ),
    25: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6c/Colorful_windows_and_canal_houses_at_blue_hour_with_water_reflection_in_Damrak_Amsterdam_Netherlands.jpg/1280px-Colorful_windows_and_canal_houses_at_blue_hour_with_water_reflection_in_Damrak_Amsterdam_Netherlands.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6c/Colorful_windows_and_canal_houses_at_blue_hour_with_water_reflection_in_Damrak_Amsterdam_Netherlands.jpg/960px-Colorful_windows_and_canal_houses_at_blue_hour_with_water_reflection_in_Damrak_Amsterdam_Netherlands.jpg',
        'Basile Morin', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Colorful_windows_and_canal_houses_at_blue_hour_with_water_reflection_in_Damrak_Amsterdam_Netherlands.jpg',
    ),
    26: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3c/Nyhavn%2C_Copenhagen%2C_20220618_1726_7351.jpg/1280px-Nyhavn%2C_Copenhagen%2C_20220618_1726_7351.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3c/Nyhavn%2C_Copenhagen%2C_20220618_1726_7351.jpg/960px-Nyhavn%2C_Copenhagen%2C_20220618_1726_7351.jpg',
        'Jakub Hałun', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Nyhavn,_Copenhagen,_20220618_1726_7351.jpg',
    ),
    27: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/78/Reykjavik_A%C3%B0flug_Braut_19.JPG/1280px-Reykjavik_A%C3%B0flug_Braut_19.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/78/Reykjavik_A%C3%B0flug_Braut_19.JPG/960px-Reykjavik_A%C3%B0flug_Braut_19.JPG',
        'Girdi', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Reykjavik_A%C3%B0flug_Braut_19.JPG',
    ),
    28: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/df/Aurora_Borealis_Troms%C3%B8_Norway.jpg/1280px-Aurora_Borealis_Troms%C3%B8_Norway.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/df/Aurora_Borealis_Troms%C3%B8_Norway.jpg/960px-Aurora_Borealis_Troms%C3%B8_Norway.jpg',
        'Andi Gentsch', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Aurora_Borealis_Troms%C3%B8_Norway.jpg',
    ),
    29: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c0/Lakeside_trees_by_S%C3%A4rkij%C3%A4rvi_in_winter_coat%2C_Muonio%2C_Lapland%2C_Finland%2C_2019_January.jpg/1280px-Lakeside_trees_by_S%C3%A4rkij%C3%A4rvi_in_winter_coat%2C_Muonio%2C_Lapland%2C_Finland%2C_2019_January.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c0/Lakeside_trees_by_S%C3%A4rkij%C3%A4rvi_in_winter_coat%2C_Muonio%2C_Lapland%2C_Finland%2C_2019_January.jpg/960px-Lakeside_trees_by_S%C3%A4rkij%C3%A4rvi_in_winter_coat%2C_Muonio%2C_Lapland%2C_Finland%2C_2019_January.jpg',
        'Ximonic (Simo Räsänen)', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Lakeside_trees_by_S%C3%A4rkij%C3%A4rvi_in_winter_coat,_Muonio,_Lapland,_Finland,_2019_January.jpg',
    ),
    30: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dc/Matterhorn_above_Zermatt_photo_by_Svein-Magne_Tunli_-_tunliweb.no.jpg/1280px-Matterhorn_above_Zermatt_photo_by_Svein-Magne_Tunli_-_tunliweb.no.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dc/Matterhorn_above_Zermatt_photo_by_Svein-Magne_Tunli_-_tunliweb.no.jpg/960px-Matterhorn_above_Zermatt_photo_by_Svein-Magne_Tunli_-_tunliweb.no.jpg',
        'Smtunli', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Matterhorn_above_Zermatt_photo_by_Svein-Magne_Tunli_-_tunliweb.no.jpg',
    ),
    31: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2b/AUT_Innsbruck%2C_Marktplatz_005.jpg/1280px-AUT_Innsbruck%2C_Marktplatz_005.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2b/AUT_Innsbruck%2C_Marktplatz_005.jpg/960px-AUT_Innsbruck%2C_Marktplatz_005.jpg',
        'wuppertaler', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:AUT_Innsbruck,_Marktplatz_005.jpg',
    ),
    32: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/25/Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg/1280px-Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/25/Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg/960px-Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg',
        'Jim Barton', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg',
    ),
    33: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Ha%27penny_Bridge_%26_River_Liffey%2C_Dublin_%28507194%29_%2832094198423%29.jpg/1280px-Ha%27penny_Bridge_%26_River_Liffey%2C_Dublin_%28507194%29_%2832094198423%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Ha%27penny_Bridge_%26_River_Liffey%2C_Dublin_%28507194%29_%2832094198423%29.jpg/960px-Ha%27penny_Bridge_%26_River_Liffey%2C_Dublin_%28507194%29_%2832094198423%29.jpg',
        'Robert Linsdell from St. Andrews, Canada', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Ha%27penny_Bridge_%26_River_Liffey,_Dublin_(507194)_(32094198423).jpg',
    ),
    34: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c6/Attica_06-13_Athens_50_View_from_Philopappos_-_Acropolis_Hill.jpg/1280px-Attica_06-13_Athens_50_View_from_Philopappos_-_Acropolis_Hill.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c6/Attica_06-13_Athens_50_View_from_Philopappos_-_Acropolis_Hill.jpg/960px-Attica_06-13_Athens_50_View_from_Philopappos_-_Acropolis_Hill.jpg',
        'A.Savin', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Attica_06-13_Athens_50_View_from_Philopappos_-_Acropolis_Hill.jpg',
    ),
    35: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/82/Oia%2C_Santorini_HDR_sunset.jpg/1280px-Oia%2C_Santorini_HDR_sunset.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/82/Oia%2C_Santorini_HDR_sunset.jpg/960px-Oia%2C_Santorini_HDR_sunset.jpg',
        'Pedro Szekely', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Oia,_Santorini_HDR_sunset.jpg',
    ),
    36: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Aerial_view_of_Balos_Beach_and_Lagoon_on_Crete%2C_Greece.jpg/1280px-Aerial_view_of_Balos_Beach_and_Lagoon_on_Crete%2C_Greece.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Aerial_view_of_Balos_Beach_and_Lagoon_on_Crete%2C_Greece.jpg/960px-Aerial_view_of_Balos_Beach_and_Lagoon_on_Crete%2C_Greece.jpg',
        'dronepicr', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Aerial_view_of_Balos_Beach_and_Lagoon_on_Crete,_Greece.jpg',
    ),
    37: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/38/Valletta_skyline_%28cropped%29.jpg/1280px-Valletta_skyline_%28cropped%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/38/Valletta_skyline_%28cropped%29.jpg/960px-Valletta_skyline_%28cropped%29.jpg',
        'Briangotts', 'Uso libero',
        'https://commons.wikimedia.org/wiki/File:Valletta_skyline_(cropped).jpg',
    ),
    38: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a2/Teide_von_Nordosten_%28Zuschnitt_1%29.jpg/1280px-Teide_von_Nordosten_%28Zuschnitt_1%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a2/Teide_von_Nordosten_%28Zuschnitt_1%29.jpg/960px-Teide_von_Nordosten_%28Zuschnitt_1%29.jpg',
        'Thomas Wolf, www.foto-tw.de', 'CC BY-SA 3.0 de',
        'https://commons.wikimedia.org/wiki/File:Teide_von_Nordosten_(Zuschnitt_1).jpg',
    ),
    39: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Krakow_-_Cloth_Hall_from_Basilica_-_1.jpg/1280px-Krakow_-_Cloth_Hall_from_Basilica_-_1.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Krakow_-_Cloth_Hall_from_Basilica_-_1.jpg/960px-Krakow_-_Cloth_Hall_from_Basilica_-_1.jpg',
        'Ingo Mehling', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Krakow_-_Cloth_Hall_from_Basilica_-_1.jpg',
    ),
    40: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3d/Sweden%2C_Stockholm%2C_Gamla_Stan_%28Old_Town%29%2C_Dusk_150628-69.jpg/1280px-Sweden%2C_Stockholm%2C_Gamla_Stan_%28Old_Town%29%2C_Dusk_150628-69.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3d/Sweden%2C_Stockholm%2C_Gamla_Stan_%28Old_Town%29%2C_Dusk_150628-69.jpg/960px-Sweden%2C_Stockholm%2C_Gamla_Stan_%28Old_Town%29%2C_Dusk_150628-69.jpg',
        'Richardmaackphotography', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Sweden,_Stockholm,_Gamla_Stan_(Old_Town),_Dusk_150628-69.jpg',
    ),
    41: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a9/Rozenhoedkaai_%28canal%29_and_Belfry_of_Bruges%2C_Bruges%2C_Belgium_%28Ank_Kumar%2C_Infosys_Limited%29_01.jpg/1280px-Rozenhoedkaai_%28canal%29_and_Belfry_of_Bruges%2C_Bruges%2C_Belgium_%28Ank_Kumar%2C_Infosys_Limited%29_01.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a9/Rozenhoedkaai_%28canal%29_and_Belfry_of_Bruges%2C_Bruges%2C_Belgium_%28Ank_Kumar%2C_Infosys_Limited%29_01.jpg/960px-Rozenhoedkaai_%28canal%29_and_Belfry_of_Bruges%2C_Bruges%2C_Belgium_%28Ank_Kumar%2C_Infosys_Limited%29_01.jpg',
        'Ank Kumar', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Rozenhoedkaai_(canal)_and_Belfry_of_Bruges,_Bruges,_Belgium_(Ank_Kumar,_Infosys_Limited)_01.jpg',
    ),
    42: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0c/Jemaa_el-Fnaa_Marrakech_at_sunset.jpg/1280px-Jemaa_el-Fnaa_Marrakech_at_sunset.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0c/Jemaa_el-Fnaa_Marrakech_at_sunset.jpg/960px-Jemaa_el-Fnaa_Marrakech_at_sunset.jpg',
        'Herokk', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Jemaa_el-Fnaa_Marrakech_at_sunset.jpg',
    ),
    43: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0b/Dubai_skyline_2010_%28censored_Burj_Khalifa%29.jpg/1280px-Dubai_skyline_2010_%28censored_Burj_Khalifa%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0b/Dubai_skyline_2010_%28censored_Burj_Khalifa%29.jpg/960px-Dubai_skyline_2010_%28censored_Burj_Khalifa%29.jpg',
        'Jan Michael Pfeiffer', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Dubai_skyline_2010_(censored_Burj_Khalifa).jpg',
    ),
    44: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d7/Sultan_Qaboos_Grand_Mosque_%281%29.jpg/1280px-Sultan_Qaboos_Grand_Mosque_%281%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d7/Sultan_Qaboos_Grand_Mosque_%281%29.jpg/960px-Sultan_Qaboos_Grand_Mosque_%281%29.jpg',
        'Mostafameraji', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Sultan_Qaboos_Grand_Mosque_(1).jpg',
    ),
    45: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Zanzibar_2012_06_06_4165_%287592265338%29.jpg/1280px-Zanzibar_2012_06_06_4165_%287592265338%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Zanzibar_2012_06_06_4165_%287592265338%29.jpg/960px-Zanzibar_2012_06_06_4165_%287592265338%29.jpg',
        'Harvey Barrison from Massapequa, NY, USA', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Zanzibar_2012_06_06_4165_(7592265338).jpg',
    ),
    46: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/97/Playa_Maya%2C_Ko_Phi_Phi%2C_Tailandia%2C_2013-08-19%2C_DD_13.JPG/1280px-Playa_Maya%2C_Ko_Phi_Phi%2C_Tailandia%2C_2013-08-19%2C_DD_13.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/97/Playa_Maya%2C_Ko_Phi_Phi%2C_Tailandia%2C_2013-08-19%2C_DD_13.JPG/960px-Playa_Maya%2C_Ko_Phi_Phi%2C_Tailandia%2C_2013-08-19%2C_DD_13.JPG',
        'Diego Delso', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Playa_Maya,_Ko_Phi_Phi,_Tailandia,_2013-08-19,_DD_13.JPG',
    ),
    47: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Templo_Wat_Arun%2C_Bangkok%2C_Tailandia%2C_2013-08-22%2C_DD_37.jpg/1280px-Templo_Wat_Arun%2C_Bangkok%2C_Tailandia%2C_2013-08-22%2C_DD_37.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Templo_Wat_Arun%2C_Bangkok%2C_Tailandia%2C_2013-08-22%2C_DD_37.jpg/960px-Templo_Wat_Arun%2C_Bangkok%2C_Tailandia%2C_2013-08-22%2C_DD_37.jpg',
        'Diego Delso', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Templo_Wat_Arun,_Bangkok,_Tailandia,_2013-08-22,_DD_37.jpg',
    ),
    48: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Rice_terraces%2C_Bali.jpg/1280px-Rice_terraces%2C_Bali.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Rice_terraces%2C_Bali.jpg/960px-Rice_terraces%2C_Bali.jpg',
        'Vyacheslav Argenberg', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Rice_terraces,_Bali.jpg',
    ),
    49: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fa/Ha_Long_Bay%2C_Vietnam%2C_View_from_above.jpg/1280px-Ha_Long_Bay%2C_Vietnam%2C_View_from_above.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fa/Ha_Long_Bay%2C_Vietnam%2C_View_from_above.jpg/960px-Ha_Long_Bay%2C_Vietnam%2C_View_from_above.jpg',
        'Vyacheslav Argenberg', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Ha_Long_Bay,_Vietnam,_View_from_above.jpg',
    ),
    50: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ed/Nine_arch_Sri_Lanka.jpg/1280px-Nine_arch_Sri_Lanka.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ed/Nine_arch_Sri_Lanka.jpg/960px-Nine_arch_Sri_Lanka.jpg',
        'Janith Pramuditha', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Nine_arch_Sri_Lanka.jpg',
    ),
    51: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e2/Eriyadu_Island._View_from_the_south._Maldives.jpg/1280px-Eriyadu_Island._View_from_the_south._Maldives.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e2/Eriyadu_Island._View_from_the_south._Maldives.jpg/960px-Eriyadu_Island._View_from_the_south._Maldives.jpg',
        'Ввласенко', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Eriyadu_Island._View_from_the_south._Maldives.jpg',
    ),
    52: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1e/Lower_Manhattan%2C_New_York_skyline_from_Liberty_Island_2021.jpg/1280px-Lower_Manhattan%2C_New_York_skyline_from_Liberty_Island_2021.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1e/Lower_Manhattan%2C_New_York_skyline_from_Liberty_Island_2021.jpg/960px-Lower_Manhattan%2C_New_York_skyline_from_Liberty_Island_2021.jpg',
        'Percival Kestreltail', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Lower_Manhattan,_New_York_skyline_from_Liberty_Island_2021.jpg',
    ),
    53: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/77/Lifeguard_stand%2C_Miami_Beach.jpg/1280px-Lifeguard_stand%2C_Miami_Beach.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/77/Lifeguard_stand%2C_Miami_Beach.jpg/960px-Lifeguard_stand%2C_Miami_Beach.jpg',
        'Radomianin', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Lifeguard_stand,_Miami_Beach.jpg',
    ),
    54: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/98/Mexico_City_Zocalo_Cathedral.jpg/1280px-Mexico_City_Zocalo_Cathedral.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/98/Mexico_City_Zocalo_Cathedral.jpg/960px-Mexico_City_Zocalo_Cathedral.jpg',
        'Jeff Kramer', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Mexico_City_Zocalo_Cathedral.jpg',
    ),
    55: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/75/Maelcon%2C_Havana%2C_Cuba_%2849080063752%29.jpg/1280px-Maelcon%2C_Havana%2C_Cuba_%2849080063752%29.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/75/Maelcon%2C_Havana%2C_Cuba_%2849080063752%29.jpg/960px-Maelcon%2C_Havana%2C_Cuba_%2849080063752%29.jpg',
        'kuhnmi', 'CC BY 2.0',
        'https://commons.wikimedia.org/wiki/File:Maelcon,_Havana,_Cuba_(49080063752).jpg',
    ),
    56: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/ca/Bavaro_Beach_045.jpg/1280px-Bavaro_Beach_045.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/ca/Bavaro_Beach_045.jpg/960px-Bavaro_Beach_045.jpg',
        'Hans Buch', 'Public domain',
        'https://commons.wikimedia.org/wiki/File:Bavaro_Beach_045.jpg',
    ),
    57: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Hot_air_balloon_in_Cappadocia_02.jpg/1280px-Hot_air_balloon_in_Cappadocia_02.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Hot_air_balloon_in_Cappadocia_02.jpg/960px-Hot_air_balloon_in_Cappadocia_02.jpg',
        'Bernard Gagnon', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Hot_air_balloon_in_Cappadocia_02.jpg',
    ),
    58: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Istanbul_Hagia_Sophia_Sultanahmed.JPG/1280px-Istanbul_Hagia_Sophia_Sultanahmed.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Istanbul_Hagia_Sophia_Sultanahmed.JPG/960px-Istanbul_Hagia_Sophia_Sultanahmed.JPG',
        'Julian Nyča', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Istanbul_Hagia_Sophia_Sultanahmed.JPG',
    ),
    59: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e0/Cape_Town_City_Bowl_and_Table_Mountain_at_dawn.jpg/1280px-Cape_Town_City_Bowl_and_Table_Mountain_at_dawn.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e0/Cape_Town_City_Bowl_and_Table_Mountain_at_dawn.jpg/960px-Cape_Town_City_Bowl_and_Table_Mountain_at_dawn.jpg',
        'Daniel Case', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Cape_Town_City_Bowl_and_Table_Mountain_at_dawn.jpg',
    ),
    60: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6d/Tokyo_Tower%2C_Minato_City.jpg/1280px-Tokyo_Tower%2C_Minato_City.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6d/Tokyo_Tower%2C_Minato_City.jpg/960px-Tokyo_Tower%2C_Minato_City.jpg',
        'David Kernan', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Tokyo_Tower,_Minato_City.jpg',
    ),
    61: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/21/Rabelo_boats_and_Ribeira_seen_from_Cais_de_Gaia%2C_20250605_1623_9879.jpg/1280px-Rabelo_boats_and_Ribeira_seen_from_Cais_de_Gaia%2C_20250605_1623_9879.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/21/Rabelo_boats_and_Ribeira_seen_from_Cais_de_Gaia%2C_20250605_1623_9879.jpg/960px-Rabelo_boats_and_Ribeira_seen_from_Cais_de_Gaia%2C_20250605_1623_9879.jpg',
        'Jakub Hałun', 'CC BY 4.0',
        'https://commons.wikimedia.org/wiki/File:Rabelo_boats_and_Ribeira_seen_from_Cais_de_Gaia,_20250605_1623_9879.jpg',
    ),
    62: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0e/Torii_path_with_lantern_at_Fushimi_Inari_Taisha_Shrine%2C_Kyoto%2C_Japan.jpg/1280px-Torii_path_with_lantern_at_Fushimi_Inari_Taisha_Shrine%2C_Kyoto%2C_Japan.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0e/Torii_path_with_lantern_at_Fushimi_Inari_Taisha_Shrine%2C_Kyoto%2C_Japan.jpg/960px-Torii_path_with_lantern_at_Fushimi_Inari_Taisha_Shrine%2C_Kyoto%2C_Japan.jpg',
        'Basile Morin', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Torii_path_with_lantern_at_Fushimi_Inari_Taisha_Shrine,_Kyoto,_Japan.jpg',
    ),
    63: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Osaka_Dotonbori_yoru_02.jpg/1280px-Osaka_Dotonbori_yoru_02.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Osaka_Dotonbori_yoru_02.jpg/960px-Osaka_Dotonbori_yoru_02.jpg',
        'Sakai Yayoi', 'CC0',
        'https://commons.wikimedia.org/wiki/File:Osaka_Dotonbori_yoru_02.jpg',
    ),
    64: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Phra_That_Doi_Suthep_01.jpg/1280px-Phra_That_Doi_Suthep_01.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Phra_That_Doi_Suthep_01.jpg/960px-Phra_That_Doi_Suthep_01.jpg',
        'เทวประภาส มากคล้าย', 'CC BY 3.0',
        'https://commons.wikimedia.org/wiki/File:Phra_That_Doi_Suthep_01.jpg',
    ),
    65: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f8/Essaouira_Citadel.jpg/1280px-Essaouira_Citadel.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f8/Essaouira_Citadel.jpg/960px-Essaouira_Citadel.jpg',
        'Ahmed.magdy', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Essaouira_Citadel.jpg',
    ),
    66: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/84/Merzouga_Dunes_2011.jpg/1280px-Merzouga_Dunes_2011.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/84/Merzouga_Dunes_2011.jpg/960px-Merzouga_Dunes_2011.jpg',
        'Bjørn Christian Tørrissen', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Merzouga_Dunes_2011.jpg',
    ),
    67: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7a/Cadaques_Pueblo_Marinero.JPG/1280px-Cadaques_Pueblo_Marinero.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7a/Cadaques_Pueblo_Marinero.JPG/960px-Cadaques_Pueblo_Marinero.JPG',
        'Anthiro 57', 'CC BY-SA 3.0 es',
        'https://commons.wikimedia.org/wiki/File:Cadaques_Pueblo_Marinero.JPG',
    ),
    68: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/48/Sal_Sta_Maria_beach_hotel.jpg/1280px-Sal_Sta_Maria_beach_hotel.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/48/Sal_Sta_Maria_beach_hotel.jpg/960px-Sal_Sta_Maria_beach_hotel.jpg',
        'Cayambe', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Sal_Sta_Maria_beach_hotel.jpg',
    ),
    69: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bb/Der_Strand_von_Cofete_03.jpg/1280px-Der_Strand_von_Cofete_03.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bb/Der_Strand_von_Cofete_03.jpg/960px-Der_Strand_von_Cofete_03.jpg',
        'JensKunstfreund', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Der_Strand_von_Cofete_03.jpg',
    ),
    70: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/00/Timanfaya-_Lanzarote-_Illas_Canarias-_Spain-T20.jpg/1280px-Timanfaya-_Lanzarote-_Illas_Canarias-_Spain-T20.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/00/Timanfaya-_Lanzarote-_Illas_Canarias-_Spain-T20.jpg/960px-Timanfaya-_Lanzarote-_Illas_Canarias-_Spain-T20.jpg',
        'Luis Miguel Bugallo Sánchez (Lmbuga)', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Timanfaya-_Lanzarote-_Illas_Canarias-_Spain-T20.jpg',
    ),
    71: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c0/Red_Sea_%E7%B4%85%E6%B5%B7_-_panoramio.jpg/1280px-Red_Sea_%E7%B4%85%E6%B5%B7_-_panoramio.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c0/Red_Sea_%E7%B4%85%E6%B5%B7_-_panoramio.jpg/960px-Red_Sea_%E7%B4%85%E6%B5%B7_-_panoramio.jpg',
        'lienyuan lee', 'CC BY 3.0',
        'https://commons.wikimedia.org/wiki/File:Red_Sea_%E7%B4%85%E6%B5%B7_-_panoramio.jpg',
    ),
    72: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/56/Petra%2C_Jordan_-The_Treasury.JPG/1280px-Petra%2C_Jordan_-The_Treasury.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/56/Petra%2C_Jordan_-The_Treasury.JPG/960px-Petra%2C_Jordan_-The_Treasury.JPG',
        'Davidchocron', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Petra,_Jordan_-The_Treasury.JPG',
    ),
    73: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a6/Reine_Lofoten_2009.JPG/1280px-Reine_Lofoten_2009.JPG',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a6/Reine_Lofoten_2009.JPG/960px-Reine_Lofoten_2009.JPG',
        'Petr Šmerkl, Wikipedia', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Reine_Lofoten_2009.JPG',
    ),
    74: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6e/Old_town_of_Tallinn_06-03-2012.jpg/1280px-Old_town_of_Tallinn_06-03-2012.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6e/Old_town_of_Tallinn_06-03-2012.jpg/960px-Old_town_of_Tallinn_06-03-2012.jpg',
        'Ivar Leidus (Iifar)', 'CC BY-SA 3.0 ee',
        'https://commons.wikimedia.org/wiki/File:Old_town_of_Tallinn_06-03-2012.jpg',
    ),
    75: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/db/Old_Town_and_Narikala%2C_Tbilisi.jpg/1280px-Old_Town_and_Narikala%2C_Tbilisi.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/db/Old_Town_and_Narikala%2C_Tbilisi.jpg/960px-Old_Town_and_Narikala%2C_Tbilisi.jpg',
        'Saskia Heijltjes', 'CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Old_Town_and_Narikala,_Tbilisi.jpg',
    ),
    76: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Mount_Ararat_and_the_Yerevan_skyline.jpg/1280px-Mount_Ararat_and_the_Yerevan_skyline.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/Mount_Ararat_and_the_Yerevan_skyline.jpg/960px-Mount_Ararat_and_the_Yerevan_skyline.jpg',
        'Սէրուժ Ուրիշեան (Serouj Ourishian)', 'CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Mount_Ararat_and_the_Yerevan_skyline.jpg',
    ),
    77: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/03/Tirana_-_Skanderbeg_Square_%28Sheshi_Sk%C3%ABnderbej%29_-_by_Pudelek.jpg/1280px-Tirana_-_Skanderbeg_Square_%28Sheshi_Sk%C3%ABnderbej%29_-_by_Pudelek.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/03/Tirana_-_Skanderbeg_Square_%28Sheshi_Sk%C3%ABnderbej%29_-_by_Pudelek.jpg/960px-Tirana_-_Skanderbeg_Square_%28Sheshi_Sk%C3%ABnderbej%29_-_by_Pudelek.jpg',
        'Pudelek', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Tirana_-_Skanderbeg_Square_(Sheshi_Sk%C3%ABnderbej)_-_by_Pudelek.jpg',
    ),
    78: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/68/Church_of_St._John_at_Kaneo_10.jpg/1280px-Church_of_St._John_at_Kaneo_10.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/68/Church_of_St._John_at_Kaneo_10.jpg/960px-Church_of_St._John_at_Kaneo_10.jpg',
        'kallerna', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Church_of_St._John_at_Kaneo_10.jpg',
    ),
    79: _p(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Ba%C5%A1%C4%8Dar%C5%A1ija.jpg/1280px-Ba%C5%A1%C4%8Dar%C5%A1ija.jpg',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Ba%C5%A1%C4%8Dar%C5%A1ija.jpg/960px-Ba%C5%A1%C4%8Dar%C5%A1ija.jpg',
        'Yukof', 'CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Ba%C5%A1%C4%8Dar%C5%A1ija.jpg',
    ),
}


# ---------------------------------------------------------------------------
# Slug: l'indirizzo breve di ogni meta nei link (?meta=creta)
# ---------------------------------------------------------------------------

# Solo dove lo slug automatico sarebbe lungo o poco naturale da scrivere.
_SLUG_OVERRIDES = {
    8: "costa-smeralda",
    9: "cortina-dolomiti",
    10: "bolzano-mercatini",
    13: "salento",
    15: "umbria",
    29: "rovaniemi",
    38: "tenerife",
    44: "oman",
    46: "phuket-krabi",
    49: "vietnam",
    50: "sri-lanka",
    55: "cuba",
    66: "merzouga",
    68: "capo-verde",
}


def slugify(text: str) -> str:
    """'Palermo & Sicilia Occidentale' -> 'palermo-sicilia-occidentale'."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    plain = re.sub(r"\([^)]*\)", " ", plain)
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def slug_for(dest_id: int, name: str) -> str:
    return _SLUG_OVERRIDES.get(int(dest_id)) or slugify(name)


def build_slug_index(df) -> dict[str, int]:
    """slug -> id per tutto il dataset. Fallisce subito se due mete finissero
    con lo stesso slug: meglio un errore in sviluppo che un link condiviso
    che apre la meta sbagliata."""
    index: dict[str, int] = {}
    for dest_id, name in zip(df["id"], df["name"]):
        slug = slug_for(dest_id, name)
        if slug in index:
            raise ValueError(f"Slug duplicato '{slug}' per le mete {index[slug]} e {dest_id}")
        index[slug] = int(dest_id)
    return index


def normalize_slug(raw: Any) -> str:
    """Pulisce uno slug arrivato da un link: maiuscole, spazi e accenti
    scritti a mano ("Creta ", "Città del Capo") non devono rompere niente."""
    return slugify(str(raw or ""))[:80]


# ---------------------------------------------------------------------------
# Zone del mondo (per la navigazione "Esplora per zona")
# ---------------------------------------------------------------------------

ZONES = ["Italia", "Europa", "Africa", "Medio Oriente e Caucaso", "Asia", "Americhe"]

_ZONE_BY_COUNTRY = {
    "Italia": "Italia",
    **{c: "Europa" for c in (
        "Albania", "Austria", "Belgio", "Bosnia ed Erzegovina", "Danimarca", "Estonia",
        "Finlandia", "Francia", "Germania", "Grecia", "Irlanda", "Islanda",
        "Macedonia del Nord", "Malta", "Norvegia", "Paesi Bassi", "Polonia", "Portogallo",
        "Regno Unito", "Repubblica Ceca", "Spagna", "Svezia", "Svizzera", "Ungheria",
    )},
    **{c: "Africa" for c in ("Capo Verde", "Egitto", "Marocco", "Sudafrica", "Tanzania")},
    **{c: "Medio Oriente e Caucaso" for c in (
        "Armenia", "Emirati Arabi Uniti", "Georgia", "Giordania", "Oman", "Turchia",
    )},
    **{c: "Asia" for c in ("Giappone", "Indonesia", "Maldive", "Sri Lanka", "Thailandia", "Vietnam")},
    **{c: "Americhe" for c in ("Cuba", "Messico", "Repubblica Dominicana", "Stati Uniti")},
}


def zone_for(country: str) -> str:
    return _ZONE_BY_COUNTRY.get(country, "Europa")


# ---------------------------------------------------------------------------
# Scheda vetrina
# ---------------------------------------------------------------------------

def months_label(months: list[int]) -> str:
    """[5, 6, 7, 9, 10] -> 'mag-lug, set-ott': gli intervalli consecutivi
    diventano un trattino, molto più leggibile di cinque mesi in fila."""
    ms = sorted({int(m) for m in months if 1 <= int(m) <= 12})
    if not ms:
        return ""
    if len(ms) == 12:
        return "tutto l'anno"
    runs: list[list[int]] = []
    for m in ms:
        if runs and m == runs[-1][-1] + 1:
            runs[-1].append(m)
        else:
            runs.append([m])
    # Un intervallo che attraversa capodanno (nov-dic + gen-feb) è uno solo.
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:
        runs[0] = runs.pop() + runs[0]
    parts = [
        MONTH_SHORT[r[0] - 1] if len(r) == 1 else f"{MONTH_SHORT[r[0] - 1]}-{MONTH_SHORT[r[-1] - 1]}"
        for r in runs
    ]
    return ", ".join(parts)


def place_label(country: str, area: str) -> str:
    """'Grecia · Europa', ma solo 'Italia' invece di 'Italia · Italia'."""
    return country if area == country else f"{country} · {area}"


def photo_for(dest_id: int) -> Photo | None:
    return PHOTOS.get(int(dest_id))


def one_liner(row: Any) -> str:
    """Una riga che descrive la meta senza bisogno di altro: è il testo che
    accompagna un link condiviso e, un domani, la descrizione per Google."""
    moods = [MOOD_OPTIONS.get(m, m).split(" ", 1)[-1].lower() for m in list(row["moods"])[:2]]
    # "Costa Smeralda (Sardegna)" dice già dove si trova: una seconda
    # parentesi col paese sarebbe solo rumore.
    name = row["name"]
    parts = [name if "(" in name or row["country"] in name else f"{name} ({row['country']})"]
    if moods:
        joiner = " ed " if len(moods) > 1 and moods[1][:1] in "aeiou" else " e "
        parts[0] += ": " + joiner.join(moods)
    when = months_label(list(row["best_months"]))
    if when:
        parts.append(f"periodo migliore {when}")
    parts.append(f"{row['days_min']}-{row['days_max']} giorni, da {format_price(row['total_cost_min'])} a persona")
    return ", ".join(parts) + "."


def catalog_entry(row: Any) -> dict[str, Any]:
    dest_id = int(row["id"])
    return {
        "id": dest_id,
        "slug": slug_for(dest_id, row["name"]),
        "name": row["name"],
        "country": row["country"],
        "zone": zone_for(row["country"]),
        "photo": photo_for(dest_id),
        "price_from": float(row["total_cost_min"]),
        "days": (int(row["days_min"]), int(row["days_max"])),
        "best_months": sorted(int(m) for m in row["best_months"]),
        "moods": list(row["moods"]),
        "summary": one_liner(row),
    }


# ---------------------------------------------------------------------------
# Vetrina della home ed Esplora
# ---------------------------------------------------------------------------

# Quando sono stati rivisti itinerari e luoghi curati: lo mostriamo in home
# perché un sito di viaggi che non dice quanto sono freschi i suoi dati non
# ispira fiducia. Da aggiornare a ogni revisione del dataset.
DATA_REVIEWED = "settembre 2026"

# (chiave mood, titolo, sottotitolo, meta da cui prendere la foto)
MOOD_SHOWCASE = [
    ("relax_beach", "Mare e relax", "Spiagge, acqua limpida, ritmi lenti", 36),
    ("nature_adventure", "Natura e avventura", "Sentieri, fiordi e paesaggi enormi", 73),
    ("city_culture", "Città d'arte", "Musei, quartieri storici, cibo di strada", 1),
    ("romantic", "Romantico", "Tramonti e cene da ricordare", 35),
    ("snow_mountain", "Neve e montagna", "Piste, baite, villaggi innevati", 30),
    ("food", "Viaggi da gustare", "Mercati, trattorie, cucine da scoprire", 63),
    ("party_nightlife", "Notti da vivere", "Locali, musica, città che non dormono", 25),
    ("unique", "Esperienze uniche", "Mongolfiere, aurore, deserti", 57),
]

# zona -> (sottotitolo, meta da cui prendere la foto)
ZONE_SHOWCASE = {
    "Italia": ("Dalle Dolomiti alle isole", 4),
    "Europa": ("Capitali, isole e fiordi a poche ore di volo", 21),
    "Africa": ("Deserti, medine e oceano", 66),
    "Medio Oriente e Caucaso": ("Città antiche e grande ospitalità", 72),
    "Asia": ("Templi, isole tropicali, street food", 62),
    "Americhe": ("Metropoli e Caraibi", 52),
}

DURATION_FILTERS = {
    "Weekend (2-3 giorni)": (2, 3),
    "4-6 giorni": (4, 6),
    "Una settimana (7-9 giorni)": (7, 9),
    "10 giorni o più": (10, 60),
}

BUDGET_FILTERS = {
    "Fino a 500 €": 500,
    "Fino a 1.000 €": 1000,
    "Fino a 1.500 €": 1500,
    "Fino a 2.500 €": 2500,
}


# Mete che il dataset consiglia anche in mesi in cui foto e nome parlano
# d'altro: "Bolzano & Mercatini di Natale" a luglio in vetrina stonerebbe.
# Restano trovabili in Esplora; qui compaiono solo nei mesi indicati.
_SHOWCASE_ONLY_IN = {10: {11, 12, 1}}


def month_picks(df, month: int, n: int = 8) -> list[int]:
    """Le mete da proporre per un mese: solo quelle per cui è un periodo
    migliore, prima le più "stagionali" (Tromsø a novembre dice di più di
    Roma, che va bene otto mesi l'anno), alternando le zone del mondo perché
    la vetrina non diventi otto città europee di fila."""
    rows = [
        r for _, r in df.iterrows()
        if month in set(int(m) for m in r["best_months"])
        and month in _SHOWCASE_ONLY_IN.get(int(r["id"]), {month})
    ]
    # Ordine stabile nel mese ma diverso da un mese all'altro, a parità di
    # stagionalità: altrimenti vincerebbero sempre gli id più bassi.
    rows.sort(key=lambda r: (len(r["best_months"]), (int(r["id"]) * 7 + month * 13) % 17))
    by_zone: dict[str, list] = {}
    for r in rows:
        by_zone.setdefault(zone_for(r["country"]), []).append(r)
    picks: list[int] = []
    while len(picks) < n and any(by_zone.values()):
        for zone in ZONES:
            if by_zone.get(zone) and len(picks) < n:
                picks.append(int(by_zone[zone].pop(0)["id"]))
    return picks


def explore(
    df,
    month: int | None = None,
    mood: str | None = None,
    zone: str | None = None,
    budget_max: float | None = None,
    days: tuple[int, int] | None = None,
    sort: str = "season",
):
    """Filtra e ordina il dataset per la pagina Esplora. Ogni filtro a None
    è "qualsiasi". Ordinamenti: "season" (prima le più stagionali per il mese
    scelto, o le più versatili se il mese non c'è) e "price"."""
    out = df
    if month:
        out = out[out["best_months"].apply(lambda ms: month in set(int(m) for m in ms))]
    if mood:
        out = out[out["moods"].apply(lambda ms: mood in list(ms))]
    if zone:
        out = out[out["country"].map(zone_for) == zone]
    if budget_max:
        out = out[out["total_cost_min"] <= budget_max]
    if days:
        low, high = days
        out = out[(out["days_min"] <= high) & (out["days_max"] >= low)]
    if sort == "price":
        return out.sort_values(["total_cost_min", "name"])
    season_len = out["best_months"].apply(len)
    # Con un mese scelto conviene vedere prima le mete "da quel mese";
    # senza, prima quelle che vanno bene più a lungo.
    key = season_len if month else -season_len
    return out.assign(_k=key).sort_values(["_k", "total_cost_min"]).drop(columns="_k")
