# Scope-Inkonsistenzen und Verwechslungsgefahren in 2b-Katalogen

## Datum: 2025-10-27

## Zusammenfassung

Nach systematischer Überprüfung aller 41 2b-Prüfkataloge wurden mehrere potenzielle Verwechslungsgefahren identifiziert, bei denen Indikatoren mit ähnlichen Beschreibungen oder Actions unterschiedliche Scopes haben.

## 🔴 KRITISCHE VERWECHSLUNGEN

### 1. "Belastende Nachrichten" vs. "Minderjährigenschutz-Voreinstellungen"

**Problem:** Beide beziehen sich auf "U6/U12/U16/U18-Umfelder", aber haben unterschiedliche Scopes.

#### Belastende Nachrichten/Dokus - Scope: `both`
- **2B-0-39** (U6): "Belastende Nachrichten/Dokus ohne altersangemessene Einordnung/Didaktik in kindgerichteten Umfeldern"
  - Rechtsgrundlage: MStV §19 i.V.m. JMStV §5
  - Scope: `both`
  
- **2B-6-42** (6-12): "Belastende Nachrichten/Dokus ohne altersangemessene Einordnung/Didaktik in U12-Umfeldern"
  - Rechtsgrundlage: MStV §19 i.V.m. JMStV §5
  - Scope: `both`
  
- **2B-12-41** (12-16): "Belastende Nachrichten/Dokus ohne altersangemessene Einordnung/Didaktik in U16-Umfeldern"
  - Rechtsgrundlage: MStV §19 i.V.m. JMStV §5
  - Scope: `both`
  
- **2B-16-39** (16-18): "Belastende Nachrichten/Dokus ohne altersangemessene Einordnung in U18-Umfeldern"
  - Rechtsgrundlage: MStV §19 i.V.m. JMStV §5
  - Scope: `both`

#### Minderjährigenschutz-Voreinstellungen - Scope: `platform`
- **2B-0-33** (U6): "Fehlende geeignete/verhältnismäßige Minderjährigenschutz-Voreinstellungen (Default-Sichtbarkeit/Autoplay/DMs) für U6-Zielgruppen"
  - Rechtsgrundlage: DSA Art.28 Abs.1
  - Scope: `platform`
  
- **2B-6-39** (6-12): "Fehlende geeignete/verhältnismäßige Minderjährigenschutz-Voreinstellungen (Default-Sichtbarkeit/Autoplay/DMs) für 6–12"
  - Rechtsgrundlage: DSA Art.28 Abs.1
  - Scope: `platform`
  
- **2B-12-37** (12-16): "Fehlende geeignete/verhältnismäßige Minderjährigenschutz-Voreinstellungen (Default-Sichtbarkeit/Autoplay/DMs) für 12–16"
  - Rechtsgrundlage: DSA Art.28 Abs.1
  - Scope: `platform`
  
- **2B-16-35** (16-18): "Fehlende geeignete/verhältnismäßige Minderjährigenschutz-Voreinstellungen (Default-Sichtbarkeit/Autoplay/DMs) (16–18)"
  - Rechtsgrundlage: DSA Art.28 Abs.1
  - Scope: `platform`

**Verwechslungsgefahr:** Im aktuellen Prüfergebnis wurde 2B-16-35 (platform) fälschlicherweise für belastende Inhalte getriggert, obwohl 2B-16-39 (both) zuständig gewesen wäre.

**Empfehlung:** 
- Beschreibung der "Voreinstellungen"-Indikatoren präzisieren: "Fehlende technische Voreinstellungen der Plattform (Default-Sichtbarkeit/Autoplay/DMs)"
- Beschreibung der "Belastende Nachrichten"-Indikatoren präzisieren: "Inhaltlich belastende Nachrichten/Dokus ohne Einordnung"

---

## 🟡 MODERATE INKONSISTENZEN

### 2. "Inhaltstrennung" - Inkonsistente Scopes

**Problem:** Die gleiche Action "Inhaltstrennung implementieren" wird mit unterschiedlichen Scopes verwendet.

#### Scope: `content`
- **2B-0-08**: "Entwicklungsbeeinträchtigende Inhalte nicht getrennt von für Kinder bestimmten Angeboten"
  - Scope: `content`
  - Datei: protection_of_minors_2b_u6_part2.yaml
  
- **2B-6-29**: "Sexualdarstellungen setzen jugendferne Perspektive/Erfahrungswissen voraus (Überforderung 6–12)"
  - Scope: `content`
  - Datei: protection_of_minors_2b_6_12_part6.yaml

#### Scope: `platform`
- **2B-6-09**: "Entwicklungsbeeinträchtigende Bereiche nicht getrennt von Kinderbereichen (z. B. Startseite/Kids-Profil)"
  - Scope: `platform`
  - Datei: protection_of_minors_2b_6_12_part2.yaml
  
- **2B-16-09**: "EB-Bereiche nicht getrennt von jugendgeeigneten Bereichen (fehlende Teens/Kids-Profile)"
  - Scope: `platform`
  - Datei: protection_of_minors_2b_16_18_part2.yaml
  
- **2B-16-38**: "VSP ohne altersgerechte Meldesysteme/Elternkontrollen/Jugendprofile (16–18)"
  - Scope: `platform`
  - Datei: protection_of_minors_2b_16_18_part8.yaml
  
- **2B-12-40**: "VSP ohne altersgerechte Meldesysteme/Elternkontrollen/Tools für Jugendprofile (12–16)"
  - Scope: `platform`
  - Datei: protection_of_minors_2b_12_16_part8.yaml

#### Scope: `both`
- **2B-12-10**: "Entwicklungsbeeinträchtigende Bereiche nicht von jugendgeeigneten Bereichen getrennt (z. B. fehlende Teens-/Kids-Profile)"
  - Scope: `both`
  - Datei: protection_of_minors_2b_12_16_part2.yaml
  
- **2B-16-01**: "Angebot geeignet die Entwicklung von Jugendlichen 16–18 zu beeinträchtigen"
  - Scope: `both`
  - Action: "Inhaltstrennung implementieren (Jugend-/Erwachsenenbereich)"
  - Datei: protection_of_minors_2b_16_18_part1.yaml
  
- **2B-12-01**: "Angebot geeignet die Entwicklung von Jugendlichen 12–16 zu beeinträchtigen"
  - Scope: `both`
  - Action: "Inhaltstrennung implementieren (Jugend-/Erwachsenenbereich)"
  - Datei: protection_of_minors_2b_12_16_part1.yaml

**Semantische Inkonsistenz:**
- 2B-0-08 (U6): "Inhalte nicht getrennt" → Scope: `content`
- 2B-6-09 (6-12): "Bereiche nicht getrennt" → Scope: `platform`
- 2B-12-10 (12-16): "Bereiche nicht getrennt" → Scope: `both` ⚠️

**Empfehlung:**
- **Entscheidung treffen:** "Entwicklungsbeeinträchtigende Bereiche nicht getrennt" sollte konsistent entweder `platform` ODER `both` sein
- Vorschlag: `platform`, da es um die Trennung von Bereichen auf der Plattform geht (technische Maßnahme)
- Konsequenz: 2B-12-10 sollte von `both` → `platform` korrigiert werden

---

## 🟢 WEITERE BEOBACHTUNGEN

### 3. Unterschiedliche Actions für ähnliche Verstöße

#### U6 vs. 6-12 Grundlagen
- **2B-0-01** (U6): Action = "Prüfen und bei Verstoß entfernen"
- **2B-6-01** (6-12): Action = "Prüfen und bei Verstoß entfernen"
- **2B-12-01** (12-16): Action = "Inhaltstrennung implementieren"
- **2B-16-01** (16-18): Action = "Inhaltstrennung implementieren"

**Beobachtung:** Für jüngere Altersgruppen (U6, 6-12) ist die Action "entfernen", für ältere (12-16, 16-18) "Inhaltstrennung". Dies ist konsistent und sinnvoll.

---

## EMPFOHLENE KORREKTUREN

### Priorität 1: Kritische Verwechslungen beheben

1. **2B-12-10 Scope korrigieren**
   - Datei: `protection_of_minors_2b_12_16_part2.yaml`
   - Von: `scope: both`
   - Nach: `scope: platform`
   - Begründung: Trennung von Bereichen ist eine Platform-Maßnahme, konsistent mit 2B-6-09 und 2B-16-09

2. **Beschreibungen präzisieren**
   - Alle "Minderjährigenschutz-Voreinstellungen"-Indikatoren: 
     - Zusatz "technische Voreinstellungen der Plattform" in Beschreibung aufnehmen
   - Alle "Belastende Nachrichten"-Indikatoren:
     - Zusatz "Inhaltlich belastende" in Beschreibung aufnehmen

### Priorität 2: Dokumentation verbessern

3. **Scope-Definitionen in README**
   - Klare Definition wann `content`, `platform` oder `both` zu verwenden ist
   - Beispiele für jede Kategorie
   - Entscheidungsbaum für grenzwertige Fälle

---

## TESTFALL: Aktuelles Prüfergebnis

**Input:** "Brutale Kampfszene in einem Onlinevideo"

**Erwartetes Verhalten:**
- ✅ 2B-16-39 sollte triggern (belastende Inhalte ohne Einordnung) - Scope: `both`
- ❌ 2B-16-35 sollte NICHT triggern (Platform-Voreinstellungen) - Scope: `platform`

**Tatsächliches Verhalten:**
- ❌ 2B-16-39 wurde als `passed: true` markiert
- ✅ 2B-16-35 wurde fälschlicherweise getriggert mit Begründung über "belastende Inhalte"

**Ursache:** LLM hat ähnliche Beschreibungen verwechselt und falsche Rule-ID zugeordnet.

---

## NÄCHSTE SCHRITTE

1. ✅ Scope-Analyse durchgeführt
2. ⏳ Korrektur von 2B-12-10 (both → platform)
3. ⏳ Beschreibungen präzisieren
4. ⏳ Test mit korrigierten Katalogen durchführen
5. ⏳ Prompt-Engineering: LLM-Instruktionen für bessere Unterscheidung

---

## METADATEN

- **Analysedatum:** 2025-10-27
- **Analysierte Kataloge:** 41 (3 Gates + 38 Parts)
- **Gefundene kritische Inkonsistenzen:** 1
- **Gefundene moderate Inkonsistenzen:** 1
- **Empfohlene Korrekturen:** 1 Scope-Änderung + Beschreibungspräzisierungen
