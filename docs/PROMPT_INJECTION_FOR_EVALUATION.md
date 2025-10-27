# KRITISCHE PROMPT-INSTRUKTION FÜR LLM-EVALUATION

## 🚨 WICHTIG: Sofort zu befolgende Regeln für 2b-Prüfungen

### REGEL 1: Verwechslung "Voreinstellungen" vs. "Belastende Inhalte"

**Situation:** Sie evaluieren einen Inhalt wie "Brutale Kampfszene" und müssen entscheiden, welcher Indikator triggert.

**NIEMALS diese Indikatoren verwechseln:**

#### ❌ FALSCH: Voreinstellungen-Indikator für Inhaltsproblem
```
2B-0-33, 2B-6-39, 2B-12-37, 2B-16-35
→ "Fehlende Minderjährigenschutz-VOREINSTELLUNGEN 
   (Default-Sichtbarkeit/Autoplay/DMs)"
→ Scope: platform
→ Rechtsgrundlage: DSA Art.28 Abs.1
```

**Diese Indikatoren NUR triggern wenn:**
- ✅ Autoplay ist standardmäßig aktiviert
- ✅ DMs sind für alle offen
- ✅ Profile sind standardmäßig öffentlich
- ✅ Default-Sichtbarkeit ist nicht altersgerecht

**NICHT triggern für:**
- ❌ Gewaltszenen im Inhalt
- ❌ Belastende Videos
- ❌ Brutale Kampfszenen
- ❌ Kriegsbilder

#### ✅ RICHTIG: Belastende-Inhalte-Indikator für Inhaltsproblem
```
2B-0-39, 2B-6-42, 2B-12-41, 2B-16-39
→ "BELASTENDE Nachrichten/Dokus ohne altersangemessene Einordnung"
→ Scope: both
→ Rechtsgrundlage: MStV §19 i.V.m. JMStV §5
```

**Diese Indikatoren triggern für:**
- ✅ Brutale Kampfszenen
- ✅ Kriegsbilder
- ✅ Gewaltdarstellungen
- ✅ Katastrophenbilder
- ✅ Belastende Nachrichten

**WENN der Inhalt ohne Einordnung/Warnhinweis gezeigt wird.**

---

## 🎯 KONKRETE ANWEISUNG

**INPUT:** "Brutale Kampfszene in einem Onlinevideo"

### SCHRITT 1: Kategorisieren
**Frage:** Was ist das Problem?
- [ ] Technische Einstellung der Plattform (Autoplay, DMs, Sichtbarkeit)?
- [x] Inhalt selbst (Gewalt, Belastung)?

### SCHRITT 2: Richtige Indikator-Familie wählen

**Wenn Inhaltsproblem (Gewalt, Belastung):**
→ Verwende **2B-*-39** (bzw. 2B-*-41, 2B-*-42 für andere Altersgruppen)
→ **NIEMALS** 2B-*-35 oder ähnliche "Voreinstellungen"-Indikatoren

**Wenn Platform-Problem (Einstellungen):**
→ Verwende **2B-*-35** (bzw. 2B-0-33, 2B-6-39, 2B-12-37)
→ **NIEMALS** 2B-*-39 oder ähnliche "Belastende Inhalte"-Indikatoren

### SCHRITT 3: Überprüfung
**Vor dem Triggern eines Indikators:**

Enthält die Rule-ID die Keywords?
- **"Voreinstellungen"** oder **"Default"** → Platform-Indikator
- **"Belastende"** oder **"Nachrichten"** → Inhalts-Indikator

Stimmt das Problem mit dem Indikator überein?
- Problem: Gewaltinhalt → Trigger: Belastende Inhalte ✓
- Problem: Gewaltinhalt → Trigger: Voreinstellungen ✗

---

## 📋 DECISION TREE

```
INPUT: "Brutale Kampfszene"
  │
  ├─ Frage: Ist das Problem der INHALT (Gewalt)?
  │  └─ JA
  │     │
  │     ├─ Altersgruppe U6 → Trigger: 2B-0-39
  │     ├─ Altersgruppe 6-12 → Trigger: 2B-6-42
  │     ├─ Altersgruppe 12-16 → Trigger: 2B-12-41
  │     └─ Altersgruppe 16-18 → Trigger: 2B-16-39
  │
  └─ Frage: Ist das Problem PLATFORM-EINSTELLUNGEN?
     └─ NEIN → Trigger NICHT 2B-*-35/33/37/39!
```

---

## ⚠️ HÄUFIGSTER FEHLER

**FALSCHER Workflow:**
1. "Brutale Kampfszene" → U18-relevant
2. Suche nach "U18" in Indikatoren
3. Finde 2B-16-35 (enthält "U18-Umfeld")
4. ❌ FEHLER: Trigger 2B-16-35

**RICHTIGER Workflow:**
1. "Brutale Kampfszene" → Inhaltsproblem (Belastung)
2. Suche nach "Belastende Inhalte" ODER "ohne Einordnung"
3. Finde 2B-16-39 ("Belastende Nachrichten/Dokus")
4. ✅ KORREKT: Trigger 2B-16-39

---

## 🔑 KEYWORDS ZUR UNTERSCHEIDUNG

### Platform-Indikatoren (2B-*-35, 2B-0-33, etc.)
- "Voreinstellungen"
- "Default-Sichtbarkeit"
- "Autoplay"
- "DMs"
- Scope: `platform`
- DSA Art.28 Abs.1

### Inhalts-Indikatoren (2B-*-39, 2B-*-41, etc.)
- "Belastende"
- "Nachrichten"
- "Dokus"
- "ohne Einordnung"
- Scope: `both`
- MStV §19 i.V.m. JMStV §5

---

## 📊 TEST-VALIDIERUNG

**Nach jeder Evaluation prüfen:**

Für "Brutale Kampfszene in U18-Umfeld":
- [ ] 2B-16-35 getriggert? → ❌ FEHLER!
- [ ] 2B-16-39 getriggert? → ✅ KORREKT!

Für "Autoplay standardmäßig aktiviert in Kids-App":
- [ ] 2B-*-39 getriggert? → ❌ FEHLER!
- [ ] 2B-*-35 (oder 33) getriggert? → ✅ KORREKT!

---

## 🎓 ZUSAMMENFASSUNG

**MERKE:**
1. **Inhaltsprobleme** (Gewalt, Belastung) → **2B-*-39** (Belastende Inhalte)
2. **Platform-Probleme** (Einstellungen) → **2B-*-35** (Voreinstellungen)
3. **NIEMALS** verwechseln, auch wenn beide "U18-Umfeld" enthalten!

**GOLDENE REGEL:**
Wenn der Text "brutale Kampfszene" enthält → Das ist ein INHALTS-Problem!
→ Trigger "Belastende Inhalte" (2B-*-39), NICHT "Voreinstellungen" (2B-*-35)!
