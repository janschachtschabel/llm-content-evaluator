# Master-Gates Übersicht

## Zweck

Diese Dokumentation beschreibt die vier neuen Master-Gates, die jeweils die a/b Kataloge der vier Hauptrechtsbereiche kombinieren.

---

## Struktur

```
MASTER-GATES (Ebene 1)
├── criminal_law_gate.yaml (Strafrecht)
├── protection_of_minors_gate.yaml (Jugendschutz)
├── personal_law_gate.yaml (Persönlichkeitsrechte)
└── data_privacy_gate.yaml (Datenschutz)

SUB-GATES (Ebene 2)
├── criminal_law_1a_gate.yaml (Per se illegal)
├── criminal_law_1b_gate.yaml (Kontextabhängig)
├── protection_of_minors_2a_gate.yaml (Jugendgefährdend)
├── protection_of_minors_2b_gate.yaml (Entwicklungsbeeinträchtigend)
├── personal_law_3a_gate.yaml (Individuelle Verletzungen)
├── personal_law_3b_gate.yaml (Strukturelle Vorsorge)
├── data_privacy_4a_gate.yaml (Profiling & Einwilligung)
└── data_privacy_4b_gate.yaml (Transparenz & KI)

PART-SCHEMAS (Ebene 3)
└── [59 Teilschemas mit insgesamt 507 Indikatoren]
```

---

## 1. Strafrecht Master-Gate

**Datei:** `criminal_law_gate.yaml`  
**ID:** `criminal_law_gate`  
**Dimension:** `criminal_law_compliance`

### Output-Werte
- **0** = ILLEGAL (Per se Strafrechtsverstoß / Hard Illegal)
- **1** = KONTEXTABHÄNGIG (Prüfung erforderlich)
- **2** = LEGAL (Kein Strafrechtsverstoß)

### Komponenten
| Katalog | Indikatoren | Beschreibung |
|---------|-------------|--------------|
| **1A - Per se illegal** | 49 | Hard Illegal (CSAM, Terrorismus, Volksverhetzung, etc.) |
| **1B - Kontextabhängig** | 43 | Kontextabhängige Straftatbestände (Beleidigung, Urheberrecht, etc.) |
| **GESAMT** | **92** | Alle strafrechtlichen Prüfungen |

### Logik
```
1A FAIL → ILLEGAL (0)
1A PASS, 1B FAIL → KONTEXTABHÄNGIG (1)
1A PASS, 1B PASS → LEGAL (2)
```

### Aktionen
- **ILLEGAL:** Hard Delete + Meldung an Strafverfolgungsbehörden
- **KONTEXTABHÄNGIG:** Einzelfallprüfung / Moderation / Kontext-Review
- **LEGAL:** Keine Aktion

---

## 2. Jugendschutz Master-Gate

**Datei:** `protection_of_minors_gate.yaml`  
**ID:** `protection_of_minors_gate`  
**Dimension:** `protection_of_minors_compliance`

### Output-Werte
- **0** = FSK 0 (Keine Altersbeschränkung)
- **6** = FSK 6 (Ab 6 Jahren)
- **12** = FSK 12 (Ab 12 Jahren)
- **16** = FSK 16 (Ab 16 Jahren)
- **18** = Keine Jugendfreigabe (Nur Erwachsene)
- **100** = JUGENDGEFÄHRDEND (AVS erforderlich)

### Komponenten
| Katalog | Indikatoren | Beschreibung |
|---------|-------------|--------------|
| **2A - Jugendgefährdend** | 37 | AVS-pflichtige Inhalte (Pornografie, Kriegsverherrlichung, etc.) |
| **2B - Entwicklungsbeeinträchtigend** | 241 | Altersgestufte Bewertung (U6, 6-12, 12-16, 16-18) |
| **GESAMT** | **278** | Alle Jugendschutzprüfungen |

### Logik (Hierarchisch)
```
Stufe 1: 2A prüfen
  2A FAIL → JUGENDGEFÄHRDEND (100)
  2A PASS → Weiter zu Stufe 2

Stufe 2: 2B prüfen (Altersfreigabe)
  2B = 0 → FSK 0 (0)
  2B = 6 → FSK 6 (6)
  2B = 12 → FSK 12 (12)
  2B = 16 → FSK 16 (16)
  2B = 18 → Keine Jugendfreigabe (18)
```

### Aktionen
- **JUGENDGEFÄHRDEND (100):** AVS + Zeitsteuerung 23:00-06:00
- **FSK 18 (18):** Alterskennzeichnung + PIN + Zeitsteuerung 22:00-06:00
- **FSK 16 (16):** Alterskennzeichnung + Zeitsteuerung 22:00-06:00
- **FSK 12 (12):** Alterskennzeichnung + Optional Zeitsteuerung 20:00-06:00
- **FSK 6 (6):** Alterskennzeichnung + Inhaltstrennung
- **FSK 0 (0):** Keine Beschränkungen

---

## 3. Persönlichkeitsrechte Master-Gate

**Datei:** `personal_law_gate.yaml`  
**ID:** `personal_law_gate`  
**Dimension:** `personal_law_compliance`

### Output-Werte
- **0** = KRITISCH (Content-Verstoß UND strukturell unzureichend)
- **1** = STRUKTURELL UNZUREICHEND (Safety Features erforderlich)
- **2** = CONTENT-VERSTOSS (Takedown erforderlich)
- **3** = COMPLIANT (Keine Verstöße)

### Komponenten
| Katalog | Indikatoren | Beschreibung |
|---------|-------------|--------------|
| **3A - Individuelle Verletzungen** | 44 | Konkrete Persönlichkeitsrechtsverletzungen (Doxing, APR, Bildrechte) |
| **3B - Strukturelle Vorsorge** | 44 | Safety Features (Meldesystem, Elternkontrollen, Safety by Default) |
| **GESAMT** | **88** | Alle Persönlichkeitsrechtsprüfungen |

### Logik (2x2 Matrix)
```
                3B PASS     3B FAIL
3A PASS    │ COMPLIANT │ STRUKTURELL │
           │    (3)    │     (1)     │
3A FAIL    │  CONTENT  │  KRITISCH   │
           │    (2)    │     (0)     │
```

### Aktionen
- **KRITISCH (0):** Takedown + Risk Assessment + Safety Features
- **STRUKTURELL (1):** Risk Assessment + Meldesystem + Elternkontrollen
- **CONTENT (2):** Takedown / Moderation / Anonymisierung
- **COMPLIANT (3):** Keine Aktion

---

## 4. Datenschutz Master-Gate

**Datei:** `data_privacy_gate.yaml`  
**ID:** `data_privacy_gate`  
**Dimension:** `data_privacy_compliance`

### Output-Werte
- **0** = KRITISCH (DSGVO-Verstoß UND Transparenz unzureichend)
- **1** = TRANSPARENZ UNZUREICHEND (KI-Kennzeichnung erforderlich)
- **2** = DSGVO-VERSTOSS (Einwilligung/Rechtsgrundlage erforderlich)
- **3** = COMPLIANT (Datenschutz-konform)

### Komponenten
| Katalog | Indikatoren | Beschreibung |
|---------|-------------|--------------|
| **4A - Profiling & Einwilligung** | 50 | DSGVO-Compliance (Rechtsgrundlage, Betroffenenrechte, Privacy by Design) |
| **4B - Transparenz & KI** | 37 | KI-Kennzeichnung, Recommender-Transparenz, DSA-Compliance |
| **GESAMT** | **87** | Alle Datenschutzprüfungen |

### Logik (2x2 Matrix)
```
                4B PASS     4B FAIL
4A PASS    │ COMPLIANT │ TRANSPARENZ │
           │    (3)    │     (1)     │
4A FAIL    │   DSGVO   │  KRITISCH   │
           │    (2)    │     (0)     │
```

### Aktionen
- **KRITISCH (0):** DSGVO-Compliance + KI-Kennzeichnung + Einwilligung
- **TRANSPARENZ (1):** KI-Kennzeichnung + Recommender-Offenlegung
- **DSGVO (2):** Einwilligung + Betroffenenrechte + Privacy by Design
- **COMPLIANT (3):** Keine Aktion

---

## Gesamtübersicht

### Indikatorenverteilung
```
Bereich                    | a-Katalog | b-Katalog | Gesamt
---------------------------|-----------|-----------|-------
1. Strafrecht              |    49     |    43     |   92
2. Jugendschutz            |    37     |   241     |  278
3. Persönlichkeitsrechte   |    44     |    44     |   88
4. Datenschutz             |    50     |    37     |   87
---------------------------|-----------|-----------|-------
GESAMT                     |   180     |   365     |  545
```

**Hinweis:** Die tatsächliche Gesamtzahl ist 507, da einige Indikatoren aus den Sub-Gates 
in mehreren Master-Gates referenziert werden (z.B. Jugendschutz-Indikatoren in 3B und 4A).

### Output-Modelle

| Master-Gate | Output-Typ | Werte | Bedeutung |
|-------------|------------|-------|-----------|
| **Strafrecht** | 3-stufig | 0, 1, 2 | Illegal / Kontextabhängig / Legal |
| **Jugendschutz** | Altersfreigabe + AVS | 0, 6, 12, 16, 18, 100 | FSK-Freigaben + Jugendgefährdung |
| **Persönlichkeitsrechte** | 2x2 Matrix | 0, 1, 2, 3 | Kombiniert Content + Struktur |
| **Datenschutz** | 2x2 Matrix | 0, 1, 2, 3 | Kombiniert DSGVO + Transparenz |

---

## Performance

### Parallel-Evaluation

Alle Master-Gates evaluieren ihre Sub-Gates parallel:

```
criminal_law_gate
├── 1a_gate (parallel)
│   └── 10 Teilschemas (parallel)
└── 1b_gate (parallel)
    └── 8 Teilschemas (parallel)

protection_of_minors_gate
├── 2a_gate (parallel)
│   └── 6 Teilschemas (parallel)
└── 2b_gate (parallel)
    ├── u6_gate (10 Teilschemas parallel)
    ├── 6_12_gate (10 Teilschemas parallel)
    ├── 12_16_gate (14 Teilschemas parallel)
    └── 16_18_gate (16 Teilschemas parallel)

personal_law_gate
├── 3a_gate (parallel)
│   └── 9 Teilschemas (parallel)
└── 3b_gate (parallel)
    └── 9 Teilschemas (parallel)

data_privacy_gate
├── 4a_gate (parallel)
│   └── 10 Teilschemas (parallel)
└── 4b_gate (parallel)
    └── 7 Teilschemas (parallel)
```

### Geschätzte Laufzeiten (bei MAX_CONCURRENT_LLM_CALLS = 20)

| Master-Gate | Teilschemas | Wellen | Geschätzte Zeit |
|-------------|-------------|--------|-----------------|
| **Strafrecht** | 18 | 1 | ~5-8 Sekunden |
| **Jugendschutz** | 50 | 3 | ~15-20 Sekunden |
| **Persönlichkeitsrechte** | 18 | 1 | ~10-15 Sekunden |
| **Datenschutz** | 17 | 1 | ~12-18 Sekunden |

**Bei vollständiger Evaluation aller 4 Master-Gates parallel:**
- Geschätzte Gesamtzeit: ~20-25 Sekunden (Maximum der vier Gates)

---

## Verwendung in der API

### Einzelnes Master-Gate evaluieren

```python
from evaluator import evaluate_content

# Nur Strafrecht prüfen
result = evaluate_content(
    content="...",
    schemes=["criminal_law_gate"]
)

# Output: 0 (ILLEGAL), 1 (KONTEXTABHÄNGIG), 2 (LEGAL)
```

### Alle vier Master-Gates parallel evaluieren

```python
result = evaluate_content(
    content="...",
    schemes=[
        "criminal_law_gate",
        "protection_of_minors_gate",
        "personal_law_gate",
        "data_privacy_gate"
    ]
)

# Output:
# {
#   "criminal_law_compliance": 2,  # LEGAL
#   "protection_of_minors_compliance": 12,  # FSK 12
#   "personal_law_compliance": 3,  # COMPLIANT
#   "data_privacy_compliance": 1  # TRANSPARENZ UNZUREICHEND
# }
```

### Nur Sub-Gates evaluieren (feinkörniger)

```python
# Nur 1A (Per se illegal) prüfen
result = evaluate_content(
    content="...",
    schemes=["criminal_law_1a_gate"]
)

# Nur 2B-16-18 (16-18 Jahre) prüfen
result = evaluate_content(
    content="...",
    schemes=["protection_of_minors_2b_16_18_gate"]
)
```

---

## Best Practices

### Wann welches Gate verwenden?

**Compliance-Check (vollständig):**
```python
schemes = [
    "criminal_law_gate",
    "protection_of_minors_gate",
    "personal_law_gate",
    "data_privacy_gate"
]
```

**Content-Moderation (schnell):**
```python
schemes = [
    "criminal_law_1a_gate",  # Hard Illegal ausschließen
    "protection_of_minors_2a_gate"  # Jugendgefährdung ausschließen
]
```

**Altersfreigabe ermitteln:**
```python
schemes = ["protection_of_minors_2b_gate"]
```

**Datenschutz-Audit:**
```python
schemes = [
    "data_privacy_4a_gate",  # DSGVO-Basics
    "data_privacy_4b_gate"   # Transparenz
]
```

---

## Migration bestehender Implementierungen

### Vorher (einzelne Sub-Gates)

```python
# Alt: Jedes Sub-Gate einzeln aufrufen
result_1a = evaluate("criminal_law_1a_gate", content)
result_1b = evaluate("criminal_law_1b_gate", content)

if result_1a == 0:
    return "ILLEGAL"
elif result_1b == 0:
    return "KONTEXTABHÄNGIG"
else:
    return "LEGAL"
```

### Nachher (Master-Gate)

```python
# Neu: Ein Master-Gate-Aufruf
result = evaluate("criminal_law_gate", content)

# result ist direkt 0 (ILLEGAL), 1 (KONTEXTABHÄNGIG), 2 (LEGAL)
return result
```

---

## Vorteile der Master-Gates

### ✅ Einfachere API
- Ein Aufruf statt zwei (a + b getrennt)
- Klare Output-Werte (nicht mehr boolesch)
- Bessere Semantik (FSK-Werte statt binär)

### ✅ Konsistente Logik
- Bewertungslogik in YAML (nicht in Code)
- Nachvollziehbar und dokumentiert
- Änderbar ohne Code-Deployment

### ✅ Performance
- Parallel-Evaluation der Sub-Gates
- Maximale Geschwindigkeit durch Concurrency
- Gesamtzeit = Max(Sub-Gate-Zeiten)

### ✅ Flexibilität
- Master-Gates für vollständige Compliance
- Sub-Gates für schnelle Checks
- Part-Schemas für granulare Tests

---

## Zusammenfassung

Die vier Master-Gates bieten eine **einheitliche Schnittstelle** für alle vier Hauptrechtsbereiche:

1. **Strafrecht:** ILLEGAL / KONTEXTABHÄNGIG / LEGAL
2. **Jugendschutz:** FSK-Freigaben + AVS-Pflicht
3. **Persönlichkeitsrechte:** Content- und Struktur-Compliance
4. **Datenschutz:** DSGVO- und Transparenz-Compliance

Insgesamt **507 Indikatoren** in **59 Teilschemas**, organisiert in **8 Sub-Gates** und **4 Master-Gates**.

**Alle Master-Gates sind produktionsbereit und können sofort verwendet werden.**
