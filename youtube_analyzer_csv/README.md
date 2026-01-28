# YouTube Channel Analyzer 📊

Ein interaktives Dashboard zur Analyse von YouTube-Kanal-Performance mit automatischer Mustererkennung und strategischen Empfehlungen.

## 🎯 Features

- **Drag & Drop CSV-Upload** - Flexible Datenintegration ohne Hardcoding
- **Automatische Kategorisierung** - Erkennt Themen aus Videotiteln
- **Interaktive Visualisierungen** - Charts.js powered
- **Top-Performer-Analyse** - Identifiziert erfolgreichste Videos
- **Korrelations-Analysen** - CTR vs. Views, Länge vs. Performance
- **Export-Funktion** - Insights als TXT-Report
- **Offline-fähig** - Keine Server-Abhängigkeit

## 📁 Projekt-Struktur

```
youtube_analyzer_csv/
├── youtube_analyzer.html    # Haupt-Dashboard
├── README.md                # Diese Datei
├── data/                    # CSV-Daten (von YouTube Studio)
│   ├── Tabellendaten.csv
│   ├── Gesamtwerte.csv
│   └── Diagrammdaten.csv
├── exports/                 # Exportierte Reports
└── docs/                    # Dokumentation & Analysen
    └── Erste_Analyse_Erkenntnisse.md
```

## 🚀 Quick Start

### 1. Dashboard öffnen
Einfach `youtube_analyzer.html` in einem Browser öffnen.

### 2. Daten laden
Die drei CSV-Dateien aus dem `data/` Ordner per Drag & Drop in den Upload-Bereich ziehen:
- `Tabellendaten.csv` (Video-Performance)
- `Gesamtwerte.csv` (Tägliche Channel-Aufrufe)
- `Diagrammdaten.csv` (Zeitreihen pro Video)

### 3. Analysieren
Das Dashboard generiert automatisch:
- Gesamtstatistiken
- Top 10 Videos
- Themen-Kategorien
- Performance-Charts
- Strategische Insights

### 4. Exportieren
Klick auf "Insights als TXT exportieren" für einen detaillierten Report.

## 📊 Benötigte CSV-Struktur

### Tabellendaten.csv
```csv
Videos,Videotitel,Veröffentlichungszeitpunkt des Videos,Dauer,Aufrufe,Wiedergabezeit (Stunden),Abonnenten,Geschätzter Umsatz (EUR),Impressionen,Klickrate der Impressionen (%)
```

### Gesamtwerte.csv
```csv
Datum,Aufrufe
2025-10-29,3415
```

### Diagrammdaten.csv
```csv
Datum,Videos,Videotitel,Veröffentlichungszeitpunkt des Videos,Dauer,Aufrufe
```

## 🎨 Kategorisierungs-Logik

Das Tool kategorisiert Videos automatisch basierend auf Titel-Keywords:

- **Debatten**: "debatte", "gespräch", "diskussion", "im gespräch"
- **Analysen**: "analysiert", "analyse", "erklärt"
- **Bias/Fehlschlüsse**: "bias", "fehlschluss", "denkfalle", "geistesblitz"
- **Philosophie**: "philosophie", "ethik", "stoizismus", "aristoteles"
- **Politik**: "afd", "merz", "politik", "ice", "rechte", "links"
- **Kritik**: "problem mit", "zerstört", "blamiert", "widerlegt"
- **Religion**: "religion", "gott", "kirche", "christfluencer"
- **Sonstiges**: Alles andere

## 💡 Strategische Erkenntnisse (Beispiel-Analyse)

### Top-Performer-Muster:
1. **Debatten performen 5x besser** als der Durchschnitt
2. **Lange Videos (>30min)** haben 4x mehr Aufrufe als mittellange
3. **Hohe CTR (>5%)** korreliert mit 4x mehr Views
4. **Politische Analysen** mit zeitkritischem Bezug funktionieren stark

### Content-Strategie-Empfehlungen:
- ✅ Mehr Debatten-Content produzieren
- ✅ "Barbell Strategy": Entweder kurz (<5min) oder lang (>30min)
- ✅ Thumbnail + Titel-Optimierung für CTR >5%
- ✅ Schnelle Reaktion auf aktuelle Ereignisse

## 🔧 Technologie-Stack

- **HTML5/CSS3/JavaScript** - Frontend
- **Chart.js** - Datenvisualisierung
- **PapaParse** - CSV-Parsing
- **Keine Backend-Abhängigkeiten** - Läuft komplett im Browser

## 📈 Nutzungsempfehlung

1. **Monatliche Updates**: Neue CSVs aus YouTube Studio laden
2. **Trend-Tracking**: Performance-Entwicklung über Zeit verfolgen
3. **A/B-Testing**: Neue Content-Strategien basierend auf Daten testen
4. **Iteratives Learning**: Reports exportieren und vergleichen

## 🔮 Mögliche Erweiterungen

- [ ] Thumbnail-Analyse-Feature
- [ ] Titel-Optimierungs-Vorschläge
- [ ] Upload-Timing-Analyse
- [ ] YouTube API Integration für Live-Daten
- [ ] Automatische Report-Generierung
- [ ] Kommentar-Sentiment-Analyse
- [ ] Konkurrenz-Vergleich

## 📝 Daten-Export aus YouTube Studio

1. Gehe zu **YouTube Studio** → **Analytics**
2. Wähle den gewünschten Zeitraum
3. Klicke auf **"Erweitert"**
4. Nutze die Export-Funktion (CSV)
5. Lade die drei benötigten Dateien herunter:
   - Tabellendaten (Video-Performance)
   - Gesamtwerte (Channel-Performance)
   - Diagrammdaten (Zeitreihen)

## 🤝 Contribution

Dieses Tool ist für Matzes YouTube-Kanal entwickelt, kann aber leicht für andere Kanäle adaptiert werden.

Verbesserungsvorschläge willkommen!

## 📄 Lizenz

Private Tool - Für internen Gebrauch

---
