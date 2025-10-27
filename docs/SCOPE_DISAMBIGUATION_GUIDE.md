# Scope-Unterscheidungsleitfaden für LLM-Evaluierung

## Zweck
Dieses Dokument dient als Referenz für LLMs bei der Evaluation von Inhalten nach den 2b-Prüfkatalogen, um Verwechslungen zwischen ähnlich klingenden Indikatoren mit unterschiedlichen Scopes zu vermeiden.

---

## 🎯 SCOPE-DEFINITIONEN

### `content` - Inhaltsbezogen
**Wann verwenden:** Der Verstoß liegt im Inhalt selbst (Text, Bild, Video, Audio).
- ✅ Gewaltdarstellungen
- ✅ Sexualisierte Inhalte  
- ✅ Ängstigende Szenen
- ✅ Diskriminierende Sprache
- ✅ Verharmlosung von Drogen

**Maßnahmen:** Inhalt anpassen, entfernen, Warnhinweise

### `platform` - Plattformbezogen
**Wann verwenden:** Der Verstoß liegt in den technischen/organisatorischen Maßnahmen der Plattform.
- ✅ Fehlende Altersverifikation
- ✅ Keine Jugendschutzprogramm-Signalisierung
- ✅ Fehlende Zeitsteuerung
- ✅ Keine Inhaltstrennung (Kids-/Teens-Profile)
- ✅ Fehlende Voreinstellungen (Default-Sichtbarkeit, Autoplay)
- ✅ Keine Elternkontrollen

**Maßnahmen:** Technische Schutzmaßnahmen, Jugendschutzprogramme, Altersfreigaben

### `both` - Beides
**Wann verwenden:** Der Verstoß betrifft sowohl Inhalt ALS AUCH Platform-Maßnahmen.
- ✅ Entwicklungsbeeinträchtigung allgemein (Inhalt + fehlende Zugangsbeschränkung)
- ✅ Werbung nicht gekennzeichnet (Inhalt selbst + Platform-Kennzeichnung)
- ✅ Riskante Challenges (Inhalt + fehlende Warnhinweise)
- ✅ Belastende Nachrichten ohne Einordnung (Inhalt + Platform-Präsentation)

---

## ⚠️ HÄUFIGE VERWECHSLUNGEN

### 1. Belastende Inhalte vs. Platform-Voreinstellungen

#### ❌ FALSCH: Platform-Indikator für Content-Problem
```yaml
Inhalt: "Brutale Kampfszene"
Fehler: 2B-16-35 getriggert 
  → "Fehlende Minderjährigenschutz-Voreinstellungen"
  → Scope: platform
```

#### ✅ RICHTIG: Both-Indikator für Content-Problem
```yaml
Inhalt: "Brutale Kampfszene"
Korrekt: 2B-16-39 triggern
  → "Belastende Nachrichten/Dokus ohne Einordnung"
  → Scope: both
```

**Unterscheidungsmerkmal:**
- **Voreinstellungen (platform)**: Betrifft technische Default-Einstellungen (Sichtbarkeit, Autoplay, DMs)
- **Belastende Inhalte (both)**: Betrifft tatsächliche Inhalte (Gewalt, Nachrichten, Dokus)

### 2. Inhaltstrennung - Bereiche vs. Inhalte

#### U6: "Inhalte nicht getrennt" → `content`
```yaml
2B-0-08: "Entwicklungsbeeinträchtigende Inhalte nicht getrennt 
          von für Kinder bestimmten Angeboten"
Scope: content
Beispiel: Ein U18-Film wird in der Kids-App-Sektion angezeigt
```

#### 6-12, 12-16, 16-18: "Bereiche nicht getrennt" → `platform`
```yaml
2B-6-09: "Entwicklungsbeeinträchtigende Bereiche nicht getrennt 
          von Kinderbereichen (z.B. Startseite/Kids-Profil)"
Scope: platform
Beispiel: Keine Kids-Mode oder Profil-Trennung vorhanden
```

**Unterscheidungsmerkmal:**
- **"Inhalte"** → Einzelne Videos/Texte → `content`
- **"Bereiche"** → Sections/Profile/Modi → `platform`

---

## 📋 ENTSCHEIDUNGSBAUM

```
Frage 1: Liegt der Verstoß im Inhalt selbst?
├─ JA: Ist eine technische Maßnahme ZUSÄTZLICH erforderlich?
│  ├─ JA → Scope: both
│  └─ NEIN → Scope: content
└─ NEIN: Betrifft es Platform-Funktionen/-Einstellungen?
   └─ JA → Scope: platform
```

### Beispiele zum Entscheidungsbaum

#### Beispiel 1: Gewaltszene
```
Inhalt selbst problematisch? → JA
Technische Maßnahme zusätzlich nötig? → JA (Zugangsbeschränkung)
→ Scope: both
```

#### Beispiel 2: Fehlende Altersverifikation
```
Inhalt selbst problematisch? → NEIN (Inhalt könnte OK sein)
Platform-Funktion betroffen? → JA
→ Scope: platform
```

#### Beispiel 3: Diskriminierende Sprache
```
Inhalt selbst problematisch? → JA
Technische Maßnahme zusätzlich nötig? → NEIN (Sprache muss angepasst werden)
→ Scope: content
```

---

## 🔍 INDIKATOR-PAARE ZUM UNTERSCHEIDEN

### Paar 1: U18-Umfelder

| Indikator | Beschreibung | Scope | Rechtsgrundlage | Kontext |
|-----------|-------------|-------|----------------|---------|
| **2B-16-35** | Fehlende Minderjährigenschutz-**Voreinstellungen** (Default-Sichtbarkeit/Autoplay/DMs) | `platform` | DSA Art.28 Abs.1 | Technische Einstellungen |
| **2B-16-39** | **Belastende Nachrichten**/Dokus ohne Einordnung in U18-Umfeldern | `both` | MStV §19 i.V.m. JMStV §5 | Inhaltliche Belastung |

**Trigger-Kriterien:**
- 2B-16-35: Wenn Default-Einstellungen (Autoplay, Sichtbarkeit, DMs) nicht kindgerecht sind
- 2B-16-39: Wenn tatsächliche Inhalte (Gewalt, Krieg, Katastrophen) ohne Einordnung gezeigt werden

### Paar 2: 12-16-Umfelder

| Indikator | Beschreibung | Scope | Rechtsgrundlage | Kontext |
|-----------|-------------|-------|----------------|---------|
| **2B-12-37** | Fehlende Minderjährigenschutz-**Voreinstellungen** (Default-Sichtbarkeit/Autoplay/DMs) | `platform` | DSA Art.28 Abs.1 | Technische Einstellungen |
| **2B-12-41** | **Belastende Nachrichten**/Dokus ohne Einordnung in U16-Umfeldern | `both` | MStV §19 i.V.m. JMStV §5 | Inhaltliche Belastung |

### Paar 3: 6-12-Umfelder

| Indikator | Beschreibung | Scope | Rechtsgrundlage | Kontext |
|-----------|-------------|-------|----------------|---------|
| **2B-6-39** | Fehlende Minderjährigenschutz-**Voreinstellungen** (Default-Sichtbarkeit/Autoplay/DMs) | `platform` | DSA Art.28 Abs.1 | Technische Einstellungen |
| **2B-6-42** | **Belastende Nachrichten**/Dokus ohne Einordnung in U12-Umfeldern | `both` | MStV §19 i.V.m. JMStV §5 | Inhaltliche Belastung |

### Paar 4: U6-Umfelder

| Indikator | Beschreibung | Scope | Rechtsgrundlage | Kontext |
|-----------|-------------|-------|----------------|---------|
| **2B-0-33** | Fehlende Minderjährigenschutz-**Voreinstellungen** (Default-Sichtbarkeit/Autoplay/DMs) | `platform` | DSA Art.28 Abs.1 | Technische Einstellungen |
| **2B-0-39** | **Belastende Nachrichten**/Dokus ohne Einordnung in kindgerichteten Umfeldern | `both` | MStV §19 i.V.m. JMStV §5 | Inhaltliche Belastung |

---

## 📝 EVALUIERUNGS-CHECKLISTE

Bei der Prüfung eines Inhalts:

1. **Identifiziere zuerst das Kernproblem:**
   - [ ] Ist der Inhalt selbst problematisch? (Gewalt, Sex, Angst, etc.)
   - [ ] Oder fehlen technische Schutzmaßnahmen der Plattform?
   - [ ] Oder beides?

2. **Suche nach Schlüsselwörtern:**
   - **Platform-Indikatoren:** "Voreinstellungen", "Default", "Autoplay", "Sichtbarkeit", "DMs", "Jugendschutzprogramm", "Altersverifikation", "Zeitsteuerung", "Profile"
   - **Content-Indikatoren:** "Gewalt", "Angst", "Sexual", "Diskriminierung", "Verharmlosung", "Inhalte"
   - **Both-Indikatoren:** "Belastende Nachrichten", "Entwicklungsbeeinträchtigung", "ohne Einordnung", "Werbung nicht gekennzeichnet"

3. **Prüfe die Rechtsgrundlage:**
   - **DSA Art.28** → meist `platform` (Voreinstellungen, Schutzmaßnahmen)
   - **MStV §19 i.V.m. JMStV §5** → meist `both` (belastende Inhalte + Einordnung)
   - **JMStV §5 Abs.1** → meist `both` oder `content` (Entwicklungsbeeinträchtigung)
   - **JuSchG §10b** → meist `content` (Inhalte selbst)
   - **JuSchG §14** → meist `platform` (Kennzeichnung, Freigabe)

4. **Vergleiche mit ähnlichen Indikatoren:**
   - Gibt es einen ähnlich klingenden Indikator mit anderem Scope?
   - Wenn ja, prüfe die Unterscheidungsmerkmale oben

---

## 🧪 TESTFÄLLE

### Testfall 1: Brutale Kampfszene
```
Input: "Brutale Kampfszene in einem Onlinevideo"

Korrekte Evaluation:
✅ Triggern: 2B-16-39 (Belastende Inhalte, scope: both)
❌ Nicht triggern: 2B-16-35 (Voreinstellungen, scope: platform)

Begründung: Der Inhalt selbst (Kampfszene) ist problematisch, 
nicht die Platform-Voreinstellungen.
```

### Testfall 2: Autoplay aktiviert
```
Input: "Platform hat standardmäßig Autoplay für alle Videos aktiviert, 
       auch in Kids-Profilen"

Korrekte Evaluation:
✅ Triggern: 2B-0-33, 2B-6-39, 2B-12-37, 2B-16-35 
            (je nach Altersgruppe, alle scope: platform)
❌ Nicht triggern: 2B-*-39/41/42 (Belastende Inhalte)

Begründung: Technische Voreinstellung der Platform, 
nicht der Inhalt selbst.
```

### Testfall 3: Kriegsdoku ohne Kontext
```
Input: "Dokumentation über Kriegsgeschehen mit Frontaufnahmen, 
       keine Einordnung für jugendliches Publikum"

Korrekte Evaluation:
✅ Triggern: 2B-16-39 (Belastende Nachrichten/Dokus, scope: both)
Evtl. auch: 2B-16-72 (Kriegs-Dokus eingeordnet)

Begründung: Inhaltlich belastend UND fehlende Einordnung = both
```

---

## 🔄 VERSION HISTORY

- **v1.0** (2025-10-27): Erste Version nach Scope-Analyse
  - Identifizierung der 4 Indikator-Paare (Voreinstellungen vs. Belastende Inhalte)
  - Korrektur von 2B-12-10 (both → platform)

---

## 📌 ZUSAMMENFASSUNG FÜR LLM-PROMPTS

**Wichtigste Regel:** 
Wenn ein Indikator mit "Voreinstellungen" / "Default" / "Autoplay" / "DMs" zu tun hat 
→ Das ist `platform` (2B-*-35, 2B-*-37, 2B-*-39, 2B-0-33)

Wenn ein Indikator mit "Belastende Nachrichten/Dokus" zu tun hat
→ Das ist `both` (2B-*-39, 2B-*-41, 2B-*-42, 2B-0-39)

**Niemals verwechseln!**
