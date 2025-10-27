"""
Automatische Annotation von gate_rules mit scope (content/platform).

Dieses Skript analysiert alle Binary Gate Schemas und fügt automatisch
`scope`-Attribute hinzu, um zwischen Content- und Platform-Rules zu unterscheiden.

VERWENDUNG:
    python scripts/annotate_scopes.py

KLASSIFIZIERUNG:
    - Content-Rules: Inhaltliche Bewertung (Gewalt, Sexualität, Thematisierung)
    - Platform-Rules: Metadaten & technische Maßnahmen (FSK, Labels, Kennzeichnung)
    - Both: Unklar oder gemischt

BEISPIEL-OUTPUT:
    ✅ protection_of_minors_2b_u6_part3.yaml
       Content: 1, Platform: 2, Both: 2

HINWEIS:
    - Bereits annotierte Schemas werden übersprungen
    - Backup empfohlen vor erster Ausführung
    - Keywords-basierte Heuristik (siehe PLATFORM_KEYWORDS, CONTENT_KEYWORDS)
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List

# Keywords für Platform-Rules (technische/Meta-Anforderungen)
PLATFORM_KEYWORDS = [
    "fehlend",
    "keine",
    "kein",
    "unzureichend",
    "kennzeichnung",
    "freigabe",
    "altersfreigabe",
    "deskriptor",
    "prüfung",
    "selbstkontrolle",
    "fsk",
    "usk",
    "fsf",
    "jugendschutzprogramm",
    "label",
    "whitelisting",
    "age-de.xml",
    "zeitsteuerung",
    "pin-",
    "profil-barriere",
    "zugangsbeschränkung",
    "maschinenlesbar",
    "inhaltstrennung",
    "kids-mode",
    "elternkontrolle",
    "meldesystem",
    "beschwerdesystem",
    "transparenzbericht",
    "audit",
    "datenzugang",
    "plattform-kennzeichnung",
    "online-kennzeichnung",
    "empfehlungssystem",
    "personalisierte werbung",
    "werbebibliothek",
    "rankingkriterien",
    "voreinstellung",
    "default",
    "kauffunktion",
    "in-app-käufe",
    "lootbox",
    "gacha",
    "endlos-feed",
    "autoplay",
    "streaks",
    "whitelist",
]

# Keywords für Content-Rules (Inhaltsdarstellung)
CONTENT_KEYWORDS = [
    "inhalt",
    "darstellung",
    "gewalt",
    "bedrohlich",
    "ängstigend",
    "sexualisiert",
    "nacktheit",
    "verletzung",
    "blut",
    "konfliktlösung",
    "kampfszene",
    "monster",
    "bedrohung",
    "hilflosigkeit",
    "dauerstress",
    "legitimiert",
    "befürwortet",
    "distanzierung",
    "entwicklungsbeeinträchtigend",
    "thematisierung",
    "rollenbilder",
    "diskriminierung",
    "herabwürdigung",
    "antisozial",
    "sprachlich",
    "obszön",
    "derb",
    "suizid",
    "selbstverletzung",
    "drogen",
    "alkohol",
    "verharmlosung",
    "körperbild",
]


def classify_rule_scope(rule: Dict[str, Any]) -> str:
    """Klassifiziert eine Rule basierend auf ihrer Beschreibung."""
    description = rule.get('description', '').lower()
    
    # Zähle Platform- und Content-Keywords
    platform_score = sum(1 for kw in PLATFORM_KEYWORDS if kw in description)
    content_score = sum(1 for kw in CONTENT_KEYWORDS if kw in description)
    
    # Spezialfälle (hohe Priorität)
    if 'entwicklungsbeeinträchtigend für altersstufe' in description:
        return 'content'  # Inhaltliche Bewertung
    
    if any(kw in description for kw in ['fehlende oder unzutreffende altersfreigabe', 
                                          'keine prüfung durch', 
                                          'fehlende kennzeichnung',
                                          'fehlende deskriptor']):
        return 'platform'  # Metadaten-Anforderung
    
    # Score-basierte Entscheidung
    if platform_score > content_score:
        return 'platform'
    elif content_score > platform_score:
        return 'content'
    else:
        # Default: content (wenn unklar, ist es meist inhaltlich)
        return 'both'


def annotate_schema_file(filepath: Path) -> bool:
    """Annotiert eine Schema-Datei mit scope-Attributen."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Nur Binary Gates haben gate_rules
        if data.get('type') != 'binary_gate':
            return False
        
        gate_rules = data.get('gate_rules', [])
        if not gate_rules:
            return False
        
        # Prüfe ob bereits annotiert
        if any('scope' in rule for rule in gate_rules):
            print(f"  ⏭️  {filepath.name} - bereits annotiert")
            return False
        
        # Annotiere jede Rule
        changes_made = False
        for rule in gate_rules:
            scope = classify_rule_scope(rule)
            rule['scope'] = scope
            changes_made = True
        
        # Schreibe zurück
        if changes_made:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            content_count = sum(1 for r in gate_rules if r.get('scope') == 'content')
            platform_count = sum(1 for r in gate_rules if r.get('scope') == 'platform')
            both_count = sum(1 for r in gate_rules if r.get('scope') == 'both')
            
            print(f"  ✅ {filepath.name}")
            print(f"     Content: {content_count}, Platform: {platform_count}, Both: {both_count}")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ {filepath.name} - Fehler: {e}")
        return False


def main():
    """Hauptfunktion."""
    schemes_dir = Path(__file__).parent.parent / 'schemes'
    
    if not schemes_dir.exists():
        print(f"❌ Schemes-Verzeichnis nicht gefunden: {schemes_dir}")
        return
    
    print(f"🔍 Suche Binary Gate Schemas in: {schemes_dir}\n")
    
    # Finde alle YAML-Dateien
    yaml_files = list(schemes_dir.glob('*.yaml'))
    binary_gates = []
    
    for filepath in yaml_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data.get('type') == 'binary_gate':
                binary_gates.append(filepath)
        except:
            pass
    
    print(f"📊 Gefunden: {len(binary_gates)} Binary Gate Schemas\n")
    
    if not binary_gates:
        print("⚠️  Keine Binary Gate Schemas gefunden!")
        return
    
    # Annotiere alle Schemas
    print("🚀 Starte Annotation...\n")
    annotated_count = 0
    
    for filepath in sorted(binary_gates):
        if annotate_schema_file(filepath):
            annotated_count += 1
    
    print(f"\n✅ Fertig! {annotated_count} von {len(binary_gates)} Schemas annotiert")


if __name__ == '__main__':
    main()
