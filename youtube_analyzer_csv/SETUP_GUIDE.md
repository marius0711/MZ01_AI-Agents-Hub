# 🚀 Setup-Anleitung für YouTube Analyzer

## Schritt 1: Ordnerstruktur erstellen

Erstelle folgende Struktur in `/Users/marize/Documents/python_files/AI-agents-hub/youtube_analyzer_csv/`:

```
youtube_analyzer_csv/
├── youtube_analyzer.html
├── README.md
├── data/
│   ├── Tabellendaten.csv
│   ├── Gesamtwerte.csv
│   └── Diagrammdaten.csv
├── exports/
└── docs/
    └── Erste_Analyse_Erkenntnisse.md
```

## Schritt 2: Dateien platzieren

### Bereits vorhanden (von dir gelegt):
- ✅ `youtube_analyzer.html` (Haupt-Dashboard)

### Aus diesem Output kopieren:
- `README.md` → In den Root-Ordner
- `Erste_Analyse_Erkenntnisse.md` → In den `docs/` Ordner

### CSV-Dateien verschieben:
Die drei CSV-Dateien aus deinen Uploads in den `data/` Ordner:
- `Tabellendaten.csv`
- `Gesamtwerte.csv`
- `Diagrammdaten.csv`

## Schritt 3: Terminal-Befehle

Öffne Terminal und führe aus:

```bash
# Navigiere zum Projekt-Ordner
cd /Users/marize/Documents/python_files/AI-agents-hub/youtube_analyzer_csv

# Erstelle Unterordner
mkdir -p data exports docs

# Wenn CSVs noch woanders sind, verschiebe sie:
# mv /path/to/Tabellendaten.csv data/
# mv /path/to/Gesamtwerte.csv data/
# mv /path/to/Diagrammdaten.csv data/
```

## Schritt 4: Dashboard testen

1. Öffne `youtube_analyzer.html` im Browser (Doppelklick)
2. Ziehe die 3 CSV-Dateien aus dem `data/` Ordner in den Upload-Bereich
3. Schaue dir die Analysen an
4. Exportiere einen Report in den `exports/` Ordner

## Schritt 5: Für Matze vorbereiten

### Was Matze braucht:
1. Den ganzen `youtube_analyzer_csv/` Ordner
2. Anleitung: "Einfach die HTML-Datei öffnen und CSVs reinziehen"

### Für neue Daten-Updates:
- Einfach neue CSVs aus YouTube Studio in den `data/` Ordner legen
- HTML-Datei öffnen
- Neue CSVs reinziehen
- Fertig!

## 🎯 Nächste Schritte

### Sofort möglich:
- [ ] Ordnerstruktur erstellen
- [ ] Dateien organisieren
- [ ] Erste Tests durchführen
- [ ] Reports exportieren

### Optional für später:
- [ ] Python-Script für automatische CSV-Downloads (YouTube API)
- [ ] GitHub Repository für Versionskontrolle
- [ ] Automatische monatliche Reports per Cron-Job
- [ ] Erweiterungen aus der Feature-Liste im README

## ⚡ Quick Commands Cheatsheet

```bash
# Projekt öffnen
cd /Users/marize/Documents/python_files/AI-agents-hub/youtube_analyzer_csv

# Neue CSV-Dateien hinzufügen
cp ~/Downloads/*.csv data/

# Exports anschauen
ls -la exports/

# Dashboard öffnen (macOS)
open youtube_analyzer.html
```

## 🐛 Troubleshooting

### Dashboard lädt nicht?
- Browser-Cache leeren (Cmd+Shift+R)
- Konsole öffnen (F12) und Fehler checken

### CSVs werden nicht erkannt?
- Format überprüfen (siehe README.md)
- Dateinamen checken (keine Sonderzeichen)

### Charts werden nicht angezeigt?
- Internet-Verbindung nötig (für CDN-Libraries)
- Alternativ: Libraries lokal hosten

---

**Bei Fragen:** Einfach melden! 🚀
