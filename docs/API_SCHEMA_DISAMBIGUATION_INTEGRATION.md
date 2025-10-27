# API Integration für Schema-basierte Disambiguation

## Zweck

Dieses Dokument beschreibt, wie die API die neuen Metadatenfelder in YAML-Schemata generisch nutzen kann, um Verwechslungen zwischen ähnlichen Indikatoren zu vermeiden **ohne** domain-spezifische Logik in der API selbst zu implementieren.

---

## Neue Schema-Felder

### 1. `trigger_keywords` (optional, Liste)
**Schlüsselwörter, die zum Triggern des Indikators führen sollten.**

```yaml
trigger_keywords:
  - gewalt
  - kampf
  - brutal
  - krieg
  - katastrophe
  - belastend
```

**Verwendung in der API:**
```python
def calculate_keyword_match_score(input_text: str, indicator: dict) -> float:
    """
    Berechnet einen Match-Score basierend auf trigger_keywords.
    Rückgabe: 0.0 bis 1.0
    """
    if 'trigger_keywords' not in indicator:
        return 0.5  # Neutral, wenn keine Keywords definiert
    
    keywords = indicator['trigger_keywords']
    text_lower = input_text.lower()
    
    matched = sum(1 for kw in keywords if kw in text_lower)
    return matched / len(keywords) if keywords else 0.5
```

### 2. `not_trigger_keywords` (optional, Liste)
**Schlüsselwörter, die GEGEN das Triggern sprechen.**

```yaml
not_trigger_keywords:
  - autoplay
  - voreinstellung
  - default
  - sichtbarkeit
```

**Verwendung in der API:**
```python
def calculate_anti_match_penalty(input_text: str, indicator: dict) -> float:
    """
    Berechnet einen Penalty-Score basierend auf not_trigger_keywords.
    Rückgabe: 0.0 (keine Penalties) bis 1.0 (viele Penalties)
    """
    if 'not_trigger_keywords' not in indicator:
        return 0.0  # Kein Penalty, wenn keine anti-keywords
    
    anti_keywords = indicator['not_trigger_keywords']
    text_lower = input_text.lower()
    
    penalty_hits = sum(1 for kw in anti_keywords if kw in text_lower)
    return penalty_hits / len(anti_keywords) if anti_keywords else 0.0
```

### 3. `evaluation_hint` (optional, String)
**Menschenlesbare Anweisung für die Evaluation.**

```yaml
evaluation_hint: Dieser Indikator prüft TECHNISCHE EINSTELLUNGEN der Plattform,
  nicht den Inhalt selbst. Trigger nur wenn Autoplay, Default-Sichtbarkeit oder
  DM-Einstellungen problematisch sind.
```

**Verwendung in der API:**
```python
def build_llm_prompt_with_hints(indicators: List[dict], input_text: str) -> str:
    """
    Baut einen LLM-Prompt mit evaluation_hints aus den Schemata.
    """
    prompt = f"Evaluate the following content: {input_text}\n\n"
    prompt += "Available indicators:\n\n"
    
    for ind in indicators:
        prompt += f"- {ind['id']}: {ind['description']}\n"
        if 'evaluation_hint' in ind:
            prompt += f"  HINT: {ind['evaluation_hint']}\n"
        prompt += "\n"
    
    return prompt
```

---

## Generischer Disambiguierungs-Algorithmus

### Phase 1: Keyword-basiertes Scoring

```python
def score_indicator_relevance(input_text: str, indicator: dict) -> float:
    """
    Generischer Algorithmus zur Berechnung der Relevanz eines Indikators.
    Keine domain-spezifische Logik - arbeitet rein mit Schema-Metadaten.
    
    Returns: Score zwischen 0.0 (irrelevant) und 1.0 (sehr relevant)
    """
    # Basis-Score: Semantische Ähnlichkeit (LLM)
    base_score = calculate_semantic_similarity(input_text, indicator['description'])
    
    # Bonus für trigger_keywords
    if 'trigger_keywords' in indicator:
        keyword_score = calculate_keyword_match_score(input_text, indicator)
        base_score += keyword_score * 0.3  # 30% Gewichtung
    
    # Penalty für not_trigger_keywords
    if 'not_trigger_keywords' in indicator:
        penalty_score = calculate_anti_match_penalty(input_text, indicator)
        base_score -= penalty_score * 0.5  # 50% Penalty-Gewichtung
    
    # Normalisierung auf 0.0 bis 1.0
    return max(0.0, min(1.0, base_score))
```

### Phase 2: Ranking und Auswahl

```python
def select_relevant_indicators(
    input_text: str, 
    all_indicators: List[dict],
    threshold: float = 0.4
) -> List[dict]:
    """
    Wählt die relevantesten Indikatoren basierend auf Scoring.
    
    Args:
        input_text: Zu evaluierender Inhalt
        all_indicators: Alle verfügbaren Indikatoren aus Schemata
        threshold: Minimum-Score für Relevanz
    
    Returns: Liste der relevanten Indikatoren, sortiert nach Score
    """
    scored_indicators = [
        {
            'indicator': ind,
            'relevance_score': score_indicator_relevance(input_text, ind)
        }
        for ind in all_indicators
    ]
    
    # Filtern nach Threshold
    relevant = [
        item for item in scored_indicators 
        if item['relevance_score'] >= threshold
    ]
    
    # Sortieren nach Score (absteigend)
    relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return [item['indicator'] for item in relevant]
```

### Phase 3: LLM-Evaluation mit Hints

```python
def evaluate_with_hints(
    input_text: str,
    relevant_indicators: List[dict]
) -> Dict[str, bool]:
    """
    Führt die finale LLM-Evaluation durch mit evaluation_hints.
    """
    # Baue Prompt mit hints
    prompt = build_evaluation_prompt(input_text, relevant_indicators)
    
    # LLM-Call
    response = call_llm(prompt)
    
    # Parse Response
    return parse_evaluation_results(response)


def build_evaluation_prompt(
    input_text: str, 
    indicators: List[dict]
) -> str:
    """
    Baut den finalen Evaluation-Prompt mit allen Metadaten aus Schemata.
    """
    prompt = f"""Evaluate the following content for compliance:

INPUT: {input_text}

INDICATORS TO CHECK:
"""
    
    for ind in indicators:
        prompt += f"\n{ind['id']}: {ind['description']}\n"
        prompt += f"  Scope: {ind['scope']}\n"
        prompt += f"  Legal Basis: {ind['legal_basis']}\n"
        
        if 'trigger_keywords' in ind:
            keywords_str = ", ".join(ind['trigger_keywords'])
            prompt += f"  Trigger wenn: {keywords_str}\n"
        
        if 'not_trigger_keywords' in ind:
            anti_keywords_str = ", ".join(ind['not_trigger_keywords'])
            prompt += f"  NICHT trigger wenn: {anti_keywords_str}\n"
        
        if 'evaluation_hint' in ind:
            prompt += f"  WICHTIG: {ind['evaluation_hint']}\n"
        
        prompt += "\n"
    
    prompt += """
For each indicator, determine if it should trigger (true/false).
Return results in JSON format.
"""
    
    return prompt
```

---

## Vollständiges Beispiel

### Eingabe

```python
input_text = "Brutale Kampfszene in einem Onlinevideo"
```

### Schema-Daten (aus YAML geladen)

```python
indicators = [
    {
        'id': '2B-16-35',
        'description': 'Fehlende Minderjährigenschutz-Voreinstellungen...',
        'scope': 'platform',
        'trigger_keywords': ['voreinstellung', 'default', 'autoplay'],
        'not_trigger_keywords': ['gewalt', 'kampf', 'brutal'],
        'evaluation_hint': 'Prüft TECHNISCHE EINSTELLUNGEN, nicht Inhalt'
    },
    {
        'id': '2B-16-39',
        'description': 'Belastende Nachrichten/Dokus ohne Einordnung...',
        'scope': 'both',
        'trigger_keywords': ['gewalt', 'kampf', 'brutal', 'krieg'],
        'not_trigger_keywords': ['autoplay', 'voreinstellung', 'default'],
        'evaluation_hint': 'Prüft INHALTLICHE BELASTUNG'
    }
]
```

### Ablauf

```python
# 1. Scoring
for ind in indicators:
    score = score_indicator_relevance(input_text, ind)
    print(f"{ind['id']}: {score:.2f}")

# Output:
# 2B-16-35: 0.15  (niedrig: nicht_trigger_keywords matchen)
# 2B-16-39: 0.85  (hoch: trigger_keywords matchen)

# 2. Auswahl (threshold=0.4)
relevant = select_relevant_indicators(input_text, indicators, 0.4)
# → nur 2B-16-39 wird ausgewählt

# 3. LLM-Evaluation mit Hints
results = evaluate_with_hints(input_text, relevant)
# → 2B-16-39: triggered=True
# → 2B-16-35: nicht in relevant, daher nicht geprüft
```

---

## API-Implementierung

### 1. Schema-Loader erweitern

```python
def load_schema_with_metadata(schema_path: str) -> dict:
    """
    Lädt YAML-Schema inklusive neuer Metadaten-Felder.
    """
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    # Validiere dass neue Felder optional sind
    for rule in schema.get('gate_rules', []):
        # trigger_keywords, not_trigger_keywords, evaluation_hint
        # sind alle optional - keine Fehler wenn sie fehlen
        pass
    
    return schema
```

### 2. Evaluation-Pipeline anpassen

```python
def evaluate_content(content: str, schemes: List[str]) -> dict:
    """
    Hauptfunktion - komplett generisch, keine domain-spezifische Logik.
    """
    # 1. Lade Schemata
    schemas = [load_schema_with_metadata(s) for s in schemes]
    
    # 2. Extrahiere alle Indikatoren
    all_indicators = []
    for schema in schemas:
        all_indicators.extend(schema.get('gate_rules', []))
    
    # 3. Scoring & Filtering (generisch mit Schema-Metadaten)
    relevant_indicators = select_relevant_indicators(
        content, 
        all_indicators,
        threshold=0.4
    )
    
    # 4. LLM-Evaluation mit Hints
    results = evaluate_with_hints(content, relevant_indicators)
    
    return results
```

---

## Vorteile dieses Ansatzes

### ✅ API bleibt generisch
- Keine domain-spezifische Logik für "Jugendschutz 2b"
- Funktioniert mit beliebigen Prüfkatalogen
- Neue Keywords einfach über YAML hinzufügbar

### ✅ Erweiterbar
- Neue Felder (z.B. `priority`, `conflicts_with`) einfach hinzufügbar
- Keine Code-Änderungen in der API nötig

### ✅ Transparent
- Disambiguation-Logik liegt in den Schemata
- Für Domain-Experten lesbar und änderbar
- Versionskontrolle über Git

### ✅ Testbar
- Unit-Tests mit Mock-Schemata
- Keine Abhängigkeit von echten Prüfkatalogen
- A/B-Tests mit verschiedenen Keywords

---

## Migration bestehender Schemata

### Schritt 1: Identifiziere kritische Indikator-Paare

```bash
# Script zum Finden ähnlicher Indikatoren
python scripts/find_similar_indicators.py
```

### Schritt 2: Füge Metadaten hinzu

Für jedes Paar:
1. `trigger_keywords` für den korrekten Indikator
2. `not_trigger_keywords` für den falschen Indikator
3. `evaluation_hint` für beide

### Schritt 3: Test

```python
# Unit-Test
def test_disambiguation():
    input_text = "Brutale Kampfszene"
    
    # Alte API: 2B-16-35 triggert (FALSCH)
    old_result = old_api_evaluate(input_text)
    assert '2B-16-35' in old_result['triggered']  # FAIL
    
    # Neue API mit Keywords: 2B-16-39 triggert (RICHTIG)
    new_result = new_api_evaluate(input_text)
    assert '2B-16-39' in new_result['triggered']  # PASS
    assert '2B-16-35' not in new_result['triggered']  # PASS
```

---

## Beispiel: Andere Prüfkataloge

Die gleiche Logik funktioniert für **beliebige** Kataloge:

### Beispiel: Datenschutz-Schema

```yaml
- id: GDPR-3.1
  description: Fehlende Einwilligungserklärung für Cookies
  scope: platform
  trigger_keywords:
    - cookie
    - einwilligung
    - consent
    - tracking
  not_trigger_keywords:
    - datenleck
    - breach
    - verlust
  evaluation_hint: Prüft Einwilligungsmechanismen, nicht Datenlecks

- id: GDPR-3.2
  description: Unbefugter Zugriff auf personenbezogene Daten
  scope: both
  trigger_keywords:
    - zugriff
    - datenleck
    - breach
    - verlust
  not_trigger_keywords:
    - cookie
    - consent
    - tracking
  evaluation_hint: Prüft Datensicherheit, nicht Cookie-Banner
```

→ API-Code ist **identisch**, nur Schemata unterscheiden sich!

---

## Zusammenfassung

**API-Änderungen:** Minimal
- Schema-Loader: +3 optionale Felder
- Scoring-Funktion: +50 LOC (generisch)
- Prompt-Builder: +20 LOC (generisch)

**Schema-Änderungen:** Explizit
- 8 kritische Indikatoren erweitert (2b-Kataloge)
- Keywords aus Domain-Expertise definiert
- Evaluation-Hints dokumentiert

**Ergebnis:**
- ✅ Verwechslungen verhindert
- ✅ API bleibt generisch
- ✅ Domain-Logik in Schemata
- ✅ Für andere Kataloge wiederverwendbar
