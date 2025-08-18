# LLM Content Evaluator - KI-gestützte Inhaltsbewertung

🎯 **Produktive FastAPI-Anwendung** mit **LLM as Judge** Methodologie zur automatisierten Bewertung von Bildungsinhalten mit KI-gestützter Analyse, deutschen Rechtsstandards und pädagogischen Qualitätskriterien.

## 🚀 Features

- ✅ **17 Bewertungsschemas** für umfassende Qualitätsprüfung
- ✅ **4 Schema-Typen**: Ordinal, Checklist, Binary Gates, Derived
- ✅ **LLM as Judge Methodologie** mit OpenAI GPT-4 Integration
- ✅ **Deutsche Rechtskonformität**: StGB, DSGVO, JuSchG, Persönlichkeitsrechte
- ✅ **Pädagogische Qualität**: Didaktik, Neutralität, Sachrichtigkeit, Aktualität
- ✅ **RESTful API** mit vollständiger OpenAPI/Swagger Dokumentation
- ✅ **Produktionsbereit** mit Error Handling und Validation
- ✅ **Flexible Ausgabe**: Detaillierte Begründungen und Kriterien-Breakdown

## 📋 Übersicht aller Schemas

### Qualitätsbewertung (13 Schemas)

| Schema ID | Typ | Beschreibung | Skala | Kriterien |
|-----------|-----|--------------|-------|-----------|
| `sachrichtigkeit_new` | Checklist | Detaillierte Sachrichtigkeit | 10 Kriterien | Faktentreue, Quellenangaben, Wissenschaftlichkeit |
| `neutralitaet_new` | Checklist | Detaillierte Neutralität | 10 Kriterien | Ausgewogenheit, Objektivität, Meinungsvielfalt |
| `aktualitaet_new` | Checklist | Detaillierte Aktualität | 10 Kriterien | Zeitgemäßheit, Relevanz, Updates |
| `didaktik_methodik_new` | Checklist | Detaillierte Didaktik | 10 Kriterien | Lernziele, Methoden, Verständlichkeit |
| `sprachliche_angemessenheit_new` | Checklist | Detaillierte Sprache | 10 Kriterien | Verständlichkeit, Stil, Zielgruppe, Grammatik |
| `medial_passend_new` | Checklist | Detaillierte Mediale Passung | 10 Kriterien | Technische Qualität, Interaktivität, Zugänglichkeit |
| `sachrichtigkeit_old` | Ordinal | Sachrichtigkeit (0-5) | 6 Stufen | Kompakte Bewertung der Faktentreue |
| `neutralitaet_old` | Ordinal | Neutralität (0-5) | 6 Stufen | Kompakte Bewertung der Ausgewogenheit |
| `aktualitaet_old` | Ordinal | Aktualität (0-5) | 6 Stufen | Kompakte Bewertung der Zeitgemäßheit |
| `sprachliche_angemessenheit_old` | Ordinal | Sprache (0-5) | 6 Stufen | Verständlichkeit, Stil, Zielgruppe |
| `didaktik_methodik_old` | Ordinal | Didaktik (0-5) | 6 Stufen | Kompakte pädagogische Bewertung |
| `medial_passend_old` | Ordinal | Mediale Passung (0-5) | 6 Stufen | Medieneignung, Darstellung |
| `overall_quality` | Derived | Gesamtqualität | 0.0-5.0 | Gewichtete Kombination aller Dimensionen |

### Compliance & Rechtssicherheit (4 Schemas)

| Schema ID | Typ | Beschreibung | Rechtsbasis | Prüfbereiche |
|-----------|-----|--------------|-------------|--------------|
| `jugendschutz_gate` | Binary Gate | Jugendschutz | JuSchG, JMStV | Altersgerechte Inhalte, Entwicklungsschutz |
| `strafrecht_gate` | Binary Gate | Strafrecht | StGB, NetzDG | Volksverhetzung, Gewaltverherrlichung |
| `persoenlichkeitsrechte_gate` | Binary Gate | Persönlichkeitsrechte | DSGVO, KUG | Bildrechte, Datenschutz, Privatsphäre |
| `rechtliche_compliance` | Derived | Rechtliche Gesamtbewertung | Alle Gates | UND-Verknüpfung aller Compliance-Gates |

## 🛠️ Installation & Setup

### Voraussetzungen
- Python 3.8+
- OpenAI API Key (für KI-basierte Bewertung)
- FastAPI, Uvicorn, Pydantic (automatisch installiert)

### Schnellstart

```bash
# Repository klonen
git clone <repository-url>
cd api-scoring-quality/api-eval-25

# Umgebung einrichten
cp .env.example .env
# .env mit OpenAI API Key bearbeiten:
# OPENAI_API_KEY=your_api_key_here

# Dependencies installieren
pip install fastapi uvicorn openai pydantic loguru pyyaml

# Server starten
python main.py
```

🌐 **Server läuft auf: http://localhost:8001**  
📚 **API Dokumentation: http://localhost:8001/docs**  
🔍 **Alternative Docs: http://localhost:8001/redoc**

## 🔗 API Endpoints

### 🏥 Health Check
```http
GET /health
```
**Status:** ✅ Funktionsfähig  
**Zweck:** API-Status und geladene Schemas prüfen

### 📋 Schema-Übersicht  
```http
GET /schemes
```
**Status:** ✅ Funktionsfähig  
**Zweck:** Alle 15 verfügbaren Bewertungsschemas auflisten

### 🎯 Text-Bewertung
```http
POST /evaluate
```
**Status:** ✅ Funktionsfähig  
**Zweck:** KI-gestützte Bewertung von Bildungsinhalten

**Beispiel-Request:**
```json
{
    "text": "Die deutsche Wiedervereinigung war ein komplexer politischer Prozess...",
    "schemes": ["neutralitaet_new", "sachrichtigkeit_old", "rechtliche_compliance"],
    "include_reasoning": true
}
```

**Beispiel-Response:**
```json
{
    "results": [
        {
            "scheme_id": "neutralitaet_new",
            "value": 4.2,
            "label": "Weitgehend neutral",
            "confidence": 0.88,
            "reasoning": "Der Text stellt verschiedene Perspektiven ausgewogen dar...",
            "criteria": {
                "ausgewogenheit": {"value": 4, "reasoning": "Mehrere Standpunkte berücksichtigt"},
                "objektivitaet": {"value": 4, "reasoning": "Sachliche Darstellung ohne Wertungen"}
            }
        }
    ],
    "gates_passed": true,
    "metadata": {
        "processing_time_ms": 1250,
        "model_used": "gpt-4"
    }
}
```

## 📖 YAML Schema-Parameter - Detaillierte Anleitung

### Grundstruktur aller Schemas

Jedes YAML-Schema folgt einer einheitlichen Grundstruktur:

```yaml
# Eindeutige Identifikation
id: schema_identifier
name: "Benutzerfreundlicher Anzeigename"
description: "Detaillierte Beschreibung des Bewertungszwecks"
dimension: dimension_name  # Technischer Dimensionsname
type: ordinal|checklist|binary_gate|derived
version: "1.0"

# Ausgabeformat definieren
output_range:
  min: 0      # Minimaler Wert
  max: 5      # Maximaler Wert  
  type: int   # int, float oder boolean
  values: [0, 1, 2, 3, 4, 5]  # Optional: Erlaubte Werte
```

**Pflichtfelder:**
- `id`: Eindeutige Schema-ID (keine Leerzeichen, Kleinbuchstaben)
- `name`: Anzeigename für Benutzeroberfläche
- `type`: Schema-Typ bestimmt Bewertungslogik
- `output_range`: Definiert mögliche Ausgabewerte

### Schema-Typen im Detail

#### 1. Ordinal Schema - Anker-basierte Bewertung (0-5 Skala)

Ordinal-Schemas verwenden vordefinierte Anker für konsistente Bewertungen:

```yaml
id: neutralitaet_old
name: "Neutralität (Ordinal)"
description: "Bewertung der politischen und weltanschaulichen Neutralität"
dimension: neutrality
type: ordinal
version: "1.0"

output_range:
  min: 0
  max: 5
  type: int

# Bewertungsstrategie
strategy: first_match  # oder best_fit

# Anker in absteigender Reihenfolge (5 → 0)
anchors:
  - value: 5
    label: "Vollständig neutral"
    criteria: |
      - Alle Standpunkte werden fair dargestellt
      - Keine erkennbare politische Tendenz
      - Ausgewogene Quellenauswahl
      - Objektive Sprache durchgehend
      
  - value: 4
    label: "Weitgehend neutral"
    criteria: |
      - Überwiegend ausgewogene Darstellung
      - Minimale Tendenz erkennbar
      - Verschiedene Perspektiven berücksichtigt
      
  - value: 3
    label: "Teilweise neutral"
    criteria: |
      - Grundsätzlich um Neutralität bemüht
      - Deutliche Tendenz in eine Richtung
      - Nicht alle Standpunkte gleichwertig dargestellt
      
  - value: 2
    label: "Wenig neutral"
    criteria: |
      - Starke Tendenz erkennbar
      - Einseitige Quellenauswahl
      - Gegenpositionen nur oberflächlich behandelt
      
  - value: 1
    label: "Einseitig"
    criteria: |
      - Deutlich parteiische Darstellung
      - Wichtige Gegenpositionen fehlen
      - Wertende Sprache dominiert
      
  - value: 0
    label: "Stark einseitig"
    criteria: |
      - Propagandistische Darstellung
      - Keine Berücksichtigung anderer Standpunkte
      - Manipulative oder hetzerische Sprache

# Fallback bei unklaren Fällen
default:
  value: 0
  label: "Unbewertet"
  reasoning: "Keine ausreichenden Informationen für Bewertung"
  confidence: 0.0

# Zusätzliche Metadaten
labels:
  "5": "Exzellent neutral"
  "4": "Gut neutral"
  "3": "Akzeptabel"
  "2": "Verbesserungsbedürftig"
  "1": "Problematisch"
  "0": "Inakzeptabel"
```

**Strategien:**
- `first_match`: Erste passende Bewertung wird verwendet
- `best_fit`: Beste Übereinstimmung wird gesucht

**Vollständiges Beispiel:** `neutralitaet_old.yaml`

#### 2. Checklist Schema - Kriterien-basierte Bewertung

Checklist-Schemas bewerten anhand gewichteter Einzelkriterien mit **kompakter Strukturbeschreibung**:

```yaml
id: sachrichtigkeit_new
name: "Sachrichtigkeit (Detailliert)"
description: "Umfassende Bewertung der faktischen Korrektheit"
dimension: factuality
type: checklist_additive
version: "1.0"

output_range:
  min: 0.0
  max: 5.0
  type: float

# Einzelkriterien mit strukturierten Werten (NEUE KOMPAKTE STRUKTUR)
items:
  - id: faktentreue
    prompt: "Sind alle Fakten und Aussagen korrekt und verifizierbar?"
    weight: 2.5
    values:
      1: {score: 0.25, description: "Viele falsche oder ungeprüfte Aussagen"}
      2: {score: 0.5, description: "Einige faktische Fehler oder Ungenauigkeiten"}
      3: {score: 0.75, description: "Überwiegend korrekte Fakten, wenige Fehler"}
      4: {score: 1.0, description: "Alle Fakten korrekt und gut verifizierbar"}
      na: null
      
  - id: quellenangaben
    prompt: "Sind alle Behauptungen mit seriösen Quellen belegt?"
    weight: 2.0
    values:
      1: {score: 0.25, description: "Keine oder unzuverlässige Quellenangaben"}
      2: {score: 0.5, description: "Wenige oder teilweise fragwürdige Quellen"}
      3: {score: 0.75, description: "Gute Quellenangaben, meist seriös"}
      4: {score: 1.0, description: "Vollständige, seriöse und aktuelle Quellenangaben"}
      na: null

# Aggregation mit gewichtetem Mittelwert
aggregator:
  strategy: weighted_mean
  params:
    missing: ignore
    scale_factor: 5.0  # Skaliert von 0-1 auf 0-5

# Labels für Ausgabe
labels:
  "0.0": "Unzureichend"
  "1.0": "Mangelhaft"
  "2.0": "Ausreichend"
  "3.0": "Befriedigend"
  "4.0": "Gut"
  "5.0": "Sehr gut"
```

**Neue Kompakte Struktur:**
- **Strukturierte Werte:** `{score: 0.25, description: "..."}` statt einfacher Kommentare
- **Bessere LLM-Prompts:** Beschreibungen werden direkt in Bewertungsprompts eingebunden
- **Einheitliche Skalierung:** Alle Kriterien verwenden 1-4 Level mit 0.25-1.0 Scores

**Vollständiges Beispiel:** `sachrichtigkeit_new.yaml`, `neutralitaet_new.yaml`, `sprachliche_angemessenheit_new.yaml`, `medial_passend_new.yaml`

#### 3. Binary Gate - Pass/Fail Bewertung

Binary Gates sind K.O.-Kriterien für Compliance-Prüfungen:

```yaml
id: strafrecht_gate
name: "Strafrechtliche Unbedenklichkeit"
description: "Prüfung auf Verstöße gegen deutsches Strafrecht"
dimension: legal_compliance
type: binary_gate
version: "1.0"

output_range:
  values: [true, false]
  type: boolean

# Prüfkriterien (wird in criteria-Feld dokumentiert)
criteria: |
  Automatische Prüfung auf strafrechtlich relevante Inhalte:
  - Volksverhetzung (§ 130 StGB)
  - Gewaltverherrlichung (§ 131 StGB)
  - Beleidigung und Verleumdung (§ 185-187 StGB)
  - Bedrohung (§ 241 StGB)
  - Verfassungswidrige Symbole (§ 86a StGB)

# Gate-Regeln (Reihenfolge wichtig!)
gate_rules:
  - condition: "volksverhetzung"
    action: reject
    reason: "Inhalt enthält volksverhetzende Äußerungen (§ 130 StGB)"
    severity: critical
    legal_reference: "§ 130 StGB"
    confidence: 0.9
    
  - condition: "gewaltverherrlichung"
    action: reject
    reason: "Inhalt verherrlicht Gewalt (§ 131 StGB)"
    severity: critical
    legal_reference: "§ 131 StGB"
    confidence: 0.85
    
  - condition: "beleidigung"
    action: reject
    reason: "Inhalt enthält Beleidigungen (§ 185-187 StGB)"
    severity: medium
    legal_reference: "§ 185-187 StGB"
    confidence: 0.7
    
  - condition: "bedrohung"
    action: reject
    reason: "Inhalt enthält Bedrohungen (§ 241 StGB)"
    severity: high
    legal_reference: "§ 241 StGB"
    confidence: 0.8

# Standard-Aktion wenn keine Regel greift
default_action: pass

# Automatische Keyword-Erkennung
detection_patterns:
  volksverhetzung:
    - "holocaustleugnung"
    - "rassenhass"
    - "judenhass"
    - "ausländer raus"
    - "vernichtung"
    
  gewaltverherrlichung:
    - "folter verherrlichen"
    - "gewalt glorifizieren"
    - "hinrichtung feiern"
    - "sadismus"
    
  beleidigung:
    - "idiot"
    - "schwachkopf"
    - "versager"
    # (Kontext-abhängig)
    
  bedrohung:
    - "ich bringe dich um"
    - "du bist tot"
    - "warte nur ab"

# Severity-Level Definitionen
severity_levels:
  critical: "Schwere Straftaten mit Gefängnisstrafe"
  high: "Straftaten mit erheblicher gesellschaftlicher Relevanz"
  medium: "Rechtsverstöße mit zivilrechtlichen Konsequenzen"
  low: "Geringfügige Rechtsverstöße"

# Compliance-Referenzen
compliance_references:
  - "Strafgesetzbuch (StGB)"
  - "Netzwerkdurchsetzungsgesetz (NetzDG)"
  - "Digital Services Act (DSA)"
```

**Gate-Logik:**
1. Regeln werden in Reihenfolge geprüft
2. Erste zutreffende Regel bestimmt Ergebnis
3. Bei keiner Regel: `default_action`

**Severity-Levels:**
- `critical`: Sofortige Sperrung erforderlich
- `high`: Manuelle Prüfung erforderlich
- `medium`: Warnung an Nutzer
- `low`: Hinweis ausreichend

**Vollständiges Beispiel:** `strafrecht_gate.yaml`

#### 4. Derived Schema - Kombination anderer Schemas

Derived Schemas kombinieren Ergebnisse anderer Schemas:

```yaml
id: overall_quality
name: "Gesamtqualität"
description: "Gewichtete Kombination aller Qualitätsdimensionen"
dimension: overall_quality
type: derived
version: "2.0"

output_range:
  min: 0.0
  max: 5.0
  type: float

# Abhängigkeiten (müssen vorher ausgewertet werden)
dependencies:
  - neutralitaet_old
  - aktualitaet_old
  - sachrichtigkeit_old
  - sprachliche_angemessenheit_old
  - didaktik_methodik_old
  - medial_passend_old

# Kombinationsregeln
rules:
  - conditions:
      - dimension: neutrality
        operator: ">="
        value: 0
      - dimension: factuality
        operator: ">="
        value: 0
    value: "weighted_average"
    label: "Gewichtete Gesamtbewertung"
    reasoning: "Berechnung basierend auf gewichteten Einzeldimensionen"
    confidence: 0.9
    
    # Gewichtung der Dimensionen
    weights:
      neutrality: 2.0              # Neutralität (wichtig)
      timeliness: 1.5              # Aktualität
      factuality: 2.5              # Sachrichtigkeit (sehr wichtig)
      language_appropriateness: 1.5 # Sprachliche Angemessenheit
      pedagogy: 2.0                # Didaktik/Methodik (wichtig)
      media_appropriateness: 1.0    # Mediale Passung
      
  # Spezialregel für niedrige Sachrichtigkeit
  - conditions:
      - dimension: factuality
        operator: "<"
        value: 2.0
    value: 1.0
    label: "Unzureichende Sachrichtigkeit"
    reasoning: "Niedrige Sachrichtigkeit führt zu schlechter Gesamtbewertung"
    confidence: 0.95

# Fallback
default:
  value: 0.0
  label: "Unbewertet"
  reasoning: "Keine ausreichenden Daten für Gesamtbewertung"
  confidence: 0.0

# Ausgabe-Labels
labels:
  "4.5-5.0": "Exzellente Qualität"
  "3.5-4.4": "Gute Qualität"
  "2.5-3.4": "Akzeptable Qualität"
  "1.5-2.4": "Verbesserungsbedürftig"
  "0.0-1.4": "Unzureichende Qualität"

# Mathematische Operationen
calculation_method: weighted_average
normalization: true
```

**Kombinationslogik:**
- `weighted_average`: Gewichteter Durchschnitt
- `min`: Minimum aller Werte
- `max`: Maximum aller Werte
- `and_gate`: Alle müssen TRUE sein
- `or_gate`: Mindestens einer TRUE

**Operatoren für Bedingungen:**
- `==`: Gleich
- `!=`: Ungleich
- `>`: Größer
- `>=`: Größer oder gleich
- `<`: Kleiner
- `<=`: Kleiner oder gleich
- `in`: Wert in Liste
- `not_in`: Wert nicht in Liste

**Vollständiges Beispiel:** `overall_quality.yaml`

### Erweiterte YAML-Features

#### Conditional Logic (Bedingte Logik)

```yaml
rules:
  # Mehrere Bedingungen (UND-verknüpft)
  - conditions:
      - dimension: neutrality
        operator: ">="
        value: 3
      - dimension: factuality
        operator: ">="
        value: 4
    value: 4.5
    label: "Hohe Qualität"
    
  # ODER-Verknüpfung mit condition_logic
  - condition_logic: "OR"
    conditions:
      - dimension: neutrality
        operator: "=="
        value: 5
      - dimension: factuality
        operator: "=="
        value: 5
    value: 4.0
    label: "Exzellenz in einer Dimension"
```

#### Gate Logic für Binary Schemas

```yaml
# UND-Verknüpfung (alle Gates müssen TRUE sein)
gate_logic: "AND"

# ODER-Verknüpfung (mindestens ein Gate TRUE)
gate_logic: "OR"

# Beispiel: Rechtliche Unbedenklichkeit
dependencies:
  - content_gate
  - jugendschutz_gate
  - strafrecht_gate
  - persoenlichkeitsrechte_gate

rules:
  - conditions:
      - dimension: content_safety
        operator: "=="
        value: true
      - dimension: youth_protection
        operator: "=="
        value: true
      - dimension: legal_compliance
        operator: "=="
        value: true
      - dimension: personality_rights
        operator: "=="
        value: true
    value: true
    label: "Rechtlich unbedenklich"
```

#### Metadata und Dokumentation

```yaml
# Zusätzliche Metadaten
metadata:
  author: "Qualitätsteam"
  created: "2025-01-17"
  last_modified: "2025-01-17"
  review_cycle: "quarterly"
  
# Dokumentation für Entwickler
documentation:
  purpose: "Bewertung der Neutralität in Bildungsinhalten"
  methodology: "Anker-basierte Bewertung mit KI-Unterstützung"
  validation: "Getestet mit 100+ Beispieltexten"
  
# Konfiguration für KI-Bewertung
ai_config:
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 500
  prompt_template: "Bewerte die Neutralität des folgenden Textes..."
```

### Validierung und Testing

#### Schema-Validierung

```bash
# YAML-Syntax prüfen
python -c "import yaml; yaml.safe_load(open('schemes/schema.yaml'))"

# Schema-Struktur validieren
python -m core.evaluation --validate-schema schemes/schema.yaml

# Alle Schemas validieren
python -m core.evaluation --validate-all
```

#### Test-Cases definieren

```yaml
# Optional: Test-Cases im Schema
test_cases:
  - input: "Neutral formulierter Text über Politik..."
    expected_value: 4
    expected_label: "Weitgehend neutral"
    
  - input: "Stark einseitiger Text..."
    expected_value: 1
    expected_label: "Einseitig"
```

### Best Practices für YAML-Schemas

#### 1. Naming Conventions
```yaml
# Schema-IDs: lowercase, underscore
id: sachrichtigkeit_new

# Dimensionen: englisch, lowercase
dimension: factuality

# Kriterien-IDs: deutsch, underscore
criteria:
  - id: faktentreue
  - id: quellenangaben
```

#### 2. Gewichtung
```yaml
# Wichtigste Kriterien: 2.0-2.5
# Normale Kriterien: 1.0-1.5
# Ergänzende Kriterien: 0.5-1.0
weights:
  factuality: 2.5      # Sehr wichtig
  neutrality: 2.0      # Wichtig
  timeliness: 1.5      # Normal
  media_fit: 1.0       # Ergänzend
```

#### 3. Confidence-Werte
```yaml
# Hohe Sicherheit: 0.9-1.0
# Mittlere Sicherheit: 0.7-0.8
# Niedrige Sicherheit: 0.5-0.6
confidence: 0.9
```

#### 4. Dokumentation
```yaml
# Immer aussagekräftige Beschreibungen
description: "Bewertung der faktischen Korrektheit und Quellenqualität"

# Konkrete Beispiele für Kriterien
examples:
  - "Zahlen sind durch seriöse Quellen belegt"
  - "Historische Fakten sind korrekt dargestellt"
```

## 🔄 Derived Schemas - Kombinationslogik

### UND-Verknüpfung (AND Logic)
```yaml
gate_logic: "AND"
```
Alle Bedingungen müssen erfüllt sein.

**Beispiel:** `rechtliche_unbedenklichkeit_derived.yaml`
- Alle 4 Gates müssen `true` sein
- Ein `false` führt zur Gesamtablehnung

### ODER-Verknüpfung (OR Logic)
```yaml
gate_logic: "OR"
```
Mindestens eine Bedingung muss erfüllt sein.

### Gewichtete Kombination
```yaml
rules:
  - conditions: [...]
    value: "weighted_average"
    weights:
      neutrality: 2.0
      factuality: 2.5
      timeliness: 1.5
```

## 🧪 Live-Tests & Swagger UI

**Interaktive API-Tests:** http://localhost:8001/docs

- ✅ **"Try it out" Funktionalität** für alle Endpoints
- ✅ **Vollständige Dokumentation** mit Beispielen
- ✅ **Schema-Validierung** und Error Handling
- ✅ **Echtzeit-Tests** direkt im Browser

## 📊 Praktische Beispiele

### Beispiel 1: Vollständige Qualitätsbewertung

**Anwendungsfall:** Bewertung von Bildungsinhalten vor Veröffentlichung

```python
import httpx

# Request
response = httpx.post("http://localhost:8001/evaluate", json={
    "text": "Die deutsche Wiedervereinigung war ein komplexer politischer Prozess, der 1989 mit dem Fall der Berliner Mauer begann. Verschiedene politische Akteure trugen zu diesem historischen Ereignis bei, darunter Bürgerbewegungen in der DDR, die Politik der Sowjetunion unter Gorbatschow und die diplomatischen Bemühungen der Bundesregierung.",
    "schemes": [
        "overall_quality",
        "rechtliche_compliance"
    ],
    "include_reasoning": true
})

# Response
result = response.json()
print(f"Gesamtqualität: {result['results'][0]['value']}/5.0")
print(f"Rechtssicherheit: {'✓' if result['results'][1]['value'] == 1 else '✗'}")
```

**Erwartete Ausgabe:**
```json
{
    "results": [
        {
            "scheme_id": "overall_quality",
            "value": 4.2,
            "label": "Gute Qualität",
            "confidence": 0.88,
            "reasoning": "Der Text zeigt hohe Sachrichtigkeit und Neutralität...",
            "criteria": {
                "neutralitaet_old": {"value": 4, "label": "Weitgehend neutral"},
                "sachrichtigkeit_old": {"value": 5, "label": "Vollständig sachrichtig"},
                "aktualitaet_old": {"value": 4, "label": "Gut aktuell"}
            }
        },
        {
            "scheme_id": "rechtliche_compliance",
            "value": 1,
            "label": "PASS",
            "confidence": 0.95,
            "reasoning": "Alle rechtlichen Prüfungen bestanden"
        }
    ]
}
```

### Beispiel 2: Detaillierte Qualitätsprüfung

**Anwendungsfall:** Wissenschaftliche Artikel mit Fokus auf Faktentreue

```python
# Request für detaillierte Bewertung
response = httpx.post("http://localhost:8001/evaluate", json={
    "text": "Laut einer Studie der Universität München aus dem Jahr 2023 zeigen 78% der befragten Schüler verbesserte Lernleistungen bei Verwendung digitaler Medien. Die Studie basiert auf einer Stichprobe von 1.200 Schülern aus 15 bayerischen Gymnasien.",
    "schemes": [
        "sachrichtigkeit_new",
        "neutralitaet_new",
        "didaktik_methodik_new"
    ],
    "include_reasoning": true
})

# Detaillierte Kriterien-Analyse
for result in response.json()['results']:
    print(f"\n{result['scheme_id']}: {result['value']}/5.0")
    for criterion, details in result['criteria'].items():
        print(f"  - {criterion}: {details['value']} - {details['reasoning'][:50]}...")
```

### Beispiel 3: Compliance-Schnellprüfung

**Anwendungsfall:** User-Generated Content vor Freischaltung

```python
# Rechtliche Schnellprüfung
response = httpx.post("http://localhost:8001/evaluate", json={
    "text": "Das ist ein normaler Kommentar zu einem Bildungsthema ohne problematische Inhalte.",
    "schemes": [
        "jugendschutz_gate",
        "strafrecht_gate",
        "persoenlichkeitsrechte_gate"
    ],
    "include_reasoning": false  # Schnelle Prüfung ohne Details
})

# Einfache Pass/Fail Auswertung
all_passed = all(r['value'] == 1 for r in response.json()['results'])
print(f"Content freigegeben: {'✓' if all_passed else '✗'}")

# Detaillierte Fehleranalyse bei Problemen
if not all_passed:
    failed_gates = [r['scheme_id'] for r in response.json()['results'] if r['value'] == 0]
    print(f"Problematische Bereiche: {', '.join(failed_gates)}")
```

### Beispiel 4: Batch-Verarbeitung

**Anwendungsfall:** Bewertung mehrerer Inhalte

```python
import asyncio
import httpx

async def evaluate_content(client, text, schemes):
    """Einzelne Inhaltsbewertung"""
    response = await client.post("/evaluate", json={
        "text": text,
        "schemes": schemes,
        "include_reasoning": false
    })
    return response.json()

async def batch_evaluate():
    """Batch-Bewertung mehrerer Inhalte"""
    contents = [
        "Lerninhalt 1: Geschichte der Demokratie...",
        "Lerninhalt 2: Mathematische Grundlagen...",
        "Lerninhalt 3: Naturwissenschaftliche Experimente..."
    ]
    
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        tasks = [
            evaluate_content(client, content, ["overall_quality", "rechtliche_compliance"])
            for content in contents
        ]
        results = await asyncio.gather(*tasks)
    
    # Ergebnisse auswerten
    for i, result in enumerate(results):
        quality = result['results'][0]['value']
        compliance = result['results'][1]['value']
        print(f"Inhalt {i+1}: Qualität {quality}/5.0, Compliance {'✓' if compliance else '✗'}")

# Ausführung
asyncio.run(batch_evaluate())
```

### Beispiel 5: Error Handling

**Anwendungsfall:** Robuste Fehlerbehandlung

```python
import httpx
from typing import Dict, Any

def safe_evaluate(text: str, schemes: list) -> Dict[str, Any]:
    """Sichere Bewertung mit Fehlerbehandlung"""
    try:
        response = httpx.post(
            "http://localhost:8001/evaluate",
            json={
                "text": text,
                "schemes": schemes,
                "include_reasoning": true
            },
            timeout=30.0  # 30 Sekunden Timeout
        )
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Timeout: Bewertung dauerte zu lange",
            "retry_recommended": True
        }
    
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "retry_recommended": e.response.status_code >= 500
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unerwarteter Fehler: {str(e)}",
            "retry_recommended": False
        }

# Verwendung
result = safe_evaluate(
    "Beispieltext für Bewertung",
    ["neutralitaet_new", "sachrichtigkeit_new"]
)

if result["success"]:
    print("Bewertung erfolgreich:", result["data"])
else:
    print("Fehler:", result["error"])
    if result["retry_recommended"]:
        print("Wiederholung empfohlen")
```

## ⚖️ Deutsche Rechtskonformität

### Abgedeckte Gesetze
- ✅ **Strafgesetzbuch (StGB)**: Volksverhetzung, Gewaltverherrlichung, Beleidigung
- ✅ **Jugendschutzgesetz (JuSchG)**: Altersgerechte Inhalte, Entwicklungsschutz
- ✅ **DSGVO**: Datenschutz, Persönlichkeitsrechte
- ✅ **Kunsturhebergesetz (KUG)**: Bildrechte, Recht am eigenen Bild
- ✅ **NetzDG**: Strafbare Inhalte in sozialen Netzwerken
- ✅ **Digital Services Act (DSA)**: EU-Digitalrecht

### Automatische Risikobewertung
- 🔴 **Critical**: Schwere Straftaten → Sofortige Sperrung
- 🟠 **High**: Erhebliche Rechtsverstöße → Manuelle Prüfung
- 🟡 **Medium**: Zivilrechtliche Folgen → Überarbeitung empfohlen
- 🟢 **Low**: Geringfügige Verstöße → Hinweis ausreichend

## 🎯 Best Practices

### Schema-Auswahl für verschiedene Anwendungsfälle

#### 📚 **Bildungsinhalte (Empfohlen)**
```json
{"schemes": ["overall_quality", "rechtliche_compliance"]}
```

#### 👥 **User-Generated Content**
```json
{"schemes": ["jugendschutz_gate", "strafrecht_gate", "persoenlichkeitsrechte_gate"]}
```

#### 🔬 **Wissenschaftliche Texte**
```json
{"schemes": ["sachrichtigkeit_new", "neutralitaet_new"]}
```

#### ⚡ **Schnelle Qualitätsprüfung**
```json
{"schemes": ["neutralitaet_old", "sachrichtigkeit_old"], "include_reasoning": false}
```

### Performance & Zuverlässigkeit
- ✅ **Automatische Fehlerbehandlung** für ungültige Schema-IDs
- ✅ **Timeout-Protection** für KI-Bewertungen
- ✅ **Dependency-Validation** für derived Schemas
- ✅ **Rate Limiting** berücksichtigen (OpenAI API)
- ✅ **Retry-Logic** für temporäre Fehler

## 🔧 Entwicklung & Erweiterung

### API Status & Monitoring
```bash
# API Health Check
curl http://localhost:8001/health

# Alle verfügbaren Schemas auflisten
curl http://localhost:8001/schemes

# Test-Bewertung durchführen
curl -X POST http://localhost:8001/evaluate \
  -H "Content-Type: application/json" \
  -d '{"text":"Testinhalt", "schemes":["neutralitaet_old"]}'
```

### Neues Schema erstellen
1. YAML-Datei in `schemes/` erstellen
2. Schema-Typ und Parameter definieren
3. Kriterien und Regeln spezifizieren
4. API neu starten für automatisches Laden

### Debugging & Logs
- ✅ **Structured Logging** mit Loguru
- ✅ **Request/Response Tracing**
- ✅ **Error Details** in API Responses
- ✅ **Schema Loading Status** beim Startup

## 📈 Produktionsstatus

### ✅ Funktionsfähige Features
- 🟢 **API Server**: Läuft stabil auf Port 8001
- 🟢 **Alle Endpoints**: Health, Schemes, Evaluate funktionsfähig
- 🟢 **15 Bewertungsschemas**: Vollständig geladen und getestet
- 🟢 **KI-Integration**: OpenAI GPT-4 Bewertungen
- 🟢 **Swagger UI**: Vollständige interaktive Dokumentation
- 🟢 **Error Handling**: Robuste Fehlerbehandlung
- 🟢 **Schema Validation**: Pydantic-basierte Validierung

### 🔄 Letzte Updates (2025-01-18)
- ✅ Fixed Swagger UI "Try it out" Funktionalität
- ✅ Erweiterte API-Dokumentation mit Beispielen
- ✅ Verbesserte Schema-Validierung für Binary Gates
- ✅ Dependency Injection Kompatibilität

## 📝 Lizenz & Rechtliches

Dieses System implementiert deutsche Rechtsstandards und ist für den Einsatz in Deutschland optimiert. Bei internationaler Nutzung sind lokale Gesetze zu beachten.

**⚠️ Haftungsausschluss**: Die automatische Rechtsprüfung ersetzt keine juristische Beratung. Bei kritischen Inhalten sollte immer eine manuelle Prüfung erfolgen.

---

**🚀 Ready for Production** | **🤖 LLM as Judge** | **📚 Full Documentation** | **🔧 Easy to Extend**
