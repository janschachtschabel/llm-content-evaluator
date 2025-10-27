# Changelog

## [Unreleased] - 2025-10-27

### Added
- **Context-Awareness System** für differenzierte Bewertung von UGC vs. kommerziellen Plattformen
  - Neuer `context_type` Parameter in API (`content`, `platform`, `both`)
  - Automatische Klassifizierung von Rules in `content` und `platform` Scopes
  - 119 von 120 Binary Gate Schemas mit Scope-Annotationen versehen
  
- **Scope-Annotation-Skript** (`scripts/annotate_scopes.py`)
  - Automatische Analyse und Annotation aller Binary Gate Schemas
  - Keyword-basierte Klassifizierung von Content- vs. Platform-Rules
  - Unterstützt Batch-Verarbeitung und Skip-Logic für bereits annotierte Schemas

### Changed
- **API-Modell** (`models/schemas.py`)
  - `EvaluationRequest` erweitert um `context_type` Parameter (Default: "content")
  
- **Evaluation Engine** (`core/evaluation.py`)
  - `_build_gate_prompt()` filtert Rules basierend auf Context
  - `evaluate_text()` propagiert `context_type` durch gesamte Pipeline
  - Rekursive Unterstützung für verschachtelte Derived Schemas
  
- **API Routes** (`api/routes/evaluate.py`)
  - `/evaluate` Endpoint nutzt `context_type` aus Request
  
- **README.md**
  - Neue Sektion "Context-Awareness" mit Beispielen
  - Aktualisierte Feature-Liste (120+ Schemas, neue Rechtsgrundlagen)
  - Dokumentation der drei Context-Modi

### Impact
**Vorher:** UGC-Inhalte wurden fälschlicherweise wegen fehlender FSK-Labels abgelehnt
```json
{
  "violations": 5,  // FSK, Kennzeichnung, Deskriptoren, etc.
  "result": "FSK 18"
}
```

**Nachher:** Nur inhaltliche Bewertung bei `context_type="content"`
```json
{
  "violations": 1,  // Nur: Gewaltdarstellung entwicklungsbeeinträchtigend
  "result": "FSK 16"  // Korrekte Einstufung!
}
```

### Removed
- Test-Skripte (`test_context.py`, `scripts/test_context_awareness.py`)

### Technical Details
- Keywords für Platform-Rules: `fehlend`, `keine`, `kennzeichnung`, `freigabe`, `fsk`, `usk`, etc.
- Keywords für Content-Rules: `gewalt`, `darstellung`, `bedrohlich`, `sexualisiert`, etc.
- Default bei unklarer Klassifizierung: `both` (sicherer Fallback)
