# Stumeta Workshop/Exkursion Zuordnung 

Sortiert Teilnehmende der StuMeTa in Workshops und Exkursionen basiert auf ihren Präferenzen ein.

Die Sortierung basiert auf dem "Minimum-Cost Flow Problem", das eine optimale Zuordnung berechnet.
Jeder erfüllten Wahl (1. Wahl, 2. Wahl, etc.) wird am Anfang ein "Kostenfaktor" als Gewichtung gegeben (siehe Anwendung).
Dann werden für jede Zuordnungskombination die "Gesamtkosten" berechnet und die Kombination mit den geringsten "Gesamtkosten" wird ausgegeben. 

## 1. Vorbereitung

### uv
Das Programm ist ein einfaches Python-Script, daher kann es auch mit einer bereits vorhandenen Python-Installation laufen, die Voraussetzungen sind in den ersten Zeilen von "allocator.py" zu finden.
uv ist jedoch die mit Abstand schnellste und einfachste Methode, Python Installationen zu verwalten. Daher verwendet diese Anleitung uv und das Programm wurde auch nur mit uv getestet. Mehr Infos zu uv hier: https://docs.astral.sh/uv/

Falls uv nicht bereits installiert wurde, kann der folgende Befehl im Terminal ausgeführt werden:

Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

### Anmeldeformular und Orga-Mailadressen
Als Input werden die Teilnehmerliste (mit Vorname, Nachname, Stadt und Präferenzen für Workshops und Exkursionen) im CSV-Format und Kapazitäts-Dateien im CSV-Format, die die maximale Anzahl an Plätzen der Workshops/Exkursionen enthält, benötigt. 

Eine Zeile in der Kapazitätdatei für Workshops sind z.B. so aus:

Beispiel Workshop,15

Im Unterordner "example/" gibt es Beispiele für alle drei Dateien.

### Setup Datei
Die Datei "setup.toml" öffnen und mit den richten Pfaden und Spalten ausfüllen. 

Wenn es noch keine realen Anmeldedaten gibt, können die default-Werte für die Input-Dateien stehen bleiben. Dann werden die Beispieldatein aus dem Unterordner "example/" verwendet.

## 2. Anwendung
Terminal öffnen und folgenden Befehl eingeben:

uv run allocator.py

Dadurch werden eine Teilnehmerliste und eine Warteliste im Unterordner "output/" (falls der Pfad im setup file nicht geändert wurde) erzeugt.

Beim ersten Ausführen kann es etwas länger dauern, da die Module geladen werden müssen. Wenn Mac/Linux benutzt wird, kann allocator.py auch ausführbar gemacht werden (chmod +x allocator.py), dann muss man als Befehl nur "./lottery.py" eingeben. 

Bei Bedarf können die Gewichtungen (cost) für die Wahlen in "setup.toml" angepasst werden. Eine höhere Zahl macht das Vorkommen dieser Wahl unwarscheinlicher.

Eine Zuordnung zu keiner der 3 Wahlen ist nicht möglich (Und würde bestimmt Leute unglücklich machen). Falls mit den in den Kapazitätsdateien angebenen Obergrenzen keine Zuordnung möglich ist, berechnet das Programm automatisch, welche Kapazitätserhöhungen bei welchen Workshops/Exkursionen eine Zuordnung möglich machen würden. Dabei ist auch eine Kombination über jeweils mehrere Workshops/Exkursionen möglich.
