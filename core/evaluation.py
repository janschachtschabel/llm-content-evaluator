"""Core evaluation engine supporting multiple scale types."""

from typing import Any, Dict, List, Optional, Union
from loguru import logger
import yaml
from pathlib import Path

# Import enums directly to avoid circular imports
from enum import Enum

class ScaleType(str, Enum):
    """Supported evaluation scale types."""
    ORDINAL_RUBRIC = "ordinal_rubric"
    CHECKLIST_ADDITIVE = "checklist_additive"
    BINARY_GATE = "binary_gate"
    DERIVED = "derived"

class SelectionStrategy(str, Enum):
    """Selection strategies for ordinal rubrics."""
    FIRST_MATCH = "first_match"
    BEST_FIT = "best_fit"
    MANUAL = "manual"

class AggregationStrategy(str, Enum):
    """Aggregation strategies for scales."""
    FIRST_MATCH = "first_match"
    WEIGHTED_MEAN = "weighted_mean"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"

class MissingStrategy(str, Enum):
    """Strategies for handling missing values."""
    IGNORE = "ignore"
    ZERO = "zero"
    IMPUTE = "impute"


class EvaluationEngine:
    """Core engine for text evaluation using various scale types."""
    
    def __init__(self, schemes_dir: str = "schemes"):
        self.schemes_dir = Path(schemes_dir)
        self.schemes: Dict[str, Dict[str, Any]] = {}
        self._load_schemes()
    
    def _load_schemes(self) -> None:
        """Load all YAML schemes from directory."""
        if not self.schemes_dir.exists():
            logger.warning(f"Schemes directory {self.schemes_dir} not found")
            return
        
        for yaml_file in self.schemes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    scheme = yaml.safe_load(f)
                    self.schemes[scheme['id']] = scheme
                    logger.info(f"Loaded scheme: {scheme['id']}")
            except Exception as e:
                logger.error(f"Failed to load scheme {yaml_file}: {e}")
    
    def get_schemes(self) -> List[Dict[str, Any]]:
        """Get list of available schemes."""
        return [
            {
                "id": scheme["id"],
                "name": scheme["name"],
                "description": scheme["description"],
                "dimension": scheme["dimension"],
                "scale_type": scheme["type"],
                "output_range": scheme.get("output_range", {}),
                "version": scheme.get("version", "1.0")
            }
            for scheme in self.schemes.values()
        ]
    
    async def evaluate_text(
        self, 
        text: str, 
        scheme_ids: List[str],
        llm_client: Any
    ) -> Dict[str, Any]:
        """Evaluate text using specified schemes."""
        results = []
        gates_passed = True
        
        # Process binary gates first
        for scheme_id in scheme_ids:
            scheme = self.schemes.get(scheme_id)
            if not scheme:
                continue
                
            if scheme["type"] == ScaleType.BINARY_GATE:
                result = await self._evaluate_binary_gate(text, scheme, llm_client)
                results.append(result)
                if result["value"] is False:
                    gates_passed = False
                    break
        
        # If gates failed, return early
        if not gates_passed:
            return {
                "results": results,
                "gates_passed": False,
                "overall_score": None,
                "overall_label": "REJECTED"
            }
        
        # Process other scale types
        for scheme_id in scheme_ids:
            scheme = self.schemes.get(scheme_id)
            if not scheme or scheme["type"] == ScaleType.BINARY_GATE:
                continue
            
            if scheme["type"] == ScaleType.ORDINAL_RUBRIC:
                result = await self._evaluate_ordinal_rubric(text, scheme, llm_client)
            elif scheme["type"] == ScaleType.CHECKLIST_ADDITIVE:
                result = await self._evaluate_checklist_additive(text, scheme, llm_client)
            elif scheme["type"] == ScaleType.DERIVED:
                result = await self._evaluate_derived(text, scheme, llm_client)
            else:
                continue
                
            results.append(result)
        
        # Calculate overall metrics
        overall_score, overall_label = self._calculate_overall(results)
        
        return {
            "results": results,
            "gates_passed": gates_passed
        }
    
    async def _evaluate_binary_gate(
        self, 
        text: str, 
        scheme: Dict[str, Any], 
        llm_client: Any
    ) -> Dict[str, Any]:
        """Evaluate binary gate (KO criteria)."""
        prompt = self._build_gate_prompt(text, scheme)
        
        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Parse structured response
            passed = None
            reasoning = "No evaluation found"
            
            for line in content.split('\n'):
                if line.strip().startswith('RESULT:'):
                    result_part = line.split(':', 1)[1].strip().upper()
                    passed = result_part in ['JA', 'YES', 'TRUE']
                elif line.strip().startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # Calculate overall pass/fail based on individual aspects
            gate_rules = scheme.get('gate_rules', [])
            all_aspects_passed = True
            
            if gate_rules:
                for i, rule in enumerate(gate_rules, 1):
                    # Look for ASPEKT_X pattern in response
                    for line in content.split('\n'):
                        if line.strip().startswith(f'ASPEKT_{i}:'):
                            parts = line.split(':', 1)[1].strip()
                            response_part = parts.split(' - ')[0] if ' - ' in parts else parts
                            # NEIN = kein Verstoß = BESTANDEN (inverted logic for gates)
                            aspect_passed = response_part.strip().upper() in ['NEIN', 'NO', 'FALSE']
                            if not aspect_passed:
                                all_aspects_passed = False
                            break
                
                passed = all_aspects_passed
            else:
                # Fallback parsing for overall result
                if passed is None:
                    content_lower = content.lower()
                    passed = "ja" in content_lower or "yes" in content_lower or "true" in content_lower
            
            reasoning = content.strip()
            
            # Parse individual aspects from gate rules
            gate_rules = scheme.get('gate_rules', [])
            criteria_results = {}
            
            if gate_rules:
                for i, rule in enumerate(gate_rules, 1):
                    aspect_key = f"aspekt_{i}"
                    aspect_passed = True  # Default to pass
                    aspect_reasoning = "Keine spezifische Bewertung gefunden"
                    
                    # Look for ASPEKT_X pattern in response
                    for line in content.split('\n'):
                        if line.strip().startswith(f'ASPEKT_{i}:'):
                            parts = line.split(':', 1)[1].strip()
                            if ' - ' in parts:
                                response_part, aspect_reasoning = parts.split(' - ', 1)
                                # NEIN = kein Verstoß = BESTANDEN (inverted logic for gates)
                                aspect_passed = response_part.strip().upper() in ['NEIN', 'NO', 'FALSE']
                            break
                    
                    criteria_results[aspect_key] = {
                        "passed": aspect_passed,
                        "reasoning": aspect_reasoning,
                        "rule": rule.get('reason', rule.get('condition', 'Unbekannter Aspekt')),
                        "severity": rule.get('severity', 'unbekannt')
                    }
            
            # Enhanced reasoning for binary gates - extract only main reasoning
            main_reasoning = ""
            if "REASONING:" in reasoning:
                # Extract the first REASONING section only
                reasoning_parts = reasoning.split("REASONING:")
                if len(reasoning_parts) > 1:
                    main_reasoning = reasoning_parts[1].split("\n")[0].strip()
            
            if not main_reasoning:
                # Fallback: use first few sentences of content
                sentences = reasoning.replace("\n", " ").split(". ")
                main_reasoning = ". ".join(sentences[:2]) + "." if sentences else "Bewertung durchgeführt."
            
            enhanced_reasoning = f"**Ergebnis:** {'BESTANDEN' if passed else 'NICHT BESTANDEN'}\n\n**Begründung:** {main_reasoning}"
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": 1 if passed else 0,
                "label": "PASS" if passed else "FAIL",
                "reasoning": enhanced_reasoning,
                "criteria": criteria_results if criteria_results else None,
                "scale_info": {
                    "type": "binary_gate",
                    "description": scheme.get("description", ""),
                    "criteria": scheme.get("criteria", ""),
                    "total_aspects": len(gate_rules)
                },
                "confidence": 0.9 if passed is not None else 0.6
            }
        except Exception as e:
            logger.error(f"Binary gate evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_ordinal_rubric(
        self, 
        text: str, 
        scheme: Dict[str, Any], 
        llm_client: Any
    ) -> Dict[str, Any]:
        """Evaluate using ordinal rubric with anchors."""
        prompt = self._build_rubric_prompt(text, scheme)
        
        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # Parse structured response
            score = None
            label = None
            reasoning = "No evaluation found"
            
            for line in content.split('\n'):
                if line.strip().startswith('SCORE:'):
                    try:
                        score = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.strip().startswith('LABEL:'):
                    label = line.split(':', 1)[1].strip()
                elif line.strip().startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # Fallback to anchor matching if structured parsing failed
            if score is None:
                if scheme.get("selection_strategy") == SelectionStrategy.FIRST_MATCH:
                    result = self._match_first_anchor(content, scheme)
                else:
                    result = self._match_best_anchor(content, scheme)
                score = result.get("value")
                label = result.get("label")
                reasoning = content.strip()
            
            # Find matching anchor for label if not parsed
            if label is None and score is not None:
                for anchor in scheme.get('anchors', []):
                    if anchor['value'] == score:
                        label = anchor['label']
                        break
            
            # Enhanced reasoning for ordinal rubrics
            enhanced_reasoning = f"**Bewertung:** Level {score} - {label}\n\n**Begründung:** {reasoning}"
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": score,
                "label": label or "Unknown",
                "reasoning": enhanced_reasoning,
                "scale_info": {
                    "type": "ordinal_rubric",
                    "range": scheme.get("output_range", {}),
                    "anchors": len(scheme.get('anchors', [])),
                    "levels": [f"{a['value']}: {a['label']}" for a in scheme.get('anchors', [])]
                },
                "confidence": 0.8 if score is not None else 0.6
            }
            
        except Exception as e:
            logger.error(f"Ordinal rubric evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_checklist_additive(
        self, 
        text: str, 
        scheme: Dict[str, Any], 
        llm_client: Any
    ) -> Dict[str, Any]:
        """Evaluate using additive checklist."""
        prompt = self._build_checklist_prompt(text, scheme)
        
        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Parse checklist responses and calculate weighted score
            score, criterion_results = self._calculate_checklist_score(content, scheme)
            
            # Generate detailed LLM reasoning
            reasoning_prompt = f"""
Erstellen Sie eine ausführliche Bewertung für die Dimension '{scheme.get('dimension', 'quality')}' basierend auf folgenden Einzelkriterien:

{chr(10).join([f"- {item.get('prompt', item.get('id', ''))}: Level {criterion_results.get(item.get('id', ''), {}).get('response', 'unbekannt')}" for item in scheme.get('items', [])])}

Gesamtscore: {score:.2f} von {scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 5.0)}

Erstellen Sie eine zusammenhängende, ausführliche Bewertung (2-3 Sätze), die die wichtigsten Stärken und Schwächen erklärt.
"""
            
            try:
                reasoning_response = await llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": reasoning_prompt}],
                    temperature=0.3
                )
                detailed_reasoning = reasoning_response.choices[0].message.content.strip()
            except Exception:
                # Fallback to simple reasoning
                percentage = (score / scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 5.0)) * 100
                dimension_name = scheme.get('dimension', 'quality').title()
                detailed_reasoning = f"Bewertung für {dimension_name}: {percentage:.0f}% der möglichen Punkte erreicht."
            
            # Build scale info from first item's values
            first_item = scheme.get('items', [{}])[0] if scheme.get('items') else {}
            scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
            raw_values = first_item.get('values', {})
            
            # Convert values to proper format for scale_info
            scale_values = {}
            for k, v in raw_values.items():
                if k == "na":
                    scale_values["na"] = None
                else:
                    scale_values[str(k)] = v
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": round(score, 2),
                "label": self._score_to_label(score, scheme),
                "confidence": 0.8,
                "reasoning": detailed_reasoning,
                "scale_info": {
                    "raw_range": "0.0-1.0",
                    "normalized_range": f"0.0-{scale_factor}",
                    "values": scale_values
                },
                "criteria": criterion_results
            }
            
        except Exception as e:
            logger.error(f"Checklist evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_derived(
        self, 
        text: str,
        scheme: Dict[str, Any],
        llm_client: Any
    ) -> Dict[str, Any]:
        """Evaluate derived metric based on dependency schemas."""
        try:
            # Get dependencies and evaluate them first
            dependencies = scheme.get("dependencies", [])
            if not dependencies:
                return {
                    "scheme_id": scheme["id"],
                    "dimension": scheme["dimension"],
                    "value": None,
                    "na_reason": "No dependencies defined"
                }
            
            # Evaluate all dependency schemas
            dependency_results = []
            for dep_scheme_id in dependencies:
                dep_scheme = self.schemes.get(dep_scheme_id)
                if not dep_scheme:
                    continue
                    
                if dep_scheme["type"] == ScaleType.CHECKLIST_ADDITIVE:
                    result = await self._evaluate_checklist_additive(text, dep_scheme, llm_client)
                elif dep_scheme["type"] == ScaleType.ORDINAL_RUBRIC:
                    result = await self._evaluate_ordinal_rubric(text, dep_scheme, llm_client)
                elif dep_scheme["type"] == ScaleType.BINARY_GATE:
                    result = await self._evaluate_binary_gate(text, dep_scheme, llm_client)
                else:
                    continue
                    
                dependency_results.append(result)
            
            # Apply derivation rules
            rules = scheme.get("rules", [])
            logger.info(f"Checking {len(rules)} rules for scheme {scheme['id']}")
            logger.info(f"Dependency results: {[(dep.get('scheme_id'), dep.get('dimension'), dep.get('value')) for dep in dependency_results]}")
            
            for rule in rules:
                conditions = rule.get("conditions", [])
                logger.info(f"Checking rule conditions: {conditions}")
                
                conditions_met = self._check_rule_conditions(dependency_results, conditions)
                logger.info(f"Rule conditions met: {conditions_met}")
                
                if conditions_met:
                    logger.info(f"Applying rule with value: {rule['value']}")
                    if rule["value"] == "weighted_average":
                        # Calculate weighted average
                        weights = rule.get("weights", {})
                        total_weighted_score = 0
                        total_weight = 0
                        
                        for dep_result in dependency_results:
                            dimension = dep_result.get("dimension")
                            value = dep_result.get("value")
                            weight = weights.get(dimension, 1.0)
                            
                            if value is not None and isinstance(value, (int, float)):
                                total_weighted_score += value * weight
                                total_weight += weight
                        
                        final_score = total_weighted_score / total_weight if total_weight > 0 else 0
                        
                        # Build comprehensive reasoning
                        detailed_reasoning = self._build_derived_reasoning(dependency_results, final_score, weights, rule)
                        
                        return {
                            "scheme_id": scheme["id"],
                            "dimension": scheme["dimension"],
                            "value": round(final_score, 2),
                            "label": self._score_to_label(final_score, scheme),
                            "reasoning": detailed_reasoning,
                            "confidence": rule.get("confidence", 0.9),
                            "scale_info": {
                                "type": "derived",
                                "method": "weighted_average",
                                "dependencies": len(dependencies),
                                "weights": weights
                            },
                            "criteria": {
                                dep["scheme_id"]: {
                                    "dimension": dep["dimension"],
                                    "value": dep.get("value"),
                                    "label": dep.get("label"),
                                    "weight": weights.get(dep.get("dimension"), 1.0),
                                    "reasoning": dep.get("reasoning", "").split('\n')[0] if dep.get("reasoning") else "Keine Begründung verfügbar"
                                }
                                for dep in dependency_results if dep.get("value") is not None
                            }
                        }
                    else:
                        # Static rule value - build detailed reasoning for binary compliance
                        detailed_reasoning = self._build_compliance_reasoning(dependency_results, rule)
                        
                        return {
                            "scheme_id": scheme["id"],
                            "dimension": scheme["dimension"],
                            "value": rule["value"],
                            "label": rule["label"],
                            "reasoning": detailed_reasoning,
                            "confidence": rule.get("confidence", 0.9),
                            "scale_info": {
                                "type": "derived",
                                "method": "rule_based",
                                "dependencies": len(dependencies),
                                "conditions": rule.get("conditions", [])
                            },
                            "criteria": {
                                dep["scheme_id"]: {
                                    "dimension": dep["dimension"],
                                    "value": dep.get("value"),
                                    "label": dep.get("label"),
                                    "passed": dep.get("value") == 1 if isinstance(dep.get("value"), int) else True,
                                    "reasoning": dep.get("reasoning", "").split('\n')[0] if dep.get("reasoning") else "Keine Begründung verfügbar"
                                }
                                for dep in dependency_results if dep.get("value") is not None
                            }
                        }
            
            # Default if no rules match - build detailed reasoning for failed compliance
            default = scheme.get("default", {})
            detailed_reasoning = self._build_compliance_reasoning(dependency_results, default)
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": default.get("value", 0.0),
                "label": default.get("label", "Unbewertet"),
                "reasoning": detailed_reasoning,
                "confidence": default.get("confidence", 0.0),
                "scale_info": {
                    "type": "derived",
                    "method": "rule_based",
                    "dependencies": len(dependencies),
                    "conditions": "default_fallback"
                },
                "criteria": {
                    dep["scheme_id"]: {
                        "dimension": dep["dimension"],
                        "value": dep.get("value"),
                        "label": dep.get("label"),
                        "passed": dep.get("value") == 1 if isinstance(dep.get("value"), int) else True,
                        "reasoning": dep.get("reasoning", "").split('\n')[0] if dep.get("reasoning") else "Keine Begründung verfügbar"
                    }
                    for dep in dependency_results if dep.get("value") is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Derived evaluation failed: {e}")
            logger.error(f"Dependencies: {dependencies}")
            logger.error(f"Dependency results: {[{k: v for k, v in dep.items() if k in ['scheme_id', 'dimension', 'value', 'label']} for dep in dependency_results]}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Derivation error: {str(e)}"
            }
    
    def _build_derived_reasoning(self, dependency_results, final_score, weights, rule):
        """Build detailed reasoning for weighted average derived schemas."""
        reasoning_parts = [f"**Gewichteter Durchschnitt:** {final_score:.2f}/5.0\n"]
        
        reasoning_parts.append("**Einzelbewertungen:**")
        for dep in dependency_results:
            if dep.get("value") is not None:
                dimension = dep.get("dimension", "unknown")
                value = dep.get("value")
                label = dep.get("label", "")
                weight = weights.get(dimension, 1.0)
                reasoning_parts.append(f"- {dimension}: {value} ({label}) × Gewicht {weight}")
        
        reasoning_parts.append(f"\n**Gesamtbewertung:** {rule.get('reasoning', 'Berechnung abgeschlossen')}")
        return "\n".join(reasoning_parts)
    
    def _build_compliance_reasoning(self, dependency_results, rule):
        """Build detailed reasoning for compliance-based derived schemas."""
        passed_count = 0
        failed_gates = []
        
        reasoning_parts = [f"**Rechtliche Compliance-Prüfung:**\n"]
        
        for dep in dependency_results:
            gate_name = dep.get("scheme_id", "unknown")
            value = dep.get("value")
            label = dep.get("label", "")
            
            if value == 1:
                passed_count += 1
                reasoning_parts.append(f"✅ {gate_name}: BESTANDEN ({label})")
            else:
                failed_gates.append(gate_name)
                reasoning_parts.append(f"❌ {gate_name}: NICHT BESTANDEN ({label})")
        
        if failed_gates:
            reasoning_parts.append(f"\n**Ergebnis:** NON_COMPLIANCE - {len(failed_gates)} von {len(dependency_results)} Prüfungen nicht bestanden")
            reasoning_parts.append(f"**Fehlgeschlagene Gates:** {', '.join(failed_gates)}")
        else:
            reasoning_parts.append(f"\n**Ergebnis:** COMPLIANCE - Alle {len(dependency_results)} rechtlichen Prüfungen bestanden")
        
        reasoning_parts.append(f"\n**Fazit:** {rule.get('reasoning', 'Compliance-Prüfung abgeschlossen')}")
        return "\n".join(reasoning_parts)
    
    def _build_gate_prompt(self, text: str, scheme: Dict[str, Any]) -> str:
        """Build prompt for binary gate evaluation."""
        # Extract gate rules for structured evaluation
        gate_rules = scheme.get('gate_rules', [])
        rules_text = ""
        if gate_rules:
            rules_text = "\n\nPrüfen Sie jeden der folgenden Aspekte einzeln:\n"
            for i, rule in enumerate(gate_rules, 1):
                rules_text += f"{i}. {rule.get('reason', rule.get('condition', 'Unbekannter Aspekt'))} (Schwere: {rule.get('severity', 'unbekannt')})\n"
            rules_text += "\nGeben Sie für jeden Aspekt eine Bewertung ab:"
        
        return f"""
Prüfen Sie diesen Text für: {scheme['description']}

Text: {text}

Prüfkriterien: {scheme.get('criteria', 'Prüfen Sie, ob der Inhalt die Gate-Anforderungen erfüllt')}
{rules_text}

Geben Sie Ihre Bewertung in diesem Format an:
RESULT: [JA/NEIN]
REASONING: [Kurze Erklärung der Entscheidung auf Deutsch in maximal 4-5 Sätzen]

{f"Bewerten Sie jeden Aspekt einzeln mit ASPEKT_[NUMMER]: [JA/NEIN] - [Begründung]" if gate_rules else ""}

Beispiel:
RESULT: NEIN
REASONING: Der Text enthält unangemessene Inhalte, die gegen Jugendschutzrichtlinien verstoßen.
{f"ASPEKT_1: NEIN - Verstößt gegen § 130 StGB (Volksverhetzung)" if gate_rules else ""}
"""
    
    def _build_rubric_prompt(self, text: str, scheme: Dict[str, Any]) -> str:
        """Build prompt for ordinal rubric evaluation."""
        anchors_text = "\n".join([
            f"Level {anchor['value']}: {anchor['label']} - {anchor['description']}"
            for anchor in scheme.get('anchors', [])
        ])
        
        return f"""
Bewerten Sie diesen Text anhand der folgenden Rubrik für {scheme['dimension']}:

{anchors_text}

Text: {text}

Geben Sie Ihre Bewertung in diesem Format an:
SCORE: [Level-Nummer]
LABEL: [Level-Bezeichnung]
REASONING: [Kurze Erklärung auf Deutsch in maximal 4-5 Sätzen, warum dieses Level gewählt wurde]

Beispiel:
SCORE: 2
LABEL: Ausreichend
REASONING: Der Text zeigt einige Hinweise auf die Kriterien, aber es fehlt an Tiefe und Vollständigkeit.
"""
    
    def _build_checklist_prompt(self, text: str, scheme: Dict[str, Any]) -> str:
        """Build prompt for checklist evaluation."""
        items_text = []
        for i, item in enumerate(scheme.get('items', []), 1):
            item_text = f"{i}. {item['prompt']} (ID: {item['id']}, Weight: {item['weight']})\n"
            
            # Add scale information from YAML
            values = item.get('values', {})
            if values:
                item_text += "   Bewertungsskala:\n"
                # Filter and sort only numeric keys first
                numeric_items = [(k, v) for k, v in values.items() if isinstance(k, int) and v is not None]
                for level, value_data in sorted(numeric_items):
                    if isinstance(value_data, dict):
                        # New format with score and description
                        score = value_data.get('score', 0)
                        description = value_data.get('description', f'Level {level}')
                        item_text += f"   {level}: {score} - {description}\n"
                    else:
                        # Old format with just numeric value
                        item_text += f"   {level}: {value_data} - Level {level}\n"
            items_text.append(item_text)
        
        return f"""
Bewerten Sie diesen Text anhand der folgenden Checkliste für {scheme['dimension']}:

{''.join(items_text)}

Text: {text}

Für jedes Kriterium geben Sie Ihre Bewertung in diesem exakten Format an:
[KRITERIUM_ID]: [LEVEL_NUMMER] - [Kurze Begründung auf Deutsch]

Beispiel:
perspektivenvielfalt: 1 - Es wird nur eine Perspektive dargestellt
neutrale_beschreibung: 2 - Enthält einige voreingenommene Elemente

Nach der Bewertung aller Kriterien geben Sie eine kurze Zusammenfassung der Gesamtbewertung.
"""
    
    def _match_first_anchor(self, content: str, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Match content to first applicable anchor."""
        # Simple keyword matching - could be enhanced with LLM parsing
        for anchor in scheme.get('anchors', []):
            if str(anchor['value']) in content or anchor['label'].lower() in content.lower():
                return {
                    "value": anchor['value'],
                    "label": anchor['label'],
                    "confidence": 0.8
                }
        
        return {"value": None, "na_reason": "No matching anchor found"}
    
    def _match_best_anchor(self, content: str, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Match content to best fitting anchor."""
        # Placeholder for more sophisticated matching
        return self._match_first_anchor(content, scheme)
    
    def _calculate_checklist_score(
        self, 
        content: str, 
        scheme: Dict[str, Any]
    ) -> tuple[float, Dict[str, Any]]:
        """Calculate weighted score from checklist responses."""
        items = scheme.get('items', [])
        total_weight = 0
        weighted_score = 0
        criterion_results = {}
        
        # Parse structured responses using the new format
        content_lines = content.split('\n')
        
        for item in items:
            weight = item.get('weight', 1.0)
            values = item.get('values', {})
            item_id = item.get('id', '')
            
            # Look for structured format: "item_id: [LEVEL_NUMBER] - reasoning"
            item_score = None
            item_response = "UNCLEAR"
            reasoning = "No evaluation found"
            
            for line in content_lines:
                if line.strip().startswith(f"{item_id}:"):
                    # Parse structured line
                    parts = line.split(':', 1)[1].strip()
                    if ' - ' in parts:
                        response_part, reasoning = parts.split(' - ', 1)
                        response_part = response_part.strip()
                    else:
                        response_part = parts.strip()
                    
                    # Parse numeric level from YAML values
                    try:
                        level = int(response_part)
                        if level in values:
                            item_response = str(level)
                            # Handle both old format (float) and new format (dict with score)
                            value_data = values[level]
                            if isinstance(value_data, dict) and 'score' in value_data:
                                item_score = value_data['score']
                            else:
                                item_score = value_data
                        else:
                            # Fallback to closest valid level
                            valid_levels = [k for k in values.keys() if isinstance(k, int)]
                            if valid_levels:
                                closest_level = min(valid_levels, key=lambda x: abs(int(x) - level))
                                item_response = str(closest_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[closest_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                    except ValueError:
                        # Handle non-numeric responses as fallback
                        response_upper = response_part.upper()
                        if response_upper in ['JA', 'YES', 'TRUE']:
                            # Map to highest level
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                max_level = max(int_keys)
                                item_response = str(max_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[max_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                        elif response_upper in ['NEIN', 'NO', 'FALSE']:
                            # Map to lowest level
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                min_level = min(int_keys)
                                item_response = str(min_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[min_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                        else:
                            item_response = "UNCLEAR"
                            item_score = values.get('na', 0.5)
                    break
            
            # Fallback parsing if structured format not found
            if item_score is None:
                item_section = ""
                for i, line in enumerate(content_lines):
                    if item_id in line.lower():
                        item_section = '\n'.join(content_lines[i:i+3])
                        break
                
                if item_section:
                    # Try to extract numeric levels from context
                    import re
                    level_matches = re.findall(r'\b([1-4])\b', item_section)
                    
                    if level_matches:
                        # Use first found level
                        level = int(level_matches[0])
                        if level in values:
                            # Handle both old format (float) and new format (dict with score)
                            value_data = values[level]
                            if isinstance(value_data, dict) and 'score' in value_data:
                                item_score = value_data['score']
                            else:
                                item_score = value_data
                            item_response = str(level)
                            reasoning = "Inferred from context"
                    else:
                        # Fallback to sentiment analysis
                        yes_count = item_section.lower().count('yes') + item_section.lower().count('ja')
                        no_count = item_section.lower().count('no') + item_section.lower().count('nein')
                        
                        if no_count > yes_count and no_count > 0:
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                min_level = min(int_keys)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[min_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                                item_response = str(min_level)
                                reasoning = "Inferred from context (negative)"
                        elif yes_count > no_count and yes_count > 0:
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                max_level = max(int_keys)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[max_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                                item_response = str(max_level)
                                reasoning = "Inferred from context (positive)"
            
            # Store detailed criterion result
            if item_score is not None:
                weighted_score += item_score * weight
                total_weight += weight
                
                # Normalize individual score to output scale for user understanding
                scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
                normalized_score = item_score * scale_factor
                
                criterion_results[item_id] = {
                    "name": item.get('prompt', item_id),
                    "response": item_response,
                    "normalized_score": round(normalized_score, 2),
                    "weight": weight,
                    "reasoning": reasoning.strip()
                }
            else:
                # Handle missing evaluation
                missing_strategy = scheme.get('aggregator', {}).get('params', {}).get('missing', 'ignore')
                if missing_strategy != 'ignore':
                    total_weight += weight
                
                criterion_results[item_id] = {
                    "name": item.get('prompt', item_id),
                    "response": "UNCLEAR",
                    "normalized_score": None,
                    "weight": weight,
                    "reasoning": "No evaluation found"
                }
        
        # Calculate base score (0-1 range)
        base_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Apply scale factor for normalization (e.g., 0-1 to 0-5)
        scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
        final_score = base_score * scale_factor
        
        return final_score, criterion_results
    
    def _score_to_label(self, score: float, scheme: Dict[str, Any]) -> str:
        """Convert numeric score to label using German labels from YAML."""
        labels = scheme.get('labels', {})
        if not labels:
            return "Unknown"
        
        # Sort thresholds in descending order and find first match
        try:
            for threshold_str, label in sorted(labels.items(), key=lambda x: float(x[0]), reverse=True):
                threshold = float(threshold_str)
                if score >= threshold:
                    return label
            
            # Fallback to lowest label if score is below all thresholds
            lowest_threshold = min(labels.keys(), key=lambda x: float(x))
            return labels[lowest_threshold]
        except (ValueError, TypeError) as e:
            # Handle any conversion errors
            return "Unknown"
    
    def _check_rule_conditions(
        self, 
        results: List[Dict[str, Any]], 
        conditions: List[Dict[str, Any]]
    ) -> bool:
        """Check if derivation rule conditions are met."""
        for condition in conditions:
            dimension = condition.get('dimension')
            operator = condition.get('operator', '>=')
            threshold = condition.get('value')
            
            result = next((r for r in results if r.get('dimension') == dimension), None)
            if not result or result.get('value') is None:
                return False
            
            value = result['value']
            if operator == '>=' and value >= threshold:
                continue
            elif operator == '>' and value > threshold:
                continue
            elif operator == '<=' and value <= threshold:
                continue
            elif operator == '<' and value < threshold:
                continue
            elif operator == '==' and value == threshold:
                continue
            else:
                return False
        
        return True
    
    def _calculate_overall(self, results: List[Dict[str, Any]]) -> tuple[Optional[float], Optional[str]]:
        """Calculate overall score and label using YAML labels from first scheme."""
        valid_results = [r for r in results if r.get('value') is not None and isinstance(r['value'], (int, float))]
        
        if not valid_results:
            return None, None
        
        overall_score = sum(r['value'] for r in valid_results) / len(valid_results)
        
        # Use label from first scheme's YAML labels
        first_result = valid_results[0]
        if 'label' in first_result:
            # Use the same label mapping logic as individual results
            overall_label = first_result['label']  # This uses YAML labels
        else:
            overall_label = "Unknown"
        
        return overall_score, overall_label
